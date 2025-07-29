# Portuguese Parliament Data Analysis - Quick Start

## 🚀 Running the Application

### Prerequisites
- Python 3.12+ installed
- Node.js 18+ installed
- npm installed

### Setup Complete ✅
The application has been set up with:
- ✅ SQLite database with sample data
- ✅ Flask backend API
- ✅ React frontend with modern UI
- ✅ Sample data: 15 deputies, 10 parties, 22 electoral districts

### Running Both Servers

**You need to run TWO separate terminal windows:**

#### Terminal 1 - Backend (Flask)
```bash
python main.py
```
Server will start at: http://127.0.0.1:5000

#### Terminal 2 - Frontend (React)
```bash
npm run dev
```
Server will start at: http://localhost:5173

### 🎯 Access the Application
Open your browser and go to: **http://localhost:5173**

### 📊 Available Features
- **Dashboard**: Overview with statistics and charts
- **Deputies**: Browse parliamentary members
- **Parties**: Political party analysis
- **Agenda**: Parliamentary schedule
- **Analysis**: Advanced insights

### 🛠 Troubleshooting
If you see import errors:
1. Make sure both servers are running
2. Check the browser console for any remaining import issues
3. Refresh the page after both servers are fully started

### 📁 Project Structure
```
├── database/app.db          # SQLite database
├── src/
│   ├── models/             # Flask models
│   ├── routes/             # API endpoints
│   ├── components/         # React components
│   └── App.jsx             # Main React app
├── main.py                 # Flask server
└── package.json            # Node.js dependencies
```