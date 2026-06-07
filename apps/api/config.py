"""
Configuration for AlphaMomentum API.

Environment-based settings for development and production.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./alphamomentum.db")

# API
API_TITLE = "AlphaMomentum Recommender API"
API_VERSION = "0.1.0"

# Market Data Provider
MARKET_DATA_PROVIDER = os.getenv("MARKET_DATA_PROVIDER", "mock")  # mock or yahoo
SYMBOL_UNIVERSE_FILE = os.getenv("SYMBOL_UNIVERSE_FILE", "config/symbol_universe.txt")

# Pipeline Configuration
PIPELINE_HOUR = int(os.getenv("PIPELINE_HOUR", "16"))  # 4 PM market close
PIPELINE_MINUTE = int(os.getenv("PIPELINE_MINUTE", "0"))
FRESHNESS_MAX_STALE_DAYS = int(os.getenv("FRESHNESS_MAX_STALE_DAYS", "5"))

# Recommendation Gates
MIN_MARKET_CAP = 2_000_000_000  # $2B
MIN_AVG_VOLUME_90D = 1_000_000  # 1M shares
MIN_PRICE = 10.0

# Momentum Gates
MIN_RSI = 60
MAX_RSI = 75
MIN_ADX = 25
MIN_RELATIVE_VOLUME = 2.0

# Sentiment
MAX_PUT_CALL_RATIO = 1.20
MIN_PUT_CALL_RATIO = 0.0

# Risk Management
STOP_ATR_MULTIPLIER = 2.0
TARGET_ATR_MULTIPLIER = 3.0

# Feature Flags
ENABLE_PUT_CALL_RATIO = os.getenv("ENABLE_PUT_CALL_RATIO", "false").lower() == "true"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
