"""
Weekly Pattern Analysis Service - Layer 2
Analyzes aggregated metadata from daily analyses
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from supabase import Client
from fastapi import HTTPException, status

from services.ai_service import ai_service


class WeeklyPatternService:
    """
    Layer 2: Weekly Pattern Analysis

    Analyzes aggregated metadata from daily analyses.
    Does NOT touch raw journal content.
    Completely isolated from daily analysis logic.
    """

    def __init__(self, supabase: Client):
        self.supabase = supabase

    def generate_weekly_insight(
        self,
        user_id: str,
        week_start_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate weekly insight from aggregated daily metadata.

        Idempotent: Returns existing insight if already generated.

        Steps:
        1. Determine week start date
        2. Check if insight already exists
        3. Fetch all daily analyses for the week
        4. Aggregate metadata and compute trends
        5. Call AI service with aggregated data
        6. Store weekly insight
        7. Return insight with trend data

        Args:
            user_id: Authenticated user ID
            week_start_date: Optional week start (defaults to current week)

        Returns:
            {
                "weekly_insight": {...},
                "weekly_averages": {...},
                "trend_data": {...}
            }
        """
        # Step 1: Determine week start
        if not week_start_date:
            week_start_date = self._get_current_week_start()

        # Step 2: Check if insight already exists (idempotent)
        existing_insight = self._get_existing_insight(user_id, week_start_date)
        if existing_insight:
            # Return cached insight with computed data
            return self._build_response_with_trends(
                user_id,
                week_start_date,
                existing_insight
            )

        # Step 3: Fetch all daily analyses for the week
        daily_analyses = self._fetch_week_analyses(user_id, week_start_date)

        if not daily_analyses:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No journal analyses found for this week"
            )

        # Step 4: Aggregate metadata and compute trends
        aggregated_metadata = self._aggregate_daily_metadata(daily_analyses)

        # Step 5: Call AI service (Layer 2) with aggregated data only
        ai_response = ai_service.generate_weekly_insight(aggregated_metadata)

        # Step 6: Store weekly insight
        stored_insight = self._store_weekly_insight(
            user_id,
            week_start_date,
            ai_response
        )

        # Step 7: Return insight with trend data
        return self._build_response_with_trends(
            user_id,
            week_start_date,
            stored_insight,
            aggregated_metadata
        )

    def _get_current_week_start(self) -> str:
        """Get Monday of current week in YYYY-MM-DD format."""
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        return week_start.strftime("%Y-%m-%d")

    def _get_existing_insight(
        self,
        user_id: str,
        week_start_date: str
    ) -> Optional[Dict[str, Any]]:
        """Check if weekly insight already exists."""
        response = self.supabase.table("weekly_insights").select("*").eq(
            "user_id", user_id
        ).eq("week_start_date", week_start_date).execute()

        return response.data[0] if response.data else None

    def _fetch_week_analyses(
        self,
        user_id: str,
        week_start_date: str
    ) -> List[Dict[str, Any]]:
        """
        Fetch all daily analyses for the specified week.
        Only fetches metadata, NOT raw journal content.
        """
        week_start = datetime.strptime(week_start_date, "%Y-%m-%d")
        week_end = week_start + timedelta(days=6)

        # Join with journal_entries to get dates, but don't fetch content
        response = self.supabase.table("ai_analyses").select(
            """
            *,
            journal_entries!inner(entry_date)
            """
        ).eq("user_id", user_id).gte(
            "journal_entries.entry_date", week_start.strftime("%Y-%m-%d")
        ).lte(
            "journal_entries.entry_date", week_end.strftime("%Y-%m-%d")
        ).execute()

        return response.data if response.data else []

    def _aggregate_daily_metadata(
        self,
        daily_analyses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Aggregate metadata from daily analyses.
        Computes averages and trends.

        Returns structured metadata for AI consumption.
        """
        if not daily_analyses:
            return {}

        # Compute averages
        total_entries = len(daily_analyses)

        avg_confidence = sum(a.get("confidence_score", 0) for a in daily_analyses) / total_entries
        avg_abundance = sum(a.get("abundance_score", 0) for a in daily_analyses) / total_entries
        avg_clarity = sum(a.get("clarity_score", 0) for a in daily_analyses) / total_entries
        avg_gratitude = sum(a.get("gratitude_score", 0) for a in daily_analyses) / total_entries
        avg_resistance = sum(a.get("resistance_score", 0) for a in daily_analyses) / total_entries

        # Compute trends (early week vs late week)
        trends = self._compute_trends(daily_analyses)

        # Find dominant emotion (most frequent)
        emotions = [a.get("dominant_emotion") for a in daily_analyses if a.get("dominant_emotion")]
        dominant_emotion = max(set(emotions), key=emotions.count) if emotions else "Reflective"

        return {
            "entry_count": total_entries,
            "avg_scores": {
                "confidence": round(avg_confidence, 1),
                "abundance": round(avg_abundance, 1),
                "clarity": round(avg_clarity, 1),
                "gratitude": round(avg_gratitude, 1),
                "resistance": round(avg_resistance, 1),
            },
            "trends": trends,
            "dominant_emotion": dominant_emotion,
        }

    def _compute_trends(
        self,
        daily_analyses: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Compute trend direction (up/down/stable) by comparing
        early week vs late week averages.
        """
        if len(daily_analyses) < 3:
            # Not enough data for trend analysis
            return {
                "confidence": "stable",
                "resistance": "stable",
                "gratitude": "stable",
            }

        # Split into early and late week
        mid_point = len(daily_analyses) // 2
        early_week = daily_analyses[:mid_point]
        late_week = daily_analyses[mid_point:]

        def avg_score(analyses, key):
            scores = [a.get(key, 0) for a in analyses]
            return sum(scores) / len(scores) if scores else 0

        def trend_direction(early_avg, late_avg, threshold=5):
            diff = late_avg - early_avg
            if diff > threshold:
                return "up"
            elif diff < -threshold:
                return "down"
            else:
                return "stable"

        return {
            "confidence": trend_direction(
                avg_score(early_week, "confidence_score"),
                avg_score(late_week, "confidence_score")
            ),
            "resistance": trend_direction(
                avg_score(early_week, "resistance_score"),
                avg_score(late_week, "resistance_score")
            ),
            "gratitude": trend_direction(
                avg_score(early_week, "gratitude_score"),
                avg_score(late_week, "gratitude_score")
            ),
        }

    def _store_weekly_insight(
        self,
        user_id: str,
        week_start_date: str,
        ai_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Store weekly insight in database."""
        insert_response = self.supabase.table("weekly_insights").insert({
            "user_id": user_id,
            "week_start_date": week_start_date,
            "summary_text": ai_response["summary_text"],
            "confidence_trend": ai_response["confidence_trend"],
            "resistance_trend": ai_response["resistance_trend"],
            "gratitude_trend": ai_response["gratitude_trend"],
            "dominant_week_emotion": ai_response["dominant_week_emotion"],
            "reflection_question": ai_response["reflection_question"],
            "created_at": datetime.now().isoformat()
        }).execute()

        if not insert_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store weekly insight"
            )

        return insert_response.data[0]

    def _build_response_with_trends(
        self,
        user_id: str,
        week_start_date: str,
        insight: Dict[str, Any],
        aggregated_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build complete response with insight and trend data.
        If aggregated_metadata not provided, recompute from stored analyses.
        """
        if not aggregated_metadata:
            # Recompute from stored analyses
            daily_analyses = self._fetch_week_analyses(user_id, week_start_date)
            aggregated_metadata = self._aggregate_daily_metadata(daily_analyses)

        return {
            "weekly_insight": insight,
            "weekly_averages": aggregated_metadata.get("avg_scores", {}),
            "trend_data": {
                "confidence": insight["confidence_trend"],
                "resistance": insight["resistance_trend"],
                "gratitude": insight["gratitude_trend"],
                "dominant_emotion": insight["dominant_week_emotion"],
            },
            "entry_count": aggregated_metadata.get("entry_count", 0),
        }


def create_weekly_pattern_service(supabase: Client) -> WeeklyPatternService:
    """Factory function to create service instance."""
    return WeeklyPatternService(supabase)
