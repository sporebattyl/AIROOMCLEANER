document.addEventListener('DOMContentLoaded', () => {
    const analyzeBtn = document.getElementById('analyze-btn');
    const taskList = document.getElementById('task-list');
    const errorMessage = document.getElementById('error-message');
    const loadingIndicator = document.getElementById('loading-indicator');

    const apiService = async (endpoint, options) => {
        const response = await fetch(endpoint, options);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.statusText}`);
        }
        return response.json();
    };

    const fetchTasks = async () => {
        try {
            const tasks = await apiService('/api/tasks');
            updateTaskList(tasks);
        } catch (error) {
            console.error('Error fetching tasks:', error);
        }
    };

    const analyzeRoom = async () => {
        analyzeBtn.disabled = true;
        loadingIndicator.style.display = 'block';
        errorMessage.textContent = '';

        try {
            const messes = await apiService('/api/analyze', { method: 'POST' });
            updateTaskList(messes);
            updatePerformanceStats(messes);
        } catch (error) {
            errorMessage.textContent = 'Failed to analyze room. Please try again.';
            console.error('Error analyzing room:', error);
        } finally {
            analyzeBtn.disabled = false;
            loadingIndicator.style.display = 'none';
        }
    };

    const updatePerformanceStats = (tasks) => {
        const tasksCompleted = document.getElementById('tasks-completed');
        const cleanlinessScore = document.getElementById('cleanliness-score');

        const numTasks = tasks.length;
        const score = Math.max(0, 100 - (numTasks * 10));

        tasksCompleted.textContent = numTasks;
        cleanlinessScore.textContent = score;
    };

    const updateTaskList = (tasks) => {
        taskList.innerHTML = '';
        if (tasks.length === 0) {
            taskList.innerHTML = '<li>No tasks found. The room is clean!</li>';
            return;
        }
        tasks.forEach(task => {
            const li = document.createElement('li');
            li.textContent = task;
            taskList.appendChild(li);
        });
    };

    analyzeBtn.addEventListener('click', analyzeRoom);
    fetchTasks();
});