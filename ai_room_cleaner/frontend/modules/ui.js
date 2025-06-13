const messesList = document.getElementById('messes-list');
const tasksCountEl = document.getElementById('tasks-count');
const cleanlinessScoreEl = document.getElementById('cleanliness-score');
const loadingOverlay = document.getElementById('loading-overlay');
const errorToast = document.getElementById('error-toast');
const historyList = document.getElementById('history-list');
const historyEmptyState = document.getElementById('history-empty-state');
const resultsContainer = document.getElementById('results-container');
const emptyState = document.getElementById('empty-state');

export const updateMessesList = (tasks) => {
    messesList.innerHTML = '';
    tasks.forEach(task => {
        const li = document.createElement('li');
        li.textContent = task.mess;
        li.title = `Reason: ${task.reason || 'N/A'}. Click to mark as complete.`;
        messesList.appendChild(li);
    });
    tasksCountEl.textContent = tasks.length;
    emptyState.classList.add('hidden');
    messesList.classList.remove('hidden');
};

export const showEmptyState = () => {
    messesList.innerHTML = '';
    messesList.classList.add('hidden');
    tasksCountEl.textContent = 0;
    emptyState.classList.remove('hidden');
};

export const updateCleanlinessScore = (score) => {
    cleanlinessScoreEl.textContent = `${score}%`;
    if (score >= 80) {
        cleanlinessScoreEl.style.color = 'var(--success-color)';
    } else if (score >= 50) {
        cleanlinessScoreEl.style.color = 'var(--secondary-color)';
    } else {
        cleanlinessScoreEl.style.color = 'var(--error-color)';
    }
};

export const showLoading = () => {
    loadingOverlay.classList.remove('hidden');
};

export const hideLoading = () => {
    loadingOverlay.classList.add('hidden');
};

export const showError = (error) => {
    let errorMessage = 'An unexpected error occurred.';
    if (typeof error === 'string') {
        errorMessage = error;
    } else if (error instanceof Error) {
        errorMessage = error.message;
        if (error.response && error.response.data && error.response.data.detail) {
            errorMessage += ` ${error.response.data.detail}`;
        }
        if (error.stack) {
            console.error(error.stack);
        }
    }
    errorToast.textContent = errorMessage;
    errorToast.classList.remove('hidden');
    setTimeout(() => {
        errorToast.classList.add('hidden');
    }, 5000); // Increased timeout for better readability
};

export const clearError = () => {
    errorToast.classList.add('hidden');
};

export const toggleTheme = () => {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
};

export const updateHistoryList = (history) => {
    historyList.innerHTML = '';
    if (history.length === 0) {
        historyEmptyState.classList.remove('hidden');
        historyList.classList.add('hidden');
    } else {
        historyEmptyState.classList.add('hidden');
        historyList.classList.remove('hidden');
        history.forEach(item => {
            const li = document.createElement('li');
            li.innerHTML = `
                <span>${item.date}</span>
                <span>${item.score}%</span>
            `;
            historyList.appendChild(li);
        });
    }
};

export const clearHistory = () => {
    historyList.innerHTML = '';
    historyEmptyState.classList.remove('hidden');
    historyList.classList.add('hidden');
};

export const showResults = () => {
    resultsContainer.classList.remove('hidden');
};