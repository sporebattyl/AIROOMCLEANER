(async () => {
    try {
        await import('./app.js');
    } catch (error) {
        console.error('Failed to load application modules:', error);
        document.body.innerHTML = `
            <div style="text-align: center; padding: 2rem; font-family: sans-serif;">
                <h1>Application Error</h1>
                <p>Could not load required components. Please check the console for details.</p>
                <p><i>This might happen if you are running the application from the local filesystem (file://). Please use a local web server.</i></p>
            </div>
        `;
    }
})();