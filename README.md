# North Assignment

A full-featured Django REST Framework application that integrates Google OAuth2 authentication, Google Drive integration, and real-time chat functionality using WebSockets.

## Features

### Authentication
- Google OAuth2 integration for secure user authentication
- Token-based authentication using Django REST Framework
- Social authentication with custom user pipeline
- Support for refresh tokens and offline access

### Google Drive Integration
- Read access to user's Google Drive
- File management capabilities
- Secure file operations with proper scopes
- Integration with Google Drive API

### Real-time Chat
- WebSocket-based chat functionality using Django Channels
- Redis backend for message handling
- Real-time message delivery
- Scalable chat architecture

### API Documentation
- Swagger/OpenAPI documentation using drf-spectacular
- Interactive API documentation interface
- Detailed endpoint descriptions and testing capabilities

## Technical Stack

### Backend
- Django 5.1.7
- Django REST Framework
- Django Channels for WebSocket support
- PostgreSQL database
- Redis for WebSocket message broker

### Authentication & Authorization
- OAuth2 Provider
- Social Auth
- DRF Token Authentication
- Custom authentication pipeline

### Third-Party Integrations
- Google OAuth2
- Google Drive API
- Social OAuth2

### Development & Documentation
- drf-spectacular for API documentation
- CORS support for frontend integration
- Comprehensive logging system

## Setup

### Prerequisites
- Python 3.x
- PostgreSQL
- Redis
- Google Cloud Platform account with OAuth2 credentials

### Environment Variables
The following environment variables need to be set:

```
DJANGO_SECRET_KEY=your_secret_key
DJANGO_DEBUG=True/False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=your_db_port

# Google OAuth2 Configuration
GOOGLE_OAUTH2_KEY=your_google_oauth_key
GOOGLE_OAUTH2_SECRET=your_google_oauth_secret
GOOGLE_DEVELOPER_KEY=your_google_developer_key
GOOGLE_APP_ID=your_google_app_id
GOOGLE_REDIRECT_URI=your_redirect_uri

# Redis Configuration
REDIS_HOST=your_redis_host
REDIS_PORT=your_redis_port
```

### Installation

1. Clone the repository:
```bash
git clone <repository_url>
cd north_Assignment
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Apply database migrations:
```bash
python manage.py migrate
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

## API Endpoints

The API documentation is available at:
- Swagger UI: `/api/schema/swagger-ui/`
- ReDoc: `/api/schema/redoc/`

## Security

- CORS configuration for specified origins
- CSRF protection enabled
- Secure token handling
- Environment variable based configuration
- Proper scope management for Google OAuth2

## Deployment

The application is configured with:
- WhiteNoise for static file serving
- Proper logging configuration
- Production-ready settings structure
- Support for various hosting environments

## Contributing

Please read our contributing guidelines before submitting pull requests.

## License

[Specify your license here] 