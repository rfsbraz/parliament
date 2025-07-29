# Project Structure Overview

## Directory Layout

```
parliament-data-analysis/
├── README.md                   # Project overview and quick start
├── PROJECT_STRUCTURE.md        # This file - detailed structure guide
├── requirements.txt            # Python dependencies
├── package.json               # Node.js scripts and dependencies
├── main.py                    # Application entry point
├── start_app.bat              # Windows startup script
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
│
├── app/                       # Flask web application
│   ├── __init__.py
│   ├── main.py               # Flask app factory and configuration
│   ├── models/               # SQLAlchemy database models
│   │   ├── __init__.py
│   │   └── parlamento.py     # Parliament data models
│   ├── routes/               # API route handlers
│   │   ├── __init__.py
│   │   ├── agenda.py         # Parliamentary agenda endpoints
│   │   ├── navegacao_relacional.py  # Relational navigation endpoints
│   │   └── parlamento.py     # Main parliament data endpoints
│   └── static/               # Static files served by Flask
│       └── dist/             # Built React frontend files
│
├── frontend/                  # React frontend application
│   ├── src/                  # Source code
│   │   ├── components/       # React components
│   │   │   ├── AgendaPage.jsx
│   │   │   ├── AnalysisPage.jsx
│   │   │   ├── AnalysisPageSimple.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── DeputadoDetalhes.jsx
│   │   │   ├── DeputadosPage.jsx
│   │   │   ├── Navigation.jsx
│   │   │   ├── PartidoDetalhes.jsx
│   │   │   └── PartidosPage.jsx
│   │   ├── contexts/         # React contexts
│   │   ├── hooks/            # Custom React hooks
│   │   ├── services/         # API service functions
│   │   ├── utils/            # Utility functions
│   │   ├── App.jsx          # Main React component
│   │   ├── App.css          # App-specific styles
│   │   ├── main.jsx         # React entry point
│   │   └── index.css        # Global styles
│   ├── public/              # Public assets
│   ├── package.json         # Frontend dependencies
│   ├── vite.config.js       # Vite build configuration
│   └── index.html           # HTML template
│
├── config/                   # Application configuration
│   ├── __init__.py
│   └── settings.py          # Centralized settings
│
├── scripts/                  # Utility and processing scripts
│   ├── data_processing/     # Data import and processing
│   │   ├── data_importer.py
│   │   ├── file_processor.py
│   │   └── import_parliament_data.py
│   ├── data_download/       # Data download utilities
│   │   ├── download_parliament_data.py
│   │   ├── download_parliament_direct.py
│   │   └── parliament_api_discovery.py
│   ├── analysis/            # Data analysis scripts
│   │   ├── analisar_*.py    # Various analysis scripts
│   │   └── verificar_*.py   # Verification scripts
│   ├── database/            # Database management
│   │   ├── create_sample_data.py
│   │   ├── implementar_*.py # Implementation scripts
│   │   └── corrigir_*.py    # Data correction scripts
│   └── utilities/           # General utilities
│
├── database/                 # Database files
│   ├── parliament_data.db   # Main SQLite database
│   ├── migrations/          # SQL migration scripts
│   │   ├── create_activities_tables.sql
│   │   ├── create_agenda_parlamentar_tables.sql
│   │   └── create_import_status.sql
│   └── backups/             # Database backups
│       └── parlamento_backup_*.db
│
├── data/                    # Data storage
│   ├── raw/                 # Raw downloaded data
│   │   ├── parliament_data/ # XML parliament data files
│   │   └── downloads/       # Downloaded resources
│   ├── processed/           # Processed data
│   └── config/              # Configuration JSON files
│       ├── parliament_*.json
│       └── relatorio_*.json
│
├── docs/                    # Documentation
│   ├── api/                 # API documentation
│   │   └── parliament_api_documentation.md
│   ├── setup/               # Setup guides
│   │   └── QUICK_START.md
│   ├── development/         # Development guides
│   ├── diagrams/            # System diagrams
│   │   ├── diagrama_*.puml
│   │   └── Design do Esquema*.md
│   └── *.md                 # Various documentation files
│
└── logs/                    # Application logs
    └── *.log               # Various log files
```

## Key Files

### Configuration
- `config/settings.py` - Central configuration with paths and settings
- `.env.example` - Template for environment variables

### Entry Points
- `main.py` - Main application launcher
- `app/main.py` - Flask application factory
- `frontend/src/main.jsx` - React application entry

### Data Processing
- `scripts/data_processing/data_importer.py` - Main data import logic
- `scripts/data_download/download_parliament_data.py` - Data fetching

### Database
- `database/parliament_data.db` - Main SQLite database (961 files tracked)
- `database/migrations/` - SQL schema definitions

## Development Workflow

1. **Backend Development**: Run `python main.py` from project root
2. **Frontend Development**: Run `npm run dev` in frontend directory
3. **Full Application**: Run `npm run dev` from project root (uses concurrently)

## Data Organization

- **Raw Data**: Original XML/JSON files in `data/raw/`
- **Processed Data**: Transformed data in `data/processed/`
- **Database**: SQLite database with relational structure

## Import Status

Current database contains:
- 961 total files tracked
- 31 successfully imported
- 919 pending processing
- 11 schema mismatches (mostly documentation files)