import { getApiConfig } from '../config.js';
import logger from './logger.js';

const API_ENDPOINTS = Object.freeze({
    ANALYZE_ROOM: 'v1/analyze-room-secure',
    HISTORY: 'history',
});

const getApiUrl = (endpoint) => {
    const { apiUrl } = getApiConfig();
    // URL constructor for robust URL creation
    const url = new URL(endpoint, apiUrl);
    return url.href;
};

export class NetworkError extends Error {
    constructor(message) {
        super(message);
        this.name = 'NetworkError';
    }
}

export class ServerError extends Error {
    constructor(message, status) {
        super(message);
        this.name = 'ServerError';
        this.status = status;
    }
}

const apiService = async (endpoint, options = {}) => {
    const url = getApiUrl(endpoint);

    const headers = { ...options.headers };
    if (!(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
    }

    try {
        const response = await fetch(url, {
            ...options,
            headers,
        });

        if (!response.ok) {
            let errorMessage = `HTTP error! status: ${response.status}`;
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorMessage;
            } catch (e) {
                // Ignore if response is not json
            }
            throw new ServerError(errorMessage, response.status);
        }

        const data = await response.json();
        logger.info({ url, status: response.status }, 'API call successful');
        return data;
    } catch (error) {
        if (error instanceof ServerError) {
            logger.error({ url, status: error.status, error: error.message }, 'Server error');
            throw error;
        }
        logger.error({ url, error: error.message }, 'Network error');
        throw new NetworkError('Failed to connect to the server. Please check your network connection.');
    }
};

export const analyzeRoom = async (imageFile) => {
    const formData = new FormData();
    formData.append('file', imageFile);

    try {
        return await apiService(API_ENDPOINTS.ANALYZE_ROOM, {
            method: 'POST',
            body: formData,
            headers: {
                'X-API-KEY': 'YOUR_API_KEY' // This should be retrieved from a config file
            }
        });
    } catch (error) {
        logger.error({ error }, 'Error analyzing room');
        throw error;
    }
};

export const getHistory = async () => {
    try {
        return await apiService(API_ENDPOINTS.HISTORY);
    } catch (error) {
        logger.error({ error }, 'Error fetching history');
        throw error;
    }
};
export const clearHistory = async () => {
    try {
        return await apiService('history', { method: 'DELETE' });
    } catch (error) {
        logger.error({ error }, 'Error clearing history');
        throw error;
    }
};