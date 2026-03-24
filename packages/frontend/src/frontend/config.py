from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    backend_url: str = "http://localhost:8000"

    model_config = {"env_prefix": "WELS_"}


settings = Settings()
