// ============================================
// Weekly Dashboard - Main Logic
// ============================================

let dashboardState = {
    weeklyData: null,
    loading: true,
    error: null
};

// ============================================
// Authentication & Initialization
// ============================================

async function checkAuth() {
    const { data: { session }, error } = await window.supabase.auth.getSession();

    if (!session) {
        console.log('No active session, redirecting to login...');
        window.location.href = '/login.html';
        return null;
    }

    console.log('✅ User authenticated:', session.user.email);

    // Set token for API calls
    api.setToken(session.access_token);

    // Update UI with user info
    const avatarImg = document.getElementById('userAvatar');
    if (session.user.user_metadata?.avatar_url || session.user.user_metadata?.picture) {
        avatarImg.src = session.user.user_metadata.avatar_url || session.user.user_metadata.picture;
    }

    return session;
}

async function handleLogout() {
    try {
        await window.supabase.auth.signOut();
        localStorage.removeItem('selfspeak_session');
        window.location.href = '/login.html';
    } catch (error) {
        console.error('❌ Logout failed:', error);
    }
}

// ============================================
// Data Loading
// ============================================

async function loadWeeklyDashboard() {
    try {
        dashboardState.loading = true;
        showLoadingSkeleton();

        console.log('📊 Loading weekly dashboard...');
        const response = await api.getWeeklyDashboard();

        if (!response || !response.success) {
            throw new Error('Failed to fetch weekly data');
        }

        dashboardState.weeklyData = response.data;
        dashboardState.loading = false;
        dashboardState.error = null;

        console.log('✅ Weekly data loaded:', dashboardState.weeklyData);

        // Show dashboard if we have any data, otherwise show empty state
        if (!dashboardState.weeklyData || dashboardState.weeklyData.entry_count === 0) {
            showNoDataState();
        } else {
            renderDashboard();
        }

    } catch (error) {
        console.error('❌ Failed to load weekly dashboard:', error);
        dashboardState.loading = false;
        dashboardState.error = error.message;

        // If 404, show no data state
        if (error.message.includes('404') || error.message.includes('No journal')) {
            showNoDataState();
        } else {
            showErrorState(error.message);
        }
    }
}

// ============================================
// UI Rendering
// ============================================

function showLoadingSkeleton() {
    document.getElementById('loadingSkeleton').style.display = 'block';
    document.getElementById('noDataState').style.display = 'none';
    document.getElementById('dashboardContent').style.display = 'none';
}

function showNoDataState() {
    document.getElementById('loadingSkeleton').style.display = 'none';
    document.getElementById('noDataState').style.display = 'block';
    document.getElementById('dashboardContent').style.display = 'none';
}

function showErrorState(message) {
    document.getElementById('loadingSkeleton').style.display = 'none';
    document.getElementById('noDataState').style.display = 'block';
    document.getElementById('dashboardContent').style.display = 'none';

    // Update no data state to show error
    const noDataState = document.getElementById('noDataState');
    noDataState.querySelector('h3').textContent = 'Unable to Load Dashboard';
    noDataState.querySelector('p').textContent = message || 'Please try again later.';
}

function renderDashboard() {
    document.getElementById('loadingSkeleton').style.display = 'none';
    document.getElementById('noDataState').style.display = 'none';
    document.getElementById('dashboardContent').style.display = 'block';

    const data = dashboardState.weeklyData;

    // Safely render week range
    renderWeekRange(data);

    // Render charts with guards against undefined
    renderWeeklyRadarChart(data.weekly_averages || {});
    renderLineChart('confidenceLineChart', data.daily_scores || [], 'confidence');
    renderLineChart('resistanceLineChart', data.daily_scores || [], 'resistance');

    // Render trend badges
    renderTrendBadge('confidenceTrend', data.trend_data?.confidence);
    renderTrendBadge('resistanceTrend', data.trend_data?.resistance);

    // Render insight
    renderInsight(data.weekly_insight || {});
}

function renderWeekRange(data) {
    const weekRangeEl = document.getElementById('weekRange');

    if (!data || !data.daily_scores || data.daily_scores.length === 0) {
        weekRangeEl.textContent = 'This Week';
        return;
    }

    try {
        const dates = data.daily_scores.map(d => d.date).sort();
        const startDate = new Date(dates[0]);
        const endDate = new Date(dates[dates.length - 1]);

        const options = { month: 'short', day: 'numeric' };
        const start = startDate.toLocaleDateString('en-US', options);
        const end = endDate.toLocaleDateString('en-US', options);

        weekRangeEl.textContent = `${start} – ${end}, ${startDate.getFullYear()}`;
    } catch (e) {
        weekRangeEl.textContent = 'This Week';
    }
}

function renderTrendBadge(elementId, trend) {
    const badge = document.getElementById(elementId);
    if (!badge) return;

    const trendValue = (trend || 'stable').toLowerCase();
    badge.className = `trend-badge ${trendValue}`;

    const trendText = {
        'up': 'Improving',
        'down': 'Declining',
        'stable': 'Steady'
    };

    badge.textContent = trendText[trendValue] || 'Steady';
}

function renderInsight(insight) {
    const summaryEl = document.getElementById('insightSummary');
    const questionEl = document.getElementById('insightQuestion');

    if (summaryEl) {
        summaryEl.textContent = insight.summary_text || 'No insight available yet.';
    }

    if (questionEl) {
        questionEl.textContent = insight.reflection_question || 'Keep journaling to unlock personalized reflections.';
    }
}

// ============================================
// Weekly Radar Chart
// ============================================

function renderWeeklyRadarChart(averages) {
    const canvas = document.getElementById('weeklyRadarChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = 180;
    const axes = 5;
    const labels = ['Confidence', 'Abundance', 'Clarity', 'Gratitude', 'Resistance'];

    // Extract scores with safe defaults
    const scores = [
        averages.confidence || 0,
        averages.abundance || 0,
        averages.clarity || 0,
        averages.gratitude || 0,
        averages.resistance || 0
    ];

    // Draw background circles
    ctx.strokeStyle = 'rgba(139, 157, 154, 0.08)';
    ctx.lineWidth = 1;
    for (let i = 1; i <= 5; i++) {
        ctx.beginPath();
        ctx.arc(centerX, centerY, (radius / 5) * i, 0, Math.PI * 2);
        ctx.stroke();
    }

    // Draw axes
    ctx.strokeStyle = 'rgba(139, 157, 154, 0.12)';
    for (let i = 0; i < axes; i++) {
        const angle = (Math.PI * 2 * i) / axes - Math.PI / 2;
        const x = centerX + Math.cos(angle) * radius;
        const y = centerY + Math.sin(angle) * radius;

        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(x, y);
        ctx.stroke();

        // Draw labels
        const labelDistance = radius + 40;
        const labelX = centerX + Math.cos(angle) * labelDistance;
        const labelY = centerY + Math.sin(angle) * labelDistance;

        ctx.fillStyle = '#5A7B7D';
        ctx.font = '14px Inter';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(labels[i], labelX, labelY);
    }

    // Animate data polygon
    animateRadarData(ctx, centerX, centerY, radius, axes, scores);
}

function animateRadarData(ctx, centerX, centerY, radius, axes, scores) {
    let progress = 0;
    const duration = 1000;
    const startTime = Date.now();

    function animate() {
        const elapsed = Date.now() - startTime;
        progress = Math.min(elapsed / duration, 1);
        const easeProgress = 1 - Math.pow(1 - progress, 3);

        // Clear only the data area
        ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);

        // Redraw background
        ctx.strokeStyle = 'rgba(139, 157, 154, 0.08)';
        ctx.lineWidth = 1;
        for (let i = 1; i <= 5; i++) {
            ctx.beginPath();
            ctx.arc(centerX, centerY, (radius / 5) * i, 0, Math.PI * 2);
            ctx.stroke();
        }

        // Redraw axes
        ctx.strokeStyle = 'rgba(139, 157, 154, 0.12)';
        for (let i = 0; i < axes; i++) {
            const angle = (Math.PI * 2 * i) / axes - Math.PI / 2;
            const x = centerX + Math.cos(angle) * radius;
            const y = centerY + Math.sin(angle) * radius;

            ctx.beginPath();
            ctx.moveTo(centerX, centerY);
            ctx.lineTo(x, y);
            ctx.stroke();
        }

        // Draw data polygon
        ctx.beginPath();
        for (let i = 0; i < axes; i++) {
            const angle = (Math.PI * 2 * i) / axes - Math.PI / 2;
            const value = ((scores[i] || 0) / 100) * radius * easeProgress;
            const x = centerX + Math.cos(angle) * value;
            const y = centerY + Math.sin(angle) * value;

            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        }
        ctx.closePath();

        ctx.fillStyle = 'rgba(123, 158, 157, 0.2)';
        ctx.fill();
        ctx.strokeStyle = 'rgba(123, 158, 157, 0.8)';
        ctx.lineWidth = 2.5;
        ctx.stroke();

        // Draw data points
        for (let i = 0; i < axes; i++) {
            const angle = (Math.PI * 2 * i) / axes - Math.PI / 2;
            const value = ((scores[i] || 0) / 100) * radius * easeProgress;
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

        if (progress < 1) {
            requestAnimationFrame(animate);
        }
    }

    animate();
}

// ============================================
// Line Charts
// ============================================

function renderLineChart(canvasId, dailyScores, metric) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!dailyScores || dailyScores.length === 0) {
        // Draw empty state
        ctx.fillStyle = '#B8C5C2';
        ctx.font = '14px Inter';
        ctx.textAlign = 'center';
        ctx.fillText('No data available', canvas.width / 2, canvas.height / 2);
        return;
    }

    const padding = 40;
    const chartWidth = canvas.width - padding * 2;
    const chartHeight = canvas.height - padding * 2;

    // Extract values safely
    const values = dailyScores.map(d => d[metric] || 0);
    const maxValue = Math.max(...values, 100);
    const minValue = Math.min(...values, 0);
    const range = maxValue - minValue || 1;

    // Draw axes
    ctx.strokeStyle = 'rgba(139, 157, 154, 0.2)';
    ctx.lineWidth = 1;

    // Y-axis
    ctx.beginPath();
    ctx.moveTo(padding, padding);
    ctx.lineTo(padding, canvas.height - padding);
    ctx.stroke();

    // X-axis
    ctx.beginPath();
    ctx.moveTo(padding, canvas.height - padding);
    ctx.lineTo(canvas.width - padding, canvas.height - padding);
    ctx.stroke();

    // Draw grid lines
    ctx.strokeStyle = 'rgba(139, 157, 154, 0.05)';
    for (let i = 0; i <= 4; i++) {
        const y = padding + (chartHeight / 4) * i;
        ctx.beginPath();
        ctx.moveTo(padding, y);
        ctx.lineTo(canvas.width - padding, y);
        ctx.stroke();
    }

    // Draw line
    ctx.strokeStyle = '#7B9E9D';
    ctx.lineWidth = 2.5;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    ctx.beginPath();
    values.forEach((value, index) => {
        const x = padding + (chartWidth / (values.length - 1 || 1)) * index;
        const y = canvas.height - padding - ((value - minValue) / range) * chartHeight;

        if (index === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });
    ctx.stroke();

    // Draw points
    values.forEach((value, index) => {
        const x = padding + (chartWidth / (values.length - 1 || 1)) * index;
        const y = canvas.height - padding - ((value - minValue) / range) * chartHeight;

        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fillStyle = '#7B9E9D';
        ctx.fill();
        ctx.strokeStyle = 'white';
        ctx.lineWidth = 2;
        ctx.stroke();
    });

    // Draw date labels
    ctx.fillStyle = '#B8C5C2';
    ctx.font = '11px Inter';
    ctx.textAlign = 'center';

    dailyScores.forEach((data, index) => {
        const x = padding + (chartWidth / (values.length - 1 || 1)) * index;
        const y = canvas.height - padding + 20;

        try {
            const date = new Date(data.date);
            const day = date.toLocaleDateString('en-US', { weekday: 'short' });
            ctx.fillText(day, x, y);
        } catch (e) {
            ctx.fillText('Day ' + (index + 1), x, y);
        }
    });
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

    // Check authentication
    const session = await checkAuth();
    if (!session) return;

    // Attach logout handler
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }

    // Load dashboard data
    await loadWeeklyDashboard();

    console.log('✅ Dashboard initialized');
});
