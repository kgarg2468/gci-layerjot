# CLABSI AR Glasses App - Use Cases

Source: formatted from `Use Cases Document.md` downloaded from Google Drive.

This document is the product behavior map for coding agents. Treat each `UC-*` ID as stable. When implementing, testing, or reviewing a feature, reference the relevant IDs in commit messages, PR descriptions, and test names.

## Product Scope

The app assists clinicians during central line insertion, maintenance, and removal workflows using:

- a Unity Android app targeting XREAL glasses,
- voice and tap navigation,
- audio prompts,
- AR checklist overlays,
- an AI assistant for procedural clarification and safety alerts,
- local procedure logs,
- offline-capable checklist flows.

The assistant is procedural support software. It should not provide diagnosis or medication dosing guidance.

## Agent Implementation Rules

- Preserve all stable UC IDs.
- Prefer small vertical slices that connect UI, state, voice/tap input, logging, and tests for a single workflow.
- Add acceptance tests or manual verification notes for every implemented UC.
- Log AI alerts, warnings, missed steps, and user confirmations with timestamps.
- Keep checklist data available locally so procedure flows work without network access.

## Capability Map

| Capability | Use Cases | Expected Behavior |
| --- | --- | --- |
| App shell | UC-01, UC-02, UC-10, UC-12 | User can launch, navigate to procedures/settings/logs, and exit. |
| Voice navigation | UC-04, UC-17, UC-24, UC-28 | User can move between pages and checklist steps hands-free. |
| Audio prompts | UC-05 | Current step is read aloud when displayed. |
| AI assistant | UC-06, UC-07 | User can ask clarifying questions; AI can flag risks or missed steps. |
| XREAL display | UC-03, UC-08 | App pairs with glasses and renders checklist/alert overlays on the HUD. |
| Offline operation | UC-09 | Local checklist flows and essential prompts work without WiFi. |
| Procedure logging | UC-11, UC-20, UC-25, UC-30 | Completed procedures save steps, alerts, warnings, missed steps, and timestamps. |
| Insert workflow | UC-13 through UC-20 | User completes insertion checklist in order. |
| Maintenance workflow | UC-21 through UC-25 | User completes maintenance checklist in order. |
| Removal workflow | UC-26 through UC-30 | User completes removal checklist in order. |

## Use Case Index

### General

| ID | User Goal | Required System Behavior | Acceptance Signal |
| --- | --- | --- | --- |
| UC-01 | Launch App | Show home screen with glasses logo and app name. | App starts on home screen with primary navigation visible. |
| UC-02 | Select a Procedure | Let user choose Insert, Maintenance, or Remove from Procedures. | Selecting each option starts the matching workflow. |
| UC-03 | Connect to XREAL Glasses | Pair with XREAL glasses and push AR checklist overlays to the HUD. | Connected glasses show the current app overlay. |
| UC-04 | Use Voice Input for Navigation | Support voice navigation between Home, Procedures, Settings, and Exit. | Spoken navigation commands trigger the same route changes as tap input. |
| UC-05 | Receive Audio Prompt | Read the current checklist step aloud. | New active step triggers audible prompt unless muted. |
| UC-06 | Talk to AI Assistant | Accept natural spoken questions for clarifications, warnings, or suggestions. | User receives an appropriate spoken and/or visible AI response. |
| UC-07 | Receive AI Safety Alert | Flag risks and remind user about missed or important steps. | Safety alert appears in the overlay and is saved to the procedure log. |
| UC-08 | Display AR Overlay on Glasses | Show checklist steps and visual cues on XREAL glasses. | HUD shows current step, progress, and relevant alerts. |
| UC-09 | Use App Offline | Keep core app behavior usable without WiFi. | Procedure checklist can start, progress, prompt, and complete offline. |
| UC-10 | Open Settings | Provide Appearance, Terms of Service, and Privacy Policy from Settings. | Settings screen exposes all required settings/legal pages. |
| UC-11 | View Procedure Log | Show completed procedure log from homepage. | User can review AI observations, alerts, warnings, missed steps, and timestamps. |
| UC-12 | Exit App | Close app from home screen. | Exit command or button terminates the app cleanly. |

### Insert Procedure

| ID | User Goal | Required System Behavior | Acceptance Signal |
| --- | --- | --- | --- |
| UC-13 | Start Insertion Procedure | Start the step-by-step insertion checklist after user selects Insert. | Insert workflow opens at the first insertion step. |
| UC-14 | Verify Sterile Field Setup | Prompt user to confirm sterile field setup. | User must confirm sterile field setup before continuing. |
| UC-15 | Hand Hygiene Reminder | Remind user to perform hand hygiene before proceeding. | Hand hygiene prompt appears and is read aloud. |
| UC-16 | Follow Insertion Steps | Walk through site prep, gloving, draping, and catheter placement. | Steps are shown in order and completion state is tracked. |
| UC-17 | Advance to Next Step | Move forward by voice command or tap. | "Next" or tap advances exactly one allowed step. |
| UC-18 | Confirm Line Inserted | Capture user confirmation that insertion is complete. | App moves to verification phase only after confirmation. |
| UC-19 | Verify Dressing Applied | Prompt user to confirm proper dressing is applied. | Dressing verification is required before completion. |
| UC-20 | Complete Insertion Procedure | Finish workflow and save AI log. | Completion screen appears and log entry is persisted. |

### Maintenance Procedure

| ID | User Goal | Required System Behavior | Acceptance Signal |
| --- | --- | --- | --- |
| UC-21 | Start Maintenance Procedure | Start the step-by-step maintenance checklist after user selects Maintenance. | Maintenance workflow opens at the first maintenance step. |
| UC-22 | Check Dressing Condition | Prompt user to inspect and assess current dressing. | Dressing condition prompt appears before maintenance steps continue. |
| UC-23 | Follow Maintenance Steps | Walk through hand hygiene, dressing change, line flush, and site inspection. | Steps are shown in order and completion state is tracked. |
| UC-24 | Advance to Next Step | Move forward by voice command or tap. | "Next" or tap advances exactly one allowed step. |
| UC-25 | Complete Maintenance Procedure | Finish workflow and save AI log. | Completion screen appears and log entry is persisted. |

### Removal Procedure

| ID | User Goal | Required System Behavior | Acceptance Signal |
| --- | --- | --- | --- |
| UC-26 | Start Removal Procedure | Start the step-by-step removal checklist after user selects Remove. | Removal workflow opens at the first removal step. |
| UC-27 | Follow Removal Steps | Walk through hand hygiene, clamp line, remove catheter, apply pressure, and dress site. | Steps are shown in order and completion state is tracked. |
| UC-28 | Advance to Next Step | Move forward by voice command or tap. | "Next" or tap advances exactly one allowed step. |
| UC-29 | Confirm Line Removed | Capture user confirmation that catheter was removed. | Completion can continue only after line removal confirmation. |
| UC-30 | Complete Removal Procedure | Finish workflow and save AI log. | Completion screen appears and log entry is persisted. |

## Cross-Cutting Acceptance Criteria

- Checklist steps cannot be skipped out of order.
- Every procedure completion creates a durable local log.
- Voice and tap inputs lead to the same state transitions.
- AR overlay, mobile UI, audio prompt, and log state stay synchronized.
- Offline mode degrades gracefully for AI features while preserving checklist execution.
- Safety alerts are visible, audible when appropriate, and timestamped in the log.
