import { useCallback, useEffect, useState } from 'react';

/**
 * Seconds-left countdown, e.g. for "Try again in 12s" after a rate limit.
 * `start(n)` (re)starts it; `secondsLeft` is 0 when idle.
 */
export function useCountdown() {
    const [secondsLeft, setSecondsLeft] = useState(0);

    useEffect(() => {
        if (secondsLeft <= 0) return;
        const timer = setTimeout(() => setSecondsLeft((s) => Math.max(0, s - 1)), 1000);
        return () => clearTimeout(timer);
    }, [secondsLeft]);

    const start = useCallback((seconds: number | undefined) => {
        if (seconds && seconds > 0) setSecondsLeft(Math.ceil(seconds));
    }, []);

    return { secondsLeft, start, active: secondsLeft > 0 };
}
