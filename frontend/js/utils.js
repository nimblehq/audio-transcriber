function formatDuration(seconds) {
    if (!seconds) return '--:--';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
    return `${m}:${String(s).padStart(2, '0')}`;
}

function formatTimestamp(seconds) {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

function formatDate(dateStr) {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

// Single source of truth for language code -> display name. The upload form
// builds its expected-language options from this map, and the transcript view
// renders per-segment language badges from it. Insertion order is the order
// shown in the upload dropdown (English/Thai first as the primary use case).
const LANGUAGE_NAMES = {
    en: 'English',
    th: 'Thai',
    fr: 'French',
    de: 'German',
    es: 'Spanish',
    it: 'Italian',
    pt: 'Portuguese',
    nl: 'Dutch',
    ja: 'Japanese',
    zh: 'Chinese',
    ko: 'Korean',
    ru: 'Russian',
    ar: 'Arabic',
    hi: 'Hindi',
    tr: 'Turkish',
    pl: 'Polish',
    vi: 'Vietnamese',
    id: 'Indonesian',
};

// Returns a human-readable language name for a code. Unknown but non-empty
// codes degrade to the uppercased code (e.g. "el" -> "EL"); empty/missing
// codes return '' so callers can omit the badge entirely.
function formatLanguageName(code) {
    if (!code) return '';
    return LANGUAGE_NAMES[code] || code.toUpperCase();
}

function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.classList.add('toast-visible'), 10);
    setTimeout(() => {
        toast.classList.remove('toast-visible');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

const SPEAKER_COLORS = [
    '#4A90D9', '#D94A4A', '#4AD97A', '#D9A84A',
    '#9B4AD9', '#4AD9D9', '#D94A9B', '#7AD94A',
];

function getSpeakerColor(index) {
    return SPEAKER_COLORS[index % SPEAKER_COLORS.length];
}

function isUnidentifiedSpeaker(name) {
    if (!name) return true;
    return name === 'UNKNOWN' || /^SPEAKER_\d+$/.test(name);
}

// Reads `window._speakerEditorState`, populated by `renderSegments()` in
// transcript-viewer.js when the meeting loads. If that contract changes,
// update this read site.
function getUnnamedSpeakersInfo() {
    const state = window._speakerEditorState;
    if (!state || !state.speakerIds || !state.speakers) return null;
    const total = state.speakerIds.length;
    const unnamed = state.speakerIds.filter(id =>
        isUnidentifiedSpeaker(state.speakers[id] || id)
    ).length;
    return { unnamed, total };
}

function renderUnnamedSpeakersWarning() {
    const info = getUnnamedSpeakersInfo();
    if (!info || info.unnamed === 0) return '';
    const { unnamed, total } = info;
    const verb = unnamed === 1 ? 'is' : 'are';
    const noun = unnamed === 1 ? 'speaker' : 'speakers';
    return `
        <div class="unnamed-speakers-warning" role="alert">
            <span class="unnamed-speakers-warning-icon" aria-hidden="true">⚠</span>
            <div class="unnamed-speakers-warning-body">
                <strong>${unnamed} of ${total} ${noun} ${verb} still unnamed.</strong>
                Rename them on the Transcript tab — copied text will use raw labels like <code>SPEAKER_00</code> until you do.
            </div>
        </div>
    `;
}

function getRecentSpeakerNames() {
    try {
        return JSON.parse(localStorage.getItem('recentSpeakerNames') || '[]');
    } catch {
        return [];
    }
}

function addRecentSpeakerName(name) {
    if (!name.trim()) return;
    let names = getRecentSpeakerNames();
    names = names.filter(n => n !== name);
    names.unshift(name);
    names = names.slice(0, 10);
    localStorage.setItem('recentSpeakerNames', JSON.stringify(names));
}

function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(() => {
            showToast('Copied to clipboard');
        }).catch(() => {
            fallbackCopy(text);
        });
    } else {
        fallbackCopy(text);
    }
}

function fallbackCopy(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    try {
        document.execCommand('copy');
        showToast('Copied to clipboard');
    } catch {
        showToast('Failed to copy', 'error');
    }
    document.body.removeChild(textarea);
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

/* Browser Notifications */

function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
}

function sendNotification(title, options = {}) {
    if (!('Notification' in window) || Notification.permission !== 'granted') return;
    if (document.visibilityState === 'visible') return;

    const notification = new Notification(title, options);
    notification.addEventListener('click', () => {
        window.focus();
        if (options.url) App.navigate(options.url);
        notification.close();
    });
}
