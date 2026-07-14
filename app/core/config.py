from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application-wide settings and configuration loader.
    Leverages Pydantic Settings (v2) to automatically parse environment variables,
    perform type coercion (e.g. converting a string PORT to an int), and supply sensible defaults.
    """
    # Application Configuration
    PROJECT_NAME: str = Field(
        default="AI Data Engineering Copilot",
        description="The name of the FastAPI application, printed in logs and docs."
    )
    PROJECT_DESCRIPTION: str = Field(
        default="Backend API for connecting to PostgreSQL databases, discovering their schemas, and exploring tables, columns, and relationships through a searchable metadata catalog.",
        description="A brief summary of what the backend API handles."
    )
    VERSION: str = Field(
        default="0.1.0",
        description="Semantic version of the application."
    )
    ENVIRONMENT: str = Field(
        default="development",
        description="Deployment stage (e.g., development, staging, production, testing)."
    )

    # Server Bind Settings
    HOST: str = Field(
        default="127.0.0.1",
        description="IP address or host name the server binds to."
    )
    PORT: int = Field(
        default=8000,
        description="Network port the server listens on."
    )

    # Database Configuration
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/copilot_db",
        description="PostgreSQL connection string (SQLAlchemy format)."
    )

    # Security
    SECRET_KEY: str = Field(
        ...,
        description=(
            "Symmetric Fernet key used to encrypt registered target-database "
            "passwords at rest (see app/core/security.py). Generate one with "
            "`python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"`. "
            "Required — there is no insecure default."
        )
    )

    # Celery / Redis (async sync & refresh jobs — see app/core/celery_app.py)
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL Celery uses to queue tasks."
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL Celery uses to store task results. Same Redis as the broker is fine at this scale."
    )


    # Pydantic Settings Configuration (v2)
    # Reads environment variables from a local `.env` file if it exists.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore additional variables in .env that are not fields of this class
    )

# Export a single global instance of Settings to be imported elsewhere
settings = Settings()
