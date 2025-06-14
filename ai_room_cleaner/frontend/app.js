// Global handler for unhandled promise rejections
window.addEventListener('unhandledrejection', event => {
    console.error('Unhandled promise rejection:', event.reason);
    // Optionally, you could show a user-facing error message here
});
import { analyzeRoom, getHistory } from './modules/api.js';
import { 
    updateMessesList, 
    updateCleanlinessScore, 
    showLoading, 
    hideLoading, 
    showError,
    clearError,
    toggleTheme,
    updateHistoryList,
    clearHistory,
    showResults,
    showEmptyState
} from './modules/ui.js';

const storage = {
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

const state = {
    history: [],
    currentTheme: 'light',
};

const elements = {};

const setupUI = async () => {
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
    try {
        const history = await getHistory();
        state.history = history;
        updateHistoryList(state.history);
    } catch (error) {
        showError("Could not load analysis history.");
    }
};

const handleAnalyzeRoom = async () => {
    showLoading();
    clearError();

    try {
        const result = await analyzeRoom();
        console.log('Analysis result:', result);

        // Prepend new result to history for immediate UI update
        state.history.unshift(result);
        if (state.history.length > 50) {
            state.history.pop();
        }

        if (result.tasks.length === 0) {
            showEmptyState();
        } else {
            updateMessesList(result.tasks);
        }

        updateCleanlinessScore(result.cleanliness_score || 0);
        updateHistoryList(state.history);
        showResults();
        hideLoading();
    } catch (error) {
        console.error('Analysis error:', error);
        hideLoading();
        showError(error, handleAnalyzeRoom);
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

const setupEventListeners = () => {
    elements.analyzeBtn.addEventListener('click', handleAnalyzeRoom);
    elements.themeToggleBtn.addEventListener('click', handleToggleTheme);
    elements.clearHistoryBtn.addEventListener('click', handleClearHistory);
    elements.messesList.addEventListener('click', handleToggleTask);
};

const init = () => {
    setupUI();
    setupEventListeners();
};

document.addEventListener('DOMContentLoaded', init);