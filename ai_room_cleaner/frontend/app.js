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

document.addEventListener('DOMContentLoaded', () => {
    const analyzeBtn = document.getElementById('analyze-btn');
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const clearHistoryBtn = document.getElementById('clear-history-btn');
    const messesList = document.getElementById('messes-list');

    // Use in-memory storage instead of localStorage for better compatibility
    let history = [];
    let currentTheme = 'light';
    
    // Try to load from localStorage if available, but don't fail if not
    try {
        const savedHistory = localStorage.getItem('analysisHistory');
        if (savedHistory) {
            history = JSON.parse(savedHistory);
        }
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            currentTheme = savedTheme;
            document.documentElement.setAttribute('data-theme', currentTheme);
        }
    } catch (error) {
        console.warn('localStorage not available, using in-memory storage');
    }
    
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
            
            // Try to save to localStorage if available
            try {
                localStorage.setItem('analysisHistory', JSON.stringify(history));
            } catch (error) {
                console.warn('Could not save to localStorage:', error);
            }

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
        try {
            localStorage.removeItem('analysisHistory');
        } catch (error) {
            console.warn('Could not clear localStorage:', error);
        }
        clearHistory();
    };

    const handleToggleTheme = () => {
        currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', currentTheme);
        try {
            localStorage.setItem('theme', currentTheme);
        } catch (error) {
            console.warn('Could not save theme to localStorage:', error);
        }
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