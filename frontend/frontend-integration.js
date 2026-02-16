// API Integration for Selfspeak Frontend
// Backend serves frontend - same domain, zero latency!

// Use same domain for API calls
const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'  // Local development (run backend separately)
    : 'https://self-speak-production.up.railway.app';   // Production - UPDATE WITH YOUR RAILWAY/RENDER URL!

// API Client Class
class SelfSpeakAPI {
    constructor() {
        this.baseURL = API_BASE_URL;
        this.token = null;
        console.log('🔗 API Base URL:', this.baseURL);
    }

    // Set JWT token (from Supabase authentication)
    setToken(token) {
        this.token = token;
    }

    // Get authorization headers
    getHeaders() {
        const headers = {
            'Content-Type': 'application/json',
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        return headers;
    }

    // Generic request handler
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            ...options,
            headers: {
                ...this.getHeaders(),
                ...options.headers,
            },
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || `HTTP ${response.status}: ${response.statusText}`);
            }

            return data;
        } catch (error) {
            console.error(`API Error (${url}):`, error);
            throw error;
        }
    }

    // GET /journal/today
    async getTodayJournal() {
        return await this.request('/journal/today', {
            method: 'GET',
        });
    }

    // POST /journal/save
    async saveJournal(content, entryDate = null) {
        const body = { content };
        if (entryDate) {
            body.entry_date = entryDate;
        }
        return await this.request('/journal/save', {
            method: 'POST',
            body: JSON.stringify(body),
        });
    }

    // POST /journal/analyze
    async analyzeJournal(entryDate = null) {
        const params = entryDate ? `?entry_date=${entryDate}` : '';
        return await this.request(`/journal/analyze${params}`, {
            method: 'POST',
        });
    }

    // GET /journal/range
    async getJournalRange(startDate, endDate) {
        return await this.request(`/journal/range?start_date=${startDate}&end_date=${endDate}`, {
            method: 'GET',
        });
    }

    // GET /dashboard/weekly
    async getWeeklyDashboard(weekStart = null) {
        const params = weekStart ? `?week_start=${weekStart}` : '';
        return await this.request(`/dashboard/weekly${params}`, {
            method: 'GET',
        });
    }
}

// Create singleton instance
const api = new SelfSpeakAPI();

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { SelfSpeakAPI, api };
}

// Example usage with Supabase authentication:
/*

// 1. Initialize Supabase client (in your main app file)
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
    'YOUR_SUPABASE_URL',
    'YOUR_SUPABASE_ANON_KEY'
)

// 2. After user signs in, get the JWT token
const { data: { session } } = await supabase.auth.getSession()
if (session) {
    api.setToken(session.access_token)
}

// 3. Load today's journal on page load
async function loadTodayJournal() {
    try {
        const data = await api.getTodayJournal();

        // Populate journal textarea
        if (data.journal_entry) {
            document.getElementById('journalText').value = data.journal_entry.content;
        }

        // Show analysis if exists
        if (data.analysis) {
            displayAnalysis(data.analysis);
        }

        // Update usage display
        updateUsageDisplay(data.usage);

    } catch (error) {
        console.error('Failed to load today\'s journal:', error);
        showNotification('Failed to load journal', 'error');
    }
}

// 4. Save journal entry
async function saveJournalEntry() {
    const content = document.getElementById('journalText').value;

    if (!content.trim()) {
        showNotification('Please write something first', 'warning');
        return;
    }

    try {
        const result = await api.saveJournal(content);
        showNotification(result.message, 'success');

    } catch (error) {
        console.error('Failed to save journal:', error);
        showNotification('Failed to save journal', 'error');
    }
}

// 5. Analyze journal entry
async function analyzeJournalEntry() {
    try {
        const result = await api.analyzeJournal();

        // Display the analysis
        displayAnalysis(result.data);

        // Update usage count
        updateUsageDisplay(result.usage);

        showNotification(result.message, 'success');

    } catch (error) {
        if (error.message.includes('limit reached')) {
            showNotification('Weekly analysis limit reached. Resets next Monday.', 'warning');
        } else if (error.message.includes('No journal entry')) {
            showNotification('Please save a journal entry first', 'warning');
        } else {
            console.error('Failed to analyze journal:', error);
            showNotification('Failed to analyze journal', 'error');
        }
    }
}

// 6. Display analysis in the UI
function displayAnalysis(analysis) {
    // Show analysis section
    const analysisSection = document.getElementById('analysisSection');
    analysisSection.classList.add('active');

    // Update radar chart with actual data
    generateRadarChart({
        confidence: analysis.confidence,
        abundance: analysis.abundance,
        clarity: analysis.clarity,
        gratitude: analysis.gratitude,
        resistance: analysis.resistance
    });

    // Update metadata badges
    document.querySelector('[data-badge="emotion"] .badge-value').textContent = analysis.dominant_emotion;
    document.querySelector('[data-badge="tone"] .badge-value').textContent = analysis.tone;
    document.querySelector('[data-badge="goal"] .badge-value').textContent = analysis.goal_present ? 'Yes' : 'No';
    document.querySelector('[data-badge="doubt"] .badge-value').textContent = analysis.self_doubt_present;

    // Scroll to analysis
    analysisSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// 7. Update usage display
function updateUsageDisplay(usage) {
    const usageText = document.querySelector('.usage-text span');
    usageText.textContent = `${usage.count} of ${usage.limit} analyses used this week`;

    // Disable analyze button if limit reached
    const analyzeBtn = document.getElementById('analyzeBtn');
    if (usage.count >= usage.limit) {
        analyzeBtn.disabled = true;
        analyzeBtn.textContent = 'Limit Reached';
        analyzeBtn.title = 'Weekly limit reached. Resets next Monday.';
    }
}

// 8. Show notification (replace with your notification system)
function showNotification(message, type) {
    console.log(`[${type.toUpperCase()}] ${message}`);
    // Implement your notification UI here
}

// 9. Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    // Check if user is authenticated
    const { data: { session } } = await supabase.auth.getSession();

    if (!session) {
        // Redirect to login page
        window.location.href = '/login';
        return;
    }

    // Set API token
    api.setToken(session.access_token);

    // Load today's journal
    await loadTodayJournal();

    // Attach event listeners
    document.getElementById('analyzeBtn').addEventListener('click', analyzeJournalEntry);
    document.querySelector('.btn-secondary').addEventListener('click', saveJournalEntry);
});

// 10. Listen for auth state changes
supabase.auth.onAuthStateChange((event, session) => {
    if (event === 'SIGNED_IN') {
        api.setToken(session.access_token);
        loadTodayJournal();
    } else if (event === 'SIGNED_OUT') {
        api.setToken(null);
        window.location.href = '/login';
    }
});

*/
