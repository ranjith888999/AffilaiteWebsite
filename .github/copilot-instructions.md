<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Affiliate Website Project Instructions

This is a comprehensive affiliate marketing website built with FastAPI and PostgreSQL, integrated with Cuelinks API.

## Project Structure
- **FastAPI Backend**: Modern Python web framework for API development
- **PostgreSQL Database**: Robust database for storing campaigns, offers, and chat messages
- **Cuelinks API Integration**: Fetch live affiliate campaigns and offers
- **Chat System**: AI-powered chat assistant for offer recommendations
- **Beautiful Frontend**: Responsive design with animations using HTML, CSS, and JavaScript

## Key Components
- **Models**: Database models in `app/models/database.py`
- **Controllers**: API endpoints in `app/controllers/`
- **Services**: Business logic in `app/services/`
- **Templates**: Jinja2 templates in `templates/`
- **Static Files**: CSS and JavaScript in `static/`

## Environment Variables
- `CUELINKS_API_KEY`: API key for Cuelinks integration
- `DATABASE_*`: PostgreSQL connection parameters

## Development Guidelines
- Follow FastAPI best practices
- Use async/await for database operations
- Implement proper error handling
- Maintain clean separation of concerns (MVC pattern)
- Use type hints for better code quality
- Write responsive and accessible frontend code
