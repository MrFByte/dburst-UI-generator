import pino from 'pino';

const config = {
    serverUrl: import.meta.env.VITE_LOG_SERVER_URL,
    env: import.meta.env.MODE,
    publicUrl: import.meta.env.VITE_PUBLIC_URL,
};

const logger = pino({
    browser: {
        asObject: true,
    },
    level: 'debug',
    base: {
        env: config.env,
    },
});

export default logger;
