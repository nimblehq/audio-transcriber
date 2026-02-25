let activePopover = null;

function openSpeakerEditor(segmentEl, speakerId, currentName, meetingId, speakers, onSave) {
    closeSpeakerPopover();

    const popover = document.createElement('div');
    popover.className = 'speaker-popover';

    const recentNames = getRecentSpeakerNames().filter(n => n !== currentName);

    popover.innerHTML = `
        <div class="popover-content">
            <input type="text" class="popover-input" value="${escapeHtml(currentName)}" placeholder="Speaker name">
            ${recentNames.length > 0 ? `
                <div class="recent-names">
                    ${recentNames.map(n => `<span class="name-chip" data-name="${escapeHtml(n)}">${escapeHtml(n)}</span>`).join('')}
                </div>
            ` : ''}
            <div class="popover-options">
                <label class="radio-label">
                    <input type="radio" name="apply-scope" value="single"> This segment only
                </label>
                <label class="radio-label">
                    <input type="radio" name="apply-scope" value="all" checked> All segments from this speaker
                </label>
            </div>
            <div class="popover-actions">
                <button class="btn btn-text popover-cancel">Cancel</button>
                <button class="btn btn-primary popover-save">Save</button>
            </div>
        </div>
    `;

    segmentEl.style.position = 'relative';
    segmentEl.appendChild(popover);
    activePopover = popover;

    const input = popover.querySelector('.popover-input');
    input.focus();
    input.select();

    // Name chip clicks
    popover.querySelectorAll('.name-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            input.value = chip.dataset.name;
            input.focus();
        });
    });

    // Cancel
    popover.querySelector('.popover-cancel').addEventListener('click', closeSpeakerPopover);

    // Save
    popover.querySelector('.popover-save').addEventListener('click', async () => {
        const newName = input.value.trim();
        if (!newName) return;

        const scope = popover.querySelector('input[name="apply-scope"]:checked').value;

        if (scope === 'all') {
            speakers[speakerId] = newName;
        } else {
            // For single segment, we don't change the speaker map
            // The segment-only rename is handled differently (not in MVP scope for simplicity)
            speakers[speakerId] = newName;
        }

        try {
            await API.updateMeeting(meetingId, { speakers });
            addRecentSpeakerName(newName);
            closeSpeakerPopover();
            showToast('Speaker name updated');
            if (onSave) onSave();
        } catch (err) {
            showToast('Failed to update speaker name', 'error');
        }
    });

    // Enter to save
    input.addEventListener('keydown', e => {
        if (e.key === 'Enter') popover.querySelector('.popover-save').click();
        if (e.key === 'Escape') closeSpeakerPopover();
    });

    // Close on outside click
    setTimeout(() => {
        document.addEventListener('click', handleOutsideClick);
    }, 0);
}

function handleOutsideClick(e) {
    if (activePopover && !activePopover.contains(e.target) && !e.target.classList.contains('speaker-label')) {
        closeSpeakerPopover();
    }
}

function closeSpeakerPopover() {
    if (activePopover) {
        activePopover.remove();
        activePopover = null;
    }
    document.removeEventListener('click', handleOutsideClick);
}
