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

    const polarityClass = (score) => {
        if (score > 0.05) return 'trajectory-point-positive';
        if (score < -0.05) return 'trajectory-point-negative';
        return 'trajectory-point-neutral';
    };

    const dots = points.map((p, i) => {
        const cx = xFor(i).toFixed(1);
        const cy = yFor(p.score).toFixed(1);
        const seekTo = p.start;
        const tooltip = `${formatWindow(p.start, p.end)} — energy ${p.score >= 0 ? '+' : ''}${p.score.toFixed(2)} (${p.count} segments)`;
        return `<circle class="trajectory-point ${polarityClass(p.score)}" cx="${cx}" cy="${cy}" r="5" data-seek="${seekTo}" tabindex="0" role="button" aria-label="${escapeHtml(tooltip)}"><title>${escapeHtml(tooltip)}</title></circle>`;
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
                <span class="trajectory-legend-item"><span class="legend-swatch legend-neutral"></span>Neutral</span>
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
    const pairCounts = {};
    const made = {};
    const received = {};
    let total = 0;

    interactions
        .filter(e => e.event_type === 'interruption')
        .forEach(e => {
            const key = `${e.speaker_b}|${e.speaker_a}`;
            pairCounts[key] = (pairCounts[key] || 0) + 1;
            made[e.speaker_b] = (made[e.speaker_b] || 0) + 1;
            received[e.speaker_a] = (received[e.speaker_a] || 0) + 1;
            total += 1;
        });

    const speakerIds = new Set([...Object.keys(made), ...Object.keys(received)]);
    const totals = [...speakerIds].map(id => ({
        speakerId: id,
        name: speakers[id] || id,
        made: made[id] || 0,
        received: received[id] || 0,
    }));
    totals.sort((a, b) => (b.made + b.received) - (a.made + a.received));

    const pairs = Object.entries(pairCounts).map(([key, count]) => {
        const [interrupter, interrupted] = key.split('|');
        return {
            interrupter,
            interrupted,
            interrupterName: speakers[interrupter] || interrupter,
            interruptedName: speakers[interrupted] || interrupted,
            count,
        };
    });
    pairs.sort((a, b) => b.count - a.count);

    return { total, totals, pairs };
}

function renderInterruptionSummary({ total, totals, pairs }) {
    if (total === 0) {
        return '<p class="overview-muted">No interruptions detected.</p>';
    }

    const totalsRows = totals.map(t => `
        <tr>
            <td>${escapeHtml(t.name)}</td>
            <td class="overview-num">${t.made}</td>
            <td class="overview-num">${t.received}</td>
        </tr>
    `).join('');

    const pairLines = pairs.slice(0, 6).map(p => `
        <li>
            <strong>${escapeHtml(p.interrupterName)}</strong>
            <span class="overview-muted"> → </span>
            <strong>${escapeHtml(p.interruptedName)}</strong>
            <span class="overview-muted">: ${p.count} time${p.count === 1 ? '' : 's'}</span>
        </li>
    `).join('');

    const more = pairs.length > 6 ? `<li class="overview-muted">+${pairs.length - 6} more pair${pairs.length - 6 === 1 ? '' : 's'}</li>` : '';

    return `
        <p class="overview-muted">${total} interruption${total === 1 ? '' : 's'} total</p>
        <table class="overview-table">
            <thead>
                <tr>
                    <th>Speaker</th>
                    <th class="overview-num">Interruptions made</th>
                    <th class="overview-num">Times interrupted</th>
                </tr>
            </thead>
            <tbody>
                ${totalsRows}
            </tbody>
        </table>
        <details class="overview-details">
            <summary>Who interrupted whom (top pairs)</summary>
            <ul class="overview-list overview-list-compact">
                ${pairLines}
                ${more}
            </ul>
        </details>
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
