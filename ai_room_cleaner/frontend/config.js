// Default configuration
const defaultConfig = {
    apiUrl: `${window.location.origin}/api/`
};

// Reads configuration from a global object, which can be populated by a CI/CD pipeline.
export const getApiConfig = () => {
    if (window.__APP_CONFIG__) {
        return { ...defaultConfig, ...window.__APP_CONFIG__ };
    }
    return defaultConfig;
};