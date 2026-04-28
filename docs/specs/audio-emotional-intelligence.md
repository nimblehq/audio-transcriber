# Audio-Based Emotional Intelligence

## Overview

### Problem Statement

Transcript-only meeting analysis misses critical non-verbal signals. Tone, volume, pacing, and emotional cues often reveal more than words alone. A statement like "That's fine" can mean genuine agreement, resignation, frustration, or sarcasm depending on how it's said.

Current analysis is limited to:
- What was said (words)
- Who said it (speaker diarization)
- When it was said (timestamps)

Missing entirely:
- How it was said (tone, emotion, energy)
- Interaction dynamics (interruptions, talking over, hesitation)
- Emotional trajectory (how sentiment shifted during the meeting)

This gap significantly limits the accuracy of:
- Hidden disagreement detection (verbal agreement + frustrated tone = not actually aligned)
- Contribution quality assessment (confident tone vs. uncertain hedging)
- Psychological safety indicators (hesitation before speaking, volume changes)
- Meeting effectiveness assessment (engagement levels, energy dynamics)

### Goals

1. Extract emotional and prosodic features from meeting audio recordings
2. Link these features to transcript segments and speakers
3. Surface word-tone mismatches that indicate potential issues
4. Provide interaction pattern analysis (interruptions, turn-taking)
5. Track emotional trajectory across the meeting duration

### Scope

**In scope:**
- Speech emotion recognition per speaker segment
- Prosodic feature extraction (volume, pace, pitch)
- Interruption and overlap detection
- Integration with existing meeting analysis templates
- Segment-level annotations linked to transcript

**Out of scope:**
- Real-time analysis during live meetings
- Video/facial expression analysis
- Sentiment analysis of text content (already handled by LLM in templates)

## User Stories

- As a Nimble team member, I want to know when someone's tone contradicts their words so I can identify hidden disagreements that verbal analysis misses.
- As a Nimble team member, I want to see who interrupted whom and how often so I can understand power dynamics and participation quality.
- As a Nimble team member, I want to track emotional shifts during the meeting so I can identify which topics triggered frustration or disengagement.
- As a Nimble team member, I want to see hesitation patterns before responses so I can identify uncertainty that hedging language alone might not reveal.

## Technical Approach

### Architecture Overview

```
Audio File
    │
    ├─→ [Existing] WhisperX Transcription → Transcript with timestamps
    │
    ├─→ [Existing] PyAnnote Diarization → Speaker segments
    │
    └─→ [New] Audio Analysis Pipeline
            │
            ├─→ Speech Emotion Recognition → Emotion labels per segment
            │
            ├─→ Prosody Extraction → Volume, pace, pitch per segment
            │
            └─→ Interaction Analysis → Interruptions, overlaps, pauses
                    │
                    └─→ Merged Output: Transcript + Emotions + Prosody + Interactions
```

### Component 1: Speech Emotion Recognition (SER)

**Purpose:** Classify emotional state for each speaker segment.

**Emotion categories:**
- Neutral
- Confident / Assertive
- Frustrated / Irritated
- Uncertain / Hesitant
- Engaged / Enthusiastic
- Disengaged / Flat

**Potential models:**
- wav2vec2 fine-tuned for emotion recognition
- Emotion2Vec (Alibaba)
- HuBERT-based emotion classifiers
- SpeechBrain emotion recognition models

**Output:** Per-segment emotion label with confidence score.

### Component 2: Prosodic Feature Extraction

**Purpose:** Extract acoustic features that correlate with emotional state and engagement.

**Features to extract:**
- **Volume (intensity):** RMS energy, peaks, variance
- **Pitch (F0):** Mean, variance, contour patterns
- **Speaking rate:** Words per minute, syllables per second
- **Voice quality:** Jitter, shimmer (indicate stress/uncertainty)
- **Pause patterns:** Duration, frequency, placement

**Potential tools:**
- OpenSMILE (extensive feature extraction)
- Praat (via Parselmouth Python wrapper)
- librosa (Python audio analysis)
- PyAudioAnalysis

**Output:** Feature vectors per segment, normalized for cross-speaker comparison.

### Component 3: Interaction Pattern Analysis

**Purpose:** Detect interruptions, overlaps, and turn-taking dynamics.

**What to detect:**
- **Interruptions:** Speaker B starts before Speaker A finishes
- **Overlaps:** Multiple speakers talking simultaneously
- **Back-channels:** Short acknowledgments ("uh-huh", "yeah") during another's speech
- **Latency:** Time between end of one turn and start of next
- **Hesitation:** Unusual pause before responding

**Detection approach:**
- Use PyAnnote speaker timestamps
- Identify overlapping segments
- Classify overlap type (interruption vs. back-channel vs. simultaneous start)
- Track interruption direction (who interrupts whom)

**Output:** Interaction events with timestamps, speakers involved, and classification.

## Data Model

### Emotion Annotation

```python
class EmotionAnnotation:
    segment_id: str           # Links to transcript segment
    speaker: str              # Speaker identifier
    start_time: float         # Segment start (seconds)
    end_time: float           # Segment end (seconds)
    primary_emotion: str      # Most likely emotion
    confidence: float         # 0.0 to 1.0
    emotion_scores: dict      # All emotion probabilities
```

### Prosody Annotation

```python
class ProsodyAnnotation:
    segment_id: str
    speaker: str
    start_time: float
    end_time: float
    volume_mean: float        # Normalized 0-1
    volume_variance: float
    pitch_mean: float         # Hz
    pitch_variance: float
    speaking_rate: float      # Words per minute
    pause_ratio: float        # Pause time / total time
```

### Interaction Event

```python
class InteractionEvent:
    event_type: str           # "interruption", "overlap", "long_pause", "hesitation"
    timestamp: float
    speaker_a: str            # Speaker who was speaking / should respond
    speaker_b: str            # Speaker who interrupted / started
    duration: float           # Overlap duration or pause duration
    context: str              # Brief transcript context
```

### Enhanced Transcript Segment

```python
class EnhancedSegment:
    # Existing fields
    text: str
    speaker: str
    start_time: float
    end_time: float

    # New fields
    emotion: EmotionAnnotation
    prosody: ProsodyAnnotation
    preceded_by_interruption: bool
    followed_by_interruption: bool
    hesitation_before: float  # Pause duration before speaking
```

## Integration with Meeting Analysis

### Template Enhancement

The meeting analysis templates will receive additional context:

```markdown
## Audio Analysis Context

### Emotional Patterns
- Speaker A: Predominantly confident (72%), with frustration spikes at 12:34 and 28:15
- Speaker B: Shifted from engaged (first 20 min) to disengaged (remainder)
- Speaker C: Consistent uncertainty markers throughout

### Word-Tone Mismatches
- 15:23 Speaker B: "That works for me" — tone indicates frustration (confidence: 0.78)
- 32:45 Speaker A: "No concerns" — preceded by 2.3s hesitation, uncertain tone

### Interaction Dynamics
- Speaker A interrupted Speaker C 4 times (reverse: 0 times)
- Average response latency: Speaker A (0.3s), Speaker B (0.8s), Speaker C (1.4s)
- Notable hesitations: Speaker C before responding to Speaker A's direct questions

### Energy Trajectory
- Meeting energy peaked at 8-15 minutes (budget discussion)
- Significant energy drop after 35 minutes
- Topic "timeline" consistently triggered lower engagement
```

### Template Instructions Update

Templates should include guidance like:

```markdown
When audio analysis is available, factor it into your assessment:

1. **Hidden Disagreements**: Weight word-tone mismatches heavily. Verbal agreement
   with frustrated/resigned tone is likely not genuine alignment.

2. **Contribution Quality**: A confident assertion is different from an uncertain
   one, even with identical words. Note tone when assessing influence.

3. **Psychological Safety**: Hesitation patterns, volume drops when addressing
   certain people, and interruption dynamics reveal power structures.

4. **Meeting Effectiveness**: Track energy trajectory. A meeting that ends with
   low energy and disengaged tones may not produce follow-through.
```

## Processing Pipeline

### Integration Points

```
1. User uploads audio file
2. [Existing] Audio saved, metadata created
3. [Existing] Transcription job started
4. [New] Audio analysis job started (can run in parallel)
5. [Existing] WhisperX transcription completes
6. [Existing] PyAnnote diarization completes
7. [New] SER analysis completes
8. [New] Prosody extraction completes
9. [New] Interaction analysis completes
10. [New] Results merged into enhanced transcript
11. Meeting status → READY
```

### Performance Considerations

Audio analysis adds processing time. Estimated additions (on Apple Silicon):

| Component | Estimated Time (1hr audio) |
|-----------|---------------------------|
| Emotion Recognition | 5-10 minutes |
| Prosody Extraction | 2-5 minutes |
| Interaction Analysis | 1-2 minutes |
| **Total Additional** | **8-17 minutes** |

This may be acceptable given current transcription takes 15-30+ minutes on local hardware.

### Optional Processing

Audio analysis could be:
- **Always on**: Every meeting gets full analysis
- **On request**: User opts in per meeting
- **Tiered**: Basic analysis always, detailed on request

Recommendation: Start with "always on" for simplicity, optimize later if needed.

## Edge Cases

### Poor Audio Quality

**Scenario:** Recording has significant background noise, echo, or low volume.

**Expected behavior:**
- Emotion recognition confidence scores will be lower
- Flag low-confidence segments in output
- Fall back to transcript-only analysis when confidence is below threshold (e.g., 0.5)
- Note in analysis: "Audio quality limited emotional analysis for segments X-Y"

### Single Speaker Dominance

**Scenario:** One speaker talks 80%+ of the meeting.

**Expected behavior:**
- Interaction analysis will have limited data
- Emotional trajectory analysis still valuable for dominant speaker
- Note the limitation in output

### Non-Speech Audio

**Scenario:** Recording contains music, hold tones, or extended silence.

**Expected behavior:**
- Detect and exclude non-speech segments
- Don't attempt emotion recognition on non-speech
- Note excluded segments in metadata

### Language Limitations

**Scenario:** Meeting is in Thai or mixed Thai/English.

**Expected behavior:**
- Prosodic features (volume, pitch, pace) are language-agnostic
- Emotion recognition may have reduced accuracy for non-English speech
- Select or fine-tune models that support Thai if available
- Note any language-specific limitations

### Emotional Ambiguity

**Scenario:** Tone is genuinely ambiguous or model is uncertain.

**Expected behavior:**
- Report confidence scores alongside classifications
- For low-confidence classifications, present as "possibly" or "may indicate"
- Don't over-interpret uncertain signals

## Open Questions

### For Engineering

1. **Model selection**: Which SER model performs best on conversational speech (vs. acted emotions)? Need to evaluate on real meeting recordings.

2. **Processing architecture**: Should audio analysis run in the same thread as transcription, or as a separate background job? Parallel would be faster but uses more resources.

3. **Storage format**: How to store audio analysis results? Extend existing transcript.json, or create separate audio_analysis.json?

4. **Calibration**: Prosodic features vary by individual (some people naturally speak louder/faster). Should we calibrate per-speaker baselines within a meeting?

### For Product

1. **UI presentation**: How should audio insights be surfaced in the transcript viewer? Inline annotations? Separate panel? Hover tooltips?

2. **Privacy sensitivity**: Emotional analysis is more sensitive than transcription. Should there be additional consent/disclosure for this feature?

3. **Accuracy expectations**: Users may over-trust emotional classifications. How do we communicate uncertainty appropriately?

## Implementation Phases

### Phase 1: Foundation
- Integrate one SER model (likely wav2vec2-based)
- Basic emotion classification per segment
- Store results alongside transcript
- No UI changes yet — data available for template analysis

### Phase 2: Prosody
- Add prosodic feature extraction
- Volume and speaking rate analysis
- Pause and hesitation detection

### Phase 3: Interactions
- Interruption detection using diarization timestamps
- Turn-taking analysis
- Interaction pattern summarization

### Phase 4: UI Integration
- Visualize emotional trajectory
- Show word-tone mismatches in transcript viewer
- Display interaction patterns

## Success Metrics

- **Accuracy**: Emotion classification accuracy >70% on held-out meeting samples
- **Value add**: Users report audio insights revealed issues they would have missed (qualitative)
- **Performance**: Total processing time increase <50% over transcript-only
- **Reliability**: <5% of meetings fail audio analysis due to technical issues
