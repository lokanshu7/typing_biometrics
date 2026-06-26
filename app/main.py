from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import time
import uuid
from datetime import datetime

from app.schemas import (
    EnrollRequest,
    AuthenticateRequest,
    StandardResponse,
    ActivityEvent,
    HealthResponse,
    VersionResponse
)

from app.services import TypingBiometricsService
from app.storage import LocalStorage

app = FastAPI(
    title="Typing Biometrics API",
    description="Behavioral biometrics authentication based on typing patterns",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

biometrics_service = TypingBiometricsService()
storage = LocalStorage(data_dir="./data")


@app.on_event("startup")
async def startup() -> None:
    profiles = storage.load_user_profiles()

    if isinstance(profiles, dict):
        biometrics_service.user_profiles = profiles


@app.get("/", tags=["System"])
async def root() -> dict:
    return {
        "message": "Typing Biometrics API",
        "version": "0.1.0",
        "users": len(biometrics_service.user_profiles),
        "endpoints": [
            "/health",
            "/version",
            "/enroll",
            "/verify",
            "/users",
            "/profile/{user_id}"
        ]
    }


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        module="typing_biometrics",
        version="0.1.0"
    )


@app.get("/version", response_model=VersionResponse, tags=["System"])
async def version() -> VersionResponse:
    return VersionResponse(
        module="typing_biometrics",
        version="0.1.0",
        model_name="keystroke_dynamics_analyzer",
        model_version="1.0.0",
        features=[
            "dwell_time_analysis",
            "flight_time_analysis",
            "digraph_timing",
            "typing_speed",
            "backspace_behavior",
            "pause_behavior"
        ],
        description="Behavioral biometrics authentication using keystroke dynamics"
    )

@app.get("/")
async def root():
    return {
        "message": "Typing Biometrics API",
        "version": "0.1.0",
        "users": len(biometrics_service.user_profiles),
        "endpoints": ["/health", "/version", "/enroll", "/verify", "/users"]
    }

@app.post("/enroll_typing", response_model=StandardResponse)
async def enroll(request: EnrollRequest):
    """Enroll a new user with typing samples"""
    start_time = time.time()
    event_id = f"evt_{uuid.uuid4().hex[:8]}"

    try:
        if request.user_id in biometrics_service.user_profiles:
            raise HTTPException(
                status_code=400,
                detail=f"User {request.user_id} already enrolled"
            )

        sessions_dict = [
            session.model_dump()
            for session in request.sessions
        ]

        result = biometrics_service.enroll_user(
            request.user_id,
            sessions_dict
        )

        latency_ms = int(
            (time.time() - start_time) * 1000
        )

        if not result["success"]:
            return StandardResponse(
                module="typing_biometrics",
                score=0.0,
                decision="fail",
                confidence=0.0,
                metadata={
                    "reason": result["message"]
                },
                activity_event=ActivityEvent(
                    event_id=event_id,
                    user_id=request.user_id,
                    action="enroll",
                    result="fail",
                    timestamp=datetime.utcnow().isoformat() + "Z"
                ),
                latency_ms=latency_ms
            )

        storage.save_user_profiles(
            biometrics_service.user_profiles
        )

        return StandardResponse(
            module="typing_biometrics",
            score=1.0,
            decision="pass",
            confidence=1.0,
            metadata={
                "samples_collected": result["sample_count"],
                "enrolled_at": datetime.utcnow().isoformat()
            },
            activity_event=ActivityEvent(
                event_id=event_id,
                user_id=request.user_id,
                action="enroll",
                result="pass",
                score=1.0,
                timestamp=datetime.utcnow().isoformat() + "Z"
            ),
            latency_ms=latency_ms
        )

    except HTTPException:
        raise

    except Exception as e:
        latency_ms = int(
            (time.time() - start_time) * 1000
        )

        return StandardResponse(
            module="typing_biometrics",
            score=0.0,
            decision="fail",
            confidence=0.0,
            metadata={"error": str(e)},
            activity_event=ActivityEvent(
                event_id=event_id,
                user_id=request.user_id,
                action="enroll",
                result="fail",
                timestamp=datetime.utcnow().isoformat() + "Z"
            ),
            latency_ms=latency_ms
        )

@app.post("/verify_typing", response_model=StandardResponse)
async def verify(request: AuthenticateRequest):
    """Verify/authenticate user based on typing pattern"""
    start_time = time.time()
    event_id = f"evt_{uuid.uuid4().hex[:8]}"

    try:
        if request.user_id not in biometrics_service.user_profiles:

            latency_ms = int(
                (time.time() - start_time) * 1000
            )

            return StandardResponse(
                module="typing_biometrics",
                score=0.0,
                decision="fail",
                confidence=0.0,
                metadata={
                    "reason": f"User {request.user_id} not enrolled"
                },
                activity_event=ActivityEvent(
                    event_id=event_id,
                    user_id=request.user_id,
                    action="verify",
                    result="fail",
                    timestamp=datetime.utcnow().isoformat() + "Z"
                ),
                latency_ms=latency_ms
            )

        session_dict = request.session.model_dump()

        authenticated, confidence = (
            biometrics_service.authenticate(
                request.user_id,
                session_dict
            )
        )

        authenticated = bool(authenticated)
        confidence = float(confidence)

        storage.save_session_log(
            request.user_id,
            {
                "authenticated": authenticated,
                "confidence": confidence,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        latency_ms = int(
            (time.time() - start_time) * 1000
        )

        if confidence >= 0.7:
            decision = "pass"
        elif confidence >= 0.6:
            decision = "inconclusive"
        else:
            decision = "fail"

        return StandardResponse(
            module="typing_biometrics",
            score=confidence,
            decision=decision,
            confidence=confidence,
            metadata={
                "threshold": 0.7,
                "authenticated": authenticated
            },
            activity_event=ActivityEvent(
                event_id=event_id,
                user_id=request.user_id,
                module="typing_biometrics",
                action="verify",
                result=decision,
                score=confidence,
                timestamp=datetime.utcnow().isoformat() + "Z"
            ),
            latency_ms=latency_ms
        )

    except Exception as e:

        latency_ms = int(
            (time.time() - start_time) * 1000
        )

        return StandardResponse(
            module="typing_biometrics",
            score=0.0,
            decision="fail",
            confidence=0.0,
            metadata={"error": str(e)},
            activity_event=ActivityEvent(
                event_id=event_id,
                user_id=request.user_id,
                action="verify",
                result="fail",
                timestamp=datetime.utcnow().isoformat() + "Z"
            ),
            latency_ms=latency_ms
        )


@app.get("/users", tags=["Users"])
async def list_users() -> dict:
    return {
        "users": biometrics_service.list_users(),
        "count": len(
            biometrics_service.user_profiles
        )
    }


@app.get("/profile/{user_id}", tags=["Users"])
async def get_profile(user_id: str) -> dict:

    profile = biometrics_service.get_user_profile(
        user_id
    )

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail=f"User {user_id} not found"
        )

    return profile


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
