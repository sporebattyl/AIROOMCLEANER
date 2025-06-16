import { getApiConfig } from '../config.js';
import logger from './logger.js';
import { NetworkError, ServerError } from './errors.js';

const getApiUrl = (endpoint) => {
    let { apiUrl } = getApiConfig();
    if (typeof process !== 'undefined' && process.env.NODE_ENV === 'test') {
        apiUrl = apiUrl || 'http://localhost';
    }
    // URL constructor for robust URL creation
    const url = new URL(endpoint, apiUrl);
    return url.href;
};

export const apiService = async (endpoint, options = {}) => {
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
            } catch {
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