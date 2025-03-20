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

## Docker Setup

### Prerequisites
- Docker
- Docker Compose
- Google Cloud Platform account with OAuth2 credentials

### Environment Setup
1. Create a `.env` file in the root directory with the following variables:

```env
DJANGO_SECRET_KEY=your_secret_key
DJANGO_DEBUG=True/False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=postgres
DB_PORT=5432

# Google OAuth2 Configuration
GOOGLE_OAUTH2_KEY=your_google_oauth_key
GOOGLE_OAUTH2_SECRET=your_google_oauth_secret
GOOGLE_DEVELOPER_KEY=your_google_developer_key
GOOGLE_APP_ID=your_google_app_id
GOOGLE_REDIRECT_URI=your_redirect_uri

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
```

### Docker Compose Services
The application is containerized with the following services:
- `web`: Django application
- `postgres`: PostgreSQL database
- `redis`: Redis for WebSocket and caching
- `nginx`: Nginx reverse proxy for production

### Quick Start

1. Clone the repository:
```bash
git clone <repository_url>
cd north_Assignment
```

2. Build and start the containers:
```bash
docker-compose up --build
```

3. Create a superuser:
```bash
docker-compose exec web python manage.py createsuperuser
```

4. Access the application:
- Development: http://localhost:8000
- API Documentation: http://localhost:8000/api/schema/swagger-ui/

### Useful Docker Commands

```bash
# Start services in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild containers
docker-compose up --build

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Shell access
docker-compose exec web python manage.py shell

# Restart specific service
docker-compose restart web
```

## API Endpoints

The API documentation is available at:
- Swagger UI: `/api/schema/swagger-ui/`
- ReDoc: `/api/schema/redoc/`

## Running and Testing the API

### Running the API

1. Start all services using Docker:
```bash
docker-compose up -d
```

2. Verify all services are running:
```bash
docker-compose ps
```

### API Endpoints Documentation

#### 1. Google Authentication
**Endpoint**: `GET /auth/google/auth-url/`
- **Purpose**: Get Google OAuth2 authentication URL
- **Authentication**: Not required
- **Response**: Returns Google authentication URL
- **Testing**:
```bash
# Using curl
curl -X GET http://localhost:8000/auth/google/auth-url/

# Expected Response
{
    "auth_url": "https://accounts.google.com/o/oauth2/auth?..."
}
```

#### 2. Google Drive Files List
**Endpoint**: `GET /drive/files/`
- **Purpose**: List files from user's Google Drive
- **Authentication**: Required (Token Authentication)
- **Parameters**: 
  - `page_size` (optional): Number of files per page
  - `page_token` (optional): Token for next page
- **Testing**:
```bash
# Using curl with auth token
curl -X GET http://localhost:8000/drive/files/ \
  -H "Authorization: Token YOUR_API_TOKEN"

# Expected Response
{
    "files": [...],
    "next_page_token": "token..."
}
```

#### 3. Download Drive File
**Endpoint**: `GET /drive/files/{file_id}/download/`
- **Purpose**: Download a specific file from Google Drive
- **Authentication**: Required (Token Authentication)
- **Parameters**: 
  - `file_id`: ID of the file to download
- **Testing**:
```bash
# Using curl with auth token
curl -X GET http://localhost:8000/drive/files/3/download/ \
  -H "Authorization: Token YOUR_API_TOKEN" \
  --output downloaded_file
```

#### 4. Upload to Drive
**Endpoint**: `POST /drive/files/upload/`
- **Purpose**: Upload a file to Google Drive
- **Authentication**: Required (Token Authentication)
- **Content-Type**: multipart/form-data
- **Parameters**:
  - `file`: File to upload
  - `folder_id` (optional): Parent folder ID
- **Testing**:
```bash
# Using curl with auth token
curl -X POST http://localhost:8000/drive/files/upload/ \
  -H "Authorization: Token YOUR_API_TOKEN" \
  -F "file=@/path/to/your/file.txt"

# Expected Response
{
    "id": "file_id",
    "name": "file.txt",
    "mimeType": "text/plain",
    ...
}
```

#### 5. Chat Rooms
**Endpoint**: `GET /api/chat/rooms/`
- **Purpose**: List available chat rooms
- **Authentication**: Required (Token Authentication)
- **Testing**:
```bash
# Using curl with auth token
curl -X GET http://localhost:8000/api/chat/rooms/ \
  -H "Authorization: Token YOUR_API_TOKEN"

# Expected Response
{
    "rooms": [
        {
            "id": 1,
            "name": "Room Name",
            ...
        }
    ]
}
```

#### 6. WebSocket Chat Connection
**WebSocket URL**: `ws://localhost:8000/ws/chat/{room_id}/`
- **Purpose**: Real-time chat communication
- **Authentication**: Required (Token Authentication in query parameter)
- **Testing using wscat**:
```bash
# Install wscat
npm install -g wscat

# Connect to WebSocket with auth token
wscat -c "ws://localhost:8000/ws/chat/2/?token=YOUR_API_TOKEN"

# Send message
{"type": "message", "content": "Hello, World!"}

# Expected Response
{"type": "message", "content": "Hello, World!", "user": "username", "timestamp": "..."}
```

### Testing Tools
1. **Swagger UI**: Access interactive API documentation at `http://localhost:8000/api/schema/swagger-ui/`
2. **Postman**: Import the collection from `http://localhost:8000/api/schema/`
3. **Curl**: Use the commands provided above
4. **wscat**: For testing WebSocket connections

### Common Testing Issues and Solutions
1. **Authentication Errors**:
   - Ensure your API token is valid and not expired
   - Token must be included in Authorization header as "Token YOUR_API_TOKEN"
   - For WebSocket connections, include token as URL query parameter

2. **File Upload Issues**:
   - Check file size limits
   - Ensure correct Content-Type header
   - Verify file permissions

3. **WebSocket Connection Issues**:
   - Verify token is included in URL query parameters
   - Check if the room_id exists
   - Ensure WebSocket connection is properly closed after use

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