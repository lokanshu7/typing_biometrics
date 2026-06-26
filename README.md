# Behavioral Biometrics: Typing Pattern Authentication

> **An educational machine learning project demonstrating behavioral biometric authentication using keystroke dynamics, statistical profiling, and anomaly detection.**

---

## Overview

Behavioral biometrics identify users based on **how they interact with a system** rather than what they know (passwords) or what they possess (security tokens). One of the most widely studied behavioral biometric modalities is **keystroke dynamics**, where typing rhythm, timing, and interaction patterns are analyzed to authenticate users.

This project demonstrates a complete typing biometrics authentication system that captures typing behavior, extracts statistical timing features, builds personalized user profiles, and verifies future typing sessions using a hybrid machine learning approach.

The system is designed as an **educational and research-oriented implementation** that showcases backend API development, feature engineering, machine learning integration, and RESTful service design.

---

## Key Features

* REST API built using **FastAPI**
* Behavioral biometric authentication using **keystroke dynamics**
* Hybrid authentication pipeline combining statistical profiling and machine learning
* Extraction of 24 timing and behavioral features
* User enrollment using multiple typing sessions
* Confidence-based authentication decisions
* Interactive Streamlit demonstration interface
* Local file-based persistence using JSON and Pickle
* Automated unit testing using Pytest
* Standardized API responses with activity logging

---

## System Architecture

```text
Typing Session
      │
      ▼
Keystroke Capture
      │
      ▼
Feature Extraction
      │
      ▼
User Enrollment
      │
      ▼
Behavioral Profile
      │
      ▼
Verification Request
      │
      ▼
Hybrid Authentication Engine
      │
      ▼
Confidence Score
      │
      ▼
Pass / Inconclusive / Fail
```

---

## Technology Stack

| Category         | Technologies                    |
| ---------------- | ------------------------------- |
| Backend          | Python, FastAPI, Uvicorn        |
| Machine Learning | NumPy, Scikit-learn             |
| Models           | Isolation Forest, One-Class SVM |
| Validation       | Pydantic                        |
| Frontend         | Streamlit                       |
| Storage          | JSON, Pickle                    |
| Testing          | Pytest                          |

---

## Project Structure

```text
typing_biometrics/
│
├── app/
│   ├── main.py
│   ├── schemas.py
│   ├── services.py
│   ├── storage.py
│   └── data/
│
├── demo/
│   ├── capture.html
│   └── streamlit_app.py
│
├── data/
│
├── tests/
│   ├── test_api.py
│   └── test_services.py
│
├── requirements.txt
├── pytest.ini
├── report.md
└── README.md
```

---

## Installation

Clone the repository

```bash
git clone https://github.com/lokanshu7/typing_biometrics.git
cd typing_biometrics
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

## Running the Project

Start the FastAPI server

```bash
python -m app.main
```

The API will be available at:

```
http://localhost:8000
```

Interactive API documentation:

```
http://localhost:8000/docs
```

Run the Streamlit application

```bash
streamlit run demo/streamlit_app.py
```

---

## API Overview

| Method | Endpoint           | Description                    |
| ------ | ------------------ | ------------------------------ |
| GET    | /                  | API information                |
| GET    | /health            | Health status                  |
| GET    | /version           | Version information            |
| POST   | /enroll_typing     | Enroll a new user              |
| POST   | /verify_typing     | Verify a user's typing pattern |
| GET    | /users             | List enrolled users            |
| GET    | /profile/{user_id} | Retrieve user profile          |

---

## Authentication Workflow

### Enrollment

1. Collect multiple typing sessions.
2. Extract behavioral features.
3. Normalize feature vectors.
4. Train user-specific models.
5. Store the behavioral profile.

### Verification

1. Capture a new typing session.
2. Extract behavioral features.
3. Compare against the enrolled profile.
4. Compute confidence using the hybrid model.
5. Return a Pass, Inconclusive, or Fail decision.

---

## Feature Engineering

The system extracts **24 behavioral features** from each typing session, including:

### Dwell Time Statistics

* Mean
* Standard deviation
* Median
* 25th percentile
* 75th percentile
* Maximum
* Minimum
* Variance

### Flight Time Statistics

* Mean
* Standard deviation
* Median
* Maximum
* Minimum

### Digraph Timing

* Mean
* Standard deviation
* Maximum
* Minimum

### Typing Behavior

* Typing speed
* Total session duration
* Backspace rate
* Backspace count
* Pause count
* Average pause duration
* Pause ratio

These features collectively describe an individual's typing rhythm and behavioral characteristics.

---

## Machine Learning Pipeline

The authentication engine combines multiple techniques:

* Statistical profile modeling
* StandardScaler normalization
* Z-score similarity
* Nearest sample distance
* Isolation Forest anomaly detection
* One-Class SVM classification
* Weighted ensemble confidence scoring

This hybrid approach improves robustness compared to relying on a single metric.

---

## Authentication Decision

Authentication confidence is mapped to three decision levels:

| Confidence  | Decision     |
| ----------- | ------------ |
| ≥ 0.70      | Pass         |
| 0.60 – 0.69 | Inconclusive |
| < 0.60      | Fail         |

---

## Local Data Storage

The project uses lightweight local storage for demonstration purposes.

Stored data includes:

* Enrolled user profiles
* Statistical feature templates
* Machine learning models
* Authentication activity logs

No external database is required.

---

## Testing

Run all tests using:

```bash
pytest tests/ -v
```

The project includes tests covering:

* API endpoints
* Enrollment workflow
* Authentication logic
* Service layer functionality

---

## Security & Privacy

This project is intended for **educational and research purposes**.

Key considerations:

* Local execution only
* File-based persistence
* Behavioral templates are stored instead of raw passwords
* Demonstrates secondary authentication concepts
* Requires user consent in real-world deployments

---

## Limitations

This implementation is not intended as a production authentication system.

Known limitations include:

* Typing behavior changes due to fatigue, stress, or device differences
* Small enrollment datasets may affect model performance
* Local storage instead of enterprise-grade persistence
* No adaptive profile updates
* No cloud deployment or distributed architecture

---

## Future Improvements

Potential enhancements include:

* Continuous authentication
* Adaptive profile updating
* Device-aware normalization
* Deep learning sequence models
* Database-backed storage
* Docker deployment
* Cloud-native architecture
* Real-time monitoring dashboards

---

## Technical Report

A detailed technical report is available in **report.md** and includes:

* System design
* Feature engineering methodology
* Machine learning pipeline
* Experimental observations
* Testing strategy
* Limitations
* Future work

---

## Team

### Contributors

| Member               | Contribution                                                                                               |
| -------------------- | ---------------------------------------------------------------------------------------------------------- |
| **Lokanshu Tanwar**  | Backend API development, feature extraction, authentication logic, FastAPI endpoints, project architecture |
| **Mani Yadav Thota** | Machine learning pipeline                                                                                  |
| **Unnat Vijay**      | Backend development                                                                                        |
| **Drishti Yadav**    | Streamlit interface                                                                                        |
| **Utkarsh**          | JavaScript-based keystroke capture                                                                         |

---

## License

This project is released under the **MIT License** and is intended for educational, learning, and research purposes.
