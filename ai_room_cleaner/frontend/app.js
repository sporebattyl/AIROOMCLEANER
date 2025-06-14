// Global handler for unhandled promise rejections
window.addEventListener('unhandledrejection', event => {
    console.error('Unhandled promise rejection:', event.reason);
    // Optionally, you could show a user-facing error message here
});
import { analyzeRoom, getHistory, NetworkError, ServerError } from './modules/api.js';
import {
    updateMessesList,
    updateCleanlinessScore,
    showLoading, 
    hideLoading, 
    showError,
    clearError,
    updateHistoryList,
    clearHistory,
    showResults,
    showEmptyState,
    showHistoryLoading,
    hideHistoryLoading,
    initializeUIElements
} from './modules/ui.js';

function isStorageAvailable(type) {
    let storage;
    try {
        storage = window[type];
        const x = '__storage_test__';
        storage.setItem(x, x);
        storage.removeItem(x);
        return true;
    } catch (e) {
        return e instanceof DOMException && (
            // everything except Firefox
            e.code === 22 ||
            // Firefox
            e.code === 1014 ||
            // test name field too, because code might not be present
            // everything except Firefox
            e.name === 'QuotaExceededError' ||
            // Firefox
            e.name === 'NS_ERROR_DOM_QUOTA_REACHED') &&
            // acknowledge QuotaExceededError only if there's something already stored
            (storage && storage.length !== 0);
    }
}

let storage;
if (isStorageAvailable('localStorage')) {
    storage = {
        get: (key, defaultValue = null) => {
            try {
                const value = localStorage.getItem(key);
                return value ? JSON.parse(value) : defaultValue;
            } catch (error) {
                console.warn(`Could not read '${key}' from localStorage:`, error);
                return defaultValue;
            }
        },
        set: (key, value) => {
            try {
                localStorage.setItem(key, JSON.stringify(value));
                return true;
            } catch (error) {
                console.warn(`Could not write '${key}' to localStorage:`, error);
                return false;
            }
        },
        remove: (key) => {
            try {
                localStorage.removeItem(key);
                return true;
            } catch (error) {
                console.warn(`Could not remove '${key}' from localStorage:`, error);
                return false;
            }
        }
    };
} else {
    console.warn("localStorage is not available. Falling back to in-memory storage.");
    const inMemoryStore = {};
    storage = {
        get: (key, defaultValue = null) => {
            return inMemoryStore.hasOwnProperty(key) ? inMemoryStore[key] : defaultValue;
        },
        set: (key, value) => {
            try {
                inMemoryStore[key] = JSON.parse(JSON.stringify(value)); // Deep copy
                return true;
            } catch (error) {
                console.warn(`Could not store '${key}' in memory:`, error);
                return false;
            }
        },
        remove: (key) => {
            if (inMemoryStore.hasOwnProperty(key)) {
                delete inMemoryStore[key];
            }
            return true;
        }
    };
}

const CONFIG = {
    MAX_HISTORY_ITEMS: 50,
    DEBOUNCE_DELAY: 500,
    ERROR_DISPLAY_DURATION: 5000,
    RETRY_ATTEMPTS: 3
};

const ERROR_MESSAGES = {
    NETWORK_ERROR: 'Unable to connect to server. Please check your internet connection.',
    SERVER_ERROR: 'Server error occurred. Please try again later.',
    ANALYSIS_FAILED: 'Room analysis failed. Please try again.',
    HISTORY_LOAD_FAILED: 'Could not load analysis history.',
};

const state = {
    history: [],
    currentTheme: 'light',
};

const elements = {};

const setupUI = async () => {
    initializeUIElements();
    elements.analyzeBtn = document.getElementById('analyze-btn');
    elements.themeToggleBtn = document.getElementById('theme-toggle-btn');
    elements.clearHistoryBtn = document.getElementById('clear-history-btn');
    elements.messesList = document.getElementById('messes-list');

    // Disable clear history button as there is no backend endpoint for it yet.
    elements.clearHistoryBtn.disabled = true;
    elements.clearHistoryBtn.title = "This feature is not available yet.";


    state.currentTheme = storage.get('theme', 'light');
    document.documentElement.setAttribute('data-theme', state.currentTheme);

    await loadHistory();
};

const loadHistory = async () => {
    showHistoryLoading();
    try {
        const history = await getHistory();
        state.history = history;
        updateHistoryList(state.history);
    } catch (error) {
        hideHistoryLoading();
        if (error instanceof ServerError) {
            showError(`Server error: ${error.message}`);
        } else if (error instanceof NetworkError) {
            showError(`Network error: ${error.message}`);
        } else {
            showError("An unexpected error occurred while loading history.");
        }
    }
};

const handleAnalyzeRoom = async () => {
    showLoading();
    clearError();

    try {
        const result = await analyzeRoom();
        console.log('Analysis result:', result);

        updateMessesList(result.tasks);
        updateCleanlinessScore(result.cleanliness_score || 0);
        showResults();
        
        // Reload history from server to ensure consistency
        await loadHistory();
        hideLoading();
    } catch (error) {
        console.error('Analysis error:', error);
        hideLoading();
        if (error instanceof ServerError) {
            showError(`Server error: ${error.message}`, handleAnalyzeRoom);
        } else if (error instanceof NetworkError) {
            showError(`Network error: ${error.message}`, handleAnalyzeRoom);
        } else {
            showError('An unexpected error occurred during analysis.', handleAnalyzeRoom);
        }
    }
};

const handleClearHistory = () => {
    // This function is currently disabled.
    // To re-enable, a backend endpoint to clear the history is needed.
    console.warn("Clear history is disabled.");
};

const handleToggleTheme = () => {
    state.currentTheme = state.currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', state.currentTheme);
    storage.set('theme', state.currentTheme);
};

const handleToggleTask = (e) => {
    if (e.target.tagName === 'LI') {
        e.target.classList.toggle('completed');
    }
};

const debounce = (func, delay) => {
    let timeoutId;
    return (...args) => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => {
            func.apply(this, args);
        }, delay);
    };
};

const setupEventListeners = () => {
    elements.analyzeBtn.addEventListener('click', debounce(handleAnalyzeRoom, 500));
    elements.themeToggleBtn.addEventListener('click', handleToggleTheme);
    elements.clearHistoryBtn.addEventListener('click', handleClearHistory);
    elements.messesList.addEventListener('click', handleToggleTask);
};

const initializeApp = async () => {
    await setupUI();
    setupEventListeners();
};

document.addEventListener('DOMContentLoaded', initializeApp);

export const cleanup = () => {
    if (elements.analyzeBtn) {
        elements.analyzeBtn.removeEventListener('click', handleAnalyzeRoom);
    }
    // ... remove other listeners
};

// Call cleanup when page unloads
window.addEventListener('beforeunload', cleanup);