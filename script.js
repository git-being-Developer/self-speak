// ============================================
// Authentication & Session Management
// ============================================

// Supabase client is initialized in supabase-client.js
// Access it via window.supabase
(function(){
'use strict';
let supabase;

// Check authentication on page load
async function checkAuth() {
    const { data: { session }, error } = await supabase.auth.getSession();

    if (!session) {
        console.log('No active session, redirecting to login...');
        window.location.href = '/login.html';
        return null;
    }

    console.log('✅ User authenticated:', session.user.email);

    // Set token for API calls
    api.setToken(session.access_token);

    // Update UI with user info
    updateUserProfile(session.user);

    return session;
}

// Update user profile in UI
function updateUserProfile(user) {
    const avatarImg = document.querySelector('.user-avatar img');
    if (user.user_metadata?.avatar_url) {
        avatarImg.src = user.user_metadata.avatar_url;
    }
    console.log('User profile updated');
}

// Load today's data from backend
async function loadTodayData() {
    try {
        console.log('📥 Loading today\'s journal data...');
        const data = await api.getTodayJournal();

        console.log('Received data:', data);

        // Populate journal entry if exists
        if (data.journal_entry) {
            journalText.value = data.journal_entry.content;
            journalText.dispatchEvent(new Event('input')); // Trigger word count update
            console.log('✅ Journal entry loaded');
        }

        // Show analysis if exists
        if (data.analysis) {
            displayAnalysis(data.analysis);
            console.log('✅ Analysis loaded');
        }

        // Update usage display
        if (data.usage) {
            const usageText = document.querySelector('.usage-text');
            usageText.textContent = `${data.usage.analyses_used} of ${data.usage.weekly_limit} analyses used this week`;
        }

    } catch (error) {
        console.error('❌ Failed to load today\'s data:', error);
        showNotification('Failed to load journal data', 'error');
    }
}

// Word Count Functionality
const journalText = document.getElementById('journalText');
const wordCountDisplay = document.querySelector('.word-count');

journalText.addEventListener('input', function() {
    const text = this.value.trim();
    const wordCount = text === '' ? 0 : text.split(/\s+/).length;
    wordCountDisplay.textContent = `${wordCount} word${wordCount !== 1 ? 's' : ''}`;

    // Auto-resize textarea
    this.style.height = 'auto';
    this.style.height = Math.max(240, this.scrollHeight) + 'px';
});

// Audio Toggle Functionality
const audioToggle = document.getElementById('audioToggle');
const audioDropdown = document.getElementById('audioDropdown');

audioToggle.addEventListener('click', function(e) {
    e.stopPropagation();
    audioDropdown.classList.toggle('active');
    this.classList.toggle('active');
});

// Close audio dropdown when clicking outside
document.addEventListener('click', function(e) {
    if (!audioDropdown.contains(e.target) && e.target !== audioToggle) {
        audioDropdown.classList.remove('active');
        audioToggle.classList.remove('active');
    }
});

// Save Button Functionality
const saveBtn = document.getElementById('saveBtn');

saveBtn.addEventListener('click', async function() {
    const content = journalText.value.trim();

    if (!content) {
        showNotification('Please write something before saving', 'warning');
        return;
    }

    // Disable button during save
    this.disabled = true;
    this.textContent = 'Saving...';

    try {
        console.log('💾 Saving journal entry...');
        const saved = await api.saveJournal(content);

        console.log('✅ Journal saved:', saved);
        showNotification('Journal saved successfully', 'success');

    } catch (error) {
        console.error('❌ Save failed:', error);
        showNotification('Failed to save journal', 'error');
    } finally {
        // Re-enable button
        this.disabled = false;
        this.textContent = 'Save';
    }
});

// Play/Stop Audio Toggle
const playButtons = document.querySelectorAll('.play-btn');
let currentlyPlaying = null;

playButtons.forEach(btn => {
    btn.addEventListener('click', function(e) {
        e.stopPropagation();

        // Stop currently playing if different
        if (currentlyPlaying && currentlyPlaying !== this) {
            currentlyPlaying.classList.remove('playing');
        }

        // Toggle current button
        this.classList.toggle('playing');

        // Update currently playing reference
        currentlyPlaying = this.classList.contains('playing') ? this : null;

        const mode = this.getAttribute('data-mode');
        console.log(`${this.classList.contains('playing') ? 'Playing' : 'Stopped'} ${mode} mode`);
    });
});

// Analyze Button Functionality
const analyzeBtn = document.getElementById('analyzeBtn');
const analysisSection = document.getElementById('analysisSection');
let chartInstance = null;

analyzeBtn.addEventListener('click', async function() {
    // Disable button during processing
    this.disabled = true;
    this.textContent = 'Analyzing...';

    try {
        console.log('🔍 Requesting analysis...');
        const analysis = await api.analyzeJournal();

        console.log('✅ Analysis received:', analysis);

        // Display the analysis
        displayAnalysis(analysis);

        // Show success notification
        showNotification('Analysis complete!', 'success');

    } catch (error) {
        console.error('❌ Analysis failed:', error);

        if (error.message.includes('Weekly limit')) {
            showNotification('Weekly analysis limit reached. Resets next Monday.', 'warning');
        } else if (error.message.includes('No journal entry')) {
            showNotification('Please write something in your journal first.', 'warning');
        } else {
            showNotification('Analysis failed. Please try again.', 'error');
        }
    } finally {
        // Re-enable button
        this.disabled = false;
        this.textContent = 'Analyze';
    }
});

// Display analysis results
function displayAnalysis(analysis) {
    // Show analysis section with animation
    analysisSection.classList.add('active');

    // Update metadata badges
    updateMetadataBadges(analysis);

    // Scroll to analysis section smoothly
    setTimeout(() => {
        analysisSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 100);

    // Generate radar chart with actual data
    setTimeout(() => {
        generateRadarChart([
            analysis.confidence_score,
            analysis.abundance_score,
            analysis.clarity_score,
            analysis.gratitude_score,
            analysis.resistance_score
        ]);
    }, 300);
}

// Update metadata badges
function updateMetadataBadges(analysis) {
    const badges = document.querySelectorAll('.badge-metadata');

    badges[0].querySelector('.badge-value').textContent = analysis.dominant_emotion;
    badges[1].querySelector('.badge-value').textContent = analysis.overall_tone;
    badges[2].querySelector('.badge-value').textContent = analysis.goal_present ? 'Yes' : 'No';
    badges[3].querySelector('.badge-value').textContent = analysis.self_doubt_present ? 'Present' : 'Minimal';
}

// Show notification
function showNotification(message, type = 'info') {
    // Create notification element
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

    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Radar Chart Generation
function generateRadarChart(dataPoints = [72, 65, 80, 85, 35]) {
    const canvas = document.getElementById('radarChart');
    const ctx = canvas.getContext('2d');

    // Clear previous chart
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
    ctx.lineWidth = 1;
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
    const animationDuration = 1000; // 1 second
    const startTime = Date.now();

    function animate() {
        const elapsed = Date.now() - startTime;
        animationProgress = Math.min(elapsed / animationDuration, 1);

        // Easing function for smooth animation
        const easeProgress = 1 - Math.pow(1 - animationProgress, 3);

        // Clear only the data area
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Redraw background
        ctx.strokeStyle = 'rgba(139, 157, 154, 0.1)';
        ctx.lineWidth = 1;
        for (let i = 1; i <= 5; i++) {
            ctx.beginPath();
            ctx.arc(centerX, centerY, (radius / 5) * i, 0, Math.PI * 2);
            ctx.stroke();
        }

        // Redraw axes
        ctx.strokeStyle = 'rgba(139, 157, 154, 0.15)';
        for (let i = 0; i < axes; i++) {
            const angle = (Math.PI * 2 * i) / axes - Math.PI / 2;
            const x = centerX + Math.cos(angle) * radius;
            const y = centerY + Math.sin(angle) * radius;

            ctx.beginPath();
            ctx.moveTo(centerX, centerY);
            ctx.lineTo(x, y);
            ctx.stroke();

            // Redraw labels
            const labelDistance = radius + 30;
            const labelX = centerX + Math.cos(angle) * labelDistance;
            const labelY = centerY + Math.sin(angle) * labelDistance;

            ctx.fillStyle = '#5A7B7D';
            ctx.font = '14px Inter';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(labels[i], labelX, labelY);
        }

        // Draw data polygon with animation
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

        // Fill
        ctx.fillStyle = 'rgba(123, 158, 157, 0.25)';
        ctx.fill();

        // Stroke
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

// Initialize
document.addEventListener('DOMContentLoaded', async function() {
    // Initialize supabase client reference
    supabase = window.supabase;

    if (!supabase) {
        console.error('❌ Supabase client not initialized!');
        alert('Failed to initialize authentication. Please refresh the page.');
        return;
    }

    // Set current date
    const dateElement = document.querySelector('.current-date');
    const now = new Date();
    const options = { weekday: 'long', month: 'short', day: 'numeric' };
    const formattedDate = now.toLocaleDateString('en-US', options).replace(',', ' ·');
    dateElement.textContent = formattedDate;

    // Check authentication
    const session = await checkAuth();

    if (session) {
        // Load today's journal data
        await loadTodayData();
    }
})
})();
