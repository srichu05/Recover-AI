"""
RecoverAI Configuration Settings
Financial units are in integer minor units (paise). 1 INR = 100 paise.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
EVAL_DIR = BASE_DIR / "evaluation"
EVAL_DIR.mkdir(exist_ok=True)


class Settings:
    APP_NAME: str = "RecoverAI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1")
    
    # Financial Guardrails (Defaults specified in PRD)
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "2"))
    AUTONOMOUS_ACTION_LIMIT_PAISE: int = int(os.getenv("AUTONOMOUS_ACTION_LIMIT_PAISE", "5000000"))  # ₹50,000.00
    MIN_AUTONOMOUS_CONFIDENCE: float = float(os.getenv("MIN_AUTONOMOUS_CONFIDENCE", "0.80"))
    
    # Degradation Detection Parameters
    DEGRADATION_THRESHOLD_PCT: float = float(os.getenv("DEGRADATION_THRESHOLD_PCT", "15.0"))  # 15 percentage points drop
    Z_SCORE_THRESHOLD: float = float(os.getenv("Z_SCORE_THRESHOLD", "2.5"))
    
    # Data & Database Paths
    DATA_DIR: Path = DATA_DIR
    EVAL_DIR: Path = EVAL_DIR
    DB_PATH: Path = DATA_DIR / "recoverai.db"
    
    # Reproducibility Seed
    DEFAULT_RANDOM_SEED: int = int(os.getenv("DEFAULT_RANDOM_SEED", "42"))
    
    # GroqCloud LLM Settings (OpenAI SDK Compatible)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_BASE_URL: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    USE_MOCK_LLM_IF_UNAVAILABLE: bool = os.getenv("USE_MOCK_LLM_IF_UNAVAILABLE", "True").lower() in ("true", "1")


settings = Settings()
