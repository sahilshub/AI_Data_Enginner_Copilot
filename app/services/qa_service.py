from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.repositories.connection_repository import ConnectionRepository
from app.repositories.metadata_repository import MetadataRepository
from app.repositories.relationship_repository import RelationshipRepository
from app.repositories.ai_provider_repository import AIProviderRepository
from app.llm.factory import get_llm_provider
from app.core.security import decrypt_password
from app.schemas.qa_schema import QARequest, QAResponse

SYSTEM_PROMPT_TEMPLATE = """You are a data engineering assistant. Answer the user's question using \
ONLY the database schema information provided below — don't assume tables or columns that aren't \
listed. If the schema doesn't contain enough information to answer, say so explicitly.

{schema_context}
"""


class QAService:
    """
    Answers natural-language questions about a connection's schema using a
    registered LLM provider (Phase 2, Step 1).

    Context assembly here is deliberately naive — a full dump of every
    table/column/relationship stored for the connection. That doesn't scale
    past a modest schema size; selecting a relevant subset is Phase 2, Step
    2's explicit job, not this one's (see docs/phase-2/step-1.md's
    "Next Step"). This step only wires up the end-to-end path.
    """

    def __init__(self, db: Session):
        self.db = db
        self.conn_repo = ConnectionRepository(db)
        self.meta_repo = MetadataRepository(db)
        self.rel_repo = RelationshipRepository(db)
        self.provider_repo = AIProviderRepository(db)

    def _build_schema_context(self, connection_id: int) -> str:
        tables = self.meta_repo.get_tables_by_connection(connection_id)
        columns_by_table = self.meta_repo.get_columns_by_connection(connection_id)
        relationships = self.rel_repo.get_by_connection(connection_id)

        lines = ["Tables:"]
        for table in tables:
            lines.append(f"- {table.schema_name}.{table.table_name}")
            for col in columns_by_table.get(table.id, []):
                nullable = "" if col.is_nullable else " NOT NULL"
                lines.append(f"    {col.column_name}: {col.data_type}{nullable}")

        if relationships:
            lines.append("\nRelationships:")
            for r in relationships:
                lines.append(
                    f"- {r.source_schema}.{r.source_table}.{r.source_column} -> "
                    f"{r.target_schema}.{r.target_table}.{r.target_column}"
                )

        return "\n".join(lines)

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

        schema_context = self._build_schema_context(connection_id)
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(schema_context=schema_context)

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
