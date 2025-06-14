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
import {
    getHistory,
    setHistory,
    getCurrentTheme,
    setCurrentTheme,
    elements,
    storage
} from './state.js';

// Fetches and displays the analysis history from the server.
export const loadHistory = async () => {
    showHistoryLoading();
    try {
        const historyData = await getHistory();
        setHistory(historyData);
        updateHistoryList(getHistory());
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

// Handles the room analysis process, including UI updates and error handling.
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

// Toggles the theme between light and dark mode.
export const handleToggleTheme = () => {
    const newTheme = getCurrentTheme() === 'dark' ? 'light' : 'dark';
    setCurrentTheme(newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
    storage.set('theme', newTheme);
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

// Debounced version of handleAnalyzeRoom to be used for event listeners
export const debouncedHandleAnalyzeRoom = debounce(handleAnalyzeRoom, 500);

// Sets up all the event listeners for the application.
export const setupEventListeners = () => {
    elements.analyzeBtn.addEventListener('click', debouncedHandleAnalyzeRoom);
    elements.themeToggleBtn.addEventListener('click', handleToggleTheme);
    elements.clearHistoryBtn.addEventListener('click', handleClearHistory);
    elements.messesList.addEventListener('click', handleToggleTask);
};