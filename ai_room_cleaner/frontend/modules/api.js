const API_BASE_URL = "/api";

const apiService = async (endpoint, options = {}) => {
    const url = new URL(endpoint, API_BASE_URL).href;

    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
        }

        return response.json();
    } catch (error) {
        console.error(`API call to ${url} failed:`, error);
        throw error;
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