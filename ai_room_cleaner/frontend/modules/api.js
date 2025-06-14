const API_BASE_URL = "api";

const getApiUrl = (endpoint) => {
    // URL constructor for robust URL creation
    const url = new URL(`${API_BASE_URL}${endpoint}`, window.location.origin);
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

    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
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

        return response.json();
    } catch (error) {
        if (error instanceof ServerError) {
            throw error;
        }
        console.error(`API call to ${url} failed:`, error);
        throw new NetworkError('Failed to connect to the server. Please check your network connection.');
    }
};

export const analyzeRoom = async () => {
    try {
        return await apiService('/analyze', { method: 'POST' });
    } catch (error) {
        console.error('Error analyzing room:', error);
        throw error;
    }
};

export const getHistory = async () => {
    try {
        return await apiService('/history');
    } catch (error) {
        console.error('Error fetching history:', error);
        throw error;
    }
};