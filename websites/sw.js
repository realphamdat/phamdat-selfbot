// Service Worker for Phamdat Selfbot
// Handles push notifications and caching

self.addEventListener('install', () => {
    self.skipWaiting();
});

self.addEventListener('activate', event => {
    event.waitUntil(self.clients.claim());
});

self.addEventListener('push', event => {
    const data = event.data ? event.data.json() : {};
    const title = data.title || 'Phamdat Selfbot';
    const options = {
        body: data.body || '',
        icon: '/assets/logo.png',
        badge: '/assets/logo.png',
        tag: data.tag || 'default',
        vibrate: [200, 100, 200],
    };
    event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', event => {
    event.notification.close();
    event.waitUntil(
        self.clients.matchAll({ type: 'window' }).then(clients => {
            const captchaClient = clients.find(c => c.url.includes('/captcha'));
            if (captchaClient) {
                return captchaClient.focus();
            }
            if (clients.length > 0) {
                return clients[0].focus();
            }
            return self.clients.openWindow('/captcha');
        })
    );
});
