# Patient Caller Bot

A Python voice bot that phones a test line, plays a patient from a scenario list, records both sides, and
helps surface bugs in the agent it calls. Built on LiveKit Agents in pipeline mode: Deepgram (STT),
OpenAI (LLM), Cartesia (TTS). No realtime or speech-to-speech models.

## Setup

1. `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
2. `cp .env.example .env` and fill in the keys.
3. LiveKit Cloud: create a project, then an outbound SIP trunk pointed at your telephony provider
   (for example a Twilio Elastic SIP Trunk with termination credentials). Create it with the `lk` CLI
   (`lk sip outbound create trunk.json`) and put the returned ID in `SIP_OUTBOUND_TRUNK_ID`.
   The trunk's number is the one caller ID you use for every call.
4. Create an S3-compatible bucket (R2 free tier works) and add a LiveKit Egress-compatible key to `.env`.

## Run

Terminal 1: `python agent.py dev`

Terminal 2: `python make_calls.py` (all scenarios) or `python make_calls.py schedule_sunday refill_standard`

Afterwards:

- `python sync_recordings.py` downloads the OGG recordings into `recordings/`
- `python analyze.py` drafts `bug_candidates.md` from the transcripts

Transcripts land in `transcripts/`. Listen to the audio and confirm every candidate before it goes into
`BUG_REPORT.md`.

## Scenarios

Twelve are defined in `scenarios.py`: basic booking, Sunday booking, reschedule, cancel, standard refill,
early controlled-substance refill, hours and location, insurance, interruptions, vague chest-discomfort call,
off-topic detour with memory check, and a wrong phone number correction.
