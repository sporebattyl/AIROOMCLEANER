import { analyzeRoom } from './modules/api.js';
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

    analyzeBtn.addEventListener('click', handleAnalyzeRoom);
});