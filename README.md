# Fiscaliza

A modern web application for analyzing Portuguese Parliament open data and government transparency, built with Flask backend and React frontend.

🌐 **Live at: https://fiscaliza.pt**

## Project Structure

```
fiscaliza/
├── README.md                   # This file
├── requirements.txt            # Python dependencies
├── main.py                     # Main application entry point
├── config/
│   ├── __init__.py
│   └── settings.py            # Centralized configuration
├── app/                       # Flask web application
│   ├── __init__.py
│   ├── main.py               # Flask app factory
│   ├── models/
│   │   ├── __init__.py
│   │   └── parlamento.py     # SQLAlchemy models
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── agenda.py         # Parliamentary agenda routes
│   │   ├── navegacao_relacional.py  # Navigation routes
│   │   └── parlamento.py     # Main parliament data routes
│   └── static/
│       └── dist/             # Built frontend files
├── frontend/                  # React frontend
│   ├── src/                  # React source files
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
├── scripts/                   # Data processing scripts
│   ├── data_processing/      # Data import and processing
│   ├── data_download/        # Data download utilities
│   ├── analysis/             # Data analysis scripts
│   ├── database/             # Database management scripts
│   └── utilities/            # General utilities
├── database/
│   ├── parliament_data.db    # Main database
│   ├── migrations/           # SQL migration files
│   └── backups/             # Database backups
├── data/
│   ├── raw/                 # Raw downloaded data
│   ├── processed/           # Processed data
│   └── config/              # Configuration JSON files
├── docs/                    # Documentation
│   ├── diagrams/            # System diagrams
│   └── api/                 # API documentation
└── logs/                    # Application logs
```

## Quick Start

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install frontend dependencies:**
   ```bash
   cd frontend
   npm install
   ```

3. **Build frontend:**
   ```bash
   npm run build
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```

5. **Access the application:**
   - Web app: http://localhost:5000
   - API: http://localhost:5000/api

## Development

**Frontend development:**
```bash
cd frontend
npm run dev  # Start development server with hot reload
```

**Backend development:**
```bash
python main.py  # Start Flask server with debug mode
```

## Database

The application uses SQLite with the main database at `database/parliament_data.db`. The database contains Portuguese Parliament data including:

- Deputies and their biographical information
- Political parties and parliamentary groups
- Legislative activities and voting records
- Parliamentary agenda and sessions
- Conflicts of interest declarations

## Import Status

Current import status can be checked via the import_status table:
- **961 total files** tracked
- **919 pending** processing
- **31 completed** successfully
- **11 schema mismatches** (mostly documentation files)

## License

This project analyzes public Portuguese Parliament data and is intended for educational and research purposes.