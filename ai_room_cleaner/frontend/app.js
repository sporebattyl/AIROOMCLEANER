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

    let history = JSON.parse(localStorage.getItem('analysisHistory')) || [];
    updateHistoryList(history);

    const handleAnalyzeRoom = async () => {
        showLoading();
        clearError();

        try {
            const result = await analyzeRoom();
            const analysis = {
                id: Date.now(),
                date: new Date().toLocaleString(),
                score: result.cleanliness_score,
                messes: result.tasks,
            };
            
            history.unshift(analysis);
            if (history.length > 10) {
                history.pop();
            }
            localStorage.setItem('analysisHistory', JSON.stringify(history));

            if (result.tasks.length === 0) {
                showEmptyState();
            } else {
                updateMessesList(result.tasks);
            }
            
            updateCleanlinessScore(result.cleanliness_score);
            updateHistoryList(history);
            showResults();
        } catch (error) {
            showError(`Failed to analyze room: ${error.message}`);
        } finally {
            hideLoading();
        }
    };

    const handleClearHistory = () => {
        history = [];
        localStorage.removeItem('analysisHistory');
        clearHistory();
    };

    const handleToggleTask = (e) => {
        if (e.target.tagName === 'LI') {
            e.target.classList.toggle('completed');
        }
    };

    analyzeBtn.addEventListener('click', handleAnalyzeRoom);
    themeToggleBtn.addEventListener('click', toggleTheme);
    clearHistoryBtn.addEventListener('click', handleClearHistory);
messesList.addEventListener('click', handleToggleTask);

    // Set initial theme
    if (localStorage.getItem('theme') === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
    }
});