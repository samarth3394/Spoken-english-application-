# 🎙️ Aspire English Hub

## AI-Powered Spoken English Practice Platform

A production-ready SaaS platform where students from spoken English coaching classes can practice English speaking anonymously with other students or AI.

### Key Features
- 🔒 Anonymous voice communication (no phone numbers shared)
- 🤖 AI Speaking Partner (Whisper + GPT + TTS)
- 🎯 Smart cross-batch matching engine
- 📊 Advanced analytics and progress tracking
- 🏆 Gamification (XP, streaks, badges, leaderboard)
- 🏢 Multi-branch, multi-batch management

### Tech Stack
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Backend**: Python FastAPI
- **Database & Auth**: Supabase PostgreSQL + Supabase Auth
- **Realtime**: WebSockets + WebRTC
- **AI**: OpenAI APIs (Whisper + GPT + TTS)

### Project Structure
```
aspire-english-hub/
├── frontend/                   # Frontend Application
│   ├── index.html             # Landing page
│   ├── css/
│   │   └── styles.css         # Global styles
│   ├── js/
│   │   ├── app.js             # Main application
│   │   ├── auth.js            # Authentication
│   │   ├── api.js             # API client
│   │   ├── websocket.js       # WebSocket handler
│   │   ├── webrtc.js          # WebRTC handler
│   │   ├── matching.js        # Matching UI
│   │   ├── ai-practice.js     # AI practice
│   │   ├── dashboard.js       # Student dashboard
│   │   ├── admin.js           # Admin dashboard
│   │   └── utils.js           # Utilities
│   └── pages/
│       ├── login.html
│       ├── signup.html
│       ├── dashboard.html
│       ├── waiting-room.html
│       ├── voice-call.html
│       ├── ai-practice.html
│       ├── reports.html
│       └── admin/
│           └── dashboard.html
├── backend/                    # Backend Application
│   ├── main.py                # FastAPI entry point
│   ├── requirements.txt
│   ├── config.py              # Configuration
│   ├── routers/
│   │   ├── auth.py
│   │   ├── students.py
│   │   ├── admin.py
│   │   ├── matching.py
│   │   ├── calls.py
│   │   └── ai.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── matching_service.py
│   │   ├── ai_service.py
│   │   ├── call_service.py
│   │   └── analytics_service.py
│   ├── websockets/
│   │   ├── manager.py
│   │   └── signaling.py
│   ├── middleware/
│   │   └── auth_middleware.py
│   ├── models/
│   │   └── schemas.py
│   └── utils/
│       └── helpers.py
├── database/
│   └── schema.sql             # Supabase schema
├── vercel.json                # Vercel config
├── railway.json               # Railway config
├── Procfile                   # Railway process
└── .env.example               # Environment template
```

### Setup Instructions

#### 1. Supabase Setup
1. Create a new Supabase project
2. Run `database/schema.sql` in the SQL editor
3. Enable Row Level Security
4. Copy API keys

#### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
uvicorn main:app --reload
```

#### 3. Frontend Setup
```bash
cd frontend
# Serve with any static server
python -m http.server 3000
```

### Deployment
- **Frontend** → Vercel (connect GitHub repo, set root to `frontend/`)
- **Backend** → Railway (connect GitHub repo, set root to `backend/`)
- **Database** → Supabase (already hosted)
