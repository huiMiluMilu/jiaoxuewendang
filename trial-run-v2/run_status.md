# Trial Run V2 Status

## Goal

This run uses the transcript-first workflow instead of sparse frame sampling.

## Expected Outputs

- `audio.wav`: extracted audio for transcription
- `transcript.md`: timestamped transcript or transcript-derived notes
- `steps.json`: step list grounded in transcript plus visible evidence
- `teaching_draft.md`: editable teaching draft
- `review_notes.md`: uncertainty list for human review

## Current Status

- Source video context is already available from the prior verified replay run.
- Audio extraction is in progress using the local ffmpeg binary from `imageio-ffmpeg`.
- Local speech-to-text tooling has not yet been confirmed in this workspace.

## Notes

- This run intentionally treats language as the primary fact layer.
- Screenshot selection and click marking are downstream enhancements, not the primary step detector.
