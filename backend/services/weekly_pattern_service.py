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
                "trend_data": {...},
                "daily_scores": [...]
            }
        """
        # Step 1: Determine week start
        if not week_start_date:
            week_start_date = self._get_current_week_start()

        # Step 2: Fetch all daily analyses for the week
        daily_analyses = self._fetch_week_analyses(user_id, week_start_date)

        if not daily_analyses:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No journal analyses found for this week"
            )

        # Step 3: Check if insight exists and if it needs regeneration
        existing_insight = self._get_existing_insight(user_id, week_start_date)

        if existing_insight:
            # Check if there are newer analyses than the cached insight
            insight_created_at = datetime.fromisoformat(existing_insight["created_at"].replace('Z', '+00:00'))
            latest_analysis_date = max(
                datetime.fromisoformat(a["created_at"].replace('Z', '+00:00'))
                for a in daily_analyses
            )

            # If no new analyses since insight was created, return cached version
            if latest_analysis_date <= insight_created_at:
                return self._build_response_with_trends(
                    user_id,
                    week_start_date,
                    existing_insight,
                    daily_analyses
                )

            # Otherwise, regenerate (delete old insight first)
            print(f"New analyses detected, regenerating weekly insight for {week_start_date}")
            self._delete_insight(user_id, week_start_date)

        # Step 4: Aggregate metadata and compute trends
        aggregated_metadata = self._aggregate_daily_metadata(daily_analyses)

        # Step 5: Call AI service (Layer 2) with aggregated data only
        try:
            ai_response = ai_service.generate_weekly_insight(aggregated_metadata)
        except ValueError as e:
            # AI call failed, return error without storing
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate weekly insight: {str(e)}"
            )

        # Step 6: Store weekly insight
        stored_insight = self._store_weekly_insight(
            user_id,
            week_start_date,
            ai_response,
            aggregated_metadata
        )

        # Step 7: Return insight with trend data
        return self._build_response_with_trends(
            user_id,
            week_start_date,
            stored_insight,
            daily_analyses,
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

    def _delete_insight(
        self,
        user_id: str,
        week_start_date: str
    ):
        """Delete existing weekly insight to allow regeneration."""
        self.supabase.table("weekly_insights").delete().eq(
            "user_id", user_id
        ).eq("week_start_date", week_start_date).execute()

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
        Computes averages, trends, tag frequency, and correlations.

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
        avg_alignment = sum(a.get("alignment_score", 0) for a in daily_analyses) / total_entries

        # Aggregate behavioral tags
        tag_frequency = {}
        for analysis in daily_analyses:
            tags = analysis.get("behavioral_tags") or []
            if tags is None:
                tags = []
            for tag in tags:
                tag_frequency[tag] = tag_frequency.get(tag, 0) + 1

        # Sort tags by frequency
        sorted_tags = sorted(tag_frequency.items(), key=lambda x: x[1], reverse=True)
        top_tags = [tag for tag, _ in sorted_tags[:5]]  # Top 5 tags

        # Compute tag correlations with resistance and clarity
        tag_correlations = self._compute_tag_correlations(daily_analyses, tag_frequency)

        # Compute trends (early week vs late week)
        trends = self._compute_trends(daily_analyses)

        # Find dominant emotion (most frequent)
        emotions = [a.get("dominant_emotion") for a in daily_analyses if a.get("dominant_emotion")]
        dominant_emotion = max(set(emotions), key=emotions.count) if emotions else "Reflective"

        # Compute goal presence and self-doubt rates
        goal_count = sum(1 for a in daily_analyses if a.get("goal_present", False))
        doubt_count = sum(1 for a in daily_analyses if a.get("self_doubt_present", False))

        return {
            "entry_count": total_entries,
            "avg_confidence": round(avg_confidence, 1),
            "avg_resistance": round(avg_resistance, 1),
            "avg_gratitude": round(avg_gratitude, 1),
            "avg_scores": {
                "confidence": round(avg_confidence, 1),
                "abundance": round(avg_abundance, 1),
                "clarity": round(avg_clarity, 1),
                "gratitude": round(avg_gratitude, 1),
                "resistance": round(avg_resistance, 1),
            },
            "weekly_alignment_score": round(avg_alignment),
            "top_tags": top_tags,
            "tag_frequency": tag_frequency,
            "tag_correlations": tag_correlations,
            "trends": trends,
            "confidence_trend": trends.get("confidence", "stable"),
            "resistance_trend": trends.get("resistance", "stable"),
            "gratitude_trend": trends.get("gratitude", "stable"),
            "dominant_emotion": dominant_emotion,
            "goal_presence_rate": round(goal_count / total_entries, 2),
            "self_doubt_rate": round(doubt_count / total_entries, 2),
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

    def _compute_tag_correlations(
        self,
        daily_analyses: List[Dict[str, Any]],
        tag_frequency: Dict[str, int]
    ) -> Dict[str, Any]:
        """
        Compute correlations between behavioral tags and resistance/clarity scores.
        Returns simplified correlation data for pattern detection.
        """
        correlations = {}

        # Only analyze tags that appear at least twice
        significant_tags = [tag for tag, freq in tag_frequency.items() if freq >= 2]

        for tag in significant_tags:
            # Collect resistance and clarity scores when this tag is present
            resistance_scores = []
            clarity_scores = []

            for analysis in daily_analyses:
                tags = analysis.get("behavioral_tags") or []
                if tag in tags:
                    resistance_scores.append(analysis.get("resistance_score", 0))
                    clarity_scores.append(analysis.get("clarity_score", 0))

            if resistance_scores and clarity_scores:
                avg_resistance = sum(resistance_scores) / len(resistance_scores)
                avg_clarity = sum(clarity_scores) / len(clarity_scores)

                correlations[tag] = {
                    "avg_resistance": round(avg_resistance, 1),
                    "avg_clarity": round(avg_clarity, 1),
                    "occurrence_count": len(resistance_scores)
                }

        return correlations

    def _store_weekly_insight(
        self,
        user_id: str,
        week_start_date: str,
        ai_response: Dict[str, Any],
        aggregated_metadata: Dict[str, Any]
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
            "pattern_summary": ai_response.get("pattern_summary"),
            "pattern_experiment": ai_response.get("pattern_experiment"),
            "dominant_behavioral_theme": ai_response.get("dominant_behavioral_theme"),
            "weekly_alignment_score": aggregated_metadata.get("weekly_alignment_score"),
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
        daily_analyses: Optional[List[Dict[str, Any]]] = None,
        aggregated_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build complete response with insight, trend data, and daily scores for graphing.
        """
        # Fetch daily analyses if not provided
        if not daily_analyses:
            daily_analyses = self._fetch_week_analyses(user_id, week_start_date)

        # Compute aggregated metadata if not provided
        if not aggregated_metadata:
            aggregated_metadata = self._aggregate_daily_metadata(daily_analyses)

        # Build daily scores array for graph rendering
        daily_scores = []
        for analysis in daily_analyses:
            # Get the journal entry date from the nested object
            entry_date = analysis.get("journal_entries", {}).get("entry_date") if isinstance(analysis.get("journal_entries"), dict) else None

            daily_scores.append({
                "date": entry_date or analysis.get("created_at", "")[:10],
                "confidence": analysis.get("confidence_score", 0),
                "abundance": analysis.get("abundance_score", 0),
                "clarity": analysis.get("clarity_score", 0),
                "gratitude": analysis.get("gratitude_score", 0),
                "resistance": analysis.get("resistance_score", 0),
                "emotion": analysis.get("dominant_emotion", ""),
            })

        # Sort by date
        daily_scores.sort(key=lambda x: x["date"])

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
            "daily_scores": daily_scores
        }


def create_weekly_pattern_service(supabase: Client) -> WeeklyPatternService:
    """Factory function to create service instance."""
    return WeeklyPatternService(supabase)
