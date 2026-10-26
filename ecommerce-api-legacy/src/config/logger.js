const LEVELS = { error: 0, warn: 1, info: 2, debug: 3 };

function createLogger(level = 'info') {
    const threshold = LEVELS[level] ?? LEVELS.info;
    const write = (name, method) => (...args) => {
        if (LEVELS[name] <= threshold) console[method](`[${new Date().toISOString()}] ${name.toUpperCase()}`, ...args);
    };
    return {
        error: write('error', 'error'),
        warn: write('warn', 'warn'),
        info: write('info', 'log'),
        debug: write('debug', 'log'),
    };
}

module.exports = { createLogger };
