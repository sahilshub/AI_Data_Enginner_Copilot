from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any, Dict, Optional

class ConnectionBase(BaseModel):
    """
    Base properties shared across request and response schemas.
    """
    name: str = Field(
        ..., 
        description="A unique friendly identifier for this database connection.", 
        json_schema_extra={"example": "Staging Postgres"}
    )
    dialect: str = Field(
        default="postgresql", 
        description="Type of the target database engine (e.g. postgresql, mysql, sqlite).",
        json_schema_extra={"example": "postgresql"}
    )
    host: str = Field(
        ..., 
        description="Hostname or IP address of the database server.",
        json_schema_extra={"example": "localhost"}
    )
    port: int = Field(
        ..., 
        description="Network port the database server listens on.",
        json_schema_extra={"example": 5432}
    )
    username: str = Field(
        ..., 
        description="Login credential username.",
        json_schema_extra={"example": "postgres"}
    )
    database: str = Field(
        ...,
        description="Name of the database catalog to connect to.",
        json_schema_extra={"example": "copilot_db"}
    )
    extra_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Source-specific config that doesn't fit host/port/username/password/database "
            "(e.g. a future BigQuery service-account key + project id, or Snowflake's "
            "warehouse/role). Unused for the currently-supported 'postgresql' dialect."
        )
    )

class ConnectionCreate(ConnectionBase):
    """
    Schema for creating a database connection.
    Includes the password, which is required to write to the database.
    """
    password: str = Field(
        ...,
        description="Password credential corresponding to username.",
        json_schema_extra={"example": "postgres"}
    )

class ConnectionUpdate(BaseModel):
    """
    Schema for partially updating a database connection. Every field is
    optional — only the ones provided are changed. `password` is optional
    too: omit it to keep the existing (encrypted) password rather than
    being forced to resupply it just to change, say, the host.

    Common use: fixing `host` after moving where the API runs — e.g.
    switching from "localhost" to "host.docker.internal" once the API
    moved into a Docker container and "localhost" started meaning the
    container itself instead of the host machine.
    """
    name: Optional[str] = Field(default=None, description="A unique friendly identifier for this database connection.")
    dialect: Optional[str] = Field(default=None, description="Type of the target database engine.")
    host: Optional[str] = Field(default=None, description="Hostname or IP address of the database server.")
    port: Optional[int] = Field(default=None, description="Network port the database server listens on.")
    username: Optional[str] = Field(default=None, description="Login credential username.")
    password: Optional[str] = Field(default=None, description="New password. Omit to keep the existing one.")
    database: Optional[str] = Field(default=None, description="Name of the database catalog to connect to.")
    extra_config: Optional[Dict[str, Any]] = Field(default=None, description="Source-specific config; see ConnectionBase.")

class ConnectionResponse(ConnectionBase):
    """
    Schema for database connection responses.
    Does NOT expose the password field, ensuring security of sensitive parameters.
    """
    id: int = Field(..., description="Unique database connection primary key ID.")
    created_at: datetime = Field(..., description="Creation timestamp.")
    updated_at: datetime = Field(..., description="Last modification timestamp.")

    model_config = {
        "from_attributes": True  # Instructs Pydantic to read ORM objects (SQLAlchemy) in serialization
    }

class ConnectionTest(BaseModel):
    """
    Payload required to test database credentials connectivity prior to registering them.
    Name is omitted since it is not needed to run connection probes.
    """
    dialect: str = Field(default="postgresql", description="Database dialect.")
    host: str = Field(..., description="Database server address.")
    port: int = Field(..., description="Database server port.")
    username: str = Field(..., description="Database username.")
    password: str = Field(..., description="Database password.")
    database: str = Field(..., description="Database name.")

class ConnectionTestResponse(BaseModel):
    """
    Schema representing database connection status check outcomes.
    """
    success: bool = Field(..., description="True if connection succeeded, False if it failed.")
    message: str = Field(..., description="Error message or success note.")
