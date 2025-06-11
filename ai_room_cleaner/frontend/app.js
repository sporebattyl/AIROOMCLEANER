import { checkHealth, fetchTasks, analyzeRoom } from './modules/api.js';
import { updateTaskList, updateCleanlinessScore, showLoading, hideLoading, showError, clearError } from './modules/ui.js';

document.addEventListener('DOMContentLoaded', () => {
    const analyzeBtn = document.getElementById('analyze-btn');

    const handleAnalyzeRoom = async () => {
        showLoading();
        clearError();

        try {
            const tasks = await analyzeRoom();
            updateTaskList(tasks);
            updateCleanlinessScore(tasks);
        } catch (error) {
            showError(`Failed to analyze room: ${error.message}`);
        } finally {
            hideLoading();
        }
    };

    const initializeApp = async () => {
        try {
            await checkHealth();
            const tasks = await fetchTasks();
            updateTaskList(tasks);
        } catch (error) {
            showError('Error: Could not connect to the backend.');
            updateTaskList([]);
        }
    };

    analyzeBtn.addEventListener('click', handleAnalyzeRoom);
    
    initializeApp();
});