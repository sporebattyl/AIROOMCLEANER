function isStorageAvailable(type) {
    let storage;
    try {
        storage = window[type];
        const x = '__storage_test__';
        storage.setItem(x, x);
        storage.removeItem(x);
        return true;
    } catch (e) {
        return e instanceof DOMException && (
            // everything except Firefox
            e.code === 22 ||
            // Firefox
            e.code === 1014 ||
            // test name field too, because code might not be present
            // everything except Firefox
            e.name === 'QuotaExceededError' ||
            // Firefox
            e.name === 'NS_ERROR_DOM_QUOTA_REACHED') &&
            // acknowledge QuotaExceededError only if there's something already stored
            (storage && storage.length !== 0);
    }
}

let storage;
if (isStorageAvailable('localStorage')) {
    storage = {
        get: (key, defaultValue = null) => {
            try {
                const value = localStorage.getItem(key);
                return value ? JSON.parse(value) : defaultValue;
            } catch (error) {
                console.warn(`Could not read '${key}' from localStorage:`, error);
                return defaultValue;
            }
        },
        set: (key, value) => {
            try {
                localStorage.setItem(key, JSON.stringify(value));
                return true;
            } catch (error) {
                console.warn(`Could not write '${key}' to localStorage:`, error);
                return false;
            }
        },
        remove: (key) => {
            try {
                localStorage.removeItem(key);
                return true;
            } catch (error) {
                console.warn(`Could not remove '${key}' from localStorage:`, error);
                return false;
            }
        }
    };
} else {
    console.warn("localStorage is not available. Falling back to in-memory storage.");
    const inMemoryStore = {};
    storage = {
        get: (key, defaultValue = null) => {
            return inMemoryStore.hasOwnProperty(key) ? inMemoryStore[key] : defaultValue;
        },
        set: (key, value) => {
            try {
                inMemoryStore[key] = JSON.parse(JSON.stringify(value)); // Deep copy
                return true;
            } catch (error) {
                console.warn(`Could not store '${key}' in memory:`, error);
                return false;
            }
        },
        remove: (key) => {
            if (inMemoryStore.hasOwnProperty(key)) {
                delete inMemoryStore[key];
            }
            return true;
        }
    };
}

export { storage };

export const CONFIG = {
    MAX_HISTORY_ITEMS: 50,
    DEBOUNCE_DELAY: 500,
    ERROR_DISPLAY_DURATION: 5000,
    RETRY_ATTEMPTS: 3
};

export const ERROR_MESSAGES = {
    NETWORK_ERROR: 'Unable to connect to server. Please check your internet connection.',
    SERVER_ERROR: 'Server error occurred. Please try again later.',
    ANALYSIS_FAILED: 'Room analysis failed. Please try again.',
    HISTORY_LOAD_FAILED: 'Could not load analysis history.',
};

// Encapsulated application state
const appState = {
    history: [],
    currentTheme: 'light', // Default theme
};

// --- Getters ---

/**
 * Gets a copy of the analysis history.
 * @returns {Array} A copy of the history array.
 */
export function getHistory() {
    return [...appState.history];
}

/**
 * Gets the current UI theme.
 * @returns {string} The current theme ('light' or 'dark').
 */
export function getCurrentTheme() {
    return appState.currentTheme;
}


// --- Setters ---

/**
 * Replaces the entire history with a new array.
 * @param {Array} newHistory - The new history array.
 */
export function setHistory(newHistory) {
    if (Array.isArray(newHistory)) {
        appState.history = [...newHistory];
    } else {
        console.error("Validation Error: setHistory expects an array.");
    }
}

/**
 * Adds a new item to the beginning of the history.
 * If the history exceeds MAX_HISTORY_ITEMS, the oldest item is removed.
 * @param {object} item - The history item to add.
 */
export function addToHistory(item) {
    if (typeof item === 'object' && item !== null) {
        appState.history.unshift(item);
        if (appState.history.length > CONFIG.MAX_HISTORY_ITEMS) {
            appState.history.pop();
        }
    } else {
         console.error("Validation Error: addToHistory expects an object.");
    }
}


/**
 * Sets the current UI theme.
 * @param {string} newTheme - The new theme name (e.g., 'light', 'dark').
 */
export function setCurrentTheme(newTheme) {
    if (typeof newTheme === 'string') {
        appState.currentTheme = newTheme;
    } else {
        console.error("Validation Error: setCurrentTheme expects a string.");
    }
}

export const elements = {};