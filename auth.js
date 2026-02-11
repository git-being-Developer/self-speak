// Supabase client is initialized in supabase-client.js

(function() {
    'use strict';
    let supabase;

// UI Elements
const googleSignInBtn = document.getElementById('googleSignIn');
const loadingState = document.getElementById('loadingState');
const errorMessage = document.getElementById('errorMessage');

// Show/Hide UI States
function showLoading() {
    googleSignInBtn.style.display = 'none';
    loadingState.style.display = 'block';
    errorMessage.style.display = 'none';
}

function hideLoading() {
    googleSignInBtn.style.display = 'flex';
    loadingState.style.display = 'none';
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
    hideLoading();
}

// Google Sign In
async function signInWithGoogle() {
    showLoading();

    try {
        const { data, error } = await supabase.auth.signInWithOAuth({
            provider: 'google',
            options: {
                redirectTo: `${window.location.origin}/index.html`,
                queryParams: {
                    access_type: 'offline',
                    prompt: 'consent',
                }
            }
        });

        if (error) {
            throw error;
        }

        // OAuth will redirect, so we don't need to do anything here
        console.log('Redirecting to Google...');

    } catch (error) {
        console.error('Sign in error:', error);
        showError(error.message || 'Failed to sign in with Google');
    }
}

// Handle OAuth Callback
async function handleOAuthCallback() {
    const hashParams = new URLSearchParams(window.location.hash.substring(1));
    const accessToken = hashParams.get('access_token');

    if (accessToken) {
        showLoading();

        try {
            // Get the current session
            const { data: { session }, error } = await supabase.auth.getSession();

            if (error) {
                throw error;
            }

            if (session) {
                console.log('✅ Authentication successful');
                console.log('User:', session.user);
                console.log('Access Token:', session.access_token);

                // Store session info securely
                storeSession(session);

                // Redirect to main app
                window.location.href = '/index.html';
            }

        } catch (error) {
            console.error('Session error:', error);
            showError('Authentication failed. Please try again.');

            // Clear hash from URL
            window.history.replaceState(null, null, window.location.pathname);
        }
    }
}

// Store session securely
function storeSession(session) {
    // Store in localStorage (in production, consider more secure options)
    localStorage.setItem('selfspeak_session', JSON.stringify({
        access_token: session.access_token,
        refresh_token: session.refresh_token,
        expires_at: session.expires_at,
        user_id: session.user.id
    }));

    console.log('✅ Session stored');
}

// Check if user is already logged in
async function checkExistingSession() {
    const { data: { session } } = await supabase.auth.getSession();

    if (session) {
        console.log('✅ Already logged in, redirecting...');
        window.location.href = '/index.html';
    }
}

// Event Listeners
googleSignInBtn.addEventListener('click', signInWithGoogle);

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    // Initialize supabase client reference
    supabase = window.supabaseClient;

    if (!supabase) {
        console.error('❌ Supabase client not initialized!');
        showError('Failed to initialize authentication. Please refresh the page.');
        return;
    }
    console.log('✅ Supabase client loaded:', typeof supabase);
    console.log('Auth available:', typeof supabase.auth);

    // Listen for auth state changes
    supabase.auth.onAuthStateChange((event, session) => {
        console.log('Auth state changed:', event);

        if (event === 'SIGNED_IN') {
            console.log('✅ User signed in:', session.user);
            storeSession(session);
            window.location.href = '/index.html';
        } else if (event === 'SIGNED_OUT') {
            console.log('⚠️ User signed out');
            localStorage.removeItem('selfspeak_session');
        } else if (event === 'TOKEN_REFRESHED') {
            console.log('🔄 Token refreshed');
            storeSession(session);
        }
    });

    // Check for existing session
    await checkExistingSession();

    // Handle OAuth callback if present
    if (window.location.hash.includes('access_token')) {
        await handleOAuthCallback();
    }
})
})();

