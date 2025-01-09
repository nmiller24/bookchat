# BookChat Application Specification (v2)

This document outlines the requirements for recreating the BookChat application, a modern real-time chat application with GitHub integration for message persistence.

## Overview

BookChat is a web-based chat application built with:
- Backend: Python with Flask
- Database: SQLite
- Frontend: Vanilla JavaScript
- Message Persistence: GitHub integration
- Testing: Comprehensive test suite

## Technical Stack Requirements

### Backend
- Python 3.8+
- Flask web framework
- SQLite3 database
- GitHub API integration via PyGithub
- Rate limiting middleware
- CORS support
- Environment variable configuration

### Frontend
- Vanilla JavaScript (ES6+)
- Modern CSS3 with animations
- Responsive design principles
- No external UI frameworks required

### Development Tools
- Git for version control
- Python virtual environment
- pytest for testing
- Coverage reporting

## Core Features

### Message System
- Real-time message display with 5-second polling
- Persistent storage in SQLite database
- Automatic GitHub synchronization
- Message timestamp tracking
- Sync status indicators

### User Interface
- Modern, gradient-styled header
- Responsive message bubbles
- Real-time update indicators
- Loading states and animations
- Error notifications
- Custom scrollbar styling
- Mobile-first responsive design

### Backend Systems
1. Database Management
   - SQLite with proper indexing
   - Message persistence
   - Sync status tracking
   - Automated backups

2. GitHub Integration
   - Automatic commit creation
   - Message synchronization
   - Commit hash tracking
   - Error handling

3. System Monitoring
   - Request logging
   - Error tracking
   - Performance metrics
   - System statistics

4. Security Features
   - Rate limiting
   - Input validation
   - Secure headers
   - Environment variable management

## Project Structure
```
bookchat/
├── app.py                 # Main application entry point
├── config.py             # Configuration management
├── requirements.txt      # Python dependencies
├── README.md            # Project documentation
├── .env                 # Environment configuration
├── .gitignore           # Git ignore patterns
├── run_tests.py         # Test runner
├── static/              # Static assets
│   ├── styles.css       # Main stylesheet
│   └── js/             # JavaScript files
├── templates/           # HTML templates
│   └── index.html      # Main application page
├── utils/              # Utility modules
│   ├── db.py          # Database operations
│   ├── git_handler.py # GitHub integration
│   ├── logger.py      # Logging system
│   ├── monitor.py     # System monitoring
│   ├── backup.py      # Backup system
│   └── rate_limiter.py# Rate limiting
└── tests/              # Test suite
    ├── conftest.py    # Test configuration
    ├── test_app.py    # Application tests
    ├── test_db.py     # Database tests
    └── test_git.py    # GitHub integration tests
```

## Required Dependencies
```
Flask==3.0.0
PyGithub==2.1.1
requests==2.31.0
python-dotenv==1.0.0
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
psutil==5.9.6
```

## Environment Configuration
Required environment variables:
```
GITHUB_TOKEN=your_github_token
FLASK_ENV=development
PORT=5002
```

## Database Schema

### Messages Table
```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    git_commit_hash TEXT,
    synced BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_created_at ON messages(created_at);
CREATE INDEX idx_synced ON messages(synced);
```

## API Endpoints

### Message Operations
- `GET /messages` - Retrieve message history
- `POST /messages` - Create new message
- `GET /status` - System status and statistics

## Implementation Phases

1. **Initial Setup**
   - Project structure creation
   - Environment configuration
   - Dependency installation

2. **Core Backend**
   - Flask server setup
   - Database initialization
   - Basic API endpoints

3. **Frontend Development**
   - HTML structure
   - CSS styling
   - JavaScript functionality
   - Real-time updates

4. **GitHub Integration**
   - Authentication setup
   - Commit management
   - Sync functionality

5. **Enhanced Features**
   - Rate limiting
   - Monitoring
   - Logging
   - Backup system

6. **Testing & Documentation**
   - Test suite implementation
   - Documentation
   - Code coverage
   - System verification

## Testing Requirements

### Test Categories
1. Unit Tests
   - Database operations
   - GitHub integration
   - Message handling

2. Integration Tests
   - API endpoints
   - Frontend functionality
   - GitHub synchronization

3. System Tests
   - End-to-end functionality
   - Performance metrics
   - Error handling

### Coverage Requirements
- Minimum 80% code coverage
- All critical paths tested
- Error scenarios covered

## Browser Support
- Chrome (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Edge (latest 2 versions)

## Verification Checklist

1. **Basic Functionality**
   - Server starts on port 5002
   - Messages can be sent and received
   - Real-time updates working
   - UI is responsive on all devices

2. **Integration Features**
   - GitHub synchronization working
   - Database persistence verified
   - Backup system operational

3. **System Health**
   - Monitoring active
   - Logging functional
   - Rate limiting effective
   - Error handling working

4. **Performance**
   - Message polling efficient
   - UI animations smooth
   - Database queries optimized
   - GitHub sync performant

This specification was generated on: 2025-01-09T14:02:34-05:00
