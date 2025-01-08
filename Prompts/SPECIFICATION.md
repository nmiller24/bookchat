# BookChat Application Specification

Create a modern chat application called "BookChat" with the following specifications. The application should be built using Python for the backend, SQLite for data storage, and vanilla JavaScript for the frontend. The application should integrate with GitHub for message persistence and include comprehensive testing.

## Core Requirements

### Server
- Python HTTP server running on port 5002
- SQLite database for message storage
- GitHub integration for message synchronization
- CORS support for cross-origin requests
- Rate limiting for API endpoints
- Comprehensive error handling
- Advanced logging system
- Automated backup system
- System monitoring

### Database
- Messages table with:
  - id (primary key)
  - content (text)
  - created_at (timestamp)
  - git_commit_hash (text)
  - synced (boolean)
- Proper indexes for performance
- Backup functionality
- Migration support

### Frontend
- Modern, responsive design
- Real-time message updates (polling every 5 seconds)
- Message input with instant feedback
- Smooth animations
- Error handling with user feedback
- Mobile-first approach
- Custom scrollbar
- Loading states

### Testing
- Comprehensive test suite
- Database tests
- API endpoint tests
- GitHub integration tests
- Frontend integration tests
- Coverage reporting

### Security
- Rate limiting
- Input validation
- Error handling
- Secure headers
- Environment variable management
- Production configurations

### Monitoring
- Request tracking
- Error logging
- Performance metrics
- System statistics
- Backup verification

## Project Structure
```
bookchat/
├── app.py                 # Main server file
├── config.py             # Configuration management
├── requirements.txt      # Python dependencies
├── README.md            # Project documentation
├── .env                 # Environment variables
├── .gitignore           # Git ignore rules
├── run_tests.py         # Test runner
├── static/              # Static files
│   ├── styles.css       # Main CSS
│   └── js/             # JavaScript files
├── templates/           # HTML templates
│   └── index.html      # Main page
├── utils/              # Utility modules
│   ├── db.py          # Database management
│   ├── git_handler.py # GitHub integration
│   ├── logger.py      # Logging setup
│   ├── monitor.py     # System monitoring
│   ├── backup.py      # Backup management
│   └── rate_limiter.py# Rate limiting
└── tests/              # Test files
    ├── conftest.py    # Test configuration
    ├── test_app.py    # Server tests
    ├── test_db.py     # Database tests
    └── test_git.py    # GitHub integration tests
```

## Implementation Steps

1. Initial Setup
   - Create GitHub repository
   - Set up project structure
   - Initialize virtual environment
   - Create requirements.txt
   Reference: [0_github_setup.txt](0_github_setup.txt)

2. Server Implementation
   - Create HTTP server
   - Implement request handlers
   - Add CORS support
   Reference: [1_initial_setup.txt](1_initial_setup.txt)

3. Database Setup
   - Create SQLite database
   - Implement message table
   - Add indexes
   Reference: [2_database_setup.txt](2_database_setup.txt)

4. Frontend Development
   - Create HTML structure
   - Implement styling
   - Add JavaScript functionality
   References: 
   - [3_frontend_html.txt](3_frontend_html.txt)
   - [4_styling.txt](4_styling.txt)
   - [5_javascript.txt](5_javascript.txt)

5. GitHub Integration
   - Implement message synchronization
   - Handle commits
   Reference: [6_github_integration.txt](6_github_integration.txt)

6. Testing
   - Create test suite
   - Implement all tests
   - Set up coverage reporting
   Reference: [8_testing.txt](8_testing.txt)

7. Production Features
   - Add rate limiting
   - Implement backup system
   - Set up monitoring
   - Configure logging
   References:
   - [9_advanced_setup.txt](9_advanced_setup.txt)
   - [10_missing_features.txt](10_missing_features.txt)

## Technical Requirements

### Dependencies
```
PyGithub==2.1.1
requests==2.31.0
python-dotenv==1.0.0
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
psutil==5.9.6
```

### Environment Variables
```
GITHUB_TOKEN=your_github_token
FLASK_ENV=development
PORT=5002
```

### Browser Support
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Features

### Message Handling
- Create new messages
- Retrieve message history
- Real-time updates
- GitHub synchronization
- Error handling
- Rate limiting

### User Interface
- Modern design with gradient header
- Responsive layout
- Message bubbles
- Loading states
- Error notifications
- Smooth animations
- Custom scrollbar

### Backend Features
- Message persistence
- GitHub integration
- Database backups
- System monitoring
- Advanced logging
- Rate limiting
- Environment configurations

## Verification Steps

1. Basic Functionality
   - Server starts successfully
   - Messages can be sent and received
   - Real-time updates work
   - UI is responsive

2. GitHub Integration
   - Messages sync to GitHub
   - Commit hashes are stored
   - Sync status updates

3. Security
   - Rate limiting works
   - Input validation functions
   - Error handling works
   - Environment variables are secure

4. Production Features
   - Backups run successfully
   - Monitoring provides insights
   - Logs are properly formatted
   - Different environments work

5. Testing
   - All tests pass
   - Coverage meets requirements
   - Edge cases are handled

## Success Criteria

The project is considered complete when:
1. All features are implemented and working
2. Tests pass with >90% coverage
3. UI is responsive and modern
4. GitHub integration is functional
5. Production features are implemented
6. Documentation is complete
7. Code follows best practices
8. Security measures are in place

## Additional Notes

1. Code Style
   - Follow PEP 8 for Python
   - Use consistent naming conventions
   - Add comprehensive comments
   - Write clear documentation

2. Security
   - Never commit sensitive data
   - Use environment variables
   - Implement rate limiting
   - Validate all inputs

3. Performance
   - Optimize database queries
   - Minimize API calls
   - Use appropriate indexes
   - Implement caching where needed

This specification provides all necessary details to recreate the BookChat application with all features and functionality. Follow the implementation steps in order, referring to the referenced prompt files for detailed instructions at each step.
