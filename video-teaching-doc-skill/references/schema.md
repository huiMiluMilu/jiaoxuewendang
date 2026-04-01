# Step Schema

Use this schema as the intermediate representation between video analysis and final document writing.

## Step Object

```json
{
  "step_id": 3,
  "title": "Open the mini program upload page",
  "start_time": "00:01:12.400",
  "end_time": "00:01:20.200",
  "transcript_excerpt": "We first open the publishing path, then upload the version.",
  "goal": "Reach the publishing entry",
  "action_type": "click_navigation",
  "raw_actions": [
    "Teacher moves cursor to the left navigation",
    "Teacher clicks the upload entry"
  ],
  "spoken_intent": "We first enter the publishing path",
  "instruction": "Click the publishing entry in the left navigation.",
  "expected_result": "The upload page is visible.",
  "caution": "If the entry is missing, confirm the project permissions first.",
  "ui_context": {
    "page_name": "WeChat Dev Platform",
    "visible_labels": ["Upload", "Version", "Submit"],
    "url_hint": ""
  },
  "screenshot_before": "frames/step3_before.png",
  "screenshot_after": "frames/step3_after.png",
  "needs_screenshot": true,
  "click_target": {
    "label": "Upload",
    "bbox": [812, 233, 104, 36],
    "confidence": 0.84,
    "evidence": ["cursor", "ocr", "spoken_action"]
  },
  "draft_paragraph": "Open the publishing entry in the left navigation so you can enter the version upload flow.",
  "confidence": 0.87,
  "issues": [],
  "teaching_notes": [
    "This step is easy to miss because the entry is in the left navigation."
  ]
}
```

## Required Fields

- `step_id`
- `title`
- `start_time`
- `end_time`
- `transcript_excerpt`
- `action_type`
- `instruction`
- `expected_result`
- `needs_screenshot`
- `confidence`

## Confidence Meaning

- `0.85-1.00`: high confidence, usable without review
- `0.60-0.84`: usable, but worth checking
- `0.00-0.59`: uncertain, must appear in review list

## Recommended Action Types

- `start_section`
- `open_page`
- `click_navigation`
- `click_button`
- `select_option`
- `input_text`
- `toggle_setting`
- `drag_drop`
- `submit_form`
- `wait_for_result`
- `verify_result`
- `handle_error`
- `explain_concept`

## Stage 1 Output Shape

The minimum usable semi-automatic package should contain:

1. timestamped transcript segments
2. step objects derived from transcript plus visible evidence
3. screenshot recommendations per step
4. click-target suggestions with confidence
5. a first-draft paragraph for each step

At this stage, human revision is assumed.

## Stage 2 Output Shape

When structured enhancement is enabled, each step should additionally map into one of:

- `main_flow`
- `explanation`
- `faq`

The final document should separate those sections clearly.

## Final Document Shape

The reconstructed teaching document should usually follow this order:

1. Lesson goal
2. Prerequisites
3. Step-by-step operations
4. Supporting explanation
5. FAQ or common mistakes
6. Expected final result

## Review List Shape

Use a compact review list like this:

```json
[
  {
    "step_id": 5,
    "issue_type": "uncertain_click_target",
    "reason": "Cursor and OCR disagree on the clicked menu item",
    "recommended_action": "Human review the click marker"
  }
]
```
