# Selfspeak Backend API

Production-ready FastAPI backend for the Selfspeak journaling application with Supabase integration.

## Features

✅ **JWT Authentication**: All endpoints verify user identity via Supabase JWT tokens  
✅ **Secure by Design**: Uses service role key securely, never trusts frontend for user_id  
✅ **Weekly Usage Limits**: Tracks and enforces AI analysis limits (2 per week)  
✅ **Clean Architecture**: Separation of concerns with helper functions  
✅ **Production Ready**: Proper error handling, type hints, and documentation  

## API Endpoints

### `GET /journal/today`
Fetch today's journal entry, analysis, and weekly usage statistics.

**Authentication**: Required (Bearer JWT)

**Response**:
```json
{
  "journal_entry": {
    "id": "uuid",
    "user_id": "uuid",
    "date": "2026-02-11",
    "content": "Today I felt...",
    "created_at": "2026-02-11T10:30:00",
    "updated_at": "2026-02-11T10:30:00"
  },
  "analysis": {
    "id": "uuid",
    "entry_id": "uuid",
    "user_id": "uuid",
    "confidence": 72,
    "abundance": 65,
    "clarity": 80,
    "gratitude": 85,
    "resistance": 35,
    "dominant_emotion": "Hopeful",
    "tone": "Reflective",
    "goal_present": true,
    "self_doubt_present": "Minimal",
    "created_at": "2026-02-11T11:00:00"
  },
  "usage": {
    "count": 1,
    "limit": 2,
    "week_start": "2026-02-10"
  }
}
```

---

### `POST /journal/save`
Save or update today's journal entry.

**Authentication**: Required (Bearer JWT)

**Request Body**:
```json
{
  "content": "What feels present today..."
}
```

**Response**:
```json
{
  "success": true,
  "message": "Journal entry created",
  "data": {
    "id": "uuid",
    "user_id": "uuid",
    "date": "2026-02-11",
    "content": "What feels present today...",
    "created_at": "2026-02-11T10:30:00",
    "updated_at": "2026-02-11T10:30:00"
  }
}
```

---

### `POST /journal/analyze`
Generate AI analysis for today's journal entry.

**Authentication**: Required (Bearer JWT)

**Request Body**: None

**Response** (Success):
```json
{
  "success": true,
  "message": "Analysis generated successfully",
  "data": {
    "id": "uuid",
    "entry_id": "uuid",
    "user_id": "uuid",
    "confidence": 72,
    "abundance": 65,
    "clarity": 80,
    "gratitude": 85,
    "resistance": 35,
    "dominant_emotion": "Hopeful",
    "tone": "Reflective",
    "goal_present": true,
    "self_doubt_present": "Minimal",
    "created_at": "2026-02-11T11:00:00"
  },
  "usage": {
    "count": 1,
    "limit": 2
  }
}
```

**Response** (Limit Reached - 429):
```json
{
  "detail": "Weekly analysis limit reached (2/2). Resets next Monday."
}
```

**Response** (No Entry - 404):
```json
{
  "detail": "No journal entry found for today. Please save an entry first."
}
```

---

## Database Schema

The backend expects the following Supabase tables:

### `profiles`
```sql
CREATE TABLE profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id),
  email TEXT,
  full_name TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### `journal_entries`
```sql
CREATE TABLE journal_entries (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES profiles(id) NOT NULL,
  date DATE NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, date)
);
```

### `ai_analyses`
```sql
CREATE TABLE ai_analyses (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  entry_id UUID REFERENCES journal_entries(id) NOT NULL,
  user_id UUID REFERENCES profiles(id) NOT NULL,
  confidence INTEGER NOT NULL,
  abundance INTEGER NOT NULL,
  clarity INTEGER NOT NULL,
  gratitude INTEGER NOT NULL,
  resistance INTEGER NOT NULL,
  dominant_emotion TEXT NOT NULL,
  tone TEXT NOT NULL,
  goal_present BOOLEAN NOT NULL,
  self_doubt_present TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(entry_id)
);
```

### `ai_usage`
```sql
CREATE TABLE ai_usage (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES profiles(id) NOT NULL,
  week_start DATE NOT NULL,
  count INTEGER DEFAULT 0,
  limit INTEGER DEFAULT 2,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, week_start)
);
```

---

## Setup

### 1. Install Dependencies
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure Environment Variables
```powershell
cp .env.example .env
```

Edit `.env` and add your Supabase credentials:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key-here
```

### 3. Run the Server
```powershell
python main.py
```

Or using uvicorn directly:
```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Access API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Security Considerations

🔒 **Service Role Key**: Stored securely in environment variables, never committed to git  
🔒 **JWT Verification**: Every request validates the JWT token with Supabase  
🔒 **User ID Extraction**: User identity always extracted from verified JWT, never from request body  
🔒 **CORS**: Configure `allow_origins` in production to only accept requests from your frontend domain  
🔒 **Rate Limiting**: Weekly usage limits enforced at the database level  

---

## Testing Endpoints

### Using curl (PowerShell):

**Get Today's Journal**:
```powershell
$headers = @{
    "Authorization" = "Bearer YOUR_JWT_TOKEN"
}
Invoke-RestMethod -Uri "http://localhost:8000/journal/today" -Headers $headers -Method Get
```

**Save Journal Entry**:
```powershell
$headers = @{
    "Authorization" = "Bearer YOUR_JWT_TOKEN"
    "Content-Type" = "application/json"
}
$body = @{
    content = "Today I reflected on my goals and felt a sense of clarity."
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/journal/save" -Headers $headers -Method Post -Body $body
```

**Analyze Journal**:
```powershell
$headers = @{
    "Authorization" = "Bearer YOUR_JWT_TOKEN"
}
Invoke-RestMethod -Uri "http://localhost:8000/journal/analyze" -Headers $headers -Method Post
```

---

## Project Structure

```
backend/
├── main.py              # FastAPI application with all endpoints
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
└── README.md           # This file
```

---

## Future Enhancements

- [ ] Integrate actual AI/LLM for sentiment analysis
- [ ] Add pagination for historical journal entries
- [ ] Implement `/journal/history` endpoint
- [ ] Add caching layer (Redis)
- [ ] Implement rate limiting middleware
- [ ] Add logging and monitoring
- [ ] Create tests (pytest)
- [ ] Add background tasks for async analysis
- [ ] Implement webhook notifications

---

## Error Codes

| Status Code | Description |
|------------|-------------|
| 200 | Success |
| 401 | Unauthorized (Invalid/Missing JWT) |
| 404 | Resource Not Found |
| 429 | Too Many Requests (Weekly limit reached) |
| 500 | Internal Server Error |

---

**Selfspeak Backend** - Reflect. Align.
