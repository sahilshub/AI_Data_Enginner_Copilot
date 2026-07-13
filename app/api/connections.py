from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.schemas.connection_schema import (
    ConnectionCreate,
    ConnectionResponse,
    ConnectionTest,
    ConnectionTestResponse
)
from app.services.connection_service import ConnectionService

router = APIRouter(prefix="/connections", tags=["Database Connections"])

@router.post(
    "",
    response_model=ConnectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new database connection",
    description="Checks the database connection integrity and saves configuration settings."
)
def create_connection(schema_in: ConnectionCreate, db: Session = Depends(get_db)) -> ConnectionResponse:
    """
    Registers a new database connection.
    Tests connectivity and performs uniqueness validations before committing data.
    """
    service = ConnectionService(db)
    return service.create_connection(schema_in)

@router.get(
    "",
    response_model=List[ConnectionResponse],
    status_code=status.HTTP_200_OK,
    summary="List database connections",
    description="Retrieves a list of all registered databases. Passwords are excluded for security."
)
def get_connections(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> List[ConnectionResponse]:
    """
    Retrieves all connection profiles with support for pagination.
    """
    service = ConnectionService(db)
    return service.get_connections(skip=skip, limit=limit)

@router.delete(
    "/{connection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a database connection",
    description="Deletes connection credentials from storage."
)
def delete_connection(connection_id: int, db: Session = Depends(get_db)) -> None:
    """
    Removes connection details by ID. Raises 404 if the connection profile is not found.
    """
    service = ConnectionService(db)
    service.delete_connection(connection_id)

@router.post(
    "/test",
    response_model=ConnectionTestResponse,
    status_code=status.HTTP_200_OK,
    summary="Test connection credentials",
    description="Pings a remote database server using specified parameters without persisting credentials."
)
def test_connection(schema_in: ConnectionTest) -> ConnectionTestResponse:
    """
    Tests database connection status before saving parameters.
    """
    return ConnectionService.test_connection(schema_in)
