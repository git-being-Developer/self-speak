// ============================================
// Selfspeak Frontend - Main Application Logic
// ============================================

// ============================================
// State Management
// ============================================

// Supabase client is already initialized in supabase-client.js as window.supabase
// We'll access it directly without redeclaring

let appState = {
    currentDate: new Date(),
    selectedDate: new Date(),
    journalCache: new Map(), // Map<dateString, {journal, analysis}>
    cacheRange: { start: null, end: null },
    usage: { used: 0, limit: 3 },
    user: null,
};

// ============================================
// Date Utilities
// ============================================
function formatDate(date) {
    const options = { weekday: 'long', month: 'short', day: 'numeric' };
    return date.toLocaleDateString('en-US', options).replace(',', ' ·');
}

function toDateString(date) {
    return date.toISOString().split('T')[0]; // YYYY-MM-DD
}

function parseDate(dateString) {
    return new Date(dateString + 'T00:00:00');
}

function addDays(date, days) {
    const newDate = new Date(date);
    newDate.setDate(newDate.getDate() + days);
    return newDate;
}

function isSameDay(date1, date2) {
    return toDateString(date1) === toDateString(date2);
}

function get7DayRange(centerDate) {
    const start = addDays(centerDate, -3);
    const end = addDays(centerDate, 3);
    return { start, end };
}

// ============================================
// Authentication
// ============================================
async function checkAuth() {
    const { data: { session }, error } = await window.supabase.auth.getSession();

    if (!session) {
        console.log('No active session, redirecting to login...');
        window.location.href = '/login.html';
        return null;
    }

    console.log('✅ User authenticated:', session.user.email);
    appState.user = session.user;

    // Set token for API calls
    api.setToken(session.access_token);

    // Update UI with user info
    updateUserProfile(session.user);

    return session;
}

function updateUserProfile(user) {
    const avatarImg = document.getElementById('userAvatar');
    if (user.user_metadata?.avatar_url) {
        avatarImg.src = user.user_metadata.avatar_url;
    } else if (user.user_metadata?.picture) {
        avatarImg.src = user.user_metadata.picture;
    }
}

async function handleLogout() {
    try {
        console.log('🔓 Logging out...');

        // Sign out from Supabase
        await window.supabase.auth.signOut();

        // Clear local state
        appState = {
            currentDate: new Date(),
            selectedDate: new Date(),
            journalCache: new Map(),
            cacheRange: { start: null, end: null },
            usage: { used: 0, limit: 3 },
            user: null,
        };

        // Clear localStorage
        localStorage.removeItem('selfspeak_session');

        // Redirect to login
        window.location.href = '/login.html';
    } catch (error) {
        console.error('❌ Logout failed:', error);
        showNotification('Failed to logout', 'error');
    }
}

// ============================================
// Data Loading
// ============================================
async function loadDateRange(startDate, endDate) {
    try {
        const startStr = toDateString(startDate);
        const endStr = toDateString(endDate);

        console.log(`📥 Loading range: ${startStr} to ${endStr}`);

        const data = await api.getJournalRange(startStr, endStr);

        // Update cache
        appState.cacheRange = { start: startDate, end: endDate };

        // Clear and repopulate cache for this range
        data.entries.forEach(entry => {
            const dateStr = entry.journal_entry.entry_date;
            appState.journalCache.set(dateStr, {
                journal: entry.journal_entry,
                analysis: entry.analysis
            });
        });

        // Update usage from API response
        if (data.usage) {
            appState.usage = {
                used: data.usage.used,
                limit: data.usage.limit
            };
            console.log('📈 Usage loaded:', appState.usage);
            updateUsageDisplay();
        }

        console.log(`✅ Loaded ${data.entries.length} entries`);
        return data;
    } catch (error) {
        console.error('❌ Failed to load date range:', error);
        throw error;
    }
}

async function loadCurrentDateData() {
    const selectedDateStr = toDateString(appState.selectedDate);

    // Check cache first
    if (appState.journalCache.has(selectedDateStr)) {
        const cached = appState.journalCache.get(selectedDateStr);
        displayJournalData(cached.journal, cached.analysis);
        return;
    }

    // Load 7-day window
    const range = get7DayRange(appState.selectedDate);

    try {
        await loadDateRange(range.start, range.end);

        // Display data for selected date
        const data = appState.journalCache.get(selectedDateStr);
        displayJournalData(data?.journal || null, data?.analysis || null);
    } catch (error) {
        console.error('Failed to load data:', error);
        displayJournalData(null, null);
    }
}

// ============================================
// UI Rendering
// ============================================
function displayJournalData(journal, analysis) {
    const journalText = document.getElementById('journalText');
    const analysisSection = document.getElementById('analysisSection');
    const saveBtn = document.getElementById('saveBtn');
    const analyzeBtn = document.getElementById('analyzeBtn');

    // Clear previous state
    journalText.value = '';
    analysisSection.classList.remove('active');

    // Check if viewing current date (today)
    const isToday = isSameDay(appState.selectedDate, appState.currentDate);
    const isPastDate = appState.selectedDate < appState.currentDate;

    // State 1: No journal
    if (!journal) {
        journalText.value = '';
        journalText.placeholder = isToday ? 'What feels present today?' : 'No entry for this date';
        journalText.disabled = isPastDate; // Disable editing for past dates
        journalText.dispatchEvent(new Event('input')); // Update word count
        console.log('📝 No journal for this date');
    } else {
        // State 2: Journal exists
        journalText.value = journal.content || '';
        journalText.placeholder = 'What feels present today?';
        journalText.disabled = isPastDate; // Disable editing for past dates
        journalText.dispatchEvent(new Event('input')); // Update word count
        console.log('✅ Journal loaded');
    }

    // Disable Save and Analyze buttons for past dates
    if (saveBtn) {
        saveBtn.disabled = isPastDate;
        saveBtn.title = isPastDate ? 'Cannot edit past entries' : '';
    }

    if (analyzeBtn) {
        if (isPastDate) {
            analyzeBtn.disabled = true;
            analyzeBtn.title = 'Cannot analyze past entries';
        } else {
            // Check usage limit for current date
            const limitReached = appState.usage.used >= appState.usage.limit;
            analyzeBtn.disabled = limitReached;
            analyzeBtn.title = limitReached ? 'Weekly limit reached. Resets next Monday.' : '';
            analyzeBtn.textContent = limitReached ? 'Limit Reached' : 'Analyze';
        }
    }

    // State 3: Journal with analysis
    if (analysis) {
        displayAnalysis(analysis);
        console.log('✅ Analysis loaded');
    }
}

function displayAnalysis(analysis) {
    if (!analysis) return;

    console.log('🎨 Displaying analysis:', analysis);

    const analysisSection = document.getElementById('analysisSection');

    // Show analysis section
    analysisSection.classList.add('active');

    // Update metadata badges safely
    updateMetadataBadges(analysis);

    // Update alignment score
    updateAlignmentScore(analysis);

    // Update reflection insight
    updateReflectionInsight(analysis);

    // Generate radar chart
    setTimeout(() => {
        generateRadarChart([
            analysis.confidence_score || 0,
            analysis.abundance_score || 0,
            analysis.clarity_score || 0,
            analysis.gratitude_score || 0,
            analysis.resistance_score || 0
        ]);
    }, 300);

    // Scroll to analysis
    setTimeout(() => {
        analysisSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 100);
}

function updateMetadataBadges(analysis) {
    if (!analysis) return;

    const badges = document.querySelectorAll('.badge-metadata');

    // Guard each badge update
    if (badges[0] && badges[0].querySelector('.badge-value')) {
        badges[0].querySelector('.badge-value').textContent = analysis.dominant_emotion || 'Reflective';
    }
    if (badges[1] && badges[1].querySelector('.badge-value')) {
        badges[1].querySelector('.badge-value').textContent = analysis.overall_tone || 'calm';
    }
    if (badges[2] && badges[2].querySelector('.badge-value')) {
        const goalValue = analysis.goal_present !== undefined ? (analysis.goal_present ? 'Yes' : 'No') : 'Unknown';
        badges[2].querySelector('.badge-value').textContent = goalValue;
    }
    if (badges[3] && badges[3].querySelector('.badge-value')) {
        const doubtValue = analysis.self_doubt_present !== undefined ? (analysis.self_doubt_present ? 'Present' : 'Minimal') : 'Unknown';
        badges[3].querySelector('.badge-value').textContent = doubtValue;
    }
}

function updateAlignmentScore(analysis) {
    const alignmentScoreCard = document.getElementById('alignmentScoreCard');
    const alignmentScoreValue = document.getElementById('alignmentScoreValue');

    if (!alignmentScoreCard || !alignmentScoreValue) {
        console.warn('⚠️ Alignment score elements not found');
        return;
    }

    // Show card and display score if available
    if (analysis && analysis.alignment_score !== undefined) {
        alignmentScoreValue.textContent = analysis.alignment_score;
        alignmentScoreCard.style.display = 'block';
        console.log('✅ Alignment score displayed:', analysis.alignment_score);
    } else {
        alignmentScoreCard.style.display = 'none';
        console.log('ℹ️ No alignment score data to display');
    }
}

function updateReflectionInsight(analysis) {
    const reflectionInsightCard = document.getElementById('reflectionInsightCard');
    const reflectionInsightText = document.getElementById('reflectionInsightText');

    if (!reflectionInsightCard || !reflectionInsightText) {
        console.warn('⚠️ Reflection insight elements not found');
        return;
    }

    // Show card only if daily_reflection_insight exists
    if (analysis && analysis.daily_reflection_insight && analysis.daily_reflection_insight.trim()) {
        reflectionInsightText.textContent = analysis.daily_reflection_insight;
        reflectionInsightCard.style.display = 'block';
        console.log('✅ Reflection insight displayed');
    } else {
        reflectionInsightCard.style.display = 'none';
        console.log('ℹ️ No reflection insight data to display');
    }
}

function updateDateDisplay() {
    const dateElement = document.querySelector('.current-date');
    dateElement.textContent = formatDate(appState.selectedDate);

    // Update navigation buttons state
    const nextBtn = document.getElementById('nextDate');
    const isToday = isSameDay(appState.selectedDate, appState.currentDate);

    // Disable next button if viewing today
    if (nextBtn) {
        nextBtn.disabled = isToday;
    }
}

function updateUsageDisplay() {
    const usageText = document.querySelector('.usage-text span');
    if (usageText && appState.usage) {
        usageText.textContent = `${appState.usage.used} of ${appState.usage.limit} analyses used this week`;
    }

    // Disable analyze button if limit reached
    const analyzeBtn = document.getElementById('analyzeBtn');
    if (analyzeBtn && appState.usage.used >= appState.usage.limit) {
        analyzeBtn.disabled = true;
        analyzeBtn.textContent = 'Limit Reached';
        analyzeBtn.title = 'Weekly limit reached. Resets next Monday.';
    } else if (analyzeBtn) {
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = 'Analyze';
        analyzeBtn.title = '';
    }
}

// ============================================
// Date Navigation
// ============================================
async function navigateDate(direction) {
    // direction: -1 for previous, +1 for next
    appState.selectedDate = addDays(appState.selectedDate, direction);

    updateDateDisplay();
    await loadCurrentDateData();

    // Update button states based on new date
    updateButtonStates();
}

function updateButtonStates() {
    const saveBtn = document.getElementById('saveBtn');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const journalText = document.getElementById('journalText');

    const isPastDate = appState.selectedDate < appState.currentDate;

    // Disable/enable textarea
    if (journalText) {
        journalText.disabled = isPastDate;
        journalText.placeholder = isPastDate ? 'No entry for this date' : 'What feels present today?';
    }

    // Disable/enable Save button
    if (saveBtn) {
        saveBtn.disabled = isPastDate;
        saveBtn.title = isPastDate ? 'Cannot edit past entries' : '';
    }

    // Disable/enable Analyze button
    if (analyzeBtn) {
        if (isPastDate) {
            analyzeBtn.disabled = true;
            analyzeBtn.title = 'Cannot analyze past entries';
            analyzeBtn.textContent = 'Analyze';
        } else {
            // Check usage limit for current date
            const limitReached = appState.usage.used >= appState.usage.limit;
            analyzeBtn.disabled = limitReached;
            analyzeBtn.title = limitReached ? 'Weekly limit reached. Resets next Monday.' : '';
            analyzeBtn.textContent = limitReached ? 'Limit Reached' : 'Analyze';
        }
    }
}

// ============================================
// Journal Actions
// ============================================
async function saveJournal() {
    const journalText = document.getElementById('journalText');
    const saveBtn = document.getElementById('saveBtn');
    const content = journalText.value.trim();

    // Prevent saving past dates
    const isPastDate = appState.selectedDate < appState.currentDate;
    if (isPastDate) {
        showNotification('Cannot edit past entries', 'warning');
        return;
    }

    if (!content) {
        showNotification('Please write something before saving', 'warning');
        return;
    }

    // Disable button during save
    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving...';

    try {
        console.log('💾 Saving journal entry...');

        // Pass the selected date to the API
        const selectedDateStr = toDateString(appState.selectedDate);
        const result = await api.saveJournal(content, selectedDateStr);

        console.log('✅ Journal saved:', result);

        // Update cache
        const existingData = appState.journalCache.get(selectedDateStr) || {};
        appState.journalCache.set(selectedDateStr, {
            journal: result.data,
            analysis: existingData.analysis || null
        });

        showNotification('Journal saved successfully', 'success');
        return result; // Return for use in analyzeJournal
    } catch (error) {
        console.error('❌ Save failed:', error);
        showNotification(error.message || 'Failed to save journal', 'error');
        throw error; // Re-throw for analyzeJournal to catch
    } finally {
        saveBtn.disabled = isPastDate; // Keep disabled if past date
        saveBtn.textContent = 'Save';
    }
}

async function analyzeJournal() {
    const analyzeBtn = document.getElementById('analyzeBtn');
    const journalText = document.getElementById('journalText');
    const content = journalText.value.trim();

    // Prevent analyzing past dates
    const isPastDate = appState.selectedDate < appState.currentDate;
    if (isPastDate) {
        showNotification('Cannot analyze past entries', 'warning');
        return;
    }

    // Check if there's content to analyze
    if (!content) {
        showNotification('Please write something before analyzing', 'warning');
        return;
    }

    // Disable button during processing
    analyzeBtn.disabled = true;
    analyzeBtn.textContent = 'Saving & Analyzing...';

    try {
        // First, save the journal entry to ensure DB has latest content
        console.log('💾 Auto-saving before analysis...');
        const selectedDateStr = toDateString(appState.selectedDate);

        try {
            await api.saveJournal(content, selectedDateStr);
            console.log('✅ Auto-save complete');
        } catch (saveError) {
            console.error('❌ Auto-save failed:', saveError);
            throw new Error('Failed to save journal before analyzing. Please try again.');
        }

        // Now analyze with the selected date
        analyzeBtn.textContent = 'Analyzing...';
        console.log('🔍 Requesting analysis for date:', selectedDateStr);
        const result = await api.analyzeJournal(selectedDateStr);

        console.log('✅ Analysis received:', result);
        console.log('📊 Analysis data:', result.data);

        // Update cache with new analysis
        const existingData = appState.journalCache.get(selectedDateStr) || {};
        appState.journalCache.set(selectedDateStr, {
            journal: existingData.journal,
            analysis: result.data
        });

        // Update usage from response
        if (result.usage) {
            appState.usage = {
                used: result.usage.used,
                limit: result.usage.limit
            };
            console.log('📈 Usage updated:', appState.usage);
            updateUsageDisplay();
        }

        // Display the analysis immediately
        displayAnalysis(result.data);

        showNotification('Analysis complete!', 'success');
    } catch (error) {
        console.error('❌ Analysis failed:', error);

        const errorMsg = error.message || '';
        if (errorMsg.includes('limit reached') || errorMsg.includes('429')) {
            showNotification('Weekly analysis limit reached. Resets next Monday.', 'warning');
        } else if (errorMsg.includes('No journal entry') || errorMsg.includes('404')) {
            showNotification('Please save a journal entry first.', 'warning');
        } else {
            showNotification(errorMsg || 'Analysis failed. Please try again.', 'error');
        }
    } finally {
        // Re-check if still on current date (user might have navigated)
        const stillCurrentDate = !isPastDate;
        const limitReached = appState.usage.used >= appState.usage.limit;
        analyzeBtn.disabled = !stillCurrentDate || limitReached;
        analyzeBtn.textContent = limitReached ? 'Limit Reached' : 'Analyze';
    }
}


// ============================================
// Notifications
// ============================================
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        background: ${type === 'success' ? '#7B9E9D' : type === 'error' ? '#C77B7B' : '#E8B86D'};
        color: white;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// ============================================
// Radar Chart
// ============================================
function generateRadarChart(dataPoints = [72, 65, 80, 85, 35]) {
    const canvas = document.getElementById('radarChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = 140;
    const axes = 5;
    const labels = ['Confidence', 'Abundance', 'Clarity', 'Gratitude', 'Resistance'];

    // Draw background circles
    ctx.strokeStyle = 'rgba(139, 157, 154, 0.1)';
    ctx.lineWidth = 1;
    for (let i = 1; i <= 5; i++) {
        ctx.beginPath();
        ctx.arc(centerX, centerY, (radius / 5) * i, 0, Math.PI * 2);
        ctx.stroke();
    }

    // Draw axes
    ctx.strokeStyle = 'rgba(139, 157, 154, 0.15)';
    for (let i = 0; i < axes; i++) {
        const angle = (Math.PI * 2 * i) / axes - Math.PI / 2;
        const x = centerX + Math.cos(angle) * radius;
        const y = centerY + Math.sin(angle) * radius;

        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(x, y);
        ctx.stroke();

        // Draw labels
        const labelDistance = radius + 30;
        const labelX = centerX + Math.cos(angle) * labelDistance;
        const labelY = centerY + Math.sin(angle) * labelDistance;

        ctx.fillStyle = '#5A7B7D';
        ctx.font = '14px Inter';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(labels[i], labelX, labelY);
    }

    // Animate data polygon
    let animationProgress = 0;
    const animationDuration = 1000;
    const startTime = Date.now();

    function animate() {
        const elapsed = Date.now() - startTime;
        animationProgress = Math.min(elapsed / animationDuration, 1);
        const easeProgress = 1 - Math.pow(1 - animationProgress, 3);

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Redraw background
        ctx.strokeStyle = 'rgba(139, 157, 154, 0.1)';
        ctx.lineWidth = 1;
        for (let i = 1; i <= 5; i++) {
            ctx.beginPath();
            ctx.arc(centerX, centerY, (radius / 5) * i, 0, Math.PI * 2);
            ctx.stroke();
        }

        // Redraw axes and labels
        ctx.strokeStyle = 'rgba(139, 157, 154, 0.15)';
        for (let i = 0; i < axes; i++) {
            const angle = (Math.PI * 2 * i) / axes - Math.PI / 2;
            const x = centerX + Math.cos(angle) * radius;
            const y = centerY + Math.sin(angle) * radius;

            ctx.beginPath();
            ctx.moveTo(centerX, centerY);
            ctx.lineTo(x, y);
            ctx.stroke();

            const labelDistance = radius + 30;
            const labelX = centerX + Math.cos(angle) * labelDistance;
            const labelY = centerY + Math.sin(angle) * labelDistance;

            ctx.fillStyle = '#5A7B7D';
            ctx.font = '14px Inter';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(labels[i], labelX, labelY);
        }

        // Draw data polygon
        ctx.beginPath();
        for (let i = 0; i < axes; i++) {
            const angle = (Math.PI * 2 * i) / axes - Math.PI / 2;
            const value = (dataPoints[i] / 100) * radius * easeProgress;
            const x = centerX + Math.cos(angle) * value;
            const y = centerY + Math.sin(angle) * value;

            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        }
        ctx.closePath();

        ctx.fillStyle = 'rgba(123, 158, 157, 0.25)';
        ctx.fill();
        ctx.strokeStyle = 'rgba(123, 158, 157, 0.8)';
        ctx.lineWidth = 2.5;
        ctx.stroke();

        // Draw data points
        for (let i = 0; i < axes; i++) {
            const angle = (Math.PI * 2 * i) / axes - Math.PI / 2;
            const value = (dataPoints[i] / 100) * radius * easeProgress;
            const x = centerX + Math.cos(angle) * value;
            const y = centerY + Math.sin(angle) * value;

            ctx.beginPath();
            ctx.arc(x, y, 5, 0, Math.PI * 2);
            ctx.fillStyle = '#7B9E9D';
            ctx.fill();
            ctx.strokeStyle = 'white';
            ctx.lineWidth = 2;
            ctx.stroke();
        }

        if (animationProgress < 1) {
            requestAnimationFrame(animate);
        }
    }

    animate();
}

// ============================================
// Event Listeners
// ============================================
document.addEventListener('DOMContentLoaded', async function() {
    // Check if Supabase client is initialized
    if (!window.supabase) {
        console.error('❌ Supabase client not initialized!');
        alert('Failed to initialize authentication. Please refresh the page.');
        return;
    }

    console.log('✅ Supabase client available');

    // Check authentication
    const session = await checkAuth();
    if (!session) return;

    // Set initial date display
    updateDateDisplay();

    // Load initial data
    await loadCurrentDateData();

    // Setup UI interactions
    const journalText = document.getElementById('journalText');
    const wordCountDisplay = document.querySelector('.word-count');

    if (journalText && wordCountDisplay) {
        journalText.addEventListener('input', function() {
            const text = this.value.trim();
            const wordCount = text === '' ? 0 : text.split(/\s+/).length;
            wordCountDisplay.textContent = `${wordCount} word${wordCount !== 1 ? 's' : ''}`;

            // Auto-resize textarea
            this.style.height = 'auto';
            this.style.height = Math.max(240, this.scrollHeight) + 'px';
        });
    }

    // Audio toggle
    const audioToggle = document.getElementById('audioToggle');
    const audioDropdown = document.getElementById('audioDropdown');

    if (audioToggle && audioDropdown) {
        audioToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            audioDropdown.classList.toggle('active');
            this.classList.toggle('active');
        });

        document.addEventListener('click', function(e) {
            if (!audioDropdown.contains(e.target) && e.target !== audioToggle) {
                audioDropdown.classList.remove('active');
                audioToggle.classList.remove('active');
            }
        });
    }

    // Audio play buttons
    const playButtons = document.querySelectorAll('.play-btn');
    let currentlyPlaying = null;

    playButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();

            if (currentlyPlaying && currentlyPlaying !== this) {
                currentlyPlaying.classList.remove('playing');
            }

            this.classList.toggle('playing');
            currentlyPlaying = this.classList.contains('playing') ? this : null;

            const mode = this.getAttribute('data-mode');
            console.log(`${this.classList.contains('playing') ? 'Playing' : 'Stopped'} ${mode} mode`);
        });
    });

    // Attach action event listeners
    const saveBtn = document.getElementById('saveBtn');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const prevDateBtn = document.getElementById('prevDate');
    const nextDateBtn = document.getElementById('nextDate');
    const logoutBtn = document.getElementById('logoutBtn');

    if (saveBtn) {
        saveBtn.addEventListener('click', saveJournal);
    }

    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', analyzeJournal);
    }

    if (prevDateBtn) {
        prevDateBtn.addEventListener('click', () => navigateDate(-1));
    }

    if (nextDateBtn) {
        nextDateBtn.addEventListener('click', () => navigateDate(1));
    }

    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }

    console.log('✅ App initialized');
});
