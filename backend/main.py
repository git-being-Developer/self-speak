from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import os
from supabase import create_client, Client
import random

# Import authentication utilities
from auth_utils import security, get_current_user_id, get_current_user, supabase

# Initialize FastAPI
app = FastAPI(
    title="Selfspeak API",
    description="Backend for Selfspeak journaling application",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic Models
class JournalSaveRequest(BaseModel):
    content: str


class JournalEntry(BaseModel):
    id: Optional[str] = None
    user_id: str
    entry_date: str
    content: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class AnalysisData(BaseModel):
    id: Optional[str] = None
    journal_id: str
    user_id: str
    confidence_score: int
    abundance_score: int
    clarity_score: int
    gratitude_score: int
    resistance_score: int
    dominant_emotion: str
    overall_tone: str
    goal_present: bool
    self_doubt_present: bool
    time_horizon: Optional[str] = None
    created_at: Optional[str] = None


class TodayResponse(BaseModel):
    journal_entry: Optional[Dict[str, Any]]
    analysis: Optional[Dict[str, Any]]
    usage: Dict[str, Any]


# Helper Functions

def get_current_date() -> str:
    """Get current date in YYYY-MM-DD format"""
    return datetime.now().strftime("%Y-%m-%d")


def get_week_start() -> str:
    """Get start of current week (Monday) in YYYY-MM-DD format"""
    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())
    return week_start.strftime("%Y-%m-%d")


def generate_test_analysis_data() -> Dict[str, Any]:
    """
    Generate realistic test analysis data.
    In production, this would be replaced by actual AI analysis.
    """
    emotions = ["Hopeful", "Calm", "Anxious", "Grateful", "Reflective", "Uncertain", "Motivated"]
    tones = ["calm", "anxious", "driven", "scattered"]
    time_horizons = ["short", "long", "vague"]

    return {
        "confidence_score": random.randint(45, 95),
        "abundance_score": random.randint(40, 90),
        "clarity_score": random.randint(50, 95),
        "gratitude_score": random.randint(55, 98),
        "resistance_score": random.randint(20, 65),
        "dominant_emotion": random.choice(emotions),
        "overall_tone": random.choice(tones),
        "goal_present": random.choice([True, False]),
        "self_doubt_present": random.choice([True, False]),
        "time_horizon": random.choice(time_horizons),
    }


# API Endpoints

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Selfspeak API",
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/auth/me")
async def get_current_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    GET /auth/me

    Test endpoint to verify authentication and get current user info.
    Returns user_id, email, and metadata from JWT.
    """
    user = await get_current_user(credentials)

    return {
        "success": True,
        "user": {
            "id": user.get("user_id"),
            "email": user.get("email"),
            "metadata": user.get("metadata"),
            "role": user.get("role")
        }
    }


@app.get("/auth/verify")
async def verify_authentication(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    GET /auth/verify

    Simple endpoint to verify JWT is valid.
    Returns 200 if authenticated, 401 if not.
    """
    user_id = await get_current_user_id(credentials)

    return {
        "success": True,
        "authenticated": True,
        "user_id": user_id
    }


@app.get("/journal/today", response_model=TodayResponse)
async def get_today_journal(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    GET /journal/today

    Fetch today's journal entry, analysis, and weekly usage.
    Authenticates user via JWT and returns combined payload.
    """
    # Extract user_id from JWT (never trust client input)
    user_id = await get_current_user_id(credentials)

    current_date = get_current_date()
    week_start = get_week_start()

    try:
        # Fetch today's journal entry
        journal_response = supabase.table("journal_entries").select("*").eq(
            "user_id", user_id
        ).eq("entry_date", current_date).execute()

        journal_entry = journal_response.data[0] if journal_response.data else None

        # Fetch today's analysis if journal exists
        analysis = None
        if journal_entry:
            analysis_response = supabase.table("ai_analyses").select("*").eq(
                "journal_id", journal_entry["id"]
            ).execute()

            analysis = analysis_response.data[0] if analysis_response.data else None

        # Fetch current week's usage
        usage_response = supabase.table("ai_usage").select("*").eq(
            "user_id", user_id
        ).eq("week_start", week_start).execute()

        # Get or create usage record
        if usage_response.data:
            usage = usage_response.data[0]
        else:
            # Create initial usage record for this week
            new_usage = supabase.table("ai_usage").insert({
                "user_id": user_id,
                "week_start": week_start,
                "analysis_count": 0
            }).execute()
            usage = new_usage.data[0] if new_usage.data else {"analysis_count": 0}

        return TodayResponse(
            journal_entry=journal_entry,
            analysis=analysis,
            usage={
                "count": usage.get("analysis_count", 0),
                "limit": 2,  # Business logic constant
                "week_start": week_start
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch today's data: {str(e)}"
        )


@app.post("/journal/save")
async def save_journal(
    request: JournalSaveRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    POST /journal/save

    Upsert journal entry for current date.
    Returns saved record.
    """
    # Extract user_id from JWT (never trust client input)
    user_id = await get_current_user_id(credentials)

    current_date = get_current_date()

    try:
        # Check if entry exists for today
        existing_response = supabase.table("journal_entries").select("*").eq(
            "user_id", user_id
        ).eq("entry_date", current_date).execute()

        if existing_response.data:
            # Update existing entry
            entry_id = existing_response.data[0]["id"]
            update_response = supabase.table("journal_entries").update({
                "content": request.content,
                "updated_at": datetime.now().isoformat()
            }).eq("id", entry_id).execute()

            return {
                "success": True,
                "message": "Journal entry updated",
                "data": update_response.data[0] if update_response.data else None
            }
        else:
            # Insert new entry
            insert_response = supabase.table("journal_entries").insert({
                "user_id": user_id,
                "entry_date": current_date,
                "content": request.content,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }).execute()

            return {
                "success": True,
                "message": "Journal entry created",
                "data": insert_response.data[0] if insert_response.data else None
            }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save journal entry: {str(e)}"
        )


@app.post("/journal/analyze")
async def analyze_journal(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    POST /journal/analyze

    Generate analysis for today's journal entry.
    Checks weekly usage limit before proceeding.
    Returns analysis record.
    """
    # Extract user_id from JWT (never trust client input)
    user_id = await get_current_user_id(credentials)

    current_date = get_current_date()
    week_start = get_week_start()
    WEEKLY_LIMIT = 2  # Business logic constant

    try:
        # Fetch today's journal entry
        journal_response = supabase.table("journal_entries").select("*").eq(
            "user_id", user_id
        ).eq("entry_date", current_date).execute()

        if not journal_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No journal entry found for today. Please save an entry first."
            )

        journal_entry = journal_response.data[0]

        # Check if analysis already exists
        existing_analysis = supabase.table("ai_analyses").select("*").eq(
            "journal_id", journal_entry["id"]
        ).execute()

        if existing_analysis.data:
            return {
                "success": True,
                "message": "Analysis already exists for today's entry",
                "data": existing_analysis.data[0]
            }

        # Check weekly usage
        usage_response = supabase.table("ai_usage").select("*").eq(
            "user_id", user_id
        ).eq("week_start", week_start).execute()

        if usage_response.data:
            usage = usage_response.data[0]
            current_count = usage.get("analysis_count", 0)

            if current_count >= WEEKLY_LIMIT:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Weekly analysis limit reached ({current_count}/{WEEKLY_LIMIT}). Resets next Monday."
                )
        else:
            # Create usage record
            new_usage = supabase.table("ai_usage").insert({
                "user_id": user_id,
                "week_start": week_start,
                "analysis_count": 0
            }).execute()
            usage = new_usage.data[0] if new_usage.data else None
            current_count = 0

        # Generate analysis data (test data for now)
        analysis_data = generate_test_analysis_data()

        # Insert analysis
        analysis_insert = supabase.table("ai_analyses").insert({
            "journal_id": journal_entry["id"],
            "user_id": user_id,
            **analysis_data,
            "created_at": datetime.now().isoformat()
        }).execute()

        if not analysis_insert.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create analysis record"
            )

        # Increment usage count
        supabase.table("ai_usage").update({
            "analysis_count": current_count + 1
        }).eq("user_id", user_id).eq("week_start", week_start).execute()

        return {
            "success": True,
            "message": "Analysis generated successfully",
            "data": analysis_insert.data[0],
            "usage": {
                "count": current_count + 1,
                "limit": WEEKLY_LIMIT
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate analysis: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
