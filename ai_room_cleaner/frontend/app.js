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

document.addEventListener('DOMContentLoaded', () => {
    const analyzeBtn = document.getElementById('analyze-btn');
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const clearHistoryBtn = document.getElementById('clear-history-btn');
    const messesList = document.getElementById('messes-list');

    let history = storage.get('analysisHistory', []);
    let currentTheme = storage.get('theme', 'light');
    document.documentElement.setAttribute('data-theme', currentTheme);
    
    updateHistoryList(history);

    const handleAnalyzeRoom = async () => {
        showLoading();
        clearError();

        try {
            const result = await analyzeRoom();
            console.log('Analysis result:', result); // Debug log
            
            const analysis = {
                id: Date.now(),
                date: new Date().toLocaleString(),
                score: result.cleanliness_score || 50, // Fallback score
                messes: result.tasks || [],
            };
            
            history.unshift(analysis);
            if (history.length > 10) {
                history.pop();
            }
            
            storage.set('analysisHistory', history);

            if (result.tasks.length === 0) {
                showEmptyState();
            } else {
                updateMessesList(result.tasks);
            }
            
            updateCleanlinessScore(result.cleanliness_score || 50);
            updateHistoryList(history);
            showResults();
        } catch (error) {
            console.error('Analysis error:', error);
            showError(`Failed to analyze room: ${error.message}`);
        } finally {
            hideLoading();
        }
    };

    const handleClearHistory = () => {
        history = [];
        storage.remove('analysisHistory');
        clearHistory();
    };

    const handleToggleTheme = () => {
        currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', currentTheme);
        storage.set('theme', currentTheme);
    };

    const handleToggleTask = (e) => {
        if (e.target.tagName === 'LI') {
            e.target.classList.toggle('completed');
        }
    };

    analyzeBtn.addEventListener('click', handleAnalyzeRoom);
    themeToggleBtn.addEventListener('click', handleToggleTheme);
    clearHistoryBtn.addEventListener('click', handleClearHistory);
    messesList.addEventListener('click', handleToggleTask);
});