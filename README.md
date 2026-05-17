# Voxa — Intelligent Offline Chatbot with Web Interface

A full-stack intelligent chatbot combining a Python Flask backend with a React frontend, featuring advanced offline natural language understanding, real-time WebSocket communication, and a modern animated user interface.

## ✨ Features

### Backend (Python Flask)
- **Advanced Offline NLU** — Hybrid intent classifier combining machine learning (Logistic Regression with TF-IDF), rule-based pattern matching, and fuzzy matching fallback (no external LLM APIs required)
- **8 Intent Types** — greetings, time, calculator, weather, search, unit conversion, smart home, and general knowledge
- **Sentiment Analysis** — Lexicon-based sentiment detection with negation and intensifier handling
- **Safe Math Evaluation** — AST-based calculator that understands natural language expressions like "18 percent of 250" and "2 to the power of 10"
- **Offline Unit Conversions** — Length, mass, temperature, speed, data size, and time conversions (e.g., "10 km to miles")
- **Smart Home Simulation** — Control lights, thermostat, doors, and fans with natural language
- **Date/Time Parsing** — Understands "today", "tomorrow", weekday names, ordinal formatting
- **Real-time WebSocket Communication** — Persistent bidirectional messaging with typing indicators
- **JWT Authentication** — Secure login/register with token-based session management
- **Message Persistence** — SQLite storage with automatic PostgreSQL fallback when available
- **Follow-up Context Inheritance** — Short follow-ups like "and tomorrow?" inherit the previous intent without re-specification

### Frontend (React + Framer Motion)
- **5 Theme Variants** — Switchable color schemes (Cyan, Green, Amber, Magenta, Ice) with CSS variables
- **Fluid Animations** — Framer Motion transitions throughout UI; toggle animations in settings
- **Markdown Chat** — Bot responses render as formatted markdown with code blocks and links
- **Typewriter Streaming** — Bot responses appear character-by-character for natural feel
- **Voice Input** — Browser-based speech-to-text with visual listening state
- **Voice Output** — Synthesized speech feedback with pitch/rate control
- **Quick Actions** — 6 chips for common queries (Time, Math, Unit, Weather, Search, Joke)
- **Slash Commands** — Ctrl+K palette with fuzzy filtering for intent discovery
- **Conversation History** — Sidebar to view, load, rename, and delete past sessions
- **Settings Panel** — Theme picker, animation toggle, sound/voice controls, font scaling
- **NLU Visualization** — Admin panel showing intent confidence, entity extraction, sentiment analysis
- **Responsive Design** — Mobile-friendly interface with glass-morphism components
- **CRT Scanline Overlay** — Optional retro aesthetic for atmosphere
- **Ambient Background** — Animated particle constellation with parallax grid and aurora glow

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- SQLite (included with Python) or PostgreSQL (optional)

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python -m flask run
```

The backend starts on `http://localhost:5000`. On first run, the NLU model trains automatically (~30 seconds).

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

The frontend starts on `http://localhost:3000`.

### One-Command Setup (macOS/Linux)

```bash
bash setup.sh
```

This installs both backend and frontend, then runs both servers.

## 📋 Available Intents

| Intent | Examples | Handler |
|--------|----------|---------|
| **greetings** | "hello", "hi", "hey", "what's up" | Built-in responses |
| **time** | "what time is it?", "today's date", "what day is tomorrow?" | `DateTime` handler |
| **calculator** | "5 plus 3", "18 percent of 250", "square root of 144" | `Calculator` handler |
| **weather** | "what's the weather?", "weather in London" | OpenWeatherMap API (API key in `.env`) |
| **search** | "search for Python", "find AI news" | Google Custom Search API (API keys in `.env`) |
| **unit_conversion** | "10 km to miles", "100 celsius in fahrenheit" | `Unit` handler |
| **smart_home** | "turn on the lights", "set temperature to 72" | `SmartHome` handler (simulated) |
| **general_knowledge** | "what is Python?", "tell me about quantum computing" | Built-in knowledge base |

## 🏗 Project Structure

```
Voxa/
├── backend/
│   ├── app.py                     # Flask app with WebSocket support
│   ├── requirements.txt           # Python dependencies (verified versions)
│   ├── .env                       # API keys and database config
│   ├── nlu/
│   │   ├── intent_classifier.py   # Hybrid ML classifier (TF-IDF + LogReg + rules)
│   │   ├── entity_extractor.py    # Location, time, number entity extraction
│   │   ├── context_manager.py     # Follow-up context and conversation state
│   │   ├── sentiment.py           # Lexicon-based sentiment analysis
│   │   └── nlu_engine.py          # NLU pipeline orchestrator
│   └── actions/
│       ├── calculator_handler.py  # Safe math evaluation via AST
│       ├── datetime_handler.py    # Date/time parsing and formatting
│       ├── unit_handler.py        # Offline unit conversions
│       ├── search_handler.py      # Web search via Google API
│       ├── weather_handler.py     # Weather via OpenWeatherMap API
│       └── smarthome_handler.py   # Simulated smart home
│
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── index.css              # Global base styles
│   │   ├── App.js                 # Root component with screen transitions
│   │   ├── App.css                # Design system (colors, buttons, forms)
│   │   ├── contexts/
│   │   │   └── SettingsContext.js # Theme, animations, sound, voice settings
│   │   ├── hooks/
│   │   │   └── useSound.js        # Web Audio API synthesized UI tones
│   │   ├── services/
│   │   │   └── chatService.js     # WebSocket and REST API client
│   │   └── components/
│   │       ├── ChatInterface.js   # Main chat UI with message rendering
│   │       ├── ChatInterface.css
│   │       ├── LoginScreen.js     # Auth UI (login/register)
│   │       ├── LoginScreen.css
│   │       ├── LoadingScreen.js   # Boot sequence animation
│   │       ├── LoadingScreen.css
│   │       ├── Background.js      # Animated particles + parallax + aurora
│   │       ├── Background.css
│   │       ├── HistorySidebar.js  # View/manage past conversations
│   │       ├── HistorySidebar.css
│   │       ├── SettingsPanel.js   # Theme, animation, and sound controls
│   │       ├── SettingsPanel.css
│   │       ├── NLUVisualization.js # Show intent confidence and entities
│   │       ├── NLUVisualization.css
│   │       ├── AdminPanel.js      # NLU training and testing
│   │       ├── AdminPanel.css
│   │       └── ui/
│   │           ├── Toast.js       # Toast notification system
│   │           └── Toast.css
│   └── package.json
│
├── docker-compose.yml             # Optional: run with Docker
├── nginx.conf                     # Optional: production reverse proxy config
└── README.md
```

## ⚙️ Configuration

### Backend `.env`

```bash
# Flask & Security
SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_SECRET_KEY=your-jwt-secret-key-change-this-in-production

# Database (defaults to SQLite; falls back if Postgres unreachable)
DATABASE_URL=sqlite:///voxa_cli.db

# Optional API Keys
WEATHER_API_KEY=your_openweathermap_api_key
GOOGLE_SEARCH_API_KEY=your_google_api_key
SEARCH_ENGINE_ID=your_search_engine_id

# Flask Config
FLASK_ENV=development
FLASK_DEBUG=True
```

The app automatically falls back to SQLite if PostgreSQL is unavailable, so you can run locally without database setup.

## 🔌 API Endpoints

### REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login and get JWT token |
| GET | `/api/auth/profile` | Get current user info |
| GET | `/api/health` | Health check |
| GET | `/api/history/<session_id>` | Get chat history for session |
| DELETE | `/api/history/<session_id>` | Delete a chat session |
| PATCH | `/api/history/<session_id>/rename` | Rename a chat session |
| GET | `/api/nlu/intents` | List all available intents |
| POST | `/api/nlu/analyze` | Analyze text and return intent/entities/sentiment |
| POST | `/api/admin/retrain` | Retrain NLU model (admin only) |
| POST | `/api/admin/upload-training` | Upload training data by intent |

### WebSocket Events

**Client → Server**
- `message` — Send user message; payload: `{ text: "..." }`

**Server → Client**
- `bot_typing` — Bot is processing (no payload)
- `bot_response` — Bot's response; payload: `{ text: "...", intent: "...", confidence: 0.95, entities: [...], sentiment: {...} }`
- `history` — List of past chat sessions
- `error` — Error message; payload: `{ message: "..." }`

## 🧠 NLU Architecture

The intent classifier uses a **hybrid approach**:

1. **ML Scoring (55%)** — Logistic Regression trained on TF-IDF features (word unigrams, bigrams, and character 2-4 grams)
2. **Rule Patterns (30%)** — Hand-crafted regex patterns for high-confidence intents (e.g., time keywords like "tomorrow", "next week")
3. **Fuzzy Matching (15%)** — SequenceMatcher fallback for typos and misspellings (threshold 0.6)

Final score: `0.55 * ml_score + 0.30 * pattern_score + 0.15 * fuzzy_score`

Training data includes 15+ examples per intent, optimized for offline accuracy without external LLM APIs.

## 🎨 Frontend Customization

### Change Theme Color
1. Click the settings gear icon in the top-right
2. Select from 5 theme colors: Cyan, Green, Amber, Magenta, Ice
3. Preference is saved to localStorage

### Disable Animations
1. Open Settings
2. Toggle "Animations" off
3. UI will use instant transitions (respects `prefers-reduced-motion`)

### Font Scaling
1. Open Settings
2. Use "Font Scale" slider (0.85x to 1.3x)
3. Affects entire UI and chat text

## 📦 Dependencies

### Backend
All pins verified for stability:
```
Flask==3.1.2
Flask-SocketIO==5.3.4
Flask-SQLAlchemy==3.0.5
Flask-JWT-Extended==4.5.3
Flask-CORS==4.0.0
SQLAlchemy==2.0.44
scikit-learn==1.7.2
nltk==3.9.2
numpy==2.3.4
requests==2.32.5
beautifulsoup4==4.14.2
```

### Frontend
```
react==18.3.1
react-dom==18.3.1
framer-motion==11.13.5
react-markdown==9.0.1
remark-gfm==4.0.0
axios==1.7.0
```

## 🧪 Testing

### Backend Integration Test
```bash
cd backend
python tests/integration_test.py
```

Tests the full NLU pipeline on sample intents: greetings, time, calculator, unit conversion.

### Frontend Development
```bash
cd frontend
npm test
```

Runs Jest tests for components and services.

## 🐳 Docker Deployment

```bash
docker-compose up
```

Starts both backend (port 5000) and frontend (port 3000) in containers with automatic database setup.

## 🔐 Security Considerations

- All math expressions evaluated via safe AST parsing (no `eval()`)
- User inputs sanitized before database storage
- JWT tokens used for session management
- Password hashing via Flask-Login
- CORS configured to allow frontend origin only
- Environment variables never exposed in client code

## 📊 Verified Features

✅ Backend registers, authenticates, and starts without errors  
✅ All REST endpoints tested and functional  
✅ WebSocket communication verified with Python socketio client  
✅ NLU model trains on startup and classifies 8 intents  
✅ Database persistence works (messages saved to SQLite)  
✅ Frontend production build compiles with zero ESLint warnings  
✅ Responsive design tested on desktop, tablet, and mobile  
✅ Animations render smoothly with Framer Motion  
✅ Theme switching and settings persistence working  
✅ Voice input/output gracefully degrades in unsupported browsers

##  Attribution Requirement

If you use this project in any form (website, app, service, or derivative code), you **must** include the following attribution in your documentation, website footer, or credits page:

> Created by Sridhanush Varma – [https://github.com/Sridhanush-Varma/Voxa](https://github.com/Sridhanush-Varma/Voxa)

Thank you for respecting the work that went into this project! 💻✨

##  License
This project is licensed under the MIT License - see the LICENSE file for details
