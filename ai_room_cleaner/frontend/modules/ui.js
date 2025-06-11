export const updateTaskList = (tasks) => {
    const taskList = document.getElementById('task-list');
    taskList.innerHTML = '';

    if (!tasks || tasks.length === 0) {
        const li = document.createElement('li');
        li.textContent = 'No tasks found. The room is clean!';
        taskList.appendChild(li);
        return;
    }

    tasks.forEach((task, index) => {
        const li = document.createElement('li');
        li.textContent = task;
        li.id = `task-${index}`;
        taskList.appendChild(li);
    });
};

export const updateCleanlinessScore = (tasks) => {
    const tasksCompleted = document.getElementById('tasks-completed');
    const cleanlinessScoreEl = document.getElementById('cleanliness-score');

    const numTasks = tasks.length;
    const score = Math.max(0, 100 - (numTasks * 10));

    tasksCompleted.textContent = numTasks;
    cleanlinessScoreEl.textContent = score;

    if (score > 80) {
        cleanlinessScoreEl.style.color = 'green';
    } else if (score >= 50) {
        cleanlinessScoreEl.style.color = 'orange';
    } else {
        cleanlinessScoreEl.style.color = 'red';
    }
};

export const showLoading = () => {
    document.getElementById('loading-indicator').style.display = 'block';
    document.getElementById('analyze-btn').disabled = true;
};

export const hideLoading = () => {
    document.getElementById('loading-indicator').style.display = 'none';
    document.getElementById('analyze-btn').disabled = false;
};

export const showError = (message) => {
    const errorMessage = document.getElementById('error-message');
    errorMessage.textContent = message;
    errorMessage.classList.add('error-message--visible');
};

export const clearError = () => {
    const errorMessage = document.getElementById('error-message');
    errorMessage.textContent = '';
    errorMessage.classList.remove('error-message--visible');
};