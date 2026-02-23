# How to Run Student Attendance Management System in VS Code

This guide will help you set up and run the Flask application on your local machine using Visual Studio Code.

## Prerequisites

1.  **Python 3.11+**: Ensure Python is installed on your system.
2.  **VS Code**: Download and install Visual Studio Code.
3.  **Python Extension for VS Code**: Install the official Python extension from the VS Code Marketplace.

## Setup Instructions

1.  **Clone or Download the Project**:
    Extract the project files into a folder on your computer.

2.  **Open in VS Code**:
    Open VS Code and select `File > Open Folder...`, then choose the project folder.

3.  **Create a Virtual Environment (Recommended)**:
    Open the integrated terminal in VS Code (`Ctrl+`` or `Terminal > New Terminal`) and run:
    ```bash
    python -m venv venv
    ```

4.  **Activate the Virtual Environment**:
    - **Windows**: `venv\Scripts\activate`
    - **macOS/Linux**: `source venv/bin/activate`

5.  **Install Dependencies**:
    The project requires `flask`, `flask-sqlalchemy`, `flask-login`, and `werkzeug`. Run the following command in the terminal:
    ```bash
    pip install flask flask-sqlalchemy flask-login werkzeug
    ```

6.  **Environment Variables**:
    The application uses a `SESSION_SECRET`. You can set this in your terminal before running:
    - **Windows (Command Prompt)**: `set SESSION_SECRET=your_secret_key_here`
    - **Windows (PowerShell)**: `$env:SESSION_SECRET="your_secret_key_here"`
    - **macOS/Linux**: `export SESSION_SECRET=your_secret_key_here`

7.  **Run the Application**:
    In the terminal, run:
    ```bash
    python app.py
    ```

8.  **Access the App**:
    Open your web browser and go to `http://127.0.0.1:5000`.

## How to Access Different Portals

- **Student Portal (Landing Page)**: `http://127.0.0.1:5000/` or `http://127.0.0.1:5000/student/login`
- **Faculty Portal**: `http://127.0.0.1:5000/faculty/login`
- **Admin Portal**: `http://127.0.0.1:5000/admin/login`

## Default Admin Credentials
- **Username**: `admin`
- **Password**: `admin123`

## How to Change Admin Credentials
If you wish to change the default admin username or password, you can do so in `app.py`.
1. Open `app.py`.
2. Locate the `with app.app_context():` block.
3. Find the line: `if not User.query.filter_by(username='admin').first():`
4. Change `'admin'` to your desired username.
5. Find the line: `admin.set_password('admin123')`
6. Change `'admin123'` to your desired password.
7. **Important**: Since the admin is created on the first run, if you have already started the app once, you will need to delete the `database.db` file (usually in the `instance/` folder) and restart the app for these changes to take effect. Alternatively, you can log in as the existing admin and use the database management tools if implemented.

## Project Structure
- `app.py`: Main entry point and Flask application configuration.
- `models.py`: Database schemas for Users and Attendance.
- `routes/`: Contains Blueprints for authentication and role-specific dashboards.
- `templates/`: HTML templates using Jinja2.
- `static/`: CSS styles.
- `database.db`: SQLite database file (created automatically on first run).
