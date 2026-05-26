# Rent This Boat API

A FastAPI-based backend for a boat rental management system with OAuth2 + PKCE authentication and MongoDB integration.

## Features

- **FastAPI Framework** - Modern, fast, and easy-to-use Python web framework
- **OAuth2 + PKCE Authentication** - Secure authentication flow for client applications
- **MongoDB Integration** - Persistent data storage with MongoDB Atlas
- **Async Support** - Full async/await support for high performance
- **Automatic API Documentation** - Built-in Swagger UI and ReDoc
- **Pydantic Validation** - Type-safe request/response validation

## Prerequisites

- Python 3.11 or higher
- MongoDB Atlas account (or local MongoDB instance)
- Git

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd rent-this-boat/backend
```

### 2. Create and activate virtual environment

```bash
# Using Python 3.11
py -3.11 -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Or on macOS/Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -e .
```

## Configuration

### Environment Variables

Create a `.env` file in the backend root directory with the following:

```env
# MongoDB Configuration
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/?appName=Cluster0
MONGO_DB_USERNAME=your_db_username
MONGO_DB_PASSWORD=your_db_password

# FastAPI Configuration
APP_NAME=Rent This Boat API
ADMIN_EMAIL=admin@rentthisboat.com
ITEMS_PER_USER=50
APP_ENV=development
FORCE_HTTPS=false

# JWT Configuration
JWT_SECRET_KEY=your_secret_key_minimum_32_bytes_long
```

**Get your MongoDB URI:**

1. Go to [MongoDB Atlas](https://cloud.mongodb.com)
2. Log in to your cluster
3. Click "Connect"
4. Choose "Drivers" → "Python"
5. Copy your connection string and paste it in the `.env` file

## Running the Server

### Quick Start (Recommended)

```bash
# Linux / macOS
./start.sh

# Windows
./start.bat
```

This script will:

- Clean up any orphaned processes
- Create/verify the virtual environment
- Install dependencies from pyproject.toml
- Start the FastAPI development server

### Manual Start

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Server URL

Once running, the API will be available at:

- **API Base**: http://127.0.0.1:8000/api/v1
- **Swagger UI**: http://127.0.0.1:8000/api/v1/docs
- **ReDoc**: http://127.0.0.1:8000/api/v1/redoc

## Development

### Install Dev Dependencies

```bash
pip install -e ".[dev]"
```

This includes tools for:

- Testing (pytest)
- Code formatting (black)
- Import sorting (isort)
- Type checking (mypy)
- Linting (flake8)

### Run Tests

```bash
pytest
```

### Format Code

```bash
black .
isort .
```

### Type Check

```bash
mypy app
```

## Stopping the Server

Press `Ctrl+C` in the terminal to gracefully stop the server.

## Troubleshooting

### MongoDB Connection Issues

- Verify your connection string in `.env` is correct
- Ensure your IP address is whitelisted in MongoDB Atlas
- Check that your MongoDB account credentials are correct

### Port Already in Use

The startup script automatically cleans up orphaned processes on port 8000. If issues persist:

```bash
# Linux / macOS
fuser -k 8000/tcp
```

### Virtual Environment Issues

Delete and recreate the virtual environment:

```bash
# Linux / macOS
rm -rf .venv
python3.11 -m venv .venv
```

## API Documentation

Once the server is running, interactive API documentation is available at:

- **Swagger UI**: http://127.0.0.1:8000/api/v1/docs
- **Alternative (ReDoc)**: http://127.0.0.1:8000/api/v1/redoc

## Contact

For questions or issues, contact: mitch.j.rose@outlook.com
