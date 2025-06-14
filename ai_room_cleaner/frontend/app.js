// Global handler for unhandled promise rejections
window.addEventListener('unhandledrejection', event => {
    console.error('Unhandled promise rejection:', event.reason);
    // Optionally, you could show a user-facing error message here
});

import { initializeUIElements } from './modules/ui.js';
import { state, elements, storage } from './modules/state.js';
import { setupEventListeners, loadHistory, handleAnalyzeRoom } from './modules/eventHandlers.js';

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