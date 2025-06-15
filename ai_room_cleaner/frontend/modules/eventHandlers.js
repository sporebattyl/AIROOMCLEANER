import { analyzeRoom, getHistory as fetchHistoryFromServer, NetworkError, ServerError } from './api.js';
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
    getHistory as getHistoryFromState,
    setHistory,
    getCurrentTheme,
    setCurrentTheme,
    getUIElements,
    storage
} from './state.js';
import logger from './logger.js';

// Create a single AbortController for all event listeners
const controller = new AbortController();

// Fetches and displays the analysis history from the server.
export const loadHistory = async () => {
    showHistoryLoading();
    try {
        logger.info('Loading history...');
        const historyData = await fetchHistoryFromServer();
        setHistory(historyData);
        updateHistoryList(getHistoryFromState());
        logger.info('History loaded successfully.');
    } catch (error) {
        hideHistoryLoading();
        logger.error({ error }, 'Error loading history');
        if (error instanceof ServerError) {
            showError(`Server error: ${error.message}`);
        } else if (error instanceof NetworkError) {
            showError(`Network error: ${error.message}`);
        } else {
            showError("An unexpected error occurred while loading history.");
        }
    } finally {
        hideHistoryLoading();
    }
};

// Handles the room analysis process, including UI updates and error handling.
export const handleAnalyzeRoom = async () => {
    const { fileInput, messesList } = getUIElements();
    const imageFile = fileInput.files[0];

    if (!imageFile) {
        showError('Please select an image to analyze.');
        return;
    }

    showLoading();
    clearError();

    try {
        logger.info({ filename: imageFile.name, size: imageFile.size }, 'Analyzing room...');
        const result = await analyzeRoom(imageFile);
        logger.info({ result }, 'Analysis successful');

        updateMessesList(result.tasks, messesList);
        updateCleanlinessScore(result.cleanliness_score || 0);
        showResults();
        
        // Reload history from server to ensure consistency
        await loadHistory();
    } catch (error) {
        logger.error({ error }, 'Analysis error');
        if (error instanceof ServerError) {
            showError(`Server error: ${error.message}`, handleAnalyzeRoom);
        } else if (error instanceof NetworkError) {
            showError(`Network error: ${error.message}`, handleAnalyzeRoom);
        } else {
            showError('An unexpected error occurred during analysis.', handleAnalyzeRoom);
        }
    } finally {
        hideLoading();
    }
};

export const handleClearHistory = () => {
    // This function is currently disabled.
    // To re-enable, a backend endpoint to clear the history is needed.
    logger.warn("Clear history is disabled.");
};

// Toggles the theme between light and dark mode.
export const handleToggleTheme = () => {
    const oldTheme = getCurrentTheme();
    const newTheme = oldTheme === 'dark' ? 'light' : 'dark';
    setCurrentTheme(newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
    storage.set('theme', newTheme);
    logger.info({ from: oldTheme, to: newTheme }, 'Theme toggled');
};

export const handleToggleTask = (e) => {
    if (e.target.tagName === 'LI') {
        e.target.classList.toggle('completed');
    }
};

const debounce = (func, delay) => {
    let timeoutId;
    return function(...args) {
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
    const { signal } = controller;
    const elements = getUIElements();
    elements.analyzeBtn.addEventListener('click', debouncedHandleAnalyzeRoom, { signal });
    elements.themeToggleBtn.addEventListener('click', handleToggleTheme, { signal });
    elements.clearHistoryBtn.addEventListener('click', handleClearHistory, { signal });
    elements.messesList.addEventListener('click', handleToggleTask, { signal });
};

// Removes all event listeners.
export const cleanupEventListeners = () => {
    controller.abort();
};