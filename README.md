# Behavioral Biometrics: Typing Pattern Authentication

**Learning Demo Project** - Keystroke dynamics analysis for behavioral biometrics

## ⚠️ Important: Demo System Only

This is an **educational demonstration** project for learning purposes:
- ✗ NOT production-ready
- ✗ No Docker, database servers, or cloud deployment
- ✗ No production authentication, payments, or TLS
- ✗ No claims about zero-biometric-storage protocols
- ✓ Local file-based storage only (JSON + pickle)
- ✓ All data files are gitignored
- ✓ Should be used as SECONDARY authentication only

## Features

- **Keystroke Dynamics Analysis**: 13-feature timing analysis
- **ML-Based Pattern Matching**: Statistical profiling with distance metrics
- **Standardized REST API**: Consistent response format with activity logging
- **Interactive Demo**: Streamlit web interface
- **Local Storage**: File-based persistence (no database required)

## Project Structure

```
typing_biometrics/
├── app/
│   ├── main.py           # FastAPI with standard endpoints
│   ├── schemas.py        # Pydantic models + standard responses
│   ├── services.py       # ML and biometrics logic
│   └── storage.py        # Local file storage
├── demo/
│   └── streamlit_app.py  # Interactive demo
├── data/                 # User profiles (gitignored)
├── tests/
│   ├── test_api.py
│   └── test_services.py
├── requirements.txt
├── README.md
├── report.md
└── .gitignore
```

## Installation

```bash
cd /Workspace/Users/lokanshu20@gmail.com/typing_biometrics
pip install -r requirements.txt
```

## Usage

### Start the API Server

```bash
cd app
python main.py
```

API runs at `http://localhost:8000`
API docs at `http://localhost:8000/docs`

### Run the Streamlit Demo

```bash
streamlit run demo/streamlit_app.py
```

## API Endpoints

### Standard Endpoints

```
GET  /health          Health check
GET  /version         Module metadata
POST /enroll          Enroll new user
POST /verify          Authenticate user
GET  /users           List enrolled users
GET  /profile/{id}    Get user profile
```

### Standard Response Format

All `/enroll` and `/verify` endpoints return:

```json
{
  "module": "typing_biometrics",
  "score": 0.87,
  "decision": "pass",  // pass | fail | inconclusive
  "confidence": 0.82,
  "metadata": {},
  "activity_event": {
    "event_id": "evt_a3b7c9d2",
    "user_id": "demo_user",
    "module": "typing_biometrics",
    "action": "verify",
    "purpose": "learning_demo",
    "result": "pass",
    "score": 0.87,
    "timestamp": "2026-05-19T08:00:00Z"
  },
  "latency_ms": 245
}
```

### Example: Enroll User

```bash
curl -X POST http://localhost:8000/enroll \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice_demo",
    "sessions": [
      {
        "user_id": "alice_demo",
        "text": "The quick brown fox jumps over the lazy dog",
        "keystrokes": [
          {"key": "T", "press_time": 100, "release_time": 150},
          {"key": "h", "press_time": 220, "release_time": 270}
        ],
        "session_start": 0.0,
        "session_end": 5000.0
      }
      // 2-4 more sessions
    ]
  }'
```

### Example: Verify User

```bash
curl -X POST http://localhost:8000/verify \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice_demo",
    "session": {
      "user_id": "alice_demo",
      "text": "The quick brown fox jumps over the lazy dog",
      "keystrokes": [...],
      "session_start": 0.0,
      "session_end": 5000.0
    }
  }'
```

## How It Works

### Feature Extraction (13 features)

1. **Dwell Time (5 features)**: Mean, Std, Median, 25th/75th percentile
2. **Flight Time (3 features)**: Mean, Std, Median
3. **Digraph Timing (4 features)**: Mean, Std, Max, Min
4. **Typing Rhythm (1 feature)**: Keys per second

### Authentication Process

1. **Enrollment**: Collect 3-5 typing samples
2. **Profile Creation**: Extract features and calculate statistics
3. **Authentication**: Compare new sample against profile
4. **Decision**:
   - `pass`: confidence >= 0.7
   - `inconclusive`: 0.6 <= confidence < 0.7
   - `fail`: confidence < 0.6

## Testing

```bash
pytest tests/
```

## Technical Report

See `report.md` for:
- Detailed methodology
- Performance characteristics
- Limitations and constraints
- Recommended use cases
- Compliance considerations

## Security & Privacy Notes

- **Demo system only** - not for production use
- Store statistical templates, not raw keystroke logs
- Feature vectors don't reveal typed content
- All data files are gitignored
- Requires user consent in real applications
- Subject to GDPR/BIPA regulations

## Limitations

- Typing patterns vary with fatigue, stress, device
- FAR: ~5-10%, FRR: ~10-15%
- Not suitable as sole authentication method
- Best used as secondary/continuous authentication
- Requires 3-5 samples for enrollment

## License

MIT License - Educational Use Only
