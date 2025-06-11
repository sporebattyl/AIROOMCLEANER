const API_BASE_URL = "/api";

const apiService = async (endpoint, options = {}) => {
    const url = `${API_BASE_URL}${endpoint.substring(1)}`;
    
    console.log(`Making API call to: ${url}`);
    
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        console.log(`Response status: ${response.status}`);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error(`API Error: ${response.status} - ${errorText}`);
            throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
        }
        
        const data = await response.json();
        console.log('Response data:', data);
        return data;
    } catch (error) {
        console.error(`API call to ${url} failed:`, error);
        throw error;
    }
};

export const checkHealth = async () => {
    try {
        const health = await apiService('/api/health');
        console.log('Health check:', health);
        return health;
    } catch (error) {
        console.error('Health check failed:', error);
        throw error;
    }
};

export const fetchTasks = async () => {
    try {
        console.log('Fetching existing tasks...');
        const tasks = await apiService('/api/tasks');
        return tasks;
    } catch (error) {
        console.error('Error fetching tasks:', error);
        throw error;
    }
};

export const analyzeRoom = async () => {
    console.log('Starting room analysis...');
    try {
        const response = await apiService('/api/analyze', { method: 'POST' });
        
        // Handle different response formats
        let messes;
        if (response.tasks) {
            messes = response.tasks;
        } else if (Array.isArray(response)) {
            messes = response;
        } else {
            console.warn('Unexpected response format:', response);
            messes = [];
        }
        
        console.log('Analysis complete, tasks:', messes);
        return messes;
    } catch (error) {
        console.error('Error analyzing room:', error);
        throw error;
    }
};