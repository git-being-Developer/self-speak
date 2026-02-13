"""
AI Service - OpenAI Integration for Daily and Weekly Analysis
Strict JSON output with validation and retry logic
"""

from typing import Dict, Any, Optional, Tuple
import json
import os
from openai import OpenAI
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AIService:
    """
    Isolated AI service for both daily and weekly analysis.
    Uses OpenAI Chat Completions API with strict JSON mode.
    """

    def __init__(self):
        """Initialize OpenAI client."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY must be set in environment variables")

        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-5.1"  # Cost-efficient stable model
        self.temperature = 0.4  # Consistency over creativity

    # Controlled taxonomy for behavioral tags
    ALLOWED_BEHAVIORAL_TAGS = [
        "future_focused",
        "past_reflecting",
        "present_anchored",
        "socially_engaged",
        "internally_focused",
        "action_oriented",
        "contemplative",
        "emotionally_processing",
        "problem_solving",
        "gratitude_expressing",
        "identity_exploring",
        "relationship_focused",
        "achievement_oriented",
        "rest_seeking",
        "growth_mindset",
        "fixed_perspective",
        "optimistic_leaning",
        "pessimistic_leaning",
        "self_compassionate",
        "self_critical"
    ]

    def analyze_daily_journal(self, journal_content: str) -> Dict[str, Any]:
        """
        Layer 1: Daily Analysis

        Analyzes a single journal entry using OpenAI.
        Enforces strict JSON output with validation.
        Retries once on parsing failure.

        Args:
            journal_content: Raw journal text

        Returns:
            Structured analysis with scores and metadata

        Raises:
            ValueError: If AI response is invalid after retry
        """
        system_prompt = """You are analyzing a personal journal entry for a self-awareness analytics platform.
You evaluate language and tone only.
You do not provide therapy, life advice, instructions, or motivational coaching.
You do not use words like:
should
must
need to
fix
change your life
You provide neutral, reflective observations.
You return conservative scores.
Output valid JSON only."""

        user_prompt = f"""Analyze this journal entry and return:
confidence (0–100)
abundance (0–100)
clarity (0–100)
gratitude (0–100)
resistance (0–100)
dominant_emotion (1 word)
goal_present (true/false)
self_doubt_present (true/false)
time_horizon (short, long, vague)
overall_tone (calm, anxious, driven, scattered)
behavioral_tags (array of 1-4 tags from allowed list)

Allowed behavioral tags:
{', '.join(self.ALLOWED_BEHAVIORAL_TAGS)}

Rules for behavioral_tags:
- Select 1-4 most relevant tags
- Base selection on observable language patterns
- Do not over-interpret
- Return as JSON array of strings

Journal:
\"\"\"
{journal_content}
\"\"\"

Return JSON only."""

        # First attempt
        response_data, error = self._call_openai_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            expected_keys=[
                "confidence", "abundance", "clarity", "gratitude", "resistance",
                "dominant_emotion", "goal_present", "self_doubt_present",
                "time_horizon", "overall_tone", "behavioral_tags"
            ]
        )

        if error:
            raise ValueError(f"AI analysis failed: {error}")

        # Validate and normalize response
        return self._validate_daily_analysis(response_data)

    def generate_weekly_insight(self, aggregated_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Layer 2: Weekly Pattern Analysis

        Generates reflective insights based on aggregated daily metadata.
        Does NOT receive raw journal text.

        Args:
            aggregated_metadata: Pre-computed trends and averages
                {
                    "avg_confidence": 75.5,
                    "avg_resistance": 34.2,
                    "avg_gratitude": 82.1,
                    "confidence_trend": "up",
                    "resistance_trend": "stable",
                    "gratitude_trend": "up",
                    "dominant_emotion": "Hopeful",
                    "goal_presence_rate": 0.6,
                    "self_doubt_rate": 0.4,
                    "entry_count": 5
                }

        Returns:
            Weekly insight with reflective language

        Raises:
            ValueError: If AI response is invalid after retry
        """
        # Require minimum 3 data points for reliable pattern detection
        entry_count = aggregated_metadata.get("entry_count", 0)
        if entry_count < 3:
            return {
                "summary_text": f"Weekly insights require at least 3 analyzed journal entries. You have {entry_count}. Keep journaling and analyzing!",
                "dominant_week_emotion": "Reflective",
                "reflection_question": "What's on your mind today?",
                "pattern_summary": None,
                "pattern_experiment": None,
                "dominant_behavioral_theme": None,
                "confidence_trend": aggregated_metadata.get("confidence_trend", "stable"),
                "resistance_trend": aggregated_metadata.get("resistance_trend", "stable"),
                "gratitude_trend": aggregated_metadata.get("gratitude_trend", "stable")
            }

        system_prompt = """You analyze structured emotional trend data from a journaling application.
You do not provide therapy, advice, or predictions.
You observe patterns neutrally.
Avoid words like: should, must, need to, fix, improve.
Return JSON only."""

        # Build structured data summary
        data_summary = json.dumps(aggregated_metadata, indent=2)

        # Extract dominant behavioral theme from top tags
        top_tags = aggregated_metadata.get("top_tags") or []
        dominant_theme = top_tags[0] if (top_tags and len(top_tags) > 0) else "reflective"

        user_prompt = f"""Here is aggregated weekly data:
{data_summary}

Return:
- summary_text (3-5 sentences describing observable patterns)
- dominant_week_emotion (single word for the week's primary emotion)
- reflection_question (1 open-ended reflective question based on trends)
- pattern_summary (2-3 sentences describing behavioral patterns observed, neutral tone)
- pattern_experiment (5-7 day exploratory experiment suggestion based on patterns, non-prescriptive)

Rules:
- No advice language
- No "you should" or "you must"
- Suggest experiments as possibilities, not instructions
- Be specific but exploratory

Return JSON only."""

        # Call OpenAI with retry
        response_data, error = self._call_openai_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            expected_keys=["summary_text", "dominant_week_emotion", "reflection_question",
                          "pattern_summary", "pattern_experiment"]
        )

        if error:
            raise ValueError(f"Weekly insight generation failed: {error}")

        # Add dominant behavioral theme from aggregated tags
        response_data["dominant_behavioral_theme"] = dominant_theme

        # Add trend fields from aggregated metadata (already computed)
        response_data["confidence_trend"] = aggregated_metadata.get("confidence_trend", "stable")
        response_data["resistance_trend"] = aggregated_metadata.get("resistance_trend", "stable")
        response_data["gratitude_trend"] = aggregated_metadata.get("gratitude_trend", "stable")

        return response_data

    def _call_openai_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        expected_keys: list,
        max_retries: int = 1
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Call OpenAI API with strict JSON mode and retry logic.

        Returns:
            Tuple of (parsed_data, error_message)
        """
        for attempt in range(max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    temperature=self.temperature,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                )

                # Extract content
                content = response.choices[0].message.content

                # Parse JSON
                try:
                    data = json.loads(content)
                except json.JSONDecodeError as e:
                    if attempt < max_retries:
                        print(f"JSON parse error on attempt {attempt + 1}, retrying...")
                        continue
                    return None, f"Invalid JSON after {max_retries + 1} attempts: {str(e)}"

                # Validate expected keys
                missing_keys = [key for key in expected_keys if key not in data]
                if missing_keys:
                    if attempt < max_retries:
                        print(f"Missing keys {missing_keys} on attempt {attempt + 1}, retrying...")
                        continue
                    return None, f"Missing required keys: {missing_keys}"

                # Success
                return data, None

            except Exception as e:
                if attempt < max_retries:
                    print(f"API error on attempt {attempt + 1}, retrying: {str(e)}")
                    continue
                return None, f"OpenAI API error: {str(e)}"

        return None, "Max retries exceeded"

    def _validate_daily_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize daily analysis response.
        Ensures scores are in valid ranges and types are correct.
        """
        validated = {}

        # Validate numeric scores (0-100)
        # Handle both formats: "confidence" or "confidence_score" from AI
        for key in ["confidence", "abundance", "clarity", "gratitude", "resistance"]:
            score = data.get(key) or data.get(f"{key}_score", 50)
            try:
                score = int(score)
                score = max(0, min(100, score))  # Clamp to 0-100
            except (ValueError, TypeError):
                score = 50  # Default fallback
            validated[f"{key}_score"] = score

        # Validate string fields
        validated["dominant_emotion"] = str(data.get("dominant_emotion", "Reflective"))[:50]

        # Validate enum fields
        valid_tones = ["calm", "anxious", "driven", "scattered"]
        tone = data.get("overall_tone", "calm").lower()
        validated["overall_tone"] = tone if tone in valid_tones else "calm"

        valid_horizons = ["short", "long", "vague"]
        horizon = data.get("time_horizon", "vague").lower()
        validated["time_horizon"] = horizon if horizon in valid_horizons else "vague"

        # Validate boolean fields
        validated["goal_present"] = bool(data.get("goal_present", False))
        validated["self_doubt_present"] = bool(data.get("self_doubt_present", False))

        # Validate behavioral_tags
        tags = data.get("behavioral_tags", [])
        if not isinstance(tags, list):
            raise ValueError("behavioral_tags must be an array")

        # Filter to valid tags only
        valid_tags = [tag for tag in tags if tag in self.ALLOWED_BEHAVIORAL_TAGS]

        # Enforce max 4 tags
        if len(valid_tags) > 4:
            valid_tags = valid_tags[:4]

        # Require at least 1 tag
        if len(valid_tags) < 1:
            raise ValueError("At least 1 valid behavioral tag is required")

        validated["behavioral_tags"] = valid_tags

        # Calculate alignment_score (backend calculation)
        # Formula: (confidence + abundance + clarity + gratitude + (100 - resistance)) / 5
        alignment_score = (
            validated["confidence_score"] +
            validated["abundance_score"] +
            validated["clarity_score"] +
            validated["gratitude_score"] +
            (100 - validated["resistance_score"])
        ) / 5
        validated["alignment_score"] = round(alignment_score)

        return validated


# Singleton instance
ai_service = AIService()
