// ============================================
// Weekly Dashboard - Main Logic
// ============================================

let dashboardState = {
    weeklyData: null,
    loading: true,
    error: null,
    userPlan: 'free' // Default to free, will be updated from backend
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

    // Fetch user subscription plan from database
    try {
        const { data: subscription } = await window.supabase
            .from('subscriptions')
            .select('plan')
            .eq('user_id', session.user.id)
            .single();

        dashboardState.userPlan = subscription?.plan || 'free';
        console.log('📋 User plan:', dashboardState.userPlan);
    } catch (err) {
        console.log('No subscription found, defaulting to free plan');
        dashboardState.userPlan = 'free';
    }

    // Update plan badge in UI
    updatePlanBadge(dashboardState.userPlan);

    // Update UI with user info
    const avatarImg = document.getElementById('userAvatar');
    if (session.user.user_metadata?.avatar_url || session.user.user_metadata?.picture) {
        avatarImg.src = session.user.user_metadata.avatar_url || session.user.user_metadata.picture;
    }

    return session;
}

function updatePlanBadge(plan) {
    const planBadge = document.getElementById('planBadge');
    if (!planBadge) return;

    const isPro = plan === 'pro';
    planBadge.textContent = isPro ? 'Pro' : 'Free';
    planBadge.className = isPro ? 'badge-pro' : 'badge-free';
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

    // Render weekly alignment score
    renderWeeklyAlignmentScore(data);

    // Render charts with guards against undefined
    renderWeeklyRadarChart(data.weekly_averages || {});
    renderLineChart('confidenceLineChart', data.daily_scores || [], 'confidence');
    renderLineChart('resistanceLineChart', data.daily_scores || [], 'resistance');

    // Render trend badges
    renderTrendBadge('confidenceTrend', data.trend_data?.confidence);
    renderTrendBadge('resistanceTrend', data.trend_data?.resistance);

    // Render behavioral theme and pattern
    renderBehavioralTheme(data.weekly_insight || {});

    // Render experiment section
    renderExperiment(data.weekly_insight || {});

    // Render insight
    renderInsight(data.weekly_insight || {});

    // Show upgrade banner for free users if applicable
    renderUpgradeBanner();
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

function renderWeeklyAlignmentScore(data) {
    const alignmentScoreEl = document.getElementById('weeklyAlignmentScore');
    const alignmentCard = document.getElementById('alignmentOverviewCard');
    const lastUpdatedEl = document.getElementById('lastUpdatedText');

    if (!alignmentScoreEl || !alignmentCard) return;

    const weeklyInsight = data.weekly_insight || {};
    const alignmentScore = weeklyInsight.weekly_alignment_score;

    if (alignmentScore !== undefined && alignmentScore !== null) {
        alignmentScoreEl.textContent = alignmentScore;
        alignmentCard.style.display = 'block';

        // Show last updated time
        if (lastUpdatedEl) {
            const now = new Date();
            const timeStr = now.toLocaleTimeString('en-US', {
                hour: 'numeric',
                minute: '2-digit'
            });
            lastUpdatedEl.textContent = `Last updated: ${timeStr}`;
        }
    } else {
        alignmentCard.style.display = 'none';
    }
}

function renderBehavioralTheme(insight) {
    const themeCard = document.getElementById('behavioralThemeCard');
    const themeBadge = document.getElementById('behavioralThemeBadge');
    const themeSummary = document.getElementById('behavioralThemeSummary');
    const patternSummaryOverlay = document.getElementById('patternSummaryOverlay');
    const patternSummaryContent = document.getElementById('patternSummaryContent');

    if (!themeCard || !themeBadge || !themeSummary) return;

    const theme = insight.dominant_behavioral_theme;
    const patternSummary = insight.pattern_summary;
    const entryCount = dashboardState.weeklyData?.entry_count || 0;

    // Check if we have enough data
    if (entryCount < 3) {
        themeCard.style.display = 'none';
        return;
    }

    // Show card if we have theme
    if (theme) {
        // Format theme for display (convert snake_case to Title Case)
        const formattedTheme = theme
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');

        themeBadge.textContent = formattedTheme;
        themeCard.style.display = 'block';

        // Handle Pro gating for pattern summary
        const isPro = dashboardState.userPlan === 'pro';

        if (patternSummary && patternSummary.trim()) {
            themeSummary.textContent = patternSummary;

            // Show/hide overlay based on plan
            if (patternSummaryOverlay && patternSummaryContent) {
                if (isPro) {
                    // Pro user: show content, hide overlay
                    patternSummaryOverlay.style.display = 'none';
                    patternSummaryContent.classList.remove('blurred');
                } else {
                    // Free user: show overlay, blur content
                    patternSummaryOverlay.style.display = 'flex';
                    patternSummaryContent.classList.add('blurred');
                }
            }
        } else {
            // No pattern summary available
            themeSummary.textContent = 'Pattern analysis in progress...';
            if (patternSummaryOverlay) {
                patternSummaryOverlay.style.display = 'none';
            }
        }
    } else {
        themeCard.style.display = 'none';
    }
}

function renderExperiment(insight) {
    const experimentCard = document.getElementById('experimentCard');
    const experimentText = document.getElementById('experimentText');
    const experimentOverlay = document.getElementById('experimentOverlay');
    const experimentContent = document.getElementById('experimentContent');

    if (!experimentCard || !experimentText) return;

    const experiment = insight.pattern_experiment;
    const entryCount = dashboardState.weeklyData?.entry_count || 0;

    // Check if we have enough data
    if (entryCount < 3) {
        experimentCard.style.display = 'none';
        return;
    }

    // Show card if we have experiment data
    if (experiment && experiment.trim()) {
        experimentText.textContent = experiment;
        experimentCard.style.display = 'block';

        // Handle Pro gating
        const isPro = dashboardState.userPlan === 'pro';

        if (experimentOverlay && experimentContent) {
            if (isPro) {
                // Pro user: show content, hide overlay
                experimentOverlay.style.display = 'none';
                experimentContent.classList.remove('blurred');
            } else {
                // Free user: show overlay, blur content
                experimentOverlay.style.display = 'flex';
                experimentContent.classList.add('blurred');
            }
        }
    } else {
        experimentCard.style.display = 'none';
    }
}

function renderUpgradeBanner() {
    const upgradeBanner = document.getElementById('upgradeBanner');

    if (!upgradeBanner) return;

    // Hide the general upgrade banner (we use inline gating instead)
    upgradeBanner.style.display = 'none';
}

// ============================================
// Pro Upgrade Handler
// ============================================

function handleProUpgrade() {
    console.log('🚀 User clicked Upgrade to Pro');

    // Show plan selection modal
    const planModal = document.getElementById('planModal');
    if (planModal) {
        planModal.style.display = 'flex';
        document.body.style.overflow = 'hidden'; // Prevent background scroll
    }
}

function closePlanModal() {
    const planModal = document.getElementById('planModal');
    if (planModal) {
        planModal.style.display = 'none';
        document.body.style.overflow = ''; // Restore scroll
    }
}

async function proceedToCheckout(planType) {
    console.log('💳 Proceeding to checkout with plan:', planType);

    try {
        // Get current session for auth token
        const { data: { session }, error } = await window.supabase.auth.getSession();

        if (!session) {
            alert('Please log in to upgrade to Pro');
            window.location.href = '/login.html';
            return;
        }

        // Show loading state
        const selectButtons = document.querySelectorAll('.btn-select-plan');
        selectButtons.forEach(btn => {
            btn.disabled = true;
            btn.textContent = 'Creating checkout...';
        });

        // Use separate backend deployment
        const apiBaseUrl = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
            ? 'http://localhost:8000'
            : 'https://self-speak-production.up.railway.app/';  // UPDATE WITH YOUR BACKEND URL!

        // Create checkout session with backend
        const response = await fetch(`${apiBaseUrl}/billing/create-checkout`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${session.access_token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                plan_type: planType  // 'monthly' or 'annual'
            })
        });

        const data = await response.json();

        if (data.success && data.checkout_url) {
            // Redirect to Lemon Squeezy checkout
            console.log('✅ Redirecting to checkout:', data.checkout_url);
            window.location.href = data.checkout_url;
        } else {
            throw new Error(data.detail || 'Failed to create checkout session');
        }

    } catch (error) {
        console.error('❌ Checkout error:', error);

        // Reset buttons
        const selectButtons = document.querySelectorAll('.btn-select-plan');
        selectButtons.forEach(btn => {
            btn.disabled = false;
            const plan = btn.getAttribute('data-plan');
            btn.textContent = plan === 'monthly' ? 'Select Monthly' : 'Select Annual';
        });

        // Show user-friendly error
        alert('Unable to start checkout. Please try again or contact support.');
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
    const labels = ['Confidence', 'Abundance', 'Clarity', 'Gratitude', 'Resistance'];

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

        // Redraw axes AND labels
        ctx.strokeStyle = 'rgba(139, 157, 154, 0.12)';
        for (let i = 0; i < axes; i++) {
            const angle = (Math.PI * 2 * i) / axes - Math.PI / 2;
            const x = centerX + Math.cos(angle) * radius;
            const y = centerY + Math.sin(angle) * radius;

            ctx.beginPath();
            ctx.moveTo(centerX, centerY);
            ctx.lineTo(x, y);
            ctx.stroke();

            // IMPORTANT: Redraw labels in animation loop
            const labelDistance = radius + 40;
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

    // Modal event listeners
    const closePlanModalBtn = document.getElementById('closePlanModal');
    if (closePlanModalBtn) {
        closePlanModalBtn.addEventListener('click', closePlanModal);
    }

    // Close modal on outside click
    const planModal = document.getElementById('planModal');
    if (planModal) {
        planModal.addEventListener('click', (e) => {
            if (e.target === planModal) {
                closePlanModal();
            }
        });
    }

    // Close modal on ESC key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closePlanModal();
        }
    });

    // Plan selection buttons
    const selectPlanButtons = document.querySelectorAll('.btn-select-plan');
    selectPlanButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const planType = btn.getAttribute('data-plan');
            proceedToCheckout(planType);
        });
    });

    // Load dashboard data
    await loadWeeklyDashboard();

    console.log('✅ Dashboard initialized');
});
