# BEHAVIORAL BIOMETRICS: TYPING PATTERN AUTHENTICATION SYSTEM
## Project 7 — Technical Submission Report
### ByoSync · Kavion Intelligence Pvt. Ltd. · Internship 2026

---

## EXECUTIVE SUMMARY

This project implements a **behavioral biometrics authentication system** based on keystroke dynamics analysis. The system captures millisecond-precision typing timing from a browser interface, engineers a 24-dimensional feature vector per session, and verifies identity using a **4-algorithm weighted ensemble** comprising z-score similarity, nearest-sample distance, Isolation Forest, and One-Class SVM.

The full stack is production-pattern: FastAPI + Uvicorn backend, JavaScript `performance.now()` keystroke capture, Streamlit demo UI, pytest test suite, and append-only JSONL activity logging — all running locally with file-based persistence.

**Key Achievements:**

| Area | Achievement |
|------|-------------|
| Feature Engineering | 24-dimensional keystroke feature vector |
| ML Ensemble | 4-algorithm weighted voting (z-score + nearest + IsoForest + OC-SVM) |
| API | REST API with standardized response shape and activity logging |
| Persistence | Profiles survive server restart via `data/profiles.pkl` |
| Frontend | JS `performance.now()` capture at sub-millisecond precision |
| Privacy | Raw keystrokes never stored; activity log stores scores only |

**Observed Performance (manual demo testing):**

| Scenario | Confidence Range | Decision |
|----------|-----------------|----------|
| Same user, consistent rhythm | 0.72 – 0.85 | pass |
| Different user, same phrase | 0.35 – 0.55 | fail |
| Same user, deliberate rhythm change | 0.55 – 0.65 | inconclusive / fail |

---

## 1. INTRODUCTION

### 1.1 Motivation

Traditional authentication methods — passwords, PINs, OTPs — provide only point-of-entry security. They are vulnerable to phishing, credential stuffing, and shoulder surfing. Once breached, they offer no ongoing protection.

**Behavioral biometrics** solves a different problem: it authenticates *how* a person interacts with a device, not just *what they know*. Keystroke dynamics in particular are:

- **Passive** — no additional hardware or user action required
- **Continuous** — can be applied throughout a session, not just at login
- **Hard to replicate** — rhythm is subconscious and difficult to mimic precisely
- **Low cost** — browser `keydown`/`keyup` events are sufficient input

### 1.2 Problem Statement

Build a local typing pattern authentication system that:

1. Captures keystroke timing at millisecond precision from a browser
2. Extracts a discriminative 24-dimensional feature vector from raw timing events
3. Enrolls a user profile from ≥ 3 typing sessions
4. Verifies subsequent sessions against that profile using a 4-algorithm ML ensemble
5. Returns standardized pass / inconclusive / fail decisions with confidence scores
6. Persists profiles across server restarts and logs all events to an audit trail

### 1.3 Scope

This is an educational demo. It runs fully locally — no database, no Docker, no cloud. Security tradeoffs (unauthenticated endpoints, pickle serialization, open CORS) are acknowledged and appropriate for this scope.

---

## 2. LITERATURE REVIEW & BACKGROUND

### 2.1 Keystroke Dynamics

Keystroke dynamics was first studied formally by Gaines et al. (1980) and formalized by Joyce & Gupta (1990) as a biometric modality. The core insight is that each individual's typing rhythm is statistically stable within a person and discriminative across people.

**Core timing signals:**

```
  Key A pressed          Key A released      Key B pressed
       |                      |                   |
  ─────▼──────────────────────▼───────────────────▼──────────▶ time
       |◄────── Dwell Time ──►|◄── Flight Time ──►|
       |                                           |
       |◄──────────── Digraph Time ───────────────►|
```

- **Dwell time**: How long a key is held (`release_time - press_time`)
- **Flight time**: Gap between releasing one key and pressing the next
- **Digraph time**: Press-to-press latency for consecutive key pairs

### 2.2 Authentication Approaches

**Statistical Methods** — profile as mean/std per feature, compute normalized distance at verify time. Fast, interpretable, low data requirement. Used as the primary signal in this project (z-score component, weight 0.35).

**Anomaly Detection** — treat enrolled samples as the inlier distribution; flag deviations as impostors. Isolation Forest (Liu et al., 2008) and One-Class SVM (Schölkopf et al., 2001) implement this without requiring negative (impostor) training data — essential for a one-class enrollment scenario.

**Deep Learning** — LSTM and Transformer approaches (TypeNet, Acien et al. 2021) show EER < 3% on large datasets. Out of scope due to data requirements.

### 2.3 Why a 4-Algorithm Ensemble?

A single algorithm has known failure modes at small enrollment sizes:

| Algorithm | Weakness at N=3 sessions |
|-----------|--------------------------|
| Z-score only | Sensitive to non-Gaussian feature distributions |
| IsolationForest only | Unreliable with fewer than 10 samples |
| One-Class SVM only | Sensitive to RBF kernel bandwidth |
| Nearest-sample only | Fails when enrollment samples have high variance |

Combining all four with calibrated weights produces a more robust decision boundary.

### 2.4 Regulatory Context

- **GDPR (Europe)**: Requires explicit consent for biometric processing; data minimisation (Article 5(1)(c))
- **BIPA (Illinois)**: Mandates written consent and data retention policies
- **CCPA (California)**: Provides opt-out rights for biometric data

This implementation stores statistical templates (feature vectors), not raw keystrokes — aligned with data minimisation principles.

---

## 3. SYSTEM ARCHITECTURE

### 3.1 Full Stack Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                            │
│                                                                │
│  ┌─────────────────────────┐   ┌──────────────────────────┐   │
│  │    demo/capture.html    │   │  demo/streamlit_app.py   │   │
│  │  JS keydown/keyup       │   │  Enroll + Verify UI      │   │
│  │  performance.now()      │   │  Score display           │   │
│  └────────────┬────────────┘   └────────────┬─────────────┘   │
└───────────────┼─────────────────────────────┼─────────────────┘
                │  HTTP POST (JSON)            │  HTTP
                ▼                             ▼
┌────────────────────────────────────────────────────────────────┐
│                  API LAYER  (app/main.py)                      │
│                                                                │
│  GET /health    GET /version    GET /users                     │
│  GET /profile/{user_id}                                        │
│  POST /enroll_typing            POST /verify_typing            │
│                                                                │
│  FastAPI + Uvicorn · Pydantic schemas · CORS middleware        │
│  StandardResponse shape on every endpoint                      │
│  startup() event loads profiles.pkl into memory               │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────┐
│               SERVICE LAYER  (app/services.py)                 │
│                                                                │
│  TypingBiometricsService                                       │
│  ├── extract_features()   → 24-D numpy array                  │
│  ├── enroll_user()        → fit scaler + IsoForest + OC-SVM   │
│  ├── authenticate()       → 4-algorithm ensemble vote         │
│  ├── _save_profiles()     → pickle to data/profiles.pkl       │
│  ├── _load_profiles()     → unpickle on init                  │
│  └── _log()               → append to data/activity_log.jsonl │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────┐
│               STORAGE LAYER  (app/storage.py)                  │
│                                                                │
│  data/profiles.pkl         enrolled user profiles (pickle)    │
│  data/activity_log.jsonl   audit log (append-only JSONL)      │
│  data/.gitkeep             keeps data/ tracked; files ignored  │
└────────────────────────────────────────────────────────────────┘
```

### 3.2 Request Lifecycle

```
  Browser types fixed phrase
          |
          ▼
  JS collects {key, press_time, release_time} per keystroke
          |
          ▼
  POST /enroll_typing  OR  POST /verify_typing
  body: { user_id, sessions: [ { keystrokes: [...] } ] }
          |
          ▼
  main.py validates with Pydantic schema
          |
          ▼
  services.py::extract_features()
  → 24-D feature vector per session
          |
          ├────────────────────────────────────┐
          ▼                                    ▼
   ENROLL path                          VERIFY path
   ─────────────                        ───────────
   fit StandardScaler                   transform features
   fit IsolationForest                  run 4 algorithms
   fit OneClassSVM                      blend scores
   store profile dict                   return confidence
   _save_profiles() → pkl               _log() → jsonl
          |                                    |
          └──────────────┬─────────────────────┘
                         ▼
               StandardResponse JSON
               { module, score, decision,
                 confidence, metadata,
                 activity_event, latency_ms }
```

### 3.3 Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, FastAPI, Uvicorn |
| Frontend capture | HTML + JavaScript (`performance.now()`) |
| Demo UI | Streamlit |
| ML | scikit-learn: `IsolationForest`, `OneClassSVM`, `StandardScaler` |
| Numerics | NumPy |
| Persistence | pickle (`profiles.pkl`), JSONL (`activity_log.jsonl`) |
| Testing | pytest, pytest-asyncio |
| API docs | OpenAPI / Swagger at `/docs` |

---

## 4. FEATURE ENGINEERING

### 4.1 Raw Input

The JavaScript capture page records one event per keystroke:

```json
{ "key": "t", "press_time": 1024.3, "release_time": 1089.7 }
```

`press_time` and `release_time` are `performance.now()` values in milliseconds.

### 4.2 Derived Timing Signals

```
Keystrokes:  [A]──────[B]──────[C]
             press release press release

Dwell(A)    = release(A) - press(A)
Flight(A→B) = press(B)   - release(A)
Digraph(A→B)= press(B)   - press(A)
```

### 4.3 24-Dimensional Feature Vector

| Index | Group | Feature |
|-------|-------|---------|
| 0 | Dwell | Mean dwell time |
| 1 | Dwell | Std deviation of dwell time |
| 2 | Dwell | Median dwell time |
| 3 | Dwell | 25th percentile dwell time |
| 4 | Dwell | 75th percentile dwell time |
| 5 | Flight | Mean flight time |
| 6 | Flight | Std deviation of flight time |
| 7 | Flight | Median flight time |
| 8 | Digraph | Mean digraph time |
| 9 | Digraph | Std deviation of digraph time |
| 10 | Digraph | Max digraph time |
| 11 | Digraph | Min digraph time |
| 12 | Rhythm | Typing speed (keystrokes/sec × 1000) |
| 13 | Behavior | Backspace rate (backspaces / total keys) |
| 14 | Pause | Pause count (flight time > 500 ms) |
| 15 | Pause | Average pause duration |
| 16 | Dwell | Max dwell time |
| 17 | Dwell | Min dwell time |
| 18 | Flight | Max flight time |
| 19 | Flight | Min flight time |
| 20 | Dwell | Variance of dwell time |
| 21 | Session | Total session duration (ms) |
| 22 | Pause | Pause ratio (pauses / total flight intervals) |
| 23 | Behavior | Raw backspace count |

**Phrase-dependence:** Features 0–11 (dwell, flight, digraph) are digraph-specific — they change with the typed phrase. Features 12–15 and 21–23 (speed, backspace, pause, duration) are phrase-agnostic and remain discriminative across different text.

---

## 5. ML ENSEMBLE — ENROLLMENT

### 5.1 Enrollment Flow

```
  3+ typing sessions
        |
        ▼
  extract_features() per session
  → matrix shape: (N_sessions × 24)
        |
        ▼
  StandardScaler.fit_transform(matrix)
  → zero-mean, unit-variance scaled matrix
        |
        ├──► IsolationForest(contamination=0.1, random_state=42).fit(scaled)
        |
        └──► OneClassSVM(kernel='rbf', gamma='auto', nu=0.1).fit(scaled)
        |
        ▼
  Store in user_profiles[user_id]:
  {
    "mean":        np.mean(matrix, axis=0),
    "std":         np.std(matrix, axis=0) + 1e-6,
    "samples":     [fv1, fv2, fv3, ...],
    "scaler":      StandardScaler instance,
    "iso_model":   IsolationForest instance,
    "oc_svm":      OneClassSVM instance,
    "enrolled_at": ISO timestamp,
    "sample_count": N
  }
        |
        ▼
  _save_profiles() → data/profiles.pkl
```

**Why one-class classifiers?** Both IsolationForest and OneClassSVM learn only from the enrolled user's samples. They require no impostor data — which is unavailable at enrollment time. This is the correct paradigm for biometric enrollment.

---

## 6. ML ENSEMBLE — VERIFICATION

### 6.1 Four-Algorithm Voting Pipeline

```
  Incoming session keystrokes
            |
            ▼
     extract_features()
     → test vector x  (shape: 24,)
            |
     ┌──────┴─────────────────────────────────┐
     |                                        |
     ▼                                        ▼
  ┌──────────────────────┐      ┌─────────────────────────┐
  │  Algorithm 1         │      │  Algorithm 2            │
  │  Z-Score Similarity  │      │  Nearest Sample Sim.    │
  │                      │      │                         │
  │  z = ||(x-μ)/σ||     │      │  For each enrolled sᵢ:  │
  │  sim = 1-(z/5.0)     │      │  d = ||(x-sᵢ)/σ||/3.0  │
  │  clip to [0,1]       │      │  nearest = max(1-d)     │
  │                      │      │  clip to [0,1]          │
  │  Weight: 0.35        │      │  Weight: 0.25           │
  └──────────┬───────────┘      └──────────┬──────────────┘
             |                             |
  ┌──────────┴───────────┐      ┌──────────┴──────────────┐
  │  Algorithm 3         │      │  Algorithm 4            │
  │  Isolation Forest    │      │  One-Class SVM          │
  │                      │      │                         │
  │  scaler.transform(x) │      │  scaler.transform(x)    │
  │  decision_function() │      │  predict()              │
  │  iso_norm =          │      │  1.0 if inlier          │
  │  clip(score+0.5,0,1) │      │  0.0 if outlier         │
  │                      │      │                         │
  │  Weight: 0.20        │      │  Weight: 0.20           │
  └──────────┬───────────┘      └──────────┬──────────────┘
             |                             |
             └──────────────┬──────────────┘
                            ▼
       confidence = 0.35 × z_sim
                  + 0.25 × nearest
                  + 0.20 × iso_norm
                  + 0.20 × svm_score
       confidence = clip(confidence, 0.0, 1.0)
                            |
               ┌────────────┼─────────────┐
               ▼            ▼             ▼
           >= 0.70      0.60–0.70      < 0.60
            PASS       INCONCLUSIVE    FAIL
```

### 6.2 Weight Rationale

| Algorithm | Weight | Rationale |
|-----------|--------|-----------|
| Z-score | **0.35** | Most interpretable; measures deviation from enrolled mean in normalized space; most reliable at N=3 |
| Nearest sample | **0.25** | Captures within-session variance; robust to outlier enrollment sessions |
| Isolation Forest | **0.20** | Adds nonlinear decision boundary; less reliable at N=3 → lower weight |
| One-Class SVM | **0.20** | Kernel-based similarity; binary output means lower score granularity |

### 6.3 Decision Thresholds

```
  0.0          0.60         0.70          1.0
   |────────────|────────────|─────────────|
   |    FAIL    |INCONCLUSIVE|    PASS     |
   └────────────┴────────────┴─────────────┘
```

---

## 7. API REFERENCE

### 7.1 Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Returns `{"status": "ok", "module": "typing_biometrics", "version": "0.1.0"}` |
| GET | `/version` | Module metadata and feature list |
| GET | `/users` | List all enrolled user IDs |
| GET | `/profile/{user_id}` | Profile summary (sample count, enrolled_at, feature means) |
| POST | `/enroll_typing` | Enroll user from ≥ 3 sessions |
| POST | `/verify_typing` | Verify session against enrolled profile |

### 7.2 Standard Response Shape

```json
{
  "module": "typing_biometrics",
  "score": 0.74,
  "decision": "pass",
  "confidence": 0.74,
  "metadata": {
    "threshold": 0.7,
    "authenticated": true
  },
  "activity_event": {
    "event_id": "evt_a1b2c3d4",
    "user_id": "alice",
    "module": "typing_biometrics",
    "action": "verify",
    "result": "pass",
    "score": 0.74,
    "timestamp": "2026-06-26T10:00:00Z"
  },
  "latency_ms": 18
}
```

### 7.3 curl Examples

```bash
# Health check
curl http://localhost:8000/health

# Enroll
curl -X POST http://localhost:8000/enroll_typing \
  -H "Content-Type: application/json" \
  -d '{"user_id": "alice", "sessions": [{"keystrokes": [...]}]}'

# Verify
curl -X POST http://localhost:8000/verify_typing \
  -H "Content-Type: application/json" \
  -d '{"user_id": "alice", "session": {"keystrokes": [...]}}'

# List users
curl http://localhost:8000/users
```

---

## 8. PERSISTENCE & AUDIT LOGGING

### 8.1 Profile Persistence Flow

```
  Server starts
       |
       ▼
  startup() event fires
       |
       ▼
  storage.load_user_profiles()
       |
       ├── data/profiles.pkl exists?
       |        YES                  NO
       |         |                   |
       |         ▼                   ▼
       |   unpickle dict         empty dict {}
       |         |
       └── biometrics_service.user_profiles = dict
       |
       ▼
  [server handles requests]
       |
  POST /enroll_typing succeeds
       |
       ▼
  _save_profiles() → pickle.dump → data/profiles.pkl
       |
       ▼
  Server restart → profiles survive ✓
```

`_save_profiles()` is called after every successful enroll — not periodically. No enrolled data is lost even if the server crashes immediately after enrollment.

### 8.2 Activity Log Format

Every enroll and verify appends one JSONL line:

```json
{"event": "enroll", "user_id": "alice", "time": "2026-06-26T10:00:00"}
{"event": "verify", "user_id": "alice", "confidence": 0.74, "result": true, "time": "2026-06-26T10:01:00"}
```

Raw keystrokes and typed text are **never written** to the log.

---

## 9. DEMO RUN COMMANDS

```bash
# 1. Clone and install
git clone https://github.com/lokanshu7/typing_biometrics.git
cd typing_biometrics
pip install -r requirements.txt

# 2. Start API (must run from inside app/ due to module imports)
cd app
uvicorn main:app --reload --port 8000

# 3. Open keystroke capture page
open ../demo/capture.html

# 4. Start Streamlit demo (new terminal, from project root)
streamlit run demo/streamlit_app.py

# 5. Run tests
pytest tests/ -v

# 6. View Swagger docs
open http://localhost:8000/docs
```

---

## 10. TEST SUITE

| Test | File | What it covers |
|------|------|----------------|
| `test_root` | test_api.py | Root endpoint returns correct message and dict type |
| `test_enroll_user` | test_api.py | Enroll unique timestamped user with 3 sessions; assert decision membership |
| Service tests | test_services.py | Feature extraction and profile logic at the service layer |

Tests use `asyncio.run()` to call FastAPI endpoints directly — appropriate for unit testing without a running server.

**Known gaps:** `/health` and `/version` tests missing; no server-restart persistence test; assertions are membership checks only.

---

## 11. RESULTS & PERFORMANCE

### 11.1 Manual Demo Results

| Test Case | Confidence | Decision |
|-----------|-----------|----------|
| Enrolled user, normal typing | 0.72 – 0.85 | pass |
| Enrolled user, deliberate slow typing | 0.55 – 0.65 | inconclusive |
| Different user, same phrase | 0.35 – 0.55 | fail |
| Enrolled user, different phrase | 0.40 – 0.60 | fail / inconclusive |

### 11.2 Comparison with Alternative Modalities

| Modality | FAR (approx.) | FRR (approx.) | Hardware | Continuous auth |
|----------|--------------|--------------|----------|-----------------|
| **Typing biometrics** | ~8% | ~12% | None | Yes |
| Fingerprint | 0.1–1% | 1–3% | Sensor | No |
| Face recognition | 0.1–5% | 2–10% | Camera | Partial |
| Voice recognition | 2–5% | 5–10% | Microphone | No |
| Password only | Variable | 0% | None | No |

*Literature estimates (Teh et al., 2020). This implementation's EER was not formally measured — insufficient test subjects for a statistically valid evaluation.*

---

## 12. SECURITY & PRIVACY

### 12.1 Threat Model

```
ATTACK SURFACE
──────────────
1. Replay Attack
   Attacker records legitimate POST body and replays it.
   Status: VULNERABLE — no nonce or timestamp validation
   Mitigation: Add per-session challenge token

2. Mimicry Attack
   Attacker practices imitating victim's typing rhythm.
   Status: LOW RISK — sub-ms timing precision is hard to replicate consciously
   Mitigation: Longer enrollment phrases; more features

3. Client-Side Spoofing
   Attacker crafts fake keystroke JSON with ideal timing values.
   Status: VULNERABLE — no server-side plausibility checks
   Mitigation: Validate dwell > 0, flight > 0, speed within human bounds

4. Profile Exfiltration
   Attacker reads data/profiles.pkl from disk.
   Status: VULNERABLE — unencrypted; unsafe pickle deserialization
   Mitigation: Encrypt at rest; replace pickle with JSON + numpy arrays
```

### 12.2 Privacy Design

- Feature vectors stored, not raw keystrokes — typed content cannot be reconstructed
- Activity log stores only scores and decisions, not timing sequences
- `data/` is gitignored — no biometric data reaches GitHub
- Aligned with GDPR Article 5(1)(c) data minimisation principle

### 12.3 Known Security Tradeoffs (Demo Scope)

| Issue | Status | Priority if productionised |
|-------|--------|--------------------------|
| CORS `allow_origins=["*"]` | Open | High — restrict to localhost |
| Unauthenticated endpoints | Open | High — add API key header |
| Pickle deserialization | Unsafe | High — replace with JSON |
| No rate limiting | Open | Medium |
| Client-side timing only | Spoofable | Medium |

---

## 13. LIMITATIONS

1. **Keyboard and device dependency.** Dwell and flight times differ substantially across keyboard types. A profile enrolled on a laptop keyboard may fail on a mechanical keyboard or phone.

2. **Fixed phrase requirement.** Features 0–11 (digraph-based) are phrase-specific. Changing the enrollment phrase degrades accuracy significantly for ~50% of the feature vector.

3. **Small enrollment set.** IsolationForest and One-Class SVM are unreliable at N < 10. EER improves significantly with 10+ sessions.

4. **No formal EER measurement.** With a 2-person demo setup, Equal Error Rate cannot be computed. A proper evaluation requires 50+ users (e.g., CMU Keystroke Dynamics Dataset).

5. **Typing pattern drift.** Rhythm changes over time with injury, fatigue, or new hardware. Profiles need periodic re-enrollment or adaptive updating.

6. **Pickle security.** `profiles.pkl` uses Python pickle, which executes arbitrary code on deserialization from untrusted sources. Acceptable locally; unacceptable in production.

---

## 14. FUTURE ENHANCEMENTS

### Short-Term

1. Restrict CORS to `localhost` — single highest-priority security fix
2. Replace pickle with JSON + base64 numpy — eliminates deserialization risk
3. Raise enrollment minimum to 5 sessions — measurably improves IsoForest/SVM reliability
4. Add `/health`, `/version`, and persistence restart tests
5. Phrase-agnostic fallback — use only features 12–23 when phrase mismatch detected

### Medium-Term

6. Evaluate on CMU Keystroke Dataset — compute proper EER, FAR, FRR across 50+ users
7. Adaptive profile updates — fold high-confidence verify sessions back into enrolled samples
8. Mobile touch events — extend `capture.html` to `touchstart`/`touchend` for mobile

### Long-Term Research Directions

9. **LSTM/Transformer** — sequence models capture inter-key dependencies that fixed feature vectors miss. TypeNet achieves EER < 3% on large datasets.
10. **Federated learning** — profile updates without sending raw features to a server
11. **Multi-modal fusion** — combine with mouse dynamics or navigation patterns for continuous session authentication
12. **Explainability** — surface which features drove a fail decision (e.g., "dwell time was 2σ above enrolled mean")

---

## 15. CONCLUSION

This project delivers a complete, end-to-end behavioral biometrics demo covering the full engineering stack: browser-level keystroke capture, a 24-feature ML pipeline, a 4-algorithm weighted ensemble, a REST API with standardized response shape, profile persistence that survives server restarts, and an append-only audit log.

The most significant technical contribution is the ensemble design — combining z-score distance (interpretable baseline, weight 0.35), nearest-sample matching (variance-aware, weight 0.25), Isolation Forest (nonlinear anomaly detection, weight 0.20), and One-Class SVM (kernel similarity, weight 0.20) — each weighted to reflect reliability at the small sample sizes typical of a demo enrollment scenario.

The system demonstrates that meaningful behavioral biometrics is achievable with no specialized hardware, no database, and no cloud infrastructure, using only browser JavaScript and a standard Python ML stack.

---

## REFERENCES

1. Gaines, R.S., et al. (1980). "Authentication by Keystroke Timing: Some Preliminary Results." RAND Corporation.
2. Joyce, R. & Gupta, G. (1990). "Identity Authentication Based on Keystroke Latencies." *Communications of the ACM, 33(2).*
3. Monrose, F. & Rubin, A. (2000). "Keystroke Dynamics as a Biometric for Authentication." *Future Generation Computer Systems, 16(4).*
4. Teh, P.S., et al. (2020). "A Survey of Keystroke Dynamics Biometrics." *The Scientific World Journal.*
5. Acien, A., et al. (2021). "TypeNet: Deep Learning Keystroke Biometrics." *IEEE Transactions on Biometrics, Behavior, and Identity Science.*
6. Liu, F.T., et al. (2008). "Isolation Forest." *IEEE International Conference on Data Mining.*
7. Schölkopf, B., et al. (2001). "Estimating the Support of a High-Dimensional Distribution." *Neural Computation.*
8. European Commission (2018). *GDPR — Article 5(1)(c): Data Minimisation.*
9. Illinois General Assembly (2008). *Biometric Information Privacy Act (BIPA).*

---

## APPENDIX A: PROJECT DELIVERABLES

| File | Description |
|------|-------------|
| `app/main.py` | FastAPI app, all endpoints, startup event |
| `app/schemas.py` | Pydantic request/response models |
| `app/services.py` | Feature extraction, enrollment, ensemble verification |
| `app/storage.py` | Local file read/write helpers |
| `demo/capture.html` | JS keystroke capture page |
| `demo/streamlit_app.py` | Interactive demo UI |
| `tests/test_api.py` | API endpoint tests |
| `tests/test_services.py` | Service layer unit tests |
| `requirements.txt` | Pinned dependencies |
| `pytest.ini` | pytest configuration |
| `data/.gitkeep` | Keeps data/ tracked; actual files gitignored |
| `README.md` | Installation and demo run guide |
| `report.md` | This document |

---

*Project 7: Behavioral Biometrics — Typing Pattern Demo*
*ByoSync · Kavion Intelligence Pvt. Ltd. · Internship 2026*
*Submitted by: Lokanshu Tanwar*