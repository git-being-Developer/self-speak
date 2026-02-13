"""
AI Service - Placeholder for actual AI integration
Provides mock responses for daily and weekly analysis
"""

from typing import Dict, Any, List
import random
from datetime import datetime


class AIService:
    """
    Isolated AI service for both daily and weekly analysis.
    Currently returns mock data - replace with actual LLM calls later.
    """

    @staticmethod
    def analyze_daily_journal(journal_content: str) -> Dict[str, Any]:
        """
        Layer 1: Daily Analysis

        Analyzes a single journal entry and returns structured metadata.

        Args:
            journal_content: Raw journal text

        Returns:
            Structured analysis with scores and metadata

        TODO: Replace with actual AI call (OpenAI, Anthropic, etc.)
        """
        # Placeholder: Generate realistic mock data
        emotions = ["Hopeful", "Calm", "Anxious", "Grateful", "Reflective",
                   "Uncertain", "Motivated", "Peaceful", "Overwhelmed"]
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

    @staticmethod
    def generate_weekly_insight(aggregated_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Layer 2: Weekly Pattern Analysis

        Generates reflective insights based on aggregated daily metadata.
        Does NOT receive raw journal text.

        Args:
            aggregated_metadata: Pre-computed trends and averages
                {
                    "avg_scores": {...},
                    "trends": {"confidence": "up", ...},
                    "dominant_emotion": "Hopeful",
                    "entry_count": 5
                }

        Returns:
            Weekly insight with reflective language

        TODO: Replace with actual AI call that generates personalized reflections
        """
        # Extract trend data
        trends = aggregated_metadata.get("trends", {})
        avg_scores = aggregated_metadata.get("avg_scores", {})
        entry_count = aggregated_metadata.get("entry_count", 0)
        dominant_emotion = aggregated_metadata.get("dominant_emotion", "Reflective")

        # Placeholder: Generate mock reflective content
        summaries = [
            f"This week showed {entry_count} days of reflection. Your {dominant_emotion.lower()} energy was prominent.",
            f"Over {entry_count} entries, you demonstrated growing self-awareness and emotional clarity.",
            f"This week's {entry_count} reflections reveal a journey toward greater understanding.",
        ]

        questions = [
            "What small win from this week deserves more celebration?",
            "Which emotion this week was trying to teach you something?",
            "What pattern emerged that you'd like to explore further?",
            "How did your perspective shift from Monday to today?",
            "What strength showed up that you might have overlooked?",
        ]

        return {
            "summary_text": random.choice(summaries),
            "confidence_trend": trends.get("confidence", "stable"),
            "resistance_trend": trends.get("resistance", "stable"),
            "gratitude_trend": trends.get("gratitude", "stable"),
            "dominant_week_emotion": dominant_emotion,
            "reflection_question": random.choice(questions),
        }


# Singleton instance
ai_service = AIService()
