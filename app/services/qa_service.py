import re
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Dict, List, Tuple

from app.repositories.connection_repository import ConnectionRepository
from app.repositories.metadata_repository import MetadataRepository
from app.repositories.relationship_repository import RelationshipRepository
from app.repositories.search_repository import SearchRepository
from app.repositories.ai_provider_repository import AIProviderRepository
from app.models.schema_table import SchemaTable
from app.llm.factory import get_llm_provider
from app.core.security import decrypt_password
from app.schemas.qa_schema import QARequest, QAResponse

# Hard ceiling on how many tables can ever end up in a prompt's context,
# regardless of how many keywords match. This — not the keyword matching
# itself — is what actually guarantees /ask can't blow past a provider's
# request-size limit the way the Step 1 full-dump approach did (a live
# 413 from Groq against this project's own 90-table test schema).
MAX_TABLES_IN_CONTEXT = 20

# Final defense-in-depth: truncate the assembled context text itself,
# independent of table count, in case even MAX_TABLES_IN_CONTEXT tables'
# worth of columns turns out to be unexpectedly large.
MAX_CONTEXT_CHARS = 12000

# Naive on purpose — this is substring/keyword matching against the
# existing pg_trgm-indexed search (Phase 1, Step 7), not semantic search.
# Real relevance ranking is RAG (Phase 7 in the original roadmap); pulling
# that in now would mean building embeddings/vector storage two phases
# early to solve a problem this simpler approach already fixes well enough.
_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "which", "what", "where", "when", "who", "whom", "how", "why",
    "of", "in", "on", "at", "for", "to", "from", "by", "with", "about",
    "and", "or", "not", "do", "does", "did", "has", "have", "had",
    "table", "tables", "column", "columns", "database", "schema",
    "store", "stores", "stored", "contain", "contains", "show", "list",
    "me", "us", "my", "our", "this", "that", "these", "those",
}


class QAService:
    """
    Answers natural-language questions about a connection's schema using a
    registered LLM provider (Phase 2, Step 1), with context bounded and
    keyword-targeted via the existing search infrastructure rather than a
    full catalog dump (Phase 2, Step 2 — see docs/phase-2/step-2.md for why
    this replaced Step 1's original naive approach).
    """

    def __init__(self, db: Session):
        self.db = db
        self.conn_repo = ConnectionRepository(db)
        self.meta_repo = MetadataRepository(db)
        self.rel_repo = RelationshipRepository(db)
        self.search_repo = SearchRepository(db)
        self.provider_repo = AIProviderRepository(db)

    @staticmethod
    def _extract_keywords(question: str) -> List[str]:
        words = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", question.lower())
        # dict.fromkeys instead of set() to preserve first-seen order —
        # doesn't change correctness, just makes which tables get picked
        # first (when over MAX_TABLES_IN_CONTEXT) deterministic per question.
        return list(dict.fromkeys(w for w in words if len(w) > 2 and w not in _STOPWORDS))

    def _select_relevant_tables(
        self, connection_id: int, question: str
    ) -> Tuple[List[SchemaTable], bool]:
        """
        Returns (selected_tables, used_fallback). Searches tables and
        columns for each keyword extracted from the question, unions the
        matches, and caps at MAX_TABLES_IN_CONTEXT. If nothing matches
        (vague question, or terminology absent from the schema), falls back
        to a bounded, arbitrary slice rather than the old "everything"
        behavior — flagged via used_fallback so the system prompt can tell
        the model this view may be incomplete.
        """
        matched: Dict[int, SchemaTable] = {}

        for keyword in self._extract_keywords(question):
            for table in self.search_repo.search_tables(keyword, connection_id):
                matched[table.id] = table
            for column in self.search_repo.search_columns(keyword, connection_id):
                matched[column.table.id] = column.table
            if len(matched) >= MAX_TABLES_IN_CONTEXT:
                break

        if matched:
            return list(matched.values())[:MAX_TABLES_IN_CONTEXT], False

        fallback_tables = self.meta_repo.get_tables_by_connection(connection_id)[:MAX_TABLES_IN_CONTEXT]
        return fallback_tables, True

    def _build_schema_context(self, connection_id: int, question: str) -> Tuple[str, bool]:
        """Returns (context_text, used_fallback)."""
        tables, used_fallback = self._select_relevant_tables(connection_id, question)
        table_names = {t.table_name for t in tables}

        lines = ["Tables:"]
        for table in tables:
            lines.append(f"- {table.schema_name}.{table.table_name}")
            for col in self.meta_repo.get_columns_by_table(table.id):
                nullable = "" if col.is_nullable else " NOT NULL"
                lines.append(f"    {col.column_name}: {col.data_type}{nullable}")

        # Only relationships touching a selected table — not the whole
        # connection's relationship set.
        relationships = [
            r for r in self.rel_repo.get_by_connection(connection_id)
            if r.source_table in table_names or r.target_table in table_names
        ]
        if relationships:
            lines.append("\nRelationships:")
            for r in relationships:
                lines.append(
                    f"- {r.source_schema}.{r.source_table}.{r.source_column} -> "
                    f"{r.target_schema}.{r.target_table}.{r.target_column}"
                )

        context = "\n".join(lines)
        if len(context) > MAX_CONTEXT_CHARS:
            context = context[:MAX_CONTEXT_CHARS] + "\n... (truncated — schema context exceeded size limit)"

        return context, used_fallback

    def ask(self, connection_id: int, request: QARequest) -> QAResponse:
        if not self.conn_repo.get_by_id(connection_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Database connection with ID {connection_id} not found."
            )

        if request.provider_id is not None:
            provider_config = self.provider_repo.get_by_id(request.provider_id)
            if not provider_config:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"AI provider config with ID {request.provider_id} not found."
                )
        else:
            provider_config = self.provider_repo.get_most_recent()
            if not provider_config:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No AI provider is registered yet. Register one via POST /ai/providers first."
                )

        llm = get_llm_provider(
            provider_config.provider,
            decrypt_password(provider_config.api_key),
            provider_config.default_model,
        )

        schema_context, used_fallback = self._build_schema_context(connection_id, request.question)

        system_prompt = (
            "You are a data engineering assistant. Answer the user's question using ONLY the "
            "database schema information provided below — don't assume tables or columns that "
            "aren't listed. If the schema doesn't contain enough information to answer, say so "
            "explicitly.\n\n"
        )
        if used_fallback:
            system_prompt += (
                "NOTE: no tables matched keywords from the question, so this is only a partial, "
                "arbitrary slice of the full schema, not a targeted match — say so if it doesn't "
                "contain what's needed.\n\n"
            )
        system_prompt += schema_context

        try:
            answer = llm.generate(request.question, system=system_prompt)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to get a response from {provider_config.provider}: {str(e)}"
            )

        return QAResponse(
            answer=answer,
            provider=provider_config.provider,
            model=llm.model,
        )
