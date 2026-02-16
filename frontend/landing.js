// ============================================
// Landing Page - Selfspeak
// ============================================

// ============================================
// Authentication Check
// ============================================

async function checkExistingSession() {
    try {
        const { data: { session }, error } = await window.supabase.auth.getSession();

        if (session) {
            // User is already logged in, redirect to journal
            console.log('✅ Existing session found, redirecting to journal...');
            window.location.href = '/index.html';
        }
    } catch (error) {
        console.log('No existing session');
    }
}

// ============================================
// Google OAuth Login
// ============================================

async function handleGoogleLogin() {
    try {
        const { data, error } = await window.supabase.auth.signInWithOAuth({
            provider: 'google',
            options: {
                redirectTo: `${window.location.origin}/index.html`
            }
        });

        if (error) {
            console.error('Login error:', error);
            showNotification('Unable to sign in. Please try again.', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showNotification('Unable to sign in. Please try again.', 'error');
    }
}

// ============================================
// Platform Activity Metrics Animation
// ============================================

function animateCounters() {
    const metricNumbers = document.querySelectorAll('.metric-number');

    metricNumbers.forEach(element => {
        const targetValue = parseInt(element.getAttribute('data-value'));
        const duration = 2000; // 2 seconds
        const increment = targetValue / (duration / 16); // 60fps
        let currentValue = 0;

        const updateCounter = () => {
            currentValue += increment;
            if (currentValue < targetValue) {
                element.textContent = Math.floor(currentValue) + '+';
                requestAnimationFrame(updateCounter);
            } else {
                element.textContent = targetValue + '+';
            }
        };

        // Start animation when element is visible
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && currentValue === 0) {
                    updateCounter();
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });

        observer.observe(element);
    });
}

// ============================================
// Hero Radar Chart Animation
// ============================================

function renderHeroRadarChart() {
    const canvas = document.getElementById('heroRadarChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = 150;
    const axes = 5;
    const labels = ['Confidence', 'Abundance', 'Clarity', 'Gratitude', 'Resistance'];

    // Sample data for demo
    const dataPoints = [75, 68, 82, 88, 35];

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
        const labelDistance = radius + 30;
        const labelX = centerX + Math.cos(angle) * labelDistance;
        const labelY = centerY + Math.sin(angle) * labelDistance;

        ctx.fillStyle = '#5A7B7D';
        ctx.font = '13px Inter';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(labels[i], labelX, labelY);
    }

    // Animate data polygon
    animateHeroRadarData(ctx, centerX, centerY, radius, axes, dataPoints);
}

function animateHeroRadarData(ctx, centerX, centerY, radius, axes, scores) {
    let progress = 0;
    const duration = 1500;
    const startTime = Date.now();
    const labels = ['Confidence', 'Abundance', 'Clarity', 'Gratitude', 'Resistance'];

    function animate() {
        const elapsed = Date.now() - startTime;
        progress = Math.min(elapsed / duration, 1);
        const easeProgress = 1 - Math.pow(1 - progress, 3);

        // Clear canvas
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
            const labelDistance = radius + 30;
            const labelX = centerX + Math.cos(angle) * labelDistance;
            const labelY = centerY + Math.sin(angle) * labelDistance;

            ctx.fillStyle = '#5A7B7D';
            ctx.font = '13px Inter';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(labels[i], labelX, labelY);
        }

        // Draw data polygon
        ctx.beginPath();
        for (let i = 0; i < axes; i++) {
            const angle = (Math.PI * 2 * i) / axes - Math.PI / 2;
            const value = (scores[i] / 100) * radius * easeProgress;
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
            const value = (scores[i] / 100) * radius * easeProgress;
            const x = centerX + Math.cos(angle) * value;
            const y = centerY + Math.sin(angle) * value;

            ctx.beginPath();
            ctx.arc(x, y, 4, 0, Math.PI * 2);
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
// Step Radar Chart
// ============================================

function renderStepRadarChart() {
    const canvas = document.getElementById('stepRadarChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = 70;
    const axes = 5;
    const dataPoints = [70, 60, 75, 80, 40];

    // Draw background
    ctx.strokeStyle = 'rgba(139, 157, 154, 0.08)';
    ctx.lineWidth = 1;
    for (let i = 1; i <= 4; i++) {
        ctx.beginPath();
        ctx.arc(centerX, centerY, (radius / 4) * i, 0, Math.PI * 2);
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
    }

    // Draw data polygon
    ctx.beginPath();
    for (let i = 0; i < axes; i++) {
        const angle = (Math.PI * 2 * i) / axes - Math.PI / 2;
        const value = (dataPoints[i] / 100) * radius;
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
    ctx.lineWidth = 2;
    ctx.stroke();
}

// ============================================
// Scroll Animations
// ============================================

function handleScrollAnimations() {
    const elements = document.querySelectorAll('.fade-in-scroll');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    });

    elements.forEach(el => observer.observe(el));
}

// ============================================
// Notifications
// ============================================

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
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
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// ============================================
// Event Listeners
// ============================================

document.addEventListener('DOMContentLoaded', async function() {
    // Check if Supabase is loaded
    if (!window.supabase) {
        console.error('❌ Supabase client not initialized');
        return;
    }

    // Check for existing session
    await checkExistingSession();

    // Render charts
    setTimeout(() => {
        renderHeroRadarChart();
        renderStepRadarChart();
    }, 100);

    // Setup scroll animations
    handleScrollAnimations();

    // Animate platform activity counters
    animateCounters();

    // Attach login handlers to all CTA buttons
    const loginButtons = [
        document.getElementById('loginBtn'),
        document.getElementById('heroCTA'),
        document.getElementById('heroGoogle'),
        document.getElementById('finalCTA')
    ];

    loginButtons.forEach(btn => {
        if (btn) {
            btn.addEventListener('click', handleGoogleLogin);
        }
    });

    console.log('✅ Landing page initialized');
});
