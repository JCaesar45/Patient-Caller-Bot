# Architecture

DRAFT: replace the bracketed items with your own measurements and decisions before submitting.

The bot is a LiveKit Agents worker. `make_calls.py` creates a room and dispatches the `patient-bot` worker
with a scenario name. The worker joins, starts recording with room-composite egress to an S3-compatible
bucket (OGG, both sides mixed), starts an `AgentSession`, then dials the target number through a LiveKit
outbound SIP trunk and waits until the call is answered. The agent under test speaks first; the bot responds
as the patient. Transcripts come from the session's conversation events, timestamped from call start, and are
written when the job shuts down.

Choices and tradeoffs: Deepgram nova-3 for streaming STT because of low first-word latency on narrowband
phone audio [add your measured latency]. gpt-4o-mini for the persona LLM because replies are short and
speed matters more than depth; the analysis pass uses the larger gpt-4o offline where latency is irrelevant.
Cartesia for TTS because of fast time-to-first-audio. Turn detection uses Silero VAD with a 0.7s endpointing
delay, which I tuned after hearing early calls [describe what you changed and why]. Interruptions are enabled
so the bot can be cut off like a real caller, and the `interrupter` scenario deliberately talks over the agent.
Persona prompts force short turns and one fact at a time to keep pacing human. A hard 240s cap and an
`end_call` tool keep calls bounded. SIP via LiveKit avoids running my own media gateway.

Alternatives considered: [e.g. Twilio Media Streams directly, ElevenLabs TTS, Whisper STT]. [Why rejected.]
