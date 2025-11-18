# MovieRecommender

A collaborative movie recommendation app where groups can vote on genres and select movies together.

## Features

- 🎭 **Genre Nomination & Voting** - Group members nominate and vote on movie genres
- 🎬 **Movie Selection** - Swipe-style voting on movie candidates
- 👥 **Group Management** - Create groups, invite friends, and track progress
- 🏆 **Winner Display** - Beautiful display of selected genres and final movie choice
- 🔐 **User Authentication** - Secure login and group membership

## Tech Stack

- **Frontend**: React + TypeScript + Vite
- **Backend**: FastAPI (Python)
- **Database**: SQLite with SQLModel
- **Movie Data**: TMDb API
- **Deployment**: AWS EC2 with GitHub Actions

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Node.js 22 or higher
- TMDb API credentials (free account)

### 1. Clone the Repository

```bash
git clone https://github.com/Henry1997Do/MovieRecommender.git
cd MovieRecommender
```

### 2. Set Up TMDb API Key

The app requires a TMDb API key to fetch movie data.

#### Get Your TMDb API Key

1. Go to [https://www.themoviedb.org/signup](https://www.themoviedb.org/signup)
2. Create a free account
3. Navigate to Settings → API
4. Request an API key (choose "Developer" option)
5. You'll receive:
   - **API Key (v3)** - shorter key
   - **API Read Access Token (v4)** - longer token (preferred)

#### Configure the API Key

Create a `.env` file in the project root:

```bash
# TMDb API Configuration
# Get your API key from: https://www.themoviedb.org/settings/api

# Option 1: Use API Key (v3)
TMDB_API_KEY=your_api_key_here

# Option 2: Use Read Access Token (v4) - preferred
TMDB_READ_TOKEN=your_long_token_here

# Region for watch providers (default: US)
TMDB_REGION=US
```

**Note**: Use either `TMDB_API_KEY` or `TMDB_READ_TOKEN`. The v4 token is preferred.

### 3. Backend Setup

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at: **http://localhost:8000**

#### Backend API Documentation

Once the backend is running, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 4. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```

The frontend will be available at: **http://localhost:5173**

## Accessing the Application

### Local Development

1. **Start Backend**: `uvicorn app.main:app --reload --port 8000` (from project root)
2. **Start Frontend**: `npm run dev` (from `frontend/` directory)
3. **Open Browser**: Navigate to http://localhost:5173

### Production Deployment

The app is automatically deployed to AWS EC2 via GitHub Actions when you push to the `master` branch.

- **Frontend**: Served via Nginx (port 80)
- **Backend**: Uvicorn on 127.0.0.1:8000 managed by systemd (`movierec`) and proxied by Nginx
- **Access**: http://ec2-13-59-13-187.us-east-2.compute.amazonaws.com

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## Project Structure

```
MovieRecommender/
├── app/                      # Backend (FastAPI)
│   ├── main.py              # Main application & API routes
│   ├── db.py                # Database models
│   └── services/
│       └── recommendations.py  # Movie recommendation logic
├── frontend/                 # Frontend (React + TypeScript)
│   ├── src/
│   │   ├── pages/           # Page components
│   │   ├── components/      # Reusable components
│   │   └── api.ts           # API client
│   └── dist/                # Production build
├── tests/                    # Backend tests
├── .github/workflows/        # CI/CD configuration
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (create this)
└── README.md                # This file
```

## Usage Guide

### Creating a Group

1. Sign up or sign in
2. Click "New Group"
3. Share the group code with friends

### Nominating Genres

1. Each member nominates up to 3 genres
2. Wait for all members to nominate

### Voting on Genres

1. Distribute your votes among nominated genres
2. Top genres are selected for movie recommendations

### Selecting a Movie

1. Swipe through movie candidates
2. Vote Yes 👍 or No 👎
3. When everyone agrees, the movie is finalized!

### Viewing Results

- **Our Group Page**: See winning genres and selected movie
- **Vote Genres Page**: View genre voting results
- **Movies Page**: See the final movie choice

## Environment Variables

### Backend (.env in project root)

```bash
# TMDb API (required)
TMDB_API_KEY=your_api_key          # Option 1: v3 API Key
TMDB_READ_TOKEN=your_token         # Option 2: v4 Read Token (preferred)
TMDB_REGION=US                     # Region for watch providers

# Database (optional, defaults to SQLite)
DATABASE_URL=sqlite:///./app.db
```

### Frontend (optional)

Create `frontend/.env` to override API base URL:

```bash
VITE_API_BASE=http://localhost:8000
```

## Testing

```bash
# Run backend tests
pytest

# Run with coverage
pytest --cov=app tests/
```

## Troubleshooting

### Backend won't start

- **Check Python version**: Must be 3.9+
  ```bash
  python3 --version
  ```
- **Verify .env file**: Ensure TMDb credentials are set
- **Check port availability**: Port 8000 must be free
  ```bash
  lsof -i :8000
  ```

### Frontend can't connect to backend

- **Verify backend is running**: Check http://localhost:8000/docs
- **Check API_BASE**: Should be `http://localhost:8000` in development
- **CORS issues**: Backend allows all origins in development

### TMDb API errors

- **503 Error**: TMDb credentials not configured or invalid
- **Verify credentials**: Test at http://localhost:8000/config
- **Check .env file**: Ensure it's in the project root, not in `frontend/`

### Movies not loading

- **Check TMDb API key**: Visit http://localhost:8000/config
- **Verify internet connection**: TMDb API requires internet access
- **Check backend logs**: Look for API errors in the terminal

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Acknowledgments

- Movie data provided by [The Movie Database (TMDb)](https://www.themoviedb.org/)
- Icons from emoji sets
- Built with React, FastAPI, and ❤️
