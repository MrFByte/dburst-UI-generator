/**
 * WebContainer Auth singleton
 *
 * Import this module as a side-effect wherever WebContainer is used.
 * It initialises the StackBlitz auth client ONCE at module load time.
 *
 * Usage:
 *   import '@/core/webcontainer/webcontainerAuth';
 */
import { auth } from '@webcontainer/api';

const clientId = import.meta.env.VITE_WEBCONTAINER_API_CLIENT_ID as string;

if (!clientId) {
    console.warn(
        '[WebContainer] VITE_WEBCONTAINER_API_CLIENT_ID is not set. ' +
        'Add it to your .env file.'
    );
}

if (clientId) {
    try {
        auth.init({
            clientId,
            scope: '',
        });
    } catch (err) {
        // auth.init throws if this origin is not in the allowed referrers list.
        // Fix: add this origin at https://stackblitz.com/settings/webcontainers
        console.warn(
            '[WebContainer] auth.init failed — origin may not be whitelisted.\n' +
            'Add it at: https://stackblitz.com/settings/webcontainers\n' +
            'Current origin:', window.location.origin,
            '\nError:', err
        );
    }
}

export { };
