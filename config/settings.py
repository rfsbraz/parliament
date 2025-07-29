"""
Configuration settings for the Parliament Data Analysis application.
"""

import os

# Base directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Database paths
DATABASE_DIR = os.path.join(BASE_DIR, 'database')
PARLIAMENT_DATABASE = os.path.join(BASE_DIR, 'parlamento.db')

# Data paths
DATA_DIR = os.path.join(BASE_DIR, 'data')
RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw')
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, 'processed')
CONFIG_DATA_DIR = os.path.join(DATA_DIR, 'config')

# Log paths
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# Flask configuration
FLASK_CONFIG = {
    'SECRET_KEY': 'asdf#FGSgvasgf$5$WGT',
    'SQLALCHEMY_DATABASE_URI': f'sqlite:///{PARLIAMENT_DATABASE}',
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'PROPAGATE_EXCEPTIONS': True
}

# Parliament data paths
PARLIAMENT_DATA_DIR = os.path.join(RAW_DATA_DIR, 'parliament_data')
DOWNLOADS_DIR = os.path.join(RAW_DATA_DIR, 'downloads')