document.addEventListener('DOMContentLoaded', () => {
    const analyzeBtn = document.getElementById('analyze-btn');
    const taskList = document.getElementById('task-list');
    const errorMessage = document.getElementById('error-message');
    const loadingIndicator = document.getElementById('loading-indicator');

    const apiService = async (endpoint, options) => {
        console.log(`Making API call to: ${endpoint}`);
        const response = await fetch(endpoint, options);
        console.log(`Response status: ${response.status}`);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error(`API Error: ${response.status} - ${errorText}`);
            throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
        }
        
        const data = await response.json();
        console.log('Response data:', data);
        return data;
    };

    const fetchTasks = async () => {
        try {
            console.log('Fetching existing tasks...');
            const tasks = await apiService('/api/tasks');
            updateTaskList(tasks);
        } catch (error) {
            console.error('Error fetching tasks:', error);
        }
    };

    const analyzeRoom = async () => {
        console.log('Starting room analysis...');
        analyzeBtn.disabled = true;
        loadingIndicator.style.display = 'block';
        errorMessage.textContent = '';

        try {
            const response = await apiService('/api/analyze', { method: 'POST' });
            
            // Handle different response formats
            let messes;
            if (response.tasks) {
                messes = response.tasks;
            } else if (Array.isArray(response)) {
                messes = response;
            } else {
                console.warn('Unexpected response format:', response);
                messes = [];
            }
            
            console.log('Analysis complete, tasks:', messes);
            updateTaskList(messes);
            updatePerformanceStats(messes);
        } catch (error) {
            console.error('Error analyzing room:', error);
            errorMessage.textContent = `Failed to analyze room: ${error.message}`;
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
        if (!tasks || tasks.length === 0) {
            taskList.innerHTML = '<li>No tasks found. The room is clean!</li>';
            return;
        }
        tasks.forEach((task, index) => {
            const li = document.createElement('li');
            li.textContent = task;
            li.id = `task-${index}`;
            taskList.appendChild(li);
        });
    };

    // Add health check
    const checkHealth = async () => {
        try {
            const health = await apiService('/api/health');
            console.log('Health check:', health);
        } catch (error) {
            console.error('Health check failed:', error);
        }
    };

    analyzeBtn.addEventListener('click', analyzeRoom);
    
    // Initialize
    checkHealth();
    fetchTasks();
});