"""
Configuration settings for the Parliament Data Analysis application.
"""

import os
from database.connection import get_database_url

# Base directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Database configuration
DATABASE_DIR = os.path.join(BASE_DIR, "database")

# Data paths
DATA_DIR = os.path.join(BASE_DIR, "data")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "downloads")
CONFIG_DATA_DIR = os.path.join(DATA_DIR, "config")

# Log paths
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Flask configuration
FLASK_CONFIG = {
    "SECRET_KEY": "asdf#FGSgvasgf$5$WGT",
    "SQLALCHEMY_DATABASE_URI": get_database_url(),
    "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    "PROPAGATE_EXCEPTIONS": True,
    "DEBUG": True,  # Enable debug mode for development
    "TRAP_HTTP_EXCEPTIONS": True,  # Trap HTTP exceptions for custom handling
}

# Parliament data paths
PARLIAMENT_DATA_DIR = os.path.join(BASE_DIR, 'scripts', 'data_processing', 'data', 'downloads')
DOWNLOADS_DIR = os.path.join(BASE_DIR, 'scripts', 'data_processing', 'data', 'downloads')
