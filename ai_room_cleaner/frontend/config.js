import { fetchServerConfig } from './modules/api.js';
import logger from './modules/logger.js';

let config = null;

const defaultConfig = {
    apiUrl: `${window.location.origin}/api/`,
};

async function loadConfig() {
    try {
        const serverConfig = await fetchServerConfig();
        config = { ...defaultConfig, ...serverConfig };
        logger.info({ config }, 'Configuration loaded from server');
    } catch (error) {
        logger.error({ error }, 'Failed to load server configuration, using defaults.');
        config = { ...defaultConfig };
    }
}

export const getApiConfig = async () => {
    if (!config) {
        await loadConfig();
    }
    return config;
};