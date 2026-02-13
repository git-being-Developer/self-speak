"""
Daily Analysis Service - Layer 1
Handles individual journal entry analysis
"""

from typing import Dict, Any, Optional
from datetime import datetime
from supabase import Client
from fastapi import HTTPException, status

from services.ai_service import ai_service


class DailyAnalysisService:
    """
    Layer 1: Daily AI Analysis

    Handles analysis of individual journal entries.
    Completely isolated from weekly analysis logic.
    """

    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.WEEKLY_LIMIT = 2

    def perform_daily_analysis(
        self,
        user_id: str,
        journal_id: str,
        journal_content: str
    ) -> Dict[str, Any]:
        """
        Execute daily analysis workflow.

        Steps:
        1. Check if analysis already exists
        2. Verify weekly quota
        3. Call AI service
        4. Store results
        5. Update usage counter

        Args:
            user_id: Authenticated user ID
            journal_id: ID of journal entry to analyze
            journal_content: Journal text content

        Returns:
            Stored analysis record

        Raises:
            HTTPException: If quota exceeded or analysis fails
        """
        # Step 1: Check if analysis already exists
        existing = self._get_existing_analysis(journal_id)
        if existing:
            return existing

        # Step 2: Verify weekly quota
        week_start = self._get_week_start()
        current_usage = self._get_weekly_usage(user_id, week_start)

        if current_usage >= self.WEEKLY_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Weekly analysis limit reached ({current_usage}/{self.WEEKLY_LIMIT}). Resets next Monday."
            )

        # Step 3: Call AI service (Layer 1)
        analysis_data = ai_service.analyze_daily_journal(journal_content)

        # Step 4: Store analysis
        stored_analysis = self._store_analysis(user_id, journal_id, analysis_data)

        # Step 5: Update usage
        self._increment_usage(user_id, week_start, current_usage)

        return stored_analysis

    def _get_existing_analysis(self, journal_id: str) -> Optional[Dict[str, Any]]:
        """Check if analysis already exists for this journal entry."""
        response = self.supabase.table("ai_analyses").select("*").eq(
            "journal_id", journal_id
        ).execute()

        return response.data[0] if response.data else None

    def _get_week_start(self) -> str:
        """Get start of current week (Monday) in YYYY-MM-DD format."""
        from datetime import datetime, timedelta
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        return week_start.strftime("%Y-%m-%d")

    def _get_weekly_usage(self, user_id: str, week_start: str) -> int:
        """Get current week's usage count."""
        response = self.supabase.table("ai_usage").select("*").eq(
            "user_id", user_id
        ).eq("week_start", week_start).execute()

        if response.data:
            return response.data[0].get("analysis_count", 0)
        return 0

    def _store_analysis(
        self,
        user_id: str,
        journal_id: str,
        analysis_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Store analysis results in database."""
        insert_response = self.supabase.table("ai_analyses").insert({
            "journal_id": journal_id,
            "user_id": user_id,
            **analysis_data,
            "created_at": datetime.now().isoformat()
        }).execute()

        if not insert_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store analysis"
            )

        return insert_response.data[0]

    def _increment_usage(self, user_id: str, week_start: str, current_count: int):
        """Increment weekly usage counter."""
        if current_count == 0:
            # Create new usage record
            self.supabase.table("ai_usage").insert({
                "user_id": user_id,
                "week_start": week_start,
                "analysis_count": 1
            }).execute()
        else:
            # Update existing record
            self.supabase.table("ai_usage").update({
                "analysis_count": current_count + 1
            }).eq("user_id", user_id).eq("week_start", week_start).execute()


def create_daily_analysis_service(supabase: Client) -> DailyAnalysisService:
    """Factory function to create service instance."""
    return DailyAnalysisService(supabase)
