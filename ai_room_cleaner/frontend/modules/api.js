const getApiBaseUrl = () => {
    // In a real app, this might come from a config file or env variable
    // For this project, we'll assume the API is at the same origin under /api
    return `${window.location.origin}/api/`;
};

const getApiUrl = (endpoint) => {
    const baseUrl = getApiBaseUrl();
    // URL constructor for robust URL creation
    const url = new URL(endpoint, baseUrl);
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
        return await apiService('v1/analyze-room-secure', { method: 'POST' });
    } catch (error) {
        console.error('Error analyzing room:', error);
        throw error;
    }
};

export const getHistory = async () => {
    try {
        return await apiService('history');
    } catch (error) {
        console.error('Error fetching history:', error);
        throw error;
    }
};