# Casino Partners Project

A Django-based web application for managing casino game cards and user interactions.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd casino-new
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Linux/Mac
# or
.\venv\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the initial setup:
```bash
./setup_local.sh
```

## Running the Development Server

1. Start the development server:
```bash
./run_dev.sh
```

The server will start at http://127.0.0.1:8000/

## Making Changes

When you make changes to the project (models, static files, etc.), run:
```bash
./update.sh
```

This will:
- Run database migrations
- Collect static files
- Clear cache

## Project Structure

- `Core/` - Main application directory
  - `models.py` - Database models
  - `views.py` - View functions
  - `urls.py` - URL routing
  - `forms.py` - Form definitions
- `templates/` - HTML templates
- `static/` - Static files (CSS, JS, images)
- `media/` - User-uploaded files
- `Casino/` - Project settings

## Features

- User authentication and authorization
- Game card management
- Click tracking
- Admin dashboard
- Blog system
- Responsive design

## Development Workflow

1. Make changes to the code
2. Run `./update.sh` to apply changes
3. The development server will automatically reload

## Troubleshooting

If you encounter any issues:

1. Check if the virtual environment is activated
2. Ensure all dependencies are installed
3. Check the logs in the `logs/` directory
4. Make sure the database is properly migrated
5. Verify that static files are collected

## Contributing

1. Create a new branch for your feature
2. Make your changes
3. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
