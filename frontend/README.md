# Movie Recommender Frontend (React + Vite + TypeScript)

This is a lightweight frontend for the FastAPI backend in this repo.
It implements:
- Sign in
- Create/join group (guest or user)
- Genre nomination (each participant picks up to 2 via toggle buttons) at /g/:code/nominate-genres
- Genre voting (plurality tally; vote up to 3 across nominated genres) at /g/:code/vote-genres
- Movie voting (swipe-style) at /g/:code/movies
- Group lobby hub with navigation and a host-only “Start Over” (reset genres) action

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


## Troubleshooting
- If you see an error like "Vite requires Node.js version 20.19+ or 22.12+" or "TypeError: crypto.hash is not a function" when running `npm run dev`, it means your environment installed a Vite version that requires a newer Node.
- This project now pins Vite to v5 which supports Node 18. To fix your local install:
  1. Remove `node_modules` in `frontend/`
  2. Reinstall deps: `npm install`
  3. Run the dev server: `npm run dev`
- Alternatively, upgrade Node to >=20.19 and you can use newer Vite versions.
