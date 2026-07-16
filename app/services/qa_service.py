from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Any, Dict

from app.repositories.connection_repository import ConnectionRepository
from app.repositories.metadata_repository import MetadataRepository
from app.repositories.relationship_repository import RelationshipRepository
from app.repositories.search_repository import SearchRepository
from app.repositories.ai_provider_repository import AIProviderRepository
from app.llm.factory import get_llm_provider
from app.llm.base import ToolDefinition
from app.core.security import decrypt_password
from app.schemas.qa_schema import QARequest, QAResponse

SYSTEM_PROMPT = (
    "You are a data engineering assistant answering questions about a database's schema. "
    "Use the provided tools to look up real tables, columns, and relationships before "
    "answering — never assume a table or column exists without checking with a tool first. "
    "Call as many tools as you need, in whatever order makes sense, following relationships "
    "to related tables if that helps answer the question. If the tools don't turn up enough "
    "information to answer, say so explicitly rather than guessing."
)

# Provider-agnostic tool definitions (Phase 2, Step 4) — the model decides
# which of these to call, and in what order, instead of being handed a
# pre-filtered static context dump (Step 2's now-retired approach). Backed
# by the same catalog repositories Step 2 used internally — only *how* the
# model consumes them changed, not where the data comes from.
TOOLS: list[ToolDefinition] = [
    {
        "name": "list_tables",
        "description": "List every table in this connection's synced metadata catalog (names only, no columns). Use this first for an overview if you don't know where to start.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "search_tables",
        "description": "Search table names for a keyword (case-insensitive substring match).",
        "parameters": {
            "type": "object",
            "properties": {"keyword": {"type": "string", "description": "Keyword to search table names for."}},
            "required": ["keyword"],
        },
    },
    {
        "name": "search_columns",
        "description": "Search column names and data types for a keyword (case-insensitive substring match). Returns which table each match belongs to.",
        "parameters": {
            "type": "object",
            "properties": {"keyword": {"type": "string", "description": "Keyword to search column names/types for."}},
            "required": ["keyword"],
        },
    },
    {
        "name": "get_table_columns",
        "description": "Get all columns (name, data type, nullability) for a specific table.",
        "parameters": {
            "type": "object",
            "properties": {
                "table_name": {"type": "string", "description": "Exact table name."},
                "schema_name": {
                    "type": "string",
                    "description": "PostgreSQL schema containing the table. Omit if unsure — matches across all schemas will be returned.",
                },
            },
            "required": ["table_name"],
        },
    },
    {
        "name": "get_relationships",
        "description": "Get foreign key relationships involving a specific table, as either the source or the target of the relationship.",
        "parameters": {
            "type": "object",
            "properties": {
                "table_name": {"type": "string", "description": "Exact table name."},
                "schema_name": {
                    "type": "string",
                    "description": "PostgreSQL schema containing the table. Omit if unsure.",
                },
            },
            "required": ["table_name"],
        },
    },
]


class QAService:
    """
    Answers natural-language questions about a connection's schema using the
    active LLM provider (Phase 2, Step 3) via adaptive tool-calling
    (Phase 2, Step 4) — the model decides which tools to call, and how many
    times, instead of receiving a pre-filtered static context dump
    (Step 2's retired approach). Tools are backed by the same catalog
    repositories Step 1/2 already used.

    Only providers with supports_tool_calling=True (OpenAI, Groq) can serve
    /ask today — see LLMProvider.generate_with_tools()'s docstring.
    """

    def __init__(self, db: Session):
        self.db = db
        self.conn_repo = ConnectionRepository(db)
        self.meta_repo = MetadataRepository(db)
        self.rel_repo = RelationshipRepository(db)
        self.search_repo = SearchRepository(db)
        self.provider_repo = AIProviderRepository(db)

    def _execute_tool(self, connection_id: int, name: str, arguments: Dict[str, Any]) -> str:
        """Dispatches one tool call to the catalog repositories and formats a text result."""

        if name == "list_tables":
            tables = self.meta_repo.get_tables_by_connection(connection_id)
            if not tables:
                return "No tables found in the catalog. Has this connection been synced via POST /metadata/refresh?"
            return "\n".join(f"{t.schema_name}.{t.table_name}" for t in tables)

        if name == "search_tables":
            keyword = arguments.get("keyword", "")
            matches = self.search_repo.search_tables(keyword, connection_id)
            if not matches:
                return f"No tables matched '{keyword}'."
            return "\n".join(f"{t.schema_name}.{t.table_name}" for t in matches)

        if name == "search_columns":
            keyword = arguments.get("keyword", "")
            matches = self.search_repo.search_columns(keyword, connection_id)
            if not matches:
                return f"No columns matched '{keyword}'."
            return "\n".join(
                f"{c.table.schema_name}.{c.table.table_name}.{c.column_name}: {c.data_type}"
                for c in matches
            )

        if name == "get_table_columns":
            table_name = arguments.get("table_name", "")
            schema_name = arguments.get("schema_name")
            tables = [
                t for t in self.meta_repo.get_tables_by_connection(connection_id)
                if t.table_name == table_name and (schema_name is None or t.schema_name == schema_name)
            ]
            if not tables:
                return f"No table named '{table_name}' found" + (f" in schema '{schema_name}'." if schema_name else ".")
            lines = []
            for t in tables:
                lines.append(f"{t.schema_name}.{t.table_name}:")
                for col in self.meta_repo.get_columns_by_table(t.id):
                    nullable = "" if col.is_nullable else " NOT NULL"
                    lines.append(f"  {col.column_name}: {col.data_type}{nullable}")
            return "\n".join(lines)

        if name == "get_relationships":
            table_name = arguments.get("table_name", "")
            schema_name = arguments.get("schema_name")
            matches = [
                r for r in self.rel_repo.get_by_connection(connection_id)
                if (r.source_table == table_name or r.target_table == table_name)
                and (schema_name is None or schema_name in (r.source_schema, r.target_schema))
            ]
            if not matches:
                return f"No relationships found involving table '{table_name}'."
            return "\n".join(
                f"{r.source_schema}.{r.source_table}.{r.source_column} -> "
                f"{r.target_schema}.{r.target_table}.{r.target_column}"
                for r in matches
            )

        return f"Unknown tool: {name}"

    def ask(self, connection_id: int, request: QARequest) -> QAResponse:
        if not self.conn_repo.get_by_id(connection_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Database connection with ID {connection_id} not found."
            )

        # Every AI task uses whichever provider is active (Phase 2, Step 3) —
        # no per-request override. Switch via PATCH /ai/providers/{id}/activate.
        provider_config = self.provider_repo.get_active()
        if not provider_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active AI provider. Register one via POST /ai/providers, "
                       "or activate one via PATCH /ai/providers/{id}/activate."
            )

        llm = get_llm_provider(
            provider_config.provider,
            decrypt_password(provider_config.api_key),
            provider_config.default_model,
        )

        if not llm.supports_tool_calling:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"The active provider ('{provider_config.provider}') doesn't support "
                       f"tool-calling yet. Activate an OpenAI or Groq provider for /ask."
            )

        def tool_executor(name: str, arguments: Dict[str, Any]) -> str:
            return self._execute_tool(connection_id, name, arguments)

        try:
            answer = llm.generate_with_tools(request.question, SYSTEM_PROMPT, TOOLS, tool_executor)
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
