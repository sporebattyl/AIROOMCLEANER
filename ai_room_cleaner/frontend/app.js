// Global handler for unhandled promise rejections
window.addEventListener('unhandledrejection', event => {
    console.error('Unhandled promise rejection:', event.reason);
    // Optionally, you could show a user-facing error message here
});
import { analyzeRoom } from './modules/api.js';
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
        } catch {
            return defaultValue;
        }
    },
    set: (key, value) => {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch {
            return false;
        }
    },
    remove: (key) => {
        try {
            localStorage.removeItem(key);
            return true;
        } catch {
            return false;
        }
    }
};

const state = {
    history: [],
    currentTheme: 'light',
};

const elements = {};

const setupUI = () => {
    elements.analyzeBtn = document.getElementById('analyze-btn');
    elements.themeToggleBtn = document.getElementById('theme-toggle-btn');
    elements.clearHistoryBtn = document.getElementById('clear-history-btn');
    elements.messesList = document.getElementById('messes-list');

    state.history = storage.get('analysisHistory', []);
    state.currentTheme = storage.get('theme', 'light');

    document.documentElement.setAttribute('data-theme', state.currentTheme);
    updateHistoryList(state.history);
};

const handleAnalyzeRoom = async () => {
    showLoading();
    clearError();

    try {
        const result = await analyzeRoom();
        console.log('Analysis result:', result);

        const analysis = {
            id: Date.now(),
            date: new Date().toLocaleString(),
            score: result.cleanliness_score || 50,
            messes: result.tasks || [],
        };

        state.history.unshift(analysis);
        if (state.history.length > 10) {
            state.history.pop();
        }

        storage.set('analysisHistory', state.history);

        if (result.tasks.length === 0) {
            showEmptyState();
        } else {
            updateMessesList(result.tasks);
        }

        updateCleanlinessScore(result.cleanliness_score || 50);
        updateHistoryList(state.history);
        showResults();
    } catch (error) {
        console.error('Analysis error:', error);
        showError(`Failed to analyze room: ${error.message}`);
    } finally {
        hideLoading();
    }
};

const handleClearHistory = () => {
    state.history = [];
    storage.remove('analysisHistory');
    clearHistory();
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