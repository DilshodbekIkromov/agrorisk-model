"""
Configuration module for AgroRisk Model
Centralizes path management and environment variables
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project paths (relative to this file)
PROJECT_ROOT = Path(__file__).parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_SYNTHETIC_DIR = DATA_DIR / "synthetic"
DATA_PROCESSED_DIR = DATA_DIR / "processed"

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Google Earth Engine (optional)
GEE_PROJECT_ID = os.getenv("GEE_PROJECT_ID")
GEE_SERVICE_ACCOUNT = os.getenv("GEE_SERVICE_ACCOUNT")

# Model configuration
MODEL_PATH = os.getenv("MODEL_DIR", str(MODELS_DIR))
DATA_PATH = os.getenv("DATA_DIR", str(DATA_DIR))
