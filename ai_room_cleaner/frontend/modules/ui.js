import logger from './logger.js';

let uiElements = {};

export const initializeUIElements = () => {
    logger.info('Initializing UI elements');
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

const clearElement = (element) => {
    while (element.firstChild) {
        element.removeChild(element.firstChild);
    }
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
    logger.info({ taskCount: tasks.length }, 'Updating messes list');
    if (tasks.length === 0) {
        showEmptyState();
        return;
    }
    
    const fragment = document.createDocumentFragment();
    tasks.forEach(task => {
        fragment.appendChild(createMessItem(task));
    });

    // Batch DOM writes
    clearElement(uiElements.messesList);
    uiElements.messesList.appendChild(fragment);
    uiElements.tasksCount.textContent = tasks.length;
    
    // Batch class changes
    uiElements.emptyState.classList.add('hidden');
    uiElements.resultsContainer.classList.remove('hidden');
    uiElements.messesList.classList.remove('hidden');
};

export const showEmptyState = () => {
    clearElement(uiElements.messesList);
    uiElements.tasksCount.textContent = 0;

    // Batch class changes
    uiElements.messesList.classList.add('hidden');
    uiElements.emptyState.classList.remove('hidden');
    uiElements.resultsContainer.classList.add('hidden');
};

export const updateCleanlinessScore = (score) => {
    logger.info({ score }, 'Updating cleanliness score');
    const scoreEl = uiElements.cleanlinessScore;
    scoreEl.textContent = `${score}%`;

    // Batch class changes for performance
    scoreEl.classList.remove('score-high', 'score-medium', 'score-low');

    if (score >= 80) {
        scoreEl.classList.add('score-high');
    } else if (score >= 50) {
        scoreEl.classList.add('score-medium');
    } else {
        scoreEl.classList.add('score-low');
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
    }
    
    logger.error({ error: errorMessage, retry: !!retryCallback }, 'Displaying error');
    
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

    clearElement(uiElements.errorToast); // Clear previous errors
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
    clearElement(uiElements.historyList);
    const loadingItem = document.createElement('li');
    loadingItem.textContent = 'Loading history...';
    uiElements.historyList.appendChild(loadingItem);
    
    // Batch class changes
    uiElements.historyEmptyState.classList.add('hidden');
    uiElements.historyList.classList.remove('hidden');
};

export const hideHistoryLoading = () => {
    clearElement(uiElements.historyList);
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
        clearElement(uiElements.historyList);
        uiElements.historyList.appendChild(fragment);
        uiElements.historyEmptyState.classList.add('hidden');
        uiElements.historyList.classList.remove('hidden');
    }
};

export const clearHistory = () => {
    clearElement(uiElements.historyList);
    
    // Batch class changes
    uiElements.historyEmptyState.classList.remove('hidden');
    uiElements.historyList.classList.add('hidden');
};

export const showResults = () => {
    uiElements.resultsContainer.classList.remove('hidden');
};