# Heuristics

## When To Split Steps

Start a new step when at least one is true:

- the transcript introduces a new actionable verb or sub-goal
- the teacher's goal changes
- a new page, modal, panel, or tab appears
- the teacher clicks, inputs, selects, drags, submits, or confirms
- the visible result materially changes
- the teacher moves from explanation into operation, or vice versa

Do not split only because time passes.

Prefer transcript-led boundaries over evenly spaced frame sampling.

## Transcript-First Rule

The first pass should answer:

- what the teacher is trying to do
- what the learner needs to do
- what result the learner should see

Only after this pass should you optimize screenshots and click markers.

If transcript and sparse frames disagree, do not force the step from frames alone. Mark it for review.

## When A Screenshot Is Worth It

Take a screenshot when it helps a learner:

- locate the entry point
- confirm a successful result
- understand a non-obvious setting
- avoid a common mistake

Prefer one of these screenshot roles:

- `locator`: where to click before the action
- `result`: what changed after the action
- `warning`: what error or risky state looks like

## When To Skip A Screenshot

Usually skip when:

- the transcript already explains the action clearly and the UI state is not ambiguous
- the action is obvious and text-only
- the screen did not meaningfully change
- the same interface was already shown clearly in a nearby step
- the screenshot would be visually redundant

## Click Target Heuristics

High confidence click markers usually combine multiple signals:

- cursor pauses near the element before state change
- OCR label matches spoken action
- the clicked area changes after the action
- the element shape and contrast are consistent with a button, menu item, tab, or field

If only one weak signal exists, keep the step but mark the click target as uncertain.

## Click Target Priority

Always decide **which exact control should be boxed** before drawing any red box.

Use this priority order:

1. if the cursor is clearly visible, box the clickable control under the cursor tip
2. if the cursor is weak or absent, but the UI label is identifiable, box that exact button, menu item, field, or link
3. if there are multiple controls with the same label, use row, card, modal, or nearby context to disambiguate
4. if the frame does not uniquely identify the control, mark the frame as unsuitable and switch frames instead of guessing

Do not treat the red box as a generic "related area" marker. It must point to the actual control used in the step.

## Hard Annotation Rules

- The boxed object must be the exact control the learner should click, select, input into, or confirm in this step.
- The box must be tight to the control boundary and must not cover large empty space.
- For text buttons such as `修改`, `下载`, `保存`, or `下一步`, box only the clickable text button area.
- For left-side menus, box only the menu item itself, not the whole menu column.
- For fields or links inside modals, box the field or link, not blank space near the modal title.
- When identical labels appear multiple times, combine OCR with row-level or panel-level context before boxing.
- If cursor location conflicts with semantic guess, prefer the control directly under the cursor tip.
- If the current frame cannot support a unique control decision, return `需要换一帧` rather than drawing a speculative box.

## Ordering For Semi-Automatic Stage

Use this order by default:

1. transcribe
2. segment into steps
3. draft the instructional text
4. choose screenshots
5. mark click targets
6. prepare the review list

Do not block the draft on perfect computer-vision accuracy.

## Reconstructing Messy Explanations

Teachers often speak in this order:

- partial explanation
- detour
- operation
- correction
- repeated explanation

The final teaching doc should instead prefer:

1. what this section is for
2. what to prepare first
3. the exact steps
4. expected result
5. cautions and verification
6. supporting explanation or FAQ

## Rules For Reordering

Reordering is allowed when it improves learning clarity, but only if:

- every operation already exists in the extracted fact sheet
- the final sequence remains executable
- moved explanations are still attached to the correct step

Reordering is not allowed when it would hide a dependency that matters in practice.

## Rules For Repetition

Condense repeated demonstrations unless repetition teaches:

- a contrast between correct and incorrect paths
- a troubleshooting pattern
- a second important variation

## Low-Confidence Fallback

When confidence is low:

- preserve the raw fact
- avoid overcommitting in prose
- add the item to the review list
- keep the final doc readable, but explicit about uncertainty if it affects correctness
