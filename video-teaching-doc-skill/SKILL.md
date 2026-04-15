---
name: video-teaching-doc-skill
description: Create teaching documentation from screen recordings, course replay videos, or software demo videos. Use when the user wants to turn a video into step-by-step teaching docs, identify where screenshots are needed, mark what the teacher clicked, restructure messy spoken explanations into clear student-facing knowledge, or generate a draft SOP/tutorial from a lesson replay.
---

# Video Teaching Doc Skill

Use this skill when the input is primarily a video, replay link, or extracted video assets, and the goal is to produce a teaching document rather than a literal transcript.

## What This Skill Optimizes For

- Turning spoken teaching content into an editable text draft first
- Turning a lesson replay into a student-friendly doc
- Splitting the lesson into action-sized steps from language plus visible evidence
- Deciding which moments deserve screenshots
- Marking likely click targets with evidence and confidence
- Separating the teacher's real-time operation order from the final teaching order
- Preserving facts while allowing pedagogical restructuring

## Core Principle

Always split the work into two layers, and start from language before screenshots:

1. **Operation extraction**
Record what the teacher actually said and did, in time order, without beautifying or reorganizing it.

2. **Teaching reconstruction**
Rewrite the material into the order that best helps a student learn, while never inventing operations that did not happen.

Do not jump directly from raw video to polished document without an intermediate transcript-plus-step schema.

## Delivery Roadmap

Build the skill in three stages instead of aiming for a perfect all-in-one system immediately.

### Stage 1. Semi-automatic baseline

The default path should be:

- automatic transcription
- automatic step segmentation
- automatic screenshot selection
- automatic click-point marking
- automatic first draft generation

This stage is designed for human revision. Optimize for editable output, not full autonomy.

### Stage 2. Structured enhancement

After the baseline is stable, add:

- separation of main flow, explanations, and FAQ
- reconstruction of messy spoken teaching
- one action per step
- expected result and cautions for each step

### Stage 3. High-quality output

Only after the first two stages work reliably, add:

- multiple output styles
- versions for different audiences
- more stable UI element recognition
- stronger click-object naming

## Workflow

### 0. Create an isolated output folder per video

Before generating any assets, create one dedicated folder for the current video run.

Rules:

- Use one folder per video link or source
- Name the folder from the actual course title or the clearest video topic you can verify
- Put both final deliverables and temporary work products inside that folder
- Prefer a structure like:
  - `simple-demo/<video-title>/`
  - `simple-demo/<video-title>/work/`
- Do not scatter intermediate files across shared top-level directories when they belong to one specific video

This keeps cleanup simple: after the user confirms the final teaching document is usable, they can delete that single folder to reclaim disk space.

### 1. Confirm the usable source

Prefer the richest source available:

- Direct video file or stream URL
- Replay page with accessible media
- Video plus transcript
- Video plus frames

If the page player is unreliable but the underlying media URL is accessible, operate on the media URL instead of the page UI.

### 2. Transcribe first

Before selecting screenshots, create a text-first working layer:

- timestamped transcript or timestamped paraphrase
- speaker turns when relevant
- visible UI context tied to transcript windows
- obvious action phrases such as click, input, select, open, submit

If the transcript is weak, say so explicitly and lower confidence for all downstream outputs.

### 3. Build a fact sheet from transcript plus visible evidence

Extract only facts and keep them grounded:

- timestamps
- transcript snippets
- visible UI states
- teacher actions
- spoken intent
- outcomes
- errors or warnings

Store these in a structured step schema before drafting prose.

Read [references/schema.md](references/schema.md) before generating step objects.

### 4. Detect candidate steps

Treat a new step as likely when one of these changes happens:

- the transcript shows a new action phrase or sub-goal
- the user's goal changes
- the visible page state changes meaningfully
- a click, input, selection, drag, submit, or navigation occurs
- a result appears, such as success, error, modal, or new panel

Read [references/heuristics.md](references/heuristics.md) for the detailed rules.

Default to language-led segmentation. Do not use sparse frame sampling as the primary step detector.

### 5. Decide whether a screenshot is needed

A screenshot is usually justified when it helps the learner:

- locate where to act
- verify what changed
- avoid a likely mistake

Do not screenshot every spoken sentence. Favor key states over dense coverage.

### 6. Mark click targets carefully

Only mark a click area when there is evidence from at least one of:

- cursor location
- UI element text
- OCR match
- before/after visual change
- spoken action phrase

If confidence is low, keep the screenshot but mark the click location as uncertain.

### 7. Generate the first draft before polishing structure

The first draft should already be useful for human revision:

- step title
- instruction
- expected result
- caution if visible or spoken
- optional screenshot note
- optional click-target note

Do not wait for perfect screenshot coverage before generating the draft.

### 8. Reconstruct the teaching document

Produce two outputs when possible:

- a raw operation timeline
- a student-facing reconstructed document

The student-facing version may reorder sections, merge repetition, remove detours, and add headings, but must not invent hidden steps.

### 9. Choose heading style from course type

Do not force all courses into the same heading pattern.

- If the lesson is primarily a lecture, concept explanation, methodology walkthrough, or case analysis, do not use `步骤1` / `步骤2` style headings.
- For lecture-style sections, use Chinese major headings such as `一、` `二、` `三、`.
- If a lecture-style major heading needs subpoints, use `1、` `2、` `3、` under that heading.
- If the lesson is primarily an operation demo or software walkthrough, `步骤1` / `步骤2` style headings are still acceptable.
- If the lesson is mixed, keep concept sections in `一、二、三、` style and reserve `步骤1` / `步骤2` for the true operation part only.
- Never label a pure concept page as a numbered operation step just to make the document look uniform.

## Output Contract

For Stage 1, default to five deliverables:

1. A timestamped transcript or transcript-derived notes
2. A structured step list
3. Screenshot and click-mark suggestions
4. A reconstructed first draft
5. A review list of uncertain items

By default, store all deliverables for the same video under one isolated folder:

- final Markdown docs at `simple-demo/<video-title>/`
- transcript, samples, intermediate media, and publish logs at `simple-demo/<video-title>/work/`

For Stage 2 and above, the reconstructed document should separate:

- main flow
- supporting explanation
- FAQ or common mistakes

The review list must explicitly call out:

- uncertain click locations
- missing or weak screenshots
- places where the teacher's explanation was ambiguous
- places where the final doc order differs from the original sequence

## Quality Bar

- Treat transcript quality as a first-class dependency
- Keep operation facts and teaching explanation separate
- Prefer one action per step where possible
- Prefer confidence annotations over false precision
- Keep repeated actions only once unless repetition teaches something important
- Preserve visible labels exactly when they matter for navigation
- Remove filler speech, tangents, and self-corrections from the final teaching doc unless pedagogically useful

## Do Not

- invent buttons, fields, menus, or results that are not visible or evidenced
- let sparse frame sampling override what the teacher actually said
- assume every mouse movement deserves a screenshot
- assume the teacher's speaking order is the best teaching order
- silently rewrite uncertain actions as certain ones

## Reference Files

- [references/schema.md](references/schema.md): step schema and output shape
- [references/heuristics.md](references/heuristics.md): screenshot, click, and restructuring heuristics
