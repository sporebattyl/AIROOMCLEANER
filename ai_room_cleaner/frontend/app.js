// Global handler for unhandled promise rejections
const handleUnhandledRejection = (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    // Optionally, you could show a user-facing error message here
};

window.addEventListener('unhandledrejection', handleUnhandledRejection);

import { initializeUIElements } from './modules/ui.js';
import {
    setCurrentTheme,
    elements,
    storage
} from './modules/state.js';
import {
    setupEventListeners,
    loadHistory,
    debouncedHandleAnalyzeRoom,
    handleToggleTheme,
    handleClearHistory,
    handleToggleTask
} from './modules/eventHandlers.js';

const setupUI = async () => {
    initializeUIElements();
    elements.analyzeBtn = document.getElementById('analyze-btn');
    elements.themeToggleBtn = document.getElementById('theme-toggle-btn');
    elements.clearHistoryBtn = document.getElementById('clear-history-btn');
    elements.messesList = document.getElementById('messes-list');

    // Disable clear history button as there is no backend endpoint for it yet.
    elements.clearHistoryBtn.disabled = true;
    elements.clearHistoryBtn.title = "This feature is not available yet.";

    const savedTheme = storage.get('theme', 'light');
    setCurrentTheme(savedTheme);
    document.documentElement.setAttribute('data-theme', savedTheme);

    await loadHistory();
};

const initializeApp = async () => {
    await setupUI();
    setupEventListeners();
};

document.addEventListener('DOMContentLoaded', initializeApp);

export const cleanup = () => {
    // Remove all event listeners to prevent memory leaks
    window.removeEventListener('unhandledrejection', handleUnhandledRejection);
    document.removeEventListener('DOMContentLoaded', initializeApp);
    window.removeEventListener('beforeunload', cleanup);

    if (elements.analyzeBtn) {
        elements.analyzeBtn.removeEventListener('click', debouncedHandleAnalyzeRoom);
    }
    if (elements.themeToggleBtn) {
        elements.themeToggleBtn.removeEventListener('click', handleToggleTheme);
    }
    if (elements.clearHistoryBtn) {
        elements.clearHistoryBtn.removeEventListener('click', handleClearHistory);
    }
    if (elements.messesList) {
        elements.messesList.removeEventListener('click', handleToggleTask);
    }
};

// Call cleanup when page unloads
window.addEventListener('beforeunload', cleanup);