# Meeting Transcriber — Product Requirements Document

## Overview

A local-first web application for transcribing meeting recordings with speaker diarization, labeling speakers, and generating AI-powered analyses. Designed for small teams who want to extract actionable insights from interviews, sales calls, and client meetings.


## Goals

1. **Replace manual meeting notes** — Upload a recording, get a searchable transcript with speaker labels
2. **Make speaker labeling effortless** — Plaud-style inline editing with bulk apply
3. **Generate actionable outputs** — Structured analyses tailored to meeting type (interview, sales, client)
4. **Keep it local** — All processing on the user's machine, no cloud dependencies (except Claude API for analysis)


## User Workflow

```
1. Upload audio file
2. Wait for transcription (~15-20 min for 1.5h meeting)
3. Label speakers (Plaud-style UI)
4. Select meeting type and generate analysis
5. Review/export transcript and analysis
```


## Technical Architecture

### Stack

- **Backend:** Python 3.12, FastAPI
- **Frontend:** Vanilla HTML/CSS/JS (keep it simple, no build step)
- **Transcription:** WhisperX with pyannote diarization
- **Analysis:** Claude API (model configurable via env var)
- **Storage:** Local filesystem (no database)

### Directory Structure

```
meeting-transcriber/
├── backend/
│   ├── main.py                 # FastAPI app, serves frontend
│   ├── routers/
│   │   ├── meetings.py         # CRUD for meetings
│   │   ├── jobs.py             # transcription job management
│   │   └── analysis.py         # analysis generation
│   ├── services/
│   │   ├── transcriber.py      # WhisperX wrapper
│   │   ├── analyzer.py         # Claude API integration
│   │   └── job_queue.py        # simple in-memory job queue
│   └── schemas.py              # Pydantic models
│
├── frontend/
│   ├── index.html              # SPA shell
│   ├── css/
│   │   └── styles.css
│   └── js/
│       ├── app.js              # main app logic, routing
│       ├── api.js              # backend API calls
│       ├── components/
│       │   ├── meeting-list.js
│       │   ├── upload.js
│       │   ├── transcript-viewer.js
│       │   ├── speaker-editor.js
│       │   └── analysis-viewer.js
│       └── utils.js
│
├── data/
│   └── meetings/               # one folder per meeting, contains all files
│       └── {meeting_id}/
│           ├── metadata.json
│           ├── audio.mp3       # original upload (keeps original extension)
│           ├── transcript.json
│           └── analysis.md
│
├── templates/                  # analysis prompt templates
│   ├── interview.md
│   ├── sales.md
│   ├── client.md
│   └── other.md
│
├── config.py                   # environment/config management
├── run.py                      # entry point
├── Makefile                    # setup and run commands
└── requirements.txt
```

### Data Storage

No database. All data stored as files:

**Meeting metadata:** `data/meetings/{meeting_id}/metadata.json`
```json
{
  "id": "uuid",
  "title": "Interview - Jane Doe - Senior PM",
  "type": "interview",
  "created_at": "2025-02-25T10:30:00Z",
  "duration_seconds": 5400,
  "audio_filename": "recording.mp3",
  "status": "ready",
  "job_id": "job_uuid",
  "speakers": {
    "SPEAKER_00": "Julien",
    "SPEAKER_01": "Jane Doe"
  }
}
```

**Transcript:** `data/meetings/{meeting_id}/transcript.json`
```json
{
  "segments": [
    {
      "id": "seg_001",
      "start": 0.0,
      "end": 15.5,
      "speaker": "SPEAKER_00",
      "text": "The very first thing I'd like to know is..."
    }
  ],
  "language": "en"
}
```

**Audio:** `data/meetings/{meeting_id}/{original_filename}` (preserves original extension)

**Analysis:** `data/meetings/{meeting_id}/analysis.md`


## Screens & Components

### 1. Meeting List (Home)

**Route:** `/`

**Features:**
- List of all meetings, sorted by date (newest first)
- Each row shows: title, type badge, date, duration, status
- Status indicators: "Processing" (with progress), "Ready", "Error"
- Click row → navigate to transcript view
- Upload button → navigate to upload screen

**Empty state:** "No meetings yet. Upload your first recording."


### 2. Upload Screen

**Route:** `/upload`

**Features:**
- Drag-and-drop zone for audio files
- Accepted formats: mp3, mp4, m4a, wav, webm
- Form fields:
  - Title (optional, defaults to filename)
  - Meeting type: dropdown (Interview / Sales / Client / Other)
- Upload button → starts upload and transcription job
- On submit → redirect to transcript view with processing state


### 3. Transcript View

**Route:** `/meetings/{id}`

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  ← Back    Interview - Jane Doe - Senior PM      [Edit] │
├─────────────────────────────────────────────────────────┤
│  [▶ Play]   advancement bar───────────  00:12 / 1:30:00 │
│            [-15s] [Play/Pause] [+15s]        [1x speed] │
├─────────────────────────────────────────────────────────┤
│  [Transcript]  [Analysis]                               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  00:00:00  [Julien ▼] [▶]                               │
│  The very first thing I'd like to know is, so far      │
│  with everything that you've seen, heard, maybe        │
│  researched, can you tell me what is your              │
│  understanding of Nimble and what we do?               │
│                                                         │
│  00:00:31  [Jane Doe ▼] [▶]                             │
│  Oh, Nimble, ah, yeah, I walked through the Nimble     │
│  website. It's about consulting firms, consulting      │
│  business, and focus on the client...                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Audio Player:**
- Global audio player at top
- Play/pause, seek bar, current time / duration
- Skip ±15 seconds buttons
- Playback speed control (0.5x, 1x, 1.25x, 1.5x, 2x)

**Transcript Segments:**
- Each segment shows: timestamp, speaker label, play button, text
- Clicking segment play button → seeks audio to that timestamp and plays
- Current segment highlighted during playback
- Auto-scroll to current segment (toggleable)

**Speaker Labeling (critical UX):**

When user clicks a speaker label (e.g., "SPEAKER_00" or "Julien"):

1. **Popover appears inline** with:
   - Text input pre-filled with current name
   - "Recently used names" as clickable chips below input
   - Radio buttons:
     - "Apply to this segment only"
     - "Apply to all segments from this speaker" (default, pre-selected)
   - Cancel and Save buttons

2. **Recently used names:**
   - Stored in localStorage
   - Show last 5-10 names used across all meetings
   - Clicking a name fills the input

3. **On Save:**
   - If "all segments" selected → update all segments with matching speaker ID
   - Update metadata.json with speaker mapping
   - Show toast: "Speaker name updated successfully"
   - Popover closes

4. **Visual design:**
   - Speaker labels are styled as clickable pills/badges
   - Different speakers get different colors (auto-assigned)
   - Hover state shows edit affordance


### 4. Analysis Tab

**Route:** `/meetings/{id}` (tab within transcript view)

**If no analysis exists:**
- Show meeting type selector (pre-filled if set during upload)
- "Generate Analysis" button
- Clicking generates analysis via Claude API
- Show loading state with spinner

**If analysis exists:**
- Render markdown content
- "Regenerate" button (with confirmation)
- "Copy to clipboard" button
- "Download .md" button


## Background Job System

### Requirements
- Transcription takes 15-20 minutes — must be async
- User should see progress updates
- Jobs should survive page refresh (in-memory is fine, restart loses jobs)

### Implementation

Simple in-memory job queue using Python threading or asyncio:

```python
# Job states
PENDING = "pending"
PROCESSING = "processing"  
COMPLETED = "completed"
FAILED = "failed"

# Job structure
{
  "id": "job_uuid",
  "meeting_id": "meeting_uuid",
  "status": "processing",
  "progress": 45,  # percentage
  "stage": "transcribing",  # transcribing | aligning | diarizing
  "error": null,
  "created_at": "...",
  "updated_at": "..."
}
```

### API Endpoints

**Start transcription:**
```
POST /api/meetings
Body: multipart form with audio file + metadata
Response: { meeting_id, job_id }
```

**Check job status:**
```
GET /api/jobs/{job_id}
Response: { status, progress, stage, error }
```

**Frontend polling:**
- Poll every 3 seconds while status is "pending" or "processing"
- Stop polling on "completed" or "failed"
- Update UI with progress bar and stage label


## API Specification

### Meetings

```
GET    /api/meetings              # List all meetings
POST   /api/meetings              # Upload + start transcription
GET    /api/meetings/{id}         # Get meeting details + transcript
PATCH  /api/meetings/{id}         # Update title, type, speakers
DELETE /api/meetings/{id}         # Delete meeting and all files
```

### Jobs

```
GET    /api/jobs/{id}             # Get job status
```

### Analysis

```
POST   /api/meetings/{id}/analysis    # Generate analysis
GET    /api/meetings/{id}/analysis    # Get existing analysis
```

### Audio

```
GET    /api/meetings/{id}/audio       # Stream audio file (for player)
```


## Analysis Templates

Four built-in templates stored in `/templates/`:

### interview.md
For candidate interviews. Evaluates:
- Problem understanding & communication
- Research & discovery approach
- Technical/domain expertise
- Planning & execution
- Leadership & collaboration
- Attention to detail & quality
- Risk awareness

Outputs: Structured evaluation with evidence quotes, red flags, recommendation (Strong Hire → No Hire)

### sales.md
For sales calls (discovery, proposal, negotiation). Captures:
- Deal snapshot (opportunity, size, timeline, temperature)
- Pain points & needs
- Decision making (stakeholders, process, competition)
- Budget signals
- Objections & concerns
- Sentiment analysis (enthusiasm, pricing reaction, confidence, urgency, momentum)
- Commitments (ours and theirs)
- Key quotes for follow-up

### client.md
For ongoing project meetings. Extracts:
- Decisions made
- Action items (Nimble vs client, with owners and deadlines)
- Open questions
- Project status (blockers, milestones, scope changes)
- Technical discussions
- Risks & concerns
- Client sentiment
- Private notes (internal only)

### other.md
Generic template for any meeting type. Extracts:
- Meeting summary
- Key discussion points
- Decisions made
- Action items (with owners and deadlines where mentioned)
- Open questions
- Notable quotes


## Configuration

Environment variables (can be in `.env` file):

```bash
HF_TOKEN=hf_xxxxx              # HuggingFace token for pyannote
ANTHROPIC_API_KEY=sk-ant-xxx   # Claude API key
WHISPER_MODEL=large-v3         # Whisper model size
WHISPER_DEVICE=auto            # cuda, mps, cpu, or auto
WHISPER_BATCH_SIZE=16          # reduce if OOM errors
CLAUDE_MODEL=claude-sonnet-4-20250514  # Claude model for analysis
DATA_DIR=./data                # where to store files
```


## Setup & Run

### Makefile

```makefile
.PHONY: setup run clean

setup:
	python3.12 -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt
	@echo ""
	@echo "Setup complete. Now configure your API keys:"
	@echo "  export HF_TOKEN='your_huggingface_token'"
	@echo "  export ANTHROPIC_API_KEY='your_anthropic_key'"

run:
	. .venv/bin/activate && python run.py

clean:
	rm -rf .venv data/meetings/*
```

### First-time setup

```bash
cd meeting-transcriber
make setup
export HF_TOKEN="hf_xxx"
export ANTHROPIC_API_KEY="sk-ant-xxx"
make run
# Opens http://localhost:8000
```


## Error Handling

### Transcription failures
- If WhisperX fails, mark job as "failed" with error message
- Show error in UI with option to retry
- Common issues: OOM (suggest reducing batch size), invalid audio format

### Analysis failures
- If Claude API fails, show error toast
- Allow retry
- Handle rate limits gracefully (show "please wait" message)

### File handling
- Validate audio files on upload (check MIME type, file size)
- Max file size: 500MB (configurable)
- Clean up partial files on failed uploads


## Future Considerations (Out of Scope for MVP)

- Authentication and multi-user support
- Cloud deployment
- Vector database integration for RAG
- Mobile upload / PWA
- Notion integration for pushing analyses
- Real-time transcription (live meetings)
- Automatic meeting type detection
- Speaker voice fingerprinting (remember voices across meetings)


## Success Criteria

MVP is complete when:
1. User can upload an audio file and see transcription progress
2. Transcription completes with speaker diarization
3. User can label speakers with Plaud-style UI
4. User can generate analysis using the four templates
5. Transcript and analysis can be viewed and exported
6. App runs locally with `make run`


## Reference Files

The following files have already been created and should be included in the project:

1. **Analysis templates** (in `/templates/`):
   - `interview.md` — interview evaluation template
   - `sales.md` — sales meeting analysis template
   - `client.md` — client meeting analysis template
   - `other.md` — generic meeting analysis template

2. **Transcription script** (reference implementation):
   - `meeting_transcriber.py` — standalone WhisperX script with diarization

These files are available in the current conversation and should be incorporated into the project structure.