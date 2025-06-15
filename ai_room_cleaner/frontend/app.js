// Global handler for unhandled promise rejections
const handleUnhandledRejection = (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    // Optionally, you could show a user-facing error message here
};

window.addEventListener('unhandledrejection', handleUnhandledRejection);

import { initializeUIElements as initializeUIStateElements } from './modules/state.js';
import {
    setCurrentTheme,
    getUIElements,
    storage
} from './modules/state.js';
import {
    setupEventListeners,
    loadHistory,
    cleanupEventListeners
} from './modules/eventHandlers.js';

const setupUI = async () => {
    initializeUIStateElements();
    const elements = getUIElements();

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

const cleanup = () => {
    window.removeEventListener('unhandledrejection', handleUnhandledRejection);
    document.removeEventListener('DOMContentLoaded', initializeApp);
    cleanupEventListeners();
};

document.addEventListener('DOMContentLoaded', initializeApp);
window.addEventListener('beforeunload', cleanup);