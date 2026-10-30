const App = {
    currentRoute: null,

    init() {
        window.addEventListener('popstate', () => this.handleRoute());
        this.handleRoute();
        // Surface the changelog once the first view is up; never blocks startup.
        checkWhatsNew();
    },

    navigate(path) {
        history.pushState(null, '', path);
        this.handleRoute();
    },

    handleRoute() {
        // Cleanup previous view
        cleanupTranscriptView();

        const path = window.location.pathname;
        const container = document.getElementById('app');

        // Don't match /static/* or /api/* paths
        if (path.startsWith('/static/') || path.startsWith('/api/')) return;

        if (path === '/' || path === '') {
            this.currentRoute = 'list';
            renderMeetingList(container);
        } else if (path === '/upload') {
            this.currentRoute = 'upload';
            renderUpload(container);
        } else if (path.startsWith('/meetings/')) {
            const id = path.split('/meetings/')[1];
            if (id) {
                this.currentRoute = 'meeting';
                renderTranscriptView(container, id);
            }
        } else {
            this.currentRoute = 'list';
            renderMeetingList(container);
        }
    },
};

document.addEventListener('DOMContentLoaded', () => App.init());
