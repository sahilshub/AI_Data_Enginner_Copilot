from pydantic import BaseModel, Field
from typing import List

class TableResponse(BaseModel):
    """
    Response schema returning a simple table description.
    """
    table_name: str = Field(
        ..., 
        description="Name of the database table.",
        json_schema_extra={"example": "customers"}
    )

class ColumnResponse(BaseModel):
    """
    Response schema returning details of a single column inside a table.
    """
    name: str = Field(
        ..., 
        description="Name of the column.",
        json_schema_extra={"example": "customer_id"}
    )
    data_type: str = Field(
        ..., 
        description="PostgreSQL native data type (e.g. integer, character varying, timestamp).",
        json_schema_extra={"example": "integer"}
    )

class TableDetailResponse(BaseModel):
    """
    Response schema returning the full structure description of a table, including all columns.
    """
    table_name: str = Field(
        ..., 
        description="Name of the table.",
        json_schema_extra={"example": "customers"}
    )
    columns: List[ColumnResponse] = Field(
        ..., 
        description="Ordered list of columns defined in the table."
    )
