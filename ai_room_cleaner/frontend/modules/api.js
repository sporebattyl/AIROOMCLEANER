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
        const response = await apiService('/analyze', { method: 'POST' });
        
        let messes;
        if (response.tasks) {
            messes = response.tasks;
        } else if (Array.isArray(response)) {
            messes = response;
        } else {
            messes = [];
        }
        
        return messes;
    } catch (error) {
        console.error('Error analyzing room:', error);
        throw error;
    }
};