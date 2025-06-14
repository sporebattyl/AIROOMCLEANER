import { analyzeRoom, getHistory, NetworkError, ServerError } from './api.js';
import {
    updateMessesList,
    updateCleanlinessScore,
    showLoading,
    hideLoading,
    showError,
    clearError,
    updateHistoryList,
    showResults,
    showHistoryLoading,
    hideHistoryLoading,
} from './ui.js';
import { state, elements, storage } from './state.js';

export const loadHistory = async () => {
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

export const handleAnalyzeRoom = async () => {
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

export const handleClearHistory = () => {
    // This function is currently disabled.
    // To re-enable, a backend endpoint to clear the history is needed.
    console.warn("Clear history is disabled.");
};

export const handleToggleTheme = () => {
    state.currentTheme = state.currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', state.currentTheme);
    storage.set('theme', state.currentTheme);
};

export const handleToggleTask = (e) => {
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

export const setupEventListeners = () => {
    elements.analyzeBtn.addEventListener('click', debounce(handleAnalyzeRoom, 500));
    elements.themeToggleBtn.addEventListener('click', handleToggleTheme);
    elements.clearHistoryBtn.addEventListener('click', handleClearHistory);
    elements.messesList.addEventListener('click', handleToggleTask);
};