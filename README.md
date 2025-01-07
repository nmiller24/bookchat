# BookChat Application

A Git-backed web-based messaging application with persistent storage using SQLite.

## Description

BookChat is a lightweight, Git-backed messaging application that enables real-time communication between users. It uses SQLite for message storage and GitHub APIs for backup and synchronization.

## Features

- Real-time messaging
- Message persistence using SQLite database
- Git-backed message history
- Simple and intuitive web interface
- No framework dependencies
- GitHub integration for backup

## Technical Stack

- Backend: Python (No frameworks)
- Database: SQLite
- Version Control: Git
- Frontend: HTML5, CSS3, JavaScript (Vanilla)
- APIs: GitHub REST API

## Prerequisites

- Python 3.x
- Git
- GitHub account
- Required Python packages (see requirements.txt)
- SQLite3

## Installation

1. Clone the repository:
```bash
git clone https://github.com/nmiller24/bookchat.git
cd bookchat
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your GitHub credentials:
   - Create a GitHub Personal Access Token
   - Set it as an environment variable named `GITHUB_TOKEN`

4. Initialize the SQLite database:
```bash
python init_db.py
```

## Usage

1. Start the server:
```bash
python app.py
```

2. Open your web browser and navigate to `http://localhost:8080`

3. Start chatting! All messages will be:
   - Stored locally in SQLite
   - Backed up to Git repository
   - Synchronized with GitHub

## Project Structure

```
bookchat/
├── README.md
├── requirements.txt
├── app.py
├── init_db.py
├── database/
│   └── chat.db
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── templates/
│   └── index.html
└── utils/
    ├── db.py
    └── git_handler.py
```

## Contributing

Feel free to fork the project and submit pull requests for any improvements.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Last Updated

2025-01-07
