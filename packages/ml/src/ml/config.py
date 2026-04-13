from pathlib import Path

from pydantic_settings import BaseSettings


class MLSettings(BaseSettings):
    model_config = {"env_prefix": "WELS_"}

    # Data
    duckdb_path: Path = Path("data/matches.duckdb")
    models_dir: Path = Path("data/models")

    # Graph construction
    window_size: int = 25  # frames per training sample (1 second at 25 FPS)
    k_neighbors: int = 5  # k-NN edges per player node

    # Model hyperparameters
    node_features: int = 10
    hidden_dim: int = 128
    lstm_hidden: int = 128

    # Training
    epochs: int = 50
    learning_rate: float = 1e-3
    batch_size: int = 32
    val_split: float = 0.2

    # Inference device
    device: str = "cuda"


settings = MLSettings()
