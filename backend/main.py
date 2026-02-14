from fastapi import FastAPI, Depends, HTTPException, status, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import os
import json
from supabase import create_client, Client
import random
from pathlib import Path

# Import authentication utilities
from auth_utils import security, get_current_user_id, get_current_user, supabase

# Import services
from services import create_daily_analysis_service, create_weekly_pattern_service
from services.billing_service import BillingService

# Initialize FastAPI
app = FastAPI(
    title="Selfspeak API",
    description="Backend for Selfspeak journaling application",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
daily_analysis_service = create_daily_analysis_service(supabase)
weekly_pattern_service = create_weekly_pattern_service(supabase)
billing_service = BillingService(supabase)

# Pydantic Models
class JournalSaveRequest(BaseModel):
    content: str
    entry_date: Optional[str] = None  # Optional YYYY-MM-DD, defaults to today


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


async def get_weekly_usage(user_id: str) -> Dict[str, Any]:
    """
    Get weekly usage for user. Always returns normalized object.
    Returns: { "used": int, "limit": 3 }
    """
    week_start = get_week_start()
    WEEKLY_LIMIT = 3  # 3 analyses per week

    try:
        usage_response = supabase.table("ai_usage").select("*").eq(
            "user_id", user_id
        ).eq("week_start", week_start).execute()

        if usage_response.data:
            usage = usage_response.data[0]
            return {
                "used": usage.get("analysis_count", 0),
                "limit": WEEKLY_LIMIT
            }
        else:
            # No usage record exists, return default
            return {
                "used": 0,
                "limit": WEEKLY_LIMIT
            }
    except Exception as e:
        # On error, return safe default
        print(f"Error fetching usage: {e}")
        return {
            "used": 0,
            "limit": WEEKLY_LIMIT
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

        # Get normalized usage
        usage = await get_weekly_usage(user_id)

        return TodayResponse(
            journal_entry=journal_entry,
            analysis=analysis,
            usage=usage
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch today's data: {str(e)}"
        )


@app.get("/journal/range")
async def get_journal_range(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    GET /journal/range?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD

    Fetch journal entries within date range for authenticated user.
    Returns entries with their analyses (null if no analysis exists).
    Always returns normalized usage object.
    """
    # Extract user_id from JWT
    user_id = await get_current_user_id(credentials)

    try:
        # Validate date format
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )

        # Fetch journal entries in range
        journal_response = supabase.table("journal_entries").select("*").eq(
            "user_id", user_id
        ).gte("entry_date", start_date).lte("entry_date", end_date).order(
            "entry_date", desc=False
        ).execute()

        entries = journal_response.data or []

        # For each entry, fetch its analysis
        entries_with_analysis = []
        for entry in entries:
            analysis_response = supabase.table("ai_analyses").select("*").eq(
                "journal_id", entry["id"]
            ).execute()

            analysis = analysis_response.data[0] if analysis_response.data else None

            entries_with_analysis.append({
                "journal_entry": entry,
                "analysis": analysis
            })

        # Get normalized usage
        usage = await get_weekly_usage(user_id)

        return {
            "entries": entries_with_analysis,
            "usage": usage,
            "range": {
                "start_date": start_date,
                "end_date": end_date
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch journal range: {str(e)}"
        )


@app.post("/journal/save")
async def save_journal(
    request: JournalSaveRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    POST /journal/save

    Upsert journal entry for specified date (or current date if not provided).
    Returns saved record.
    """
    # Extract user_id from JWT (never trust client input)
    user_id = await get_current_user_id(credentials)

    # Use provided entry_date or default to today
    entry_date = request.entry_date if request.entry_date else get_current_date()

    try:
        # Validate date format if provided
        if request.entry_date:
            try:
                datetime.strptime(request.entry_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date format. Use YYYY-MM-DD"
                )

        # Check if entry exists for this date
        existing_response = supabase.table("journal_entries").select("*").eq(
            "user_id", user_id
        ).eq("entry_date", entry_date).execute()

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
                "entry_date": entry_date,
                "content": request.content,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }).execute()

            return {
                "success": True,
                "message": "Journal entry created",
                "data": insert_response.data[0] if insert_response.data else None
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save journal entry: {str(e)}"
        )


@app.post("/journal/analyze")
async def analyze_journal(
    entry_date: Optional[str] = Query(None, description="Entry date in YYYY-MM-DD format, defaults to today"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    POST /journal/analyze

    Layer 1: Daily AI Analysis

    Generate analysis for specified journal entry (or today's if not provided).
    Checks weekly usage limit before proceeding.
    Returns analysis record with updated usage.
    """
    # Extract user_id from JWT (never trust client input)
    user_id = await get_current_user_id(credentials)

    # Use provided entry_date or default to today
    target_date = entry_date if entry_date else get_current_date()

    try:
        # Validate date format if provided
        if entry_date:
            try:
                datetime.strptime(entry_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date format. Use YYYY-MM-DD"
                )

        # Fetch journal entry for target date
        journal_response = supabase.table("journal_entries").select("*").eq(
            "user_id", user_id
        ).eq("entry_date", target_date).execute()

        if not journal_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No journal entry found for {target_date}. Please save an entry first."
            )

        journal_entry = journal_response.data[0]

        # Use daily analysis service (Layer 1)
        analysis = daily_analysis_service.perform_daily_analysis(
            user_id=user_id,
            journal_id=journal_entry["id"],
            journal_content=journal_entry["content"]
        )

        # Get updated usage
        usage = await get_weekly_usage(user_id)

        return {
            "success": True,
            "message": "Analysis generated successfully",
            "data": analysis,
            "usage": usage
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate analysis: {str(e)}"
        )


@app.get("/dashboard/weekly")
async def get_weekly_dashboard(
    week_start: Optional[str] = Query(None, description="Week start date (YYYY-MM-DD), defaults to current week"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    GET /dashboard/weekly?week_start=YYYY-MM-DD

    Layer 2: Weekly Pattern Analysis

    Generates weekly insight from aggregated daily metadata.
    Idempotent: Returns cached insight if already generated.

    Returns:
        {
            "weekly_insight": {
                "summary_text": "...",
                "confidence_trend": "up|down|stable",
                "resistance_trend": "up|down|stable",
                "gratitude_trend": "up|down|stable",
                "dominant_week_emotion": "...",
                "reflection_question": "..."
            },
            "weekly_averages": {
                "confidence": 75.5,
                "abundance": 68.2,
                ...
            },
            "trend_data": {...},
            "entry_count": 5
        }
    """
    # Extract user_id from JWT (never trust client input)
    user_id = await get_current_user_id(credentials)

    try:
        # Use weekly pattern service (Layer 2)
        result = weekly_pattern_service.generate_weekly_insight(
            user_id=user_id,
            week_start_date=week_start
        )

        return {
            "success": True,
            "data": result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate weekly insight: {str(e)}"
        )


# ============================================
# Billing Routes - Lemon Squeezy Integration
# ============================================

class CheckoutRequest(BaseModel):
    plan_type: str  # "monthly" or "annual"


@app.post("/billing/create-checkout")
async def create_checkout_session(
    request: CheckoutRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create Lemon Squeezy checkout session for Pro subscription."""

    # Get authenticated user ID (never trust frontend)
    user_id = await get_current_user_id(credentials)

    # Get user email from Supabase
    try:
        user_response = supabase.auth.admin.get_user_by_id(user_id)
        user_email = user_response.user.email
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user email: {str(e)}"
        )

    # Validate plan type
    if request.plan_type not in ["monthly", "annual"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plan type must be 'monthly' or 'annual'"
        )

    try:
        # Create checkout session
        result = billing_service.create_checkout_session(
            user_id=user_id,
            user_email=user_email,
            plan_type=request.plan_type
        )

        return {
            "success": True,
            "checkout_url": result["checkout_url"],
            "plan_type": result["plan_type"]
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create checkout session: {str(e)}"
        )


@app.post("/billing/webhook")
async def lemon_squeezy_webhook(request: Request):
    """Handle Lemon Squeezy webhook events."""

    # Get raw body for signature verification
    raw_body = await request.body()
    signature = request.headers.get("X-Signature")

    if not signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Signature header"
        )

    # Verify webhook signature
    if not billing_service.verify_webhook_signature(raw_body, signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature"
        )

    # Parse webhook payload
    try:
        event_data = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )

    # Process webhook
    try:
        result = billing_service.process_webhook(event_data)

        return {
            "success": True,
            "message": result.get("status", "processed"),
            "event_id": event_data.get("meta", {}).get("event_id")
        }

    except ValueError as e:
        # Log error but return 200 to prevent retries
        print(f"⚠️ Webhook processing error: {str(e)}")
        return {
            "success": False,
            "message": str(e),
            "event_id": event_data.get("meta", {}).get("event_id")
        }
    except Exception as e:
        # Log critical error
        print(f"❌ Critical webhook error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}"
        )


@app.get("/billing/subscription")
async def get_subscription_status(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get current user's subscription details."""

    user_id = await get_current_user_id(credentials)
    subscription = billing_service.get_user_subscription(user_id)

    if not subscription:
        return {
            "plan": "free",
            "status": "none",
            "renewal_date": None
        }

    return {
        "plan": subscription.get("plan", "free"),
        "status": subscription.get("status"),
        "renewal_date": subscription.get("renewal_date"),
        "started_at": subscription.get("started_at")
    }


# ============================================
# Serve Frontend Static Files
# ============================================

# Mount frontend files (for single-service deployment on Render/Railway)
frontend_path = Path(__file__).parent.parent
if (frontend_path / "landing.html").exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
    print("✅ Serving frontend from backend (single service mode)")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
