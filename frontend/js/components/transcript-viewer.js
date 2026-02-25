let currentAudio = null;
let pollInterval = null;
let autoScroll = true;

function renderTranscriptView(container, meetingId) {
    container.innerHTML = '<div class="loading">Loading meeting...</div>';
    loadMeetingView(container, meetingId);
}

async function loadMeetingView(container, meetingId) {
    try {
        const meeting = await API.getMeeting(meetingId);
        const meta = meeting.metadata;
        const transcript = meeting.transcript;

        const isProcessing = meta.status === 'processing';
        const isError = meta.status === 'error';

        container.innerHTML = `
            <div class="meeting-view">
                <div class="page-header">
                    <button class="btn btn-text" onclick="App.navigate('/')">← Back</button>
                    <h1 id="meeting-title">${escapeHtml(meta.title)}</h1>
                    <div class="header-actions">
                        <span class="badge badge-${meta.type}">${meta.type}</span>
                        <button class="btn btn-text btn-delete" onclick="handleDeleteMeeting('${meetingId}')">Delete</button>
                    </div>
                </div>

                ${isProcessing ? `<div id="progress-section" class="progress-section"></div>` : ''}
                ${isError ? `<div class="error-state">Transcription failed. <button class="btn btn-text" onclick="retryTranscription('${meetingId}')">Retry</button></div>` : ''}

                ${!isProcessing && !isError ? `
                    <div class="audio-player" id="audio-player">
                        <audio id="audio-element" preload="metadata"></audio>
                        <div class="player-controls">
                            <button class="btn btn-icon" id="skip-back" title="Back 15s">-15s</button>
                            <button class="btn btn-icon btn-play" id="play-pause" title="Play/Pause">▶</button>
                            <button class="btn btn-icon" id="skip-forward" title="Forward 15s">+15s</button>
                        </div>
                        <div class="player-seek">
                            <span id="current-time">0:00</span>
                            <input type="range" id="seek-bar" min="0" max="100" value="0" step="0.1">
                            <span id="total-time">${formatDuration(meta.duration_seconds)}</span>
                        </div>
                        <div class="player-speed">
                            <select id="speed-select">
                                <option value="0.5">0.5x</option>
                                <option value="1" selected>1x</option>
                                <option value="1.25">1.25x</option>
                                <option value="1.5">1.5x</option>
                                <option value="2">2x</option>
                            </select>
                        </div>
                    </div>

                    <div class="tabs">
                        <button class="tab tab-active" data-tab="transcript" onclick="switchTab('transcript', '${meetingId}', '${meta.type}')">Transcript</button>
                        <button class="tab" data-tab="analysis" onclick="switchTab('analysis', '${meetingId}', '${meta.type}')">Analysis</button>
                        <label class="auto-scroll-toggle">
                            <input type="checkbox" id="auto-scroll-check" ${autoScroll ? 'checked' : ''} onchange="autoScroll = this.checked">
                            Auto-scroll
                        </label>
                    </div>

                    <div id="transcript-tab" class="tab-content tab-content-active"></div>
                    <div id="analysis-tab" class="tab-content" hidden></div>
                ` : ''}
            </div>
        `;

        if (isProcessing && meta.job_id) {
            startPolling(meetingId, meta.job_id);
        }

        if (!isProcessing && !isError && transcript) {
            setupAudioPlayer(meetingId);
            renderSegments(document.getElementById('transcript-tab'), transcript, meta, meetingId);
        }
    } catch (err) {
        container.innerHTML = `<div class="error-state">Failed to load meeting: ${escapeHtml(err.message)}</div>`;
    }
}

function setupAudioPlayer(meetingId) {
    const audio = document.getElementById('audio-element');
    if (!audio) return;

    audio.src = API.audioUrl(meetingId);
    currentAudio = audio;

    const playPause = document.getElementById('play-pause');
    const seekBar = document.getElementById('seek-bar');
    const currentTimeEl = document.getElementById('current-time');
    const speedSelect = document.getElementById('speed-select');

    playPause.addEventListener('click', () => {
        if (audio.paused) {
            audio.play();
            playPause.textContent = '⏸';
        } else {
            audio.pause();
            playPause.textContent = '▶';
        }
    });

    document.getElementById('skip-back').addEventListener('click', () => {
        audio.currentTime = Math.max(0, audio.currentTime - 15);
    });

    document.getElementById('skip-forward').addEventListener('click', () => {
        audio.currentTime = Math.min(audio.duration || 0, audio.currentTime + 15);
    });

    audio.addEventListener('timeupdate', () => {
        if (audio.duration) {
            seekBar.value = (audio.currentTime / audio.duration) * 100;
            currentTimeEl.textContent = formatDuration(audio.currentTime);
            highlightCurrentSegment(audio.currentTime);
        }
    });

    audio.addEventListener('ended', () => {
        playPause.textContent = '▶';
    });

    seekBar.addEventListener('input', () => {
        if (audio.duration) {
            audio.currentTime = (seekBar.value / 100) * audio.duration;
        }
    });

    speedSelect.addEventListener('change', () => {
        audio.playbackRate = parseFloat(speedSelect.value);
    });
}

function renderSegments(container, transcript, meta, meetingId) {
    const speakers = { ...meta.speakers };
    const speakerIds = [...new Set(transcript.segments.map(s => s.speaker))];
    const speakerColorMap = {};
    speakerIds.forEach((id, i) => { speakerColorMap[id] = getSpeakerColor(i); });

    // Store speakers data globally so onclick handlers can reference it without inline JSON
    window._speakerEditorState = { speakers, meetingId };

    container.innerHTML = `
        <div class="segments" id="segments-container">
            ${transcript.segments.map((seg, i) => {
                const speakerName = speakers[seg.speaker] || seg.speaker;
                const color = speakerColorMap[seg.speaker];
                return `
                    <div class="segment" id="seg-${i}" data-start="${seg.start}" data-end="${seg.end}">
                        <div class="segment-header">
                            <span class="segment-time">${formatTimestamp(seg.start)}</span>
                            <span class="speaker-label" style="background-color: ${color}" data-speaker="${seg.speaker}"
                                onclick="handleSpeakerClick(this, '${seg.speaker}', '${seg.id}')">
                                ${escapeHtml(speakerName)} ▾
                            </span>
                            <button class="btn btn-icon btn-segment-play" onclick="playFromSegment(${seg.start})" title="Play from here">▶</button>
                        </div>
                        <div class="segment-text">${escapeHtml(seg.text)}</div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

function handleSpeakerClick(element, speakerId, segmentId) {
    const state = window._speakerEditorState;
    const speakerName = state.speakers[speakerId] || speakerId;
    openSpeakerEditor(
        element.closest('.segment'),
        speakerId,
        speakerName,
        state.meetingId,
        { ...state.speakers },
        () => App.navigate('/meetings/' + state.meetingId),
        segmentId
    );
}

function playFromSegment(startTime) {
    if (!currentAudio) return;
    currentAudio.currentTime = startTime;
    currentAudio.play();
    const playPause = document.getElementById('play-pause');
    if (playPause) playPause.textContent = '⏸';
}

function highlightCurrentSegment(currentTime) {
    const segments = document.querySelectorAll('.segment');
    let activeSegment = null;

    segments.forEach(seg => {
        const start = parseFloat(seg.dataset.start);
        const end = parseFloat(seg.dataset.end);
        if (currentTime >= start && currentTime < end) {
            seg.classList.add('segment-active');
            activeSegment = seg;
        } else {
            seg.classList.remove('segment-active');
        }
    });

    if (activeSegment && autoScroll) {
        activeSegment.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

function switchTab(tabName, meetingId, meetingType) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('tab-active'));
    document.querySelectorAll('.tab-content').forEach(t => { t.hidden = true; t.classList.remove('tab-content-active'); });

    document.querySelector(`[data-tab="${tabName}"]`).classList.add('tab-active');
    const tabEl = document.getElementById(`${tabName}-tab`);
    tabEl.hidden = false;
    tabEl.classList.add('tab-content-active');

    if (tabName === 'analysis' && !tabEl.dataset.loaded) {
        tabEl.dataset.loaded = 'true';
        renderAnalysisTab(tabEl, meetingId, meetingType);
    }
}

function startPolling(meetingId, jobId) {
    updateProgress(meetingId, jobId);
    pollInterval = setInterval(() => updateProgress(meetingId, jobId), 3000);
}

async function updateProgress(meetingId, jobId) {
    try {
        const job = await API.getJob(jobId);
        const section = document.getElementById('progress-section');
        if (!section) return;

        if (job.status === 'completed') {
            clearInterval(pollInterval);
            App.navigate(`/meetings/${meetingId}`);
            return;
        }

        if (job.status === 'failed') {
            clearInterval(pollInterval);
            section.innerHTML = `
                <div class="error-state">
                    Transcription failed: ${escapeHtml(job.error || 'Unknown error')}
                </div>
            `;
            return;
        }

        const stageLabels = {
            uploading: 'Uploading...',
            transcribing: 'Transcribing audio...',
            aligning: 'Aligning timestamps...',
            diarizing: 'Identifying speakers...',
            saving: 'Saving results...',
        };

        section.innerHTML = `
            <div class="progress-info">
                <div class="progress-bar-container">
                    <div class="progress-bar" style="width: ${job.progress}%"></div>
                </div>
                <span class="progress-label">${stageLabels[job.stage] || 'Processing...'} ${job.progress}%</span>
            </div>
        `;
    } catch {
        // Silently continue polling
    }
}

async function retryTranscription(meetingId) {
    try {
        await API.retryTranscription(meetingId);
        showToast('Retrying transcription...');
        App.navigate(`/meetings/${meetingId}`);
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function handleDeleteMeeting(meetingId) {
    if (!confirm('Delete this meeting and all its files?')) return;
    try {
        await API.deleteMeeting(meetingId);
        showToast('Meeting deleted');
        App.navigate('/');
    } catch (err) {
        showToast('Failed to delete meeting', 'error');
    }
}

function cleanupTranscriptView() {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
    if (currentAudio) {
        currentAudio.pause();
        currentAudio = null;
    }
    closeSpeakerPopover();
}
