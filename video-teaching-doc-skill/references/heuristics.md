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
