function renderUpload(container) {
    container.innerHTML = `
        <div class="page-header">
            <button class="btn btn-text" onclick="App.navigate('/')">← Back</button>
            <h1>Upload Recording</h1>
        </div>
        <form id="upload-form" class="upload-form">
            <div id="drop-zone" class="drop-zone">
                <div class="drop-zone-content">
                    <div class="drop-zone-icon">🎙</div>
                    <p>Drag & drop an audio file here</p>
                    <p class="drop-zone-hint">or click to select a file</p>
                    <p class="drop-zone-formats">mp3, mp4, m4a, wav, webm</p>
                </div>
                <input type="file" id="file-input" accept=".mp3,.mp4,.m4a,.wav,.webm" hidden>
            </div>
            <div id="file-info" class="file-info" hidden>
                <span id="file-name"></span>
                <button type="button" class="btn btn-text" onclick="clearFile()">Remove</button>
            </div>
            <div class="form-group">
                <label for="title-input">Title</label>
                <input type="text" id="title-input" placeholder="Optional — defaults to filename">
            </div>
            <div class="form-group">
                <label for="type-select">Meeting Type</label>
                <select id="type-select">
                    <option value="interview">Interview</option>
                    <option value="sales">Sales</option>
                    <option value="client">Client</option>
                    <option value="other" selected>Other</option>
                </select>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label for="language-select">Language</label>
                    <select id="language-select">
                        <option value="auto" selected>Auto-detect</option>
                        <option value="en">English</option>
                        <option value="fr">French</option>
                        <option value="de">German</option>
                        <option value="es">Spanish</option>
                        <option value="it">Italian</option>
                        <option value="pt">Portuguese</option>
                        <option value="nl">Dutch</option>
                        <option value="ja">Japanese</option>
                        <option value="zh">Chinese</option>
                        <option value="ko">Korean</option>
                        <option value="ru">Russian</option>
                        <option value="th">Thai</option>
                        <option value="ar">Arabic</option>
                        <option value="hi">Hindi</option>
                        <option value="tr">Turkish</option>
                        <option value="pl">Polish</option>
                        <option value="vi">Vietnamese</option>
                        <option value="id">Indonesian</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="speakers-input">Number of Speakers</label>
                    <input type="text" id="speakers-input" placeholder="Auto" value="">
                </div>
            </div>
            <button type="submit" id="upload-btn" class="btn btn-primary btn-large" disabled>
                Upload & Transcribe
            </button>
        </form>
    `;

    setupUploadHandlers();
}

let selectedFile = null;

function setupUploadHandlers() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const form = document.getElementById('upload-form');

    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', e => {
        e.preventDefault();
        dropZone.classList.add('drop-zone-active');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('drop-zone-active');
    });

    dropZone.addEventListener('drop', e => {
        e.preventDefault();
        dropZone.classList.remove('drop-zone-active');
        if (e.dataTransfer.files.length > 0) {
            setFile(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            setFile(fileInput.files[0]);
        }
    });

    form.addEventListener('submit', handleUpload);
}

function setFile(file) {
    selectedFile = file;
    document.getElementById('drop-zone').hidden = true;
    document.getElementById('file-info').hidden = false;
    document.getElementById('file-name').textContent = file.name;
    document.getElementById('upload-btn').disabled = false;

    // Default title to filename without extension
    const titleInput = document.getElementById('title-input');
    if (!titleInput.value) {
        titleInput.value = file.name.replace(/\.[^.]+$/, '');
    }
}

function clearFile() {
    selectedFile = null;
    document.getElementById('drop-zone').hidden = false;
    document.getElementById('file-info').hidden = true;
    document.getElementById('upload-btn').disabled = true;
    document.getElementById('file-input').value = '';
}

async function handleUpload(e) {
    e.preventDefault();
    if (!selectedFile) return;

    const btn = document.getElementById('upload-btn');
    btn.disabled = true;
    btn.textContent = 'Uploading...';

    try {
        const title = document.getElementById('title-input').value;
        const type = document.getElementById('type-select').value;
        const language = document.getElementById('language-select').value;
        const numSpeakers = document.getElementById('speakers-input').value.trim() || 'auto';
        const result = await API.createMeeting(selectedFile, title, type, language, numSpeakers);
        requestNotificationPermission();
        App.navigate(`/meetings/${result.meeting_id}`);
    } catch (err) {
        showToast(err.message, 'error');
        btn.disabled = false;
        btn.textContent = 'Upload & Transcribe';
    }
}
