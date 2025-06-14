const messesList = document.getElementById('messes-list');
const tasksCountEl = document.getElementById('tasks-count');
const cleanlinessScoreEl = document.getElementById('cleanliness-score');
const loadingOverlay = document.getElementById('loading-overlay');
const errorToast = document.getElementById('error-toast');
const historyList = document.getElementById('history-list');
const historyEmptyState = document.getElementById('history-empty-state');
const resultsContainer = document.getElementById('results-container');
const emptyState = document.getElementById('empty-state');

const createMessItem = (task) => {
    const li = document.createElement('li');
    li.textContent = task.mess;
    li.title = `Reason: ${task.reason || 'N/A'}. Click to mark as complete.`;
    li.setAttribute('role', 'listitem');
    return li;
};

export const updateMessesList = (tasks) => {
    if (tasks.length === 0) {
        showEmptyState();
        return;
    }
    
    messesList.innerHTML = '';
    const fragment = document.createDocumentFragment();
    tasks.forEach(task => {
        fragment.appendChild(createMessItem(task));
    });
    messesList.appendChild(fragment);

    tasksCountEl.textContent = tasks.length;
    emptyState.classList.add('hidden');
    resultsContainer.classList.remove('hidden');
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

export const showError = (error, retryCallback = null) => {
    let errorMessage = 'An unexpected error occurred.';

    if (!navigator.onLine) {
        errorMessage = "You are offline. Please check your internet connection.";
    } else if (typeof error === 'string') {
        errorMessage = error;
    } else if (error instanceof Error) {
        errorMessage = error.message;
        if (error.response && error.response.data && error.response.data.detail) {
            errorMessage = error.response.data.detail;
        }
    }
    
    errorToast.innerHTML = ''; // Clear previous errors
    const errorSpan = document.createElement('span');
    errorSpan.textContent = errorMessage;
    errorToast.appendChild(errorSpan);

    if (retryCallback) {
        const retryButton = document.createElement('button');
        retryButton.textContent = 'Retry';
        retryButton.onclick = () => {
            clearError();
            retryCallback();
        };
        errorToast.appendChild(retryButton);
    }

    errorToast.classList.remove('hidden');

    // Do not auto-hide if there's a retry button
    if (!retryCallback) {
        setTimeout(() => {
            errorToast.classList.add('hidden');
        }, 5000);
    }
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

const createHistoryItem = (item) => {
    const li = document.createElement('li');
    li.setAttribute('role', 'listitem');

    const dateSpan = document.createElement('span');
    dateSpan.textContent = item.date;

    const scoreSpan = document.createElement('span');
    scoreSpan.textContent = `${item.score}%`;

    li.appendChild(dateSpan);
    li.appendChild(scoreSpan);

    return li;
};

export const showHistoryLoading = () => {
    historyList.innerHTML = '<li>Loading history...</li>';
    historyEmptyState.classList.add('hidden');
    historyList.classList.remove('hidden');
};

export const hideHistoryLoading = () => {
    historyList.innerHTML = '';
};


export const updateHistoryList = (history) => {
    hideHistoryLoading();
    if (history.length === 0) {
        historyEmptyState.classList.remove('hidden');
        historyList.classList.add('hidden');
    } else {
        historyEmptyState.classList.add('hidden');
        historyList.classList.remove('hidden');
        historyList.innerHTML = '';
        const fragment = document.createDocumentFragment();
        history.forEach(item => {
            fragment.appendChild(createHistoryItem(item));
        });
        historyList.appendChild(fragment);
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