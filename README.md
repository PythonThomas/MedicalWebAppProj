# WBS Project v1

A simple web application with HTML frontend and Python Flask backend, with PostgreSQL database support.

## Project Structure

```
WBS project v1/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (create this)
├── .github/
│   └── copilot-instructions.md
├── templates/
│   └── index.html        # HTML frontend
├── static/
│   ├── style.css         # Styling
│   └── script.js         # Frontend JavaScript
└── README.md             # This file
```

## Getting Started

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Installation

1. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

2. **Activate the virtual environment:**
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

```bash
python app.py
```

The application will be available at `http://localhost:5000`

## API Endpoints

- **GET** `/` - Serves the main HTML page
- **GET** `/api/hello` - Returns a hello message
- **POST** `/api/data` - Receives JSON data from frontend

## Adding PostgreSQL

When ready to add PostgreSQL:

1. Install PostgreSQL client library:
   ```bash
   pip install psycopg2-binary
   ```

2. Update `app.py` with database connection:
   ```python
   import psycopg2
   from psycopg2 import sql
   
   # Add your database connection code
   ```

3. Create environment variables for database connection:
   ```
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=your_database
   DB_USER=your_user
   DB_PASSWORD=your_password
   ```

## Features

- Simple and clean user interface
- RESTful API endpoints
- CORS enabled for cross-origin requests
- Ready for database integration
- Environment variable support

## Technologies Used

- **Frontend**: HTML5, CSS3, JavaScript
- **Backend**: Python Flask
- **Database**: PostgreSQL (ready for integration)
- **Package Manager**: pip

## Future Enhancements

- Add PostgreSQL database integration
- Add user authentication
- Add form validation
- Add data persistence
