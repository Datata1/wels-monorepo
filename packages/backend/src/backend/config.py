from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "WELS Handball Analytics"
    debug: bool = False
    database_url: str = "sqlite:///./wels.db"
    video_input_dir: str = "../../"
    duckdb_path: str = "../../data/output/duckdb/matches.duckdb"
    model_config = {"env_prefix": "WELS_"}


settings = Settings()
