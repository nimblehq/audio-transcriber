/* "What's new" changelog panel.
 *
 * On first load after the running version changes, surfaces the changes between
 * the user's last-seen version and the current one. The current version is the
 * latest released heading in CHANGELOG.md (served by GET /api/changelog). A
 * clickable version label in the footer reopens the panel on demand. See #155.
 */

const LAST_SEEN_VERSION_KEY = 'lastSeenVersion';

// Keep a Changelog section order; unknown sections fall to the end alphabetically.
const SECTION_ORDER = ['Added', 'Changed', 'Deprecated', 'Removed', 'Fixed', 'Security'];

/* Numeric semver compare. Returns >0 if a>b, <0 if a<b, 0 if equal.
 * Non-numeric or missing parts sort as 0, so odd values never throw. */
function compareSemver(a, b) {
    const parse = (v) => String(v || '').split('.').map((n) => parseInt(n, 10) || 0);
    const pa = parse(a);
    const pb = parse(b);
    const len = Math.max(pa.length, pb.length);
    for (let i = 0; i < len; i++) {
        const diff = (pa[i] || 0) - (pb[i] || 0);
        if (diff !== 0) return diff;
    }
    return 0;
}

function orderedSections(sections) {
    const names = Object.keys(sections || {});
    names.sort((a, b) => {
        const ia = SECTION_ORDER.indexOf(a);
        const ib = SECTION_ORDER.indexOf(b);
        if (ia !== -1 && ib !== -1) return ia - ib;
        if (ia !== -1) return -1;
        if (ib !== -1) return 1;
        return a.localeCompare(b);
    });
    return names;
}

function renderEntry(entry) {
    const date = entry.date ? `<span class="whats-new-date">${escapeHtml(entry.date)}</span>` : '';
    const sections = orderedSections(entry.sections).map((name) => {
        const items = (entry.sections[name] || [])
            .map((text) => `<li>${escapeHtml(text)}</li>`)
            .join('');
        return `
            <div class="whats-new-section">
                <h4 class="whats-new-section-title">${escapeHtml(name)}</h4>
                <ul>${items}</ul>
            </div>`;
    }).join('');
    return `
        <section class="whats-new-entry">
            <h3 class="whats-new-version">${escapeHtml(entry.version)}${date}</h3>
            ${sections}
        </section>`;
}

function closeWhatsNew() {
    const overlay = document.getElementById('whats-new-overlay');
    if (overlay) overlay.remove();
    document.removeEventListener('keydown', onWhatsNewKeydown);
}

function onWhatsNewKeydown(e) {
    if (e.key === 'Escape') closeWhatsNew();
}

function renderWhatsNewModal(entries, { heading } = {}) {
    if (!entries || entries.length === 0) return;
    closeWhatsNew();

    const overlay = document.createElement('div');
    overlay.id = 'whats-new-overlay';
    overlay.className = 'whats-new-overlay';
    overlay.innerHTML = `
        <div class="whats-new-modal" role="dialog" aria-modal="true" aria-label="What's new">
            <div class="whats-new-header">
                <h2>${escapeHtml(heading || "What's new")}</h2>
                <button type="button" class="whats-new-close" aria-label="Close">&times;</button>
            </div>
            <div class="whats-new-body">${entries.map(renderEntry).join('')}</div>
        </div>`;

    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) closeWhatsNew();
    });
    overlay.querySelector('.whats-new-close').addEventListener('click', closeWhatsNew);
    document.addEventListener('keydown', onWhatsNewKeydown);
    document.body.appendChild(overlay);
}

function setVersionLabel(version) {
    const footer = document.getElementById('app-footer');
    const label = document.getElementById('version-label');
    if (!footer || !label || !version) return;
    label.textContent = `v${version}`;
    label.onclick = showWhatsNew;
    footer.hidden = false;
}

/* Fetch the changelog, swallowing any error so app startup is never blocked. */
async function fetchChangelog() {
    try {
        const data = await API.getChangelog();
        if (!data || !data.current_version || !Array.isArray(data.entries)) return null;
        return data;
    } catch (e) {
        return null;
    }
}

/* Run on load: show the panel only when the running version advanced past the
 * user's last-seen version. First-ever load is silent (baseline is stored). */
async function checkWhatsNew() {
    const data = await fetchChangelog();
    if (!data) return;

    setVersionLabel(data.current_version);

    const lastSeen = localStorage.getItem(LAST_SEEN_VERSION_KEY);
    localStorage.setItem(LAST_SEEN_VERSION_KEY, data.current_version);

    // First run, or a downgrade / unknown last-seen: store baseline, show nothing.
    if (!lastSeen || compareSemver(lastSeen, data.current_version) >= 0) return;

    const newEntries = data.entries.filter((e) => compareSemver(e.version, lastSeen) > 0);
    renderWhatsNewModal(newEntries, { heading: "What's new" });
}

/* Manual reopen from the footer version label: show the full history. */
async function showWhatsNew() {
    const data = await fetchChangelog();
    if (!data) {
        showToast('No changelog available', 'error');
        return;
    }
    localStorage.setItem(LAST_SEEN_VERSION_KEY, data.current_version);
    renderWhatsNewModal(data.entries, { heading: "What's new" });
}
