// supabase-client.js
(function() {
    'use strict';

    // Configuration
    const SUPABASE_URL = 'https://qlmxusbpbjfcyihjqmow.supabase.co';
    const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFsbXh1c2JwYmpmY3lpaGpxbW93Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA3NzU2NzYsImV4cCI6MjA4NjM1MTY3Nn0.GTDfOfaRap2i-EkbvYRe2Luo0qhtSGlnDpoiazRItTU';

    if (typeof window.supabase === 'undefined') {
        console.error('❌ Supabase SDK not loaded! Make sure the CDN script is included before this file.');
        return;
    }

    try {
        const supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
        window.supabaseClient = supabaseClient;
        window.supabase = supabaseClient;
        console.log('✅ Supabase client initialized successfully');
        console.log('Client available as: window.supabaseClient and window.supabase');
    } catch (error) {
        console.error('❌ Failed to initialize Supabase client:', error);
    }
})();
