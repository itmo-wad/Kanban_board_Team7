# Kanban Board Application

A full-featured Kanban board application built with Flask, SQLite, and modern web technologies. This application helps users organize tasks using the Kanban methodology, featuring multiple boards, drag-and-drop functionality, and a clean, responsive interface.

## Features

- **User Authentication**
  - Secure login and signup system
  - Profile management with photo upload
  - Password hashing for security

- **Multiple Kanban Boards**
  - Create and manage multiple boards
  - Organize tasks by project or workflow
  - Intuitive board navigation

- **Task Management**
  - Create, edit, and delete tasks
  - Drag-and-drop functionality
  - Due dates and descriptions
  - Search and filter tasks

- **Customization**
  - Dark and light theme support
  - Responsive design for all devices
  - Column management

## Prerequisites

- Python 3.7 or higher
- pip (Python package manager)
- Web browser (Chrome, Firefox, Safari, or Edge)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd kanban-board
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Initialize the database:
   ```bash
   python
   >>> from app import db
   >>> db.create_all()
   >>> exit()
   ```

## Running the Application

1. Start the Flask development server:
   ```bash
   python app.py
   ```

2. Open your web browser and navigate to:
   ```
   http://localhost:5000
   ```

## Project Structure

```
kanban-board/
├── app.py                 # Main application file
├── requirements.txt       # Python dependencies
├── static/               # Static files
│   ├── css/             # CSS stylesheets
│   └── uploads/         # User uploads
├── templates/           # HTML templates
│   ├── base.html       # Base template
│   ├── index.html      # Landing page
│   ├── login.html      # Login page
│   ├── signup.html     # Signup page
│   ├── profile.html    # User profile
│   ├── dashboards.html # Dashboards list
│   └── dashboard.html  # Individual board view
└── README.md           # This file
```

## Usage

1. Create an account or log in
2. Create a new dashboard
3. Add columns to your dashboard (e.g., "To Do", "In Progress", "Done")
4. Create tasks within columns
5. Drag and drop tasks between columns
6. Use the search feature to find specific tasks
7. Toggle between light and dark themes as needed

## Security Features

- Password hashing using Werkzeug
- CSRF protection
- Secure file uploads
- User session management
- Input validation and sanitization

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 