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
            <div class="form-group">
                <label>Expected languages</label>
                <p class="form-hint">Leave all unchecked to auto-detect a single language. Select two or more for a mixed-language meeting — each passage is transcribed in the language detected for it.</p>
                <div class="language-options" id="language-options">
                    <label class="language-option"><input type="checkbox" value="en"> English</label>
                    <label class="language-option"><input type="checkbox" value="fr"> French</label>
                    <label class="language-option"><input type="checkbox" value="de"> German</label>
                    <label class="language-option"><input type="checkbox" value="es"> Spanish</label>
                    <label class="language-option"><input type="checkbox" value="it"> Italian</label>
                    <label class="language-option"><input type="checkbox" value="pt"> Portuguese</label>
                    <label class="language-option"><input type="checkbox" value="nl"> Dutch</label>
                    <label class="language-option"><input type="checkbox" value="ja"> Japanese</label>
                    <label class="language-option"><input type="checkbox" value="zh"> Chinese</label>
                    <label class="language-option"><input type="checkbox" value="ko"> Korean</label>
                    <label class="language-option"><input type="checkbox" value="ru"> Russian</label>
                    <label class="language-option"><input type="checkbox" value="th"> Thai</label>
                    <label class="language-option"><input type="checkbox" value="ar"> Arabic</label>
                    <label class="language-option"><input type="checkbox" value="hi"> Hindi</label>
                    <label class="language-option"><input type="checkbox" value="tr"> Turkish</label>
                    <label class="language-option"><input type="checkbox" value="pl"> Polish</label>
                    <label class="language-option"><input type="checkbox" value="vi"> Vietnamese</label>
                    <label class="language-option"><input type="checkbox" value="id"> Indonesian</label>
                </div>
            </div>
            <div class="form-group">
                <label for="speakers-input">Number of Speakers</label>
                <input type="text" id="speakers-input" placeholder="Auto" value="">
            </div>
            <div class="form-group">
                <label for="context-input">Context</label>
                <textarea id="context-input" rows="3" placeholder="What is this meeting about? Any important context for analysis..."></textarea>
            </div>
            <div class="form-group form-checkbox">
                <label>
                    <input type="checkbox" id="preprocess-checkbox" checked>
                    Audio preprocessing
                    <span class="form-hint">High-pass filter, noise reduction, and loudness normalization</span>
                </label>
            </div>
            <div class="form-group form-checkbox">
                <label>
                    <input type="checkbox" id="audio-analysis-checkbox">
                    Audio emotional analysis
                </label>
                <div class="form-disclosure">
                    <p class="form-disclosure-heading">What you get</p>
                    <ul>
                        <li>Per-speaker emotion classification</li>
                        <li>Prosody signals (volume, pitch, pace)</li>
                        <li>Interaction dynamics (interruptions, hesitations)</li>
                        <li>Word-tone mismatches that hint at hidden disagreement</li>
                    </ul>
                    <p class="form-disclosure-cost">
                        Adds 8–17 minutes to a 1-hour meeting (roughly +50% processing time).
                    </p>
                    <p class="form-disclosure-note">
                        Currently optimized for English. Results may be less reliable for other languages,
                        and analysis is skipped entirely when the detected language isn't supported.
                    </p>
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
        const expectedLanguages = Array.from(
            document.querySelectorAll('#language-options input[type="checkbox"]:checked')
        ).map(cb => cb.value);
        const numSpeakers = document.getElementById('speakers-input').value.trim() || 'auto';
        const preprocessAudio = document.getElementById('preprocess-checkbox').checked;
        const audioAnalysisEnabled = document.getElementById('audio-analysis-checkbox').checked;
        const context = document.getElementById('context-input').value.trim();
        requestNotificationPermission();
        const result = await API.createMeeting(selectedFile, title, type, expectedLanguages, numSpeakers, preprocessAudio, context, audioAnalysisEnabled);
        App.navigate(`/meetings/${result.meeting_id}`);
    } catch (err) {
        showToast(err.message, 'error');
        btn.disabled = false;
        btn.textContent = 'Upload & Transcribe';
    }
}
