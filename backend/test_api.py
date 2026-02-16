"""
Test suite for Selfspeak API endpoints
Run with: pytest test_api.py -v
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from frontend.main import app

client = TestClient(app)

# Mock JWT token for testing
MOCK_JWT_TOKEN = "mock.jwt.token"
MOCK_USER_ID = "123e4567-e89b-12d3-a456-426614174000"


@pytest.fixture
def mock_supabase():
    """Mock Supabase client for testing"""
    with patch('main.supabase') as mock:
        yield mock


@pytest.fixture
def mock_auth():
    """Mock JWT authentication"""
    with patch('main.verify_jwt_and_get_user_id') as mock:
        mock.return_value = MOCK_USER_ID
        yield mock


def test_root_endpoint():
    """Test health check endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Selfspeak API"
    assert data["status"] == "healthy"


def test_get_today_journal_success(mock_auth, mock_supabase):
    """Test successful retrieval of today's journal"""
    # Mock database responses
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {
            "id": "entry-123",
            "user_id": MOCK_USER_ID,
            "date": "2026-02-11",
            "content": "Test entry",
            "created_at": "2026-02-11T10:00:00",
            "updated_at": "2026-02-11T10:00:00"
        }
    ]

    # Mock analysis response
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {
            "id": "analysis-123",
            "entry_id": "entry-123",
            "confidence": 75,
            "abundance": 70
        }
    ]

    # Mock usage response
    mock_supabase.table.return_value.select.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value.data = [
        {
            "id": "usage-123",
            "count": 1,
            "limit": 2
        }
    ]

    response = client.get(
        "/journal/today",
        headers={"Authorization": f"Bearer {MOCK_JWT_TOKEN}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "journal_entry" in data
    assert "analysis" in data
    assert "usage" in data


def test_save_journal_create_new(mock_auth, mock_supabase):
    """Test creating a new journal entry"""
    # Mock no existing entry
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []

    # Mock successful insert
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
        {
            "id": "new-entry-123",
            "user_id": MOCK_USER_ID,
            "date": "2026-02-11",
            "content": "New journal entry"
        }
    ]

    response = client.post(
        "/journal/save",
        headers={"Authorization": f"Bearer {MOCK_JWT_TOKEN}"},
        json={"content": "New journal entry"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Journal entry created"


def test_save_journal_update_existing(mock_auth, mock_supabase):
    """Test updating an existing journal entry"""
    # Mock existing entry
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {
            "id": "existing-entry-123",
            "user_id": MOCK_USER_ID,
            "date": "2026-02-11",
            "content": "Old content"
        }
    ]

    # Mock successful update
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
        {
            "id": "existing-entry-123",
            "user_id": MOCK_USER_ID,
            "date": "2026-02-11",
            "content": "Updated content"
        }
    ]

    response = client.post(
        "/journal/save",
        headers={"Authorization": f"Bearer {MOCK_JWT_TOKEN}"},
        json={"content": "Updated content"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Journal entry updated"


def test_analyze_journal_no_entry(mock_auth, mock_supabase):
    """Test analysis when no journal entry exists"""
    # Mock no journal entry
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []

    response = client.post(
        "/journal/analyze",
        headers={"Authorization": f"Bearer {MOCK_JWT_TOKEN}"}
    )

    assert response.status_code == 404
    data = response.json()
    assert "No journal entry found" in data["detail"]


def test_analyze_journal_limit_reached(mock_auth, mock_supabase):
    """Test analysis when weekly limit is reached"""
    # Mock journal entry exists
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {
            "id": "entry-123",
            "user_id": MOCK_USER_ID,
            "content": "Test entry"
        }
    ]

    # Mock no existing analysis
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

    # Mock usage at limit
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {
            "id": "usage-123",
            "count": 2,
            "limit": 2
        }
    ]

    response = client.post(
        "/journal/analyze",
        headers={"Authorization": f"Bearer {MOCK_JWT_TOKEN}"}
    )

    assert response.status_code == 429
    data = response.json()
    assert "limit reached" in data["detail"]


def test_analyze_journal_success(mock_auth, mock_supabase):
    """Test successful analysis generation"""
    # Mock journal entry
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {
            "id": "entry-123",
            "user_id": MOCK_USER_ID,
            "content": "Test entry"
        }
    ]

    # Mock no existing analysis
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

    # Mock usage available
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {
            "id": "usage-123",
            "count": 0,
            "limit": 2
        }
    ]

    # Mock successful analysis insert
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
        {
            "id": "analysis-123",
            "entry_id": "entry-123",
            "confidence": 75,
            "abundance": 80,
            "clarity": 70,
            "gratitude": 85,
            "resistance": 30,
            "dominant_emotion": "Hopeful",
            "tone": "Reflective",
            "goal_present": True,
            "self_doubt_present": "Minimal"
        }
    ]

    response = client.post(
        "/journal/analyze",
        headers={"Authorization": f"Bearer {MOCK_JWT_TOKEN}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "analysis generated" in data["message"].lower()
    assert data["usage"]["count"] == 1


def test_unauthorized_access():
    """Test that endpoints require authentication"""
    response = client.get("/journal/today")
    assert response.status_code == 403  # No Authorization header


def test_invalid_token():
    """Test invalid JWT token"""
    with patch('main.supabase.auth.get_user') as mock_get_user:
        mock_get_user.side_effect = Exception("Invalid token")

        response = client.get(
            "/journal/today",
            headers={"Authorization": "Bearer invalid.token"}
        )

        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
