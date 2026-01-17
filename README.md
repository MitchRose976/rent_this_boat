# Rent This Boat

A full-stack boat rental management platform built with modern technologies for secure authentication and seamless user experience.

## Project Overview

**Rent This Boat** is a comprehensive platform that connects boat owners with renters. This repository contains both the frontend and backend components of the application.

### Tech Stack

- **Frontend**: [Next.js](https://nextjs.org/) with React and TypeScript
- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) with Python 3.11
- **Database**: MongoDB Atlas
- **Authentication**: OAuth2 + PKCE

## 📁 Project Structure

```
rent-this-boat/
├── frontend/          # Next.js React application
├── backend/           # FastAPI Python API
├── .gitignore        # Git ignore rules for both frontend and backend
└── README.md         # This file
```

## 🚀 Quick Start

### Frontend Setup

See [Frontend README](./frontend/README.md) for detailed instructions.

```bash
cd frontend
npm install
npm run dev
```

**Frontend runs on**: http://localhost:3000

### Backend Setup

See [Backend README](./backend/README.md) for detailed instructions.

#### Windows
```bash
cd backend
./start.bat
```

#### macOS/Linux
```bash
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Backend runs on**: http://127.0.0.1:8000

**API Documentation**: http://127.0.0.1:8000/docs (Swagger UI)

## 📋 Prerequisites

### Frontend
- Node.js 18+ and npm

### Backend
- Python 3.11+
- MongoDB Atlas account

## 🔗 Integration

The frontend communicates with the backend API at `http://127.0.0.1:8000`

- Backend API endpoints are available at `/api/v1/*`
- Authentication uses OAuth2 with PKCE flow
- Session management through JWT tokens

## 📚 Documentation

For more detailed information, refer to:

- **[Frontend Documentation](./frontend/README.md)** - React/Next.js setup, components, deployment
- **[Backend Documentation](./backend/README.md)** - API setup, database, authentication, development

## 🛠️ Development

### Working on Frontend

```bash
cd frontend
npm run dev
```

### Working on Backend

```bash
cd backend
./start.bat          # Windows
# or
python -m uvicorn app.main:app --reload  # macOS/Linux
```

### Making Changes

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes (frontend or backend)
3. Test thoroughly
4. Commit and push: `git push origin feature/your-feature`
5. Create a Pull Request

## 🐛 Troubleshooting

### Frontend Issues
- See [Frontend README](./frontend/README.md#troubleshooting)

### Backend Issues
- See [Backend README](./backend/README.md#troubleshooting)

### Common Issues

**Backend port already in use?**
```powershell
# Windows
Get-NetTCPConnection -LocalPort 8000 | Stop-Process -Force

# macOS/Linux
lsof -ti:8000 | xargs kill -9
```

**MongoDB connection failed?**
- Verify connection string in `backend/.env`
- Check IP whitelisting in MongoDB Atlas
- Ensure credentials are correct

## 📝 License

This project is proprietary and confidential.

## 👤 Contact

For questions or issues, contact: mitch.j.rose@outlook.com




