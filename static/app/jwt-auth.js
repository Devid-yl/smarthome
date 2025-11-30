/**
 * JWT Authentication utilities for SmartHome frontend
 */

// Token storage key
const TOKEN_KEY = 'smarthome_jwt_token';
const USER_KEY = 'smarthome_user';

/**
 * Store JWT token and user info in localStorage
 */
function setAuthToken(token, user) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
}

/**
 * Get stored JWT token
 */
function getAuthToken() {
    return localStorage.getItem(TOKEN_KEY);
}

/**
 * Get stored user info
 */
function getStoredUser() {
    const userStr = localStorage.getItem(USER_KEY);
    return userStr ? JSON.parse(userStr) : null;
}

/**
 * Clear authentication (logout)
 */
function clearAuth() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
}

/**
 * Check if user is authenticated
 */
function isAuthenticated() {
    return !!getAuthToken();
}

/**
 * Add Authorization header to fetch options
 */
function addAuthHeader(options = {}) {
    const token = getAuthToken();
    if (token) {
        options.headers = options.headers || {};
        options.headers['Authorization'] = `Bearer ${token}`;
    }
    return options;
}

/**
 * Fetch wrapper with automatic JWT authentication
 */
async function authFetch(url, options = {}) {
    const authOptions = addAuthHeader(options);
    const response = await fetch(url, authOptions);
    
    // If 401, token may be expired - redirect to login
    if (response.status === 401) {
        clearAuth();
        window.location.href = '/app/login.html';
        return null;
    }
    
    return response;
}

/**
 * Login with JWT
 */
async function loginWithJWT(email, password) {
    const response = await fetch('/api/auth/jwt/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password })
    });
    
    const data = await response.json();
    
    if (response.ok) {
        setAuthToken(data.token, data.user);
        return { success: true, user: data.user };
    } else {
        return { success: false, error: data.error };
    }
}

/**
 * Register with JWT
 */
async function registerWithJWT(username, email, password, phone = '') {
    const response = await fetch('/api/auth/jwt/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, email, password, phone })
    });
    
    const data = await response.json();
    
    if (response.ok) {
        setAuthToken(data.token, data.user);
        return { success: true, user: data.user };
    } else {
        return { success: false, error: data.error };
    }
}

/**
 * Logout
 */
function logout() {
    clearAuth();
    window.location.href = '/app/login.html';
}

/**
 * Redirect to login if not authenticated
 */
function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = '/app/login.html';
    }
}
