from sqlalchemy import create_engine, text
from typing import Any, Dict, List, Tuple

from app.connectors.base import SourceConnector
from app.repositories.schema_repository import SchemaRepository
from app.repositories.relationship_repository import RelationshipRepository


class PostgresConnector(SourceConnector):
    """
    The only real SourceConnector implementation today. Owns engine creation
    and delegates actual introspection to the existing SchemaRepository /
    RelationshipRepository — those already take a bare SQLAlchemy Engine and
    know nothing about credentials or HTTP, so they needed no changes here.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        url = (
            f"postgresql+psycopg2://{self.username}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )
        self._engine = create_engine(url, connect_args={"connect_timeout": 5})
        self._schema_repo = SchemaRepository(self._engine)

    def test_connection(self) -> Tuple[bool, str]:
        try:
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True, "Successfully established connection!"
        except Exception as e:
            return False, f"Connection failure: {str(e)}"

    def get_tables(self, schema_name: str) -> List[Dict[str, Any]]:
        return self._schema_repo.get_tables(schema_name)

    def get_columns(self, table_name: str, schema_name: str) -> List[Dict[str, Any]]:
        return self._schema_repo.get_columns(table_name, schema_name)

    def get_columns_bulk(self, schema_name: str) -> Dict[str, List[Dict[str, Any]]]:
        return self._schema_repo.get_columns_bulk(schema_name)

    def get_foreign_keys(self, schema_name: str) -> List[Dict[str, Any]]:
        return RelationshipRepository.get_foreign_keys_from_target(self._engine, schema_name)
