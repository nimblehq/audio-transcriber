# Audio Transcriber

Local audio/video transcription with speaker diarization, speaker labeling, and AI-powered meeting analysis. Built with WhisperX and Claude.

Works in two ways:
- **Web app** -- upload recordings, view synced transcripts, rename speakers, and generate AI analyses from your browser
- **CLI** -- transcribe files directly from the terminal

## Getting Started

### Prerequisites

- **Python 3.12**
- **ffmpeg** (handles audio/video format conversion)

Install ffmpeg if you don't have it:
```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg
```

Not sure if you have it? Run `ffmpeg -version` in your terminal. If you see a version number, you're good.

### Step 1: Install the project

```bash
make setup
```

This creates a Python virtual environment and installs all dependencies. It may take a few minutes (PyTorch is a large download).

### Step 2: Set up your API keys

You need two API keys. Both are free to create.

**HuggingFace token** (identifies who is speaking):

1. Create an account at https://huggingface.co
2. Go to https://huggingface.co/settings/tokens and create a token
3. Accept the license agreement on each of these model pages (click "Agree and access repository" on each):
   - https://huggingface.co/pyannote/speaker-diarization-3.1
   - https://huggingface.co/pyannote/segmentation-3.0
   - https://huggingface.co/pyannote/speaker-diarization-community-1

**Anthropic API key** (powers the meeting analysis):

1. Create an account at https://console.anthropic.com
2. Go to https://console.anthropic.com/settings/keys and create a key

### Step 3: Configure your `.env` file

```bash
cp .env.example .env
```

Open `.env` in any text editor and paste your keys:

```
HF_TOKEN=hf_your_token_here
ANTHROPIC_API_KEY=sk-ant-your_key_here
```

The `.env` file is gitignored, so your keys stay private.

### Step 4: Run the app

```bash
make run
```

Open http://localhost:8000 in your browser. You can now upload audio/video files and start transcribing.

## Web App

The web app lets you upload recordings, track transcription progress, view transcripts synchronized with audio playback, and generate AI analyses.

### Features

- **Upload** audio/video files (mp3, mp4, m4a, wav, webm) up to 500 MB
- **Real-time progress** tracking as files are transcribed
- **Audio player** synced with the transcript -- click any line to jump to that moment
- **Playback speed** control (0.5x to 2x)
- **Speaker renaming** -- click a speaker label to assign a real name; recent names are remembered
- **AI meeting analysis** powered by Claude, with templates for different meeting types:
  - Interview evaluations
  - Sales call summaries
  - Client meeting notes
  - General meeting summaries
- **Retry** failed transcriptions
- **Copy or download** analyses as Markdown

### Upload Options

When uploading, you can optionally specify:

| Option | Default | What it does |
|--------|---------|-------------|
| Title | Filename | Display name for the meeting |
| Meeting type | Other | Determines which analysis template is used |
| Language | Auto-detect | Set explicitly for faster transcription |
| Number of speakers | Auto-detect | Set explicitly for better speaker identification |

## CLI

The CLI is useful for batch processing or scripting.

**Basic transcription:**
```bash
python transcriber.py meeting.mp3
```

Supports mp3, mp4, wav, m4a, and other ffmpeg-compatible formats. Output is saved alongside the input file (e.g., `meeting.mp3` -> `meeting.txt`).

**With speaker names:**
```bash
# First, identify who's who
python transcriber.py meeting.mp3 --identify-speakers

# Then run with names mapped
python transcriber.py meeting.mp3 --speakers "Julien,Alice,Bob"

# Or use interactive mode to name speakers as you go
python transcriber.py meeting.mp3 --interactive
```

**Options:**
```bash
# Specify language (faster -- skips auto-detection)
python transcriber.py meeting.mp3 --language en

# Use smaller model (faster, less accurate)
python transcriber.py meeting.mp3 --model medium

# Output as SRT subtitles
python transcriber.py meeting.mp3 --format srt

# Output as JSON
python transcriber.py meeting.mp3 --format json -o transcript.json

# Help with diarization accuracy
python transcriber.py meeting.mp3 --num-speakers 3

# Lower batch size if you get out-of-memory errors
python transcriber.py meeting.mp3 --batch-size 4

# Skip diarization entirely
python transcriber.py meeting.mp3 --no-diarization

# Quiet mode (suppress progress messages)
python transcriber.py meeting.mp3 --quiet
```

## Output Example

```
[00:00:15] Julien: So let's start with the Q4 roadmap discussion.
[00:00:42] Alice: I think we should prioritize the API work first.
[00:01:03] Julien: Makes sense. What's the timeline looking like?
[00:01:15] Bob: I'd estimate about three weeks for the core functionality.
```

## Configuration

All settings are configured via environment variables (in your `.env` file or exported in your shell).

| Variable | Default | Description |
|----------|---------|-------------|
| `HF_TOKEN` | | HuggingFace token for speaker diarization |
| `ANTHROPIC_API_KEY` | | Anthropic API key for meeting analysis |
| `CLAUDE_MODEL` | `claude-sonnet-4-20250514` | Claude model used for analysis |
| `WHISPER_MODEL` | `large-v3` | Whisper model size (`large-v3`, `medium`, `small`, `base`) |
| `WHISPER_DEVICE` | `auto` | Compute device (`auto`, `cuda`, `cpu`) |
| `WHISPER_BATCH_SIZE` | `16` | Batch size for transcription (lower if out of memory) |
| `DATA_DIR` | `./data` | Where meeting data is stored |
| `MAX_UPLOAD_SIZE` | `500MB` | Maximum upload file size |

## Tips

- **Language:** Use `--language en` (or `fr`, `de`, etc.) to skip auto-detection and speed up transcription.
- **Model choice:** `large-v3` is best quality but slower. `medium` is a good balance. `small` or `base` for quick drafts.
- **GPU memory:** If you run out, reduce `--batch-size` (CLI) or set `WHISPER_BATCH_SIZE` in `.env` (web app) to 8 or 4.
- **Known speaker count:** Specifying the number of speakers improves diarization accuracy.
- **No GPU?** It still works on CPU, just slower. Set `WHISPER_DEVICE=cpu` if auto-detection has issues.
