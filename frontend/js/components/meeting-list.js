function renderMeetingList(container) {
    container.innerHTML = `
        <header class="page-header page-header--meetings">
            <div>
                <div class="page-eyebrow">Library</div>
                <h1>Meetings</h1>
            </div>
            <button class="btn btn-primary" onclick="App.navigate('/upload')">Upload Recording</button>
        </header>
        <div id="meetings-list" class="meetings-list">
            <div class="loading">Loading meetings...</div>
        </div>
    `;

    loadMeetings();
}

async function loadMeetings() {
    const listEl = document.getElementById('meetings-list');
    try {
        const meetings = await API.listMeetings();
        if (meetings.length === 0) {
            listEl.innerHTML = `
                <div class="empty-state">
                    <p>No meetings yet. Upload your first recording.</p>
                    <button class="btn btn-primary" onclick="App.navigate('/upload')">Upload Recording</button>
                </div>
            `;
            return;
        }

        listEl.innerHTML = meetings.map(m => `
            <button class="meeting-row" type="button" onclick="App.navigate('/meetings/${m.id}')">
                <div class="meeting-info">
                    <span class="meeting-title">${escapeHtml(m.title)}</span>
                    <span class="meeting-meta">
                        <span class="meta-pill meta-pill-${m.type}">${escapeHtml(m.type)}</span>
                        <span class="meta-sep">&middot;</span>
                        <span>${formatDate(m.created_at)}</span>
                        <span class="meta-sep">&middot;</span>
                        <span class="meeting-duration">${formatDuration(m.duration_seconds)}</span>
                    </span>
                </div>
                <div class="meeting-status status-${m.status}">
                    ${m.status === 'processing' ? '<span class="spinner-small"></span>' : '<span class="meeting-status-dot"></span>'}
                    <span>${escapeHtml(m.status)}</span>
                </div>
            </button>
        `).join('');
    } catch (err) {
        listEl.innerHTML = `<div class="error-state">Failed to load meetings: ${escapeHtml(err.message)}</div>`;
    }
}
