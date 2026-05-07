/* Overview tab: per-meeting energy/emotion trajectory + interaction summary. */

function renderOverviewTab(container, meeting) {
    const meta = meeting.metadata || meeting._meta || window._meetingMeta;
    const audioAnalysis = meeting.audio_analysis || window._meetingAudioAnalysis || null;
    const transcript = meeting.transcript || null;

    if (!meta || !meta.audio_analysis_enabled) {
        container.innerHTML = renderOptedOutEmptyState();
        return;
    }

    if (!audioAnalysis || audioAnalysis.status !== 'completed') {
        container.innerHTML = renderUnavailableState(audioAnalysis);
        return;
    }

    const trajectory = AudioInsights.buildEnergyTrajectory(audioAnalysis.emotions || []);
    const interruptions = summarizeInterruptions(audioAnalysis.interactions || [], meta);
    const latencies = summarizeLatencies(audioAnalysis.segment_interactions || [], transcript, meta);

    container.innerHTML = `
        <div class="overview-view">
            ${audioAnalysis.dominant_speaker_limitation ? `
                <div class="overview-notice">
                    Limited interaction data: a single speaker dominates this meeting, so interruption and turn-taking
                    signals are sparse.
                </div>
            ` : ''}

            <section class="overview-section">
                <h3 class="overview-heading">Energy &amp; emotion trajectory</h3>
                ${renderTrajectoryChart(trajectory)}
            </section>

            <section class="overview-section">
                <h3 class="overview-heading">Interruptions</h3>
                ${renderInterruptionSummary(interruptions)}
            </section>

            <section class="overview-section">
                <h3 class="overview-heading">Average response latency</h3>
                ${renderLatencyTable(latencies)}
            </section>
        </div>
    `;

    wireTrajectorySeek(container);
}

function renderOptedOutEmptyState() {
    return `
        <div class="overview-empty">
            <p>Audio analysis was not run for this meeting.</p>
            <p class="overview-empty-hint">
                To get emotion and interaction insights, opt in to audio analysis on the
                <a href="#/upload" onclick="App.navigate('/upload'); return false;">upload form</a>
                when uploading the recording.
            </p>
        </div>
    `;
}

function renderUnavailableState(audioAnalysis) {
    const reason = (audioAnalysis && audioAnalysis.reason) || 'audio analysis was not produced for this meeting';
    return `
        <div class="overview-empty">
            <p>Audio analysis is unavailable for this meeting.</p>
            <p class="overview-empty-hint">${escapeHtml(reason)}</p>
        </div>
    `;
}

function renderTrajectoryChart(trajectory) {
    const points = trajectory.filter(w => w.score !== null);
    if (points.length === 0) {
        return '<p class="overview-muted">No emotion data to chart.</p>';
    }

    const width = 720;
    const height = 160;
    const padX = 32;
    const padY = 20;
    const innerW = width - padX * 2;
    const innerH = height - padY * 2;

    const xFor = (i) => padX + (points.length === 1 ? innerW / 2 : (i / (points.length - 1)) * innerW);
    const yFor = (score) => padY + innerH / 2 - (score * (innerH / 2));

    const baselineY = padY + innerH / 2;
    const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${xFor(i).toFixed(1)} ${yFor(p.score).toFixed(1)}`).join(' ');

    const dots = points.map((p, i) => {
        const cx = xFor(i).toFixed(1);
        const cy = yFor(p.score).toFixed(1);
        const seekTo = p.start;
        const tooltip = `${formatWindow(p.start, p.end)} — energy ${p.score >= 0 ? '+' : ''}${p.score.toFixed(2)} (${p.count} segments)`;
        return `<circle class="trajectory-point" cx="${cx}" cy="${cy}" r="5" data-seek="${seekTo}" tabindex="0" role="button" aria-label="${escapeHtml(tooltip)}"><title>${escapeHtml(tooltip)}</title></circle>`;
    }).join('');

    const labels = points.map((p, i) => {
        const x = xFor(i).toFixed(1);
        return `<text class="trajectory-label" x="${x}" y="${height - 4}" text-anchor="middle">${formatStart(p.start)}</text>`;
    }).join('');

    return `
        <div class="trajectory-chart" id="trajectory-chart">
            <svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" role="img" aria-label="Energy and emotion trajectory across the meeting">
                <line class="trajectory-baseline" x1="${padX}" y1="${baselineY}" x2="${width - padX}" y2="${baselineY}"/>
                <path class="trajectory-line" d="${linePath}" fill="none"/>
                ${dots}
                ${labels}
            </svg>
            <div class="trajectory-legend">
                <span class="trajectory-legend-item"><span class="legend-swatch legend-positive"></span>Positive: engaged, confident</span>
                <span class="trajectory-legend-item"><span class="legend-swatch legend-negative"></span>Negative: disengaged, frustrated</span>
                <span class="trajectory-legend-item overview-muted">Click a point to seek</span>
            </div>
        </div>
    `;
}

function wireTrajectorySeek(container) {
    container.querySelectorAll('.trajectory-point').forEach(node => {
        const seekTo = parseFloat(node.dataset.seek);
        const handler = () => {
            if (!Number.isFinite(seekTo)) return;
            playFromSegment(seekTo);
        };
        node.addEventListener('click', handler);
        node.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                handler();
            }
        });
    });
}

function summarizeInterruptions(interactions, meta) {
    const speakers = (meta && meta.speakers) || {};
    const counts = {};
    interactions
        .filter(e => e.event_type === 'interruption')
        .forEach(e => {
            const key = `${e.speaker_b}|${e.speaker_a}`;
            counts[key] = (counts[key] || 0) + 1;
        });

    const pairs = Object.entries(counts).map(([key, count]) => {
        const [interrupter, interrupted] = key.split('|');
        const reverseKey = `${interrupted}|${interrupter}`;
        return {
            interrupter,
            interrupted,
            interrupterName: speakers[interrupter] || interrupter,
            interruptedName: speakers[interrupted] || interrupted,
            count,
            reverse: counts[reverseKey] || 0,
        };
    });
    pairs.sort((a, b) => b.count - a.count);
    return pairs;
}

function renderInterruptionSummary(pairs) {
    if (pairs.length === 0) {
        return '<p class="overview-muted">No interruptions detected.</p>';
    }
    return `
        <ul class="overview-list">
            ${pairs.map(p => `
                <li>
                    <strong>${escapeHtml(p.interrupterName)}</strong> interrupted
                    <strong>${escapeHtml(p.interruptedName)}</strong>
                    ${p.count} time${p.count === 1 ? '' : 's'}
                    <span class="overview-muted">(reverse: ${p.reverse})</span>
                </li>
            `).join('')}
        </ul>
    `;
}

function summarizeLatencies(segmentInteractions, transcript, meta) {
    if (!transcript || !transcript.segments) return [];
    const segmentsById = {};
    transcript.segments.forEach(s => { segmentsById[s.id] = s; });

    const speakers = (meta && meta.speakers) || {};
    const bySpeaker = {};
    segmentInteractions.forEach(si => {
        if (!(si.hesitation_before > 0)) return;
        const seg = segmentsById[si.segment_id];
        if (!seg) return;
        if (!bySpeaker[seg.speaker]) bySpeaker[seg.speaker] = [];
        bySpeaker[seg.speaker].push(si.hesitation_before);
    });

    return Object.entries(bySpeaker).map(([speakerId, vals]) => ({
        speakerId,
        name: speakers[speakerId] || speakerId,
        average: vals.reduce((a, b) => a + b, 0) / vals.length,
        count: vals.length,
    })).sort((a, b) => b.average - a.average);
}

function renderLatencyTable(latencies) {
    if (latencies.length === 0) {
        return '<p class="overview-muted">No measurable response latencies.</p>';
    }
    return `
        <ul class="overview-list">
            ${latencies.map(l => `
                <li>
                    <strong>${escapeHtml(l.name)}</strong>:
                    ${l.average.toFixed(1)}s
                    <span class="overview-muted">(${l.count} response${l.count === 1 ? '' : 's'})</span>
                </li>
            `).join('')}
        </ul>
    `;
}

function formatStart(seconds) {
    const m = Math.floor(seconds / 60);
    return `${String(m).padStart(2, '0')}:00`;
}

function formatWindow(start, end) {
    const fmt = (s) => {
        const m = Math.floor(s / 60);
        const sec = Math.floor(s % 60);
        return `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
    };
    return `${fmt(start)}–${fmt(end)}`;
}
