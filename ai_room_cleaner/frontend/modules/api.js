import { getApiConfig as getLocalConfig } from '../config.js';
import logger from './logger.js';
import { apiService } from './service.js';
import { API_ENDPOINTS } from './constants.js';

export { NetworkError, ServerError } from './errors.js';

export const analyzeRoom = async (imageFile) => {
    const { apiKey } = await getLocalConfig();
    const formData = new FormData();
    formData.append('file', imageFile);

    try {
        return await apiService(API_ENDPOINTS.ANALYZE_ROOM, {
            method: 'POST',
            body: formData,
            headers: {
                'X-API-KEY': apiKey
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

export const fetchServerConfig = async () => {
    try {
        return await apiService(API_ENDPOINTS.CONFIG);
    } catch (error) {
        logger.error({ error }, 'Error fetching config');
        throw error;
    }
};
export const clearHistory = async () => {
    const { apiKey } = await getLocalConfig();
    try {
        return await apiService(API_ENDPOINTS.HISTORY, {
            method: 'DELETE',
            headers: {
                'X-API-KEY': apiKey,
            },
        });
    } catch (error) {
        logger.error({ error }, 'Error clearing history');
        throw error;
    }
};