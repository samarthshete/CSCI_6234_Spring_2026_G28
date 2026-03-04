from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "BudgetFlow"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "development_secret_key_change_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    DATABASE_URL: Optional[str] = None

    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "budgetflow_user"
    POSTGRES_PASSWORD: str = "budgetflow_password"
    POSTGRES_DB: str = "budgetflow_db"
    POSTGRES_PORT: str = "5432"

    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET: str = "budgetflow-reports"
    S3_REGION: str = "us-east-1"
    S3_USE_SSL: bool = False

    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    ADVISOR_ENABLED: bool = True

    @property
    def effective_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
