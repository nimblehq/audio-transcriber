function renderMeetingList(container) {
    container.innerHTML = `
        <div class="page-header">
            <h1>Meetings</h1>
            <button class="btn btn-primary" onclick="App.navigate('/upload')">Upload Recording</button>
        </div>
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
            <div class="meeting-row" onclick="App.navigate('/meetings/${m.id}')">
                <div class="meeting-info">
                    <span class="meeting-title">${escapeHtml(m.title)}</span>
                    <span class="meeting-meta">
                        <span class="badge badge-${m.type}">${m.type}</span>
                        <span>${formatDate(m.created_at)}</span>
                        <span>${formatDuration(m.duration_seconds)}</span>
                    </span>
                </div>
                <div class="meeting-status status-${m.status}">
                    ${m.status === 'processing' ? '<span class="spinner-small"></span>' : ''}
                    ${m.status}
                </div>
            </div>
        `).join('');
    } catch (err) {
        listEl.innerHTML = `<div class="error-state">Failed to load meetings: ${escapeHtml(err.message)}</div>`;
    }
}
