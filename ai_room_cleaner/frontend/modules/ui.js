let uiElements = {};

export const initializeUIElements = () => {
    uiElements = {
        messesList: document.getElementById('messes-list'),
        tasksCount: document.getElementById('tasks-count'),
        cleanlinessScore: document.getElementById('cleanliness-score'),
        loadingOverlay: document.getElementById('loading-overlay'),
        errorToast: document.getElementById('error-toast'),
        historyList: document.getElementById('history-list'),
        historyEmptyState: document.getElementById('history-empty-state'),
        resultsContainer: document.getElementById('results-container'),
        emptyState: document.getElementById('empty-state'),
    };
};

const createMessItem = (task) => {
    const li = document.createElement('li');
    li.textContent = task.mess;
    li.title = `Reason: ${task.reason || 'N/A'}. Click to mark as complete.`;
    li.setAttribute('role', 'listitem');
    return li;
};

export const updateStatus = (message, isError = false) => {
    const statusEl = uiElements.errorToast;
    statusEl.textContent = message;
    statusEl.className = isError ? 'error' : ''; // Batch class changes

    setTimeout(() => {
        statusEl.classList.add('hidden');
    }, 5000);
};

export const updateMessesList = (tasks) => {
    if (tasks.length === 0) {
        showEmptyState();
        return;
    }
    
    const fragment = document.createDocumentFragment();
    tasks.forEach(task => {
        fragment.appendChild(createMessItem(task));
    });

    // Batch DOM writes
    uiElements.messesList.innerHTML = '';
    uiElements.messesList.appendChild(fragment);
    uiElements.tasksCount.textContent = tasks.length;
    
    // Batch class changes
    uiElements.emptyState.classList.add('hidden');
    uiElements.resultsContainer.classList.remove('hidden');
    uiElements.messesList.classList.remove('hidden');
};

export const showEmptyState = () => {
    uiElements.messesList.innerHTML = '';
    uiElements.tasksCount.textContent = 0;

    // Batch class changes
    uiElements.messesList.classList.add('hidden');
    uiElements.emptyState.classList.remove('hidden');
    uiElements.resultsContainer.classList.add('hidden');
};

export const updateCleanlinessScore = (score) => {
    uiElements.cleanlinessScore.textContent = `${score}%`;
    if (score >= 80) {
        uiElements.cleanlinessScore.style.color = 'var(--success-color)';
    } else if (score >= 50) {
        uiElements.cleanlinessScore.style.color = 'var(--secondary-color)';
    } else {
        uiElements.cleanlinessScore.style.color = 'var(--error-color)';
    }
};

export const showLoading = () => {
    uiElements.loadingOverlay.classList.remove('hidden');
};

export const hideLoading = () => {
    uiElements.loadingOverlay.classList.add('hidden');
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
    
    const fragment = document.createDocumentFragment();
    const errorSpan = document.createElement('span');
    errorSpan.textContent = errorMessage;
    fragment.appendChild(errorSpan);

    if (retryCallback) {
        const retryButton = document.createElement('button');
        retryButton.textContent = 'Retry';
        retryButton.onclick = () => {
            clearError();
            retryCallback();
        };
        fragment.appendChild(retryButton);
    }

    uiElements.errorToast.innerHTML = ''; // Clear previous errors
    uiElements.errorToast.appendChild(fragment);
    uiElements.errorToast.classList.remove('hidden');

    // Do not auto-hide if there's a retry button
    if (!retryCallback) {
        setTimeout(() => {
            uiElements.errorToast.classList.add('hidden');
        }, 5000);
    }
};

export const clearError = () => {
    uiElements.errorToast.classList.add('hidden');
};


const createHistoryItem = (item) => {
    const li = document.createElement('li');
    li.setAttribute('role', 'listitem');

    const dateSpan = document.createElement('span');
    dateSpan.textContent = item.date;

    const scoreSpan = document.createElement('span');
    scoreSpan.textContent = `${item.cleanliness_score}%`;

    li.appendChild(dateSpan);
    li.appendChild(scoreSpan);

    return li;
};

export const showHistoryLoading = () => {
    uiElements.historyList.innerHTML = '<li>Loading history...</li>';
    
    // Batch class changes
    uiElements.historyEmptyState.classList.add('hidden');
    uiElements.historyList.classList.remove('hidden');
};

export const hideHistoryLoading = () => {
    uiElements.historyList.innerHTML = '';
};


export const updateHistoryList = (history) => {
    hideHistoryLoading();
    const fragment = document.createDocumentFragment();

    if (history.length === 0) {
        uiElements.historyEmptyState.classList.remove('hidden');
        uiElements.historyList.classList.add('hidden');
    } else {
        history.forEach(item => {
            fragment.appendChild(createHistoryItem(item));
        });
        uiElements.historyList.innerHTML = '';
        uiElements.historyList.appendChild(fragment);
        uiElements.historyEmptyState.classList.add('hidden');
        uiElements.historyList.classList.remove('hidden');
    }
};

export const clearHistory = () => {
    uiElements.historyList.innerHTML = '';
    
    // Batch class changes
    uiElements.historyEmptyState.classList.remove('hidden');
    uiElements.historyList.classList.add('hidden');
};

export const showResults = () => {
    uiElements.resultsContainer.classList.remove('hidden');
};