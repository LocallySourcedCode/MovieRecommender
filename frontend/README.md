# Movie Recommender Frontend (React + Vite + TypeScript)

This is a lightweight frontend for the FastAPI backend in this repo.
It implements:
- Sign in
- Create/join group (guest or user)
- Group lobby with swipe-style movie selection
- Veto button (when enabled in the group)

## Requirements
- Node.js 18+

## Install
```
cd frontend
npm install
```

## Run (dev)
```
npm run dev
```
The app will run at http://localhost:5173 and expects the API at http://localhost:8000 (configure with VITE_API_BASE).

FastAPI backend (in another shell):
```
uvicorn app.main:app --reload
```

## Tests
Run unit tests with Vitest + React Testing Library:
```
npm test
```

## Config
- VITE_API_BASE (optional): override the API base URL. Defaults to http://localhost:8000.
- Backend CORS is enabled for http://localhost:5173 in app/main.py for local development.
