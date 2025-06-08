document.addEventListener('DOMContentLoaded', () => {
    const analyzeBtn = document.getElementById('analyze-btn');
    const taskList = document.getElementById('task-list');

    const fetchTasks = async () => {
        try {
            const response = await fetch('/api/tasks');
            const tasks = await response.json();
            updateTaskList(tasks);
        } catch (error) {
            console.error('Error fetching tasks:', error);
        }
    };

    const analyzeRoom = async () => {
        try {
            const response = await fetch('/api/analyze', { method: 'POST' });
            const data = await response.json();
            if (data.messes) {
                updateTaskList(data.messes);
            }
        } catch (error) {
            console.error('Error analyzing room:', error);
        }
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