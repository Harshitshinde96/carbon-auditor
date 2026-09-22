from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    AWS_REGION: str

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    OPENROUTER_API_KEY: str
    GEMINI_API_KEY: str | None = None
    QDRANT_API_KEY: str
    QDRANT_URL: str

    S3_UPLOAD_BUCKET: str
    DYNAMO_TABLE_USERS: str
    DYNAMO_TABLE_BILLS: str
    DYNAMO_TABLE_EMISSIONS: str
    DYNAMO_TABLE_SETTINGS: str
    DYNAMO_TABLE_REPORTS: str

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()  # type: ignore
