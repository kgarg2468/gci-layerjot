# CLABSI AR Glasses App - Build Checklist

Source: formatted from `App Checklist.md` downloaded from Google Drive.

This is an implementation checklist for coding agents. Each item has a stable task ID, related use case IDs, and a short completion test. Use these IDs when creating issues, commits, PR descriptions, and test names.

## Repo Orientation

| Area | Likely Repo Location | Notes |
| --- | --- | --- |
| Unity/XREAL app | `XREALSDK/Assets/` | Primary target for Android/XREAL UI, HUD overlays, voice/tap controls, and procedure flows. |
| Backend AI assistant | `backend/` | Existing FastAPI/LangChain-style backend for AI routing, tools, safety, and RAG. |
| Mac demo client | `mac_client/` | Existing local voice demo path; useful for validating AI behavior before Unity integration. |
| Product docs | `docs/product/` | Use cases and build checklist. |

## Agent Workflow

1. Pick a small vertical slice from this checklist.
2. Read the linked use cases in [use-cases.md](use-cases.md).
3. Implement the feature with the smallest practical code change.
4. Add or update tests where the repo has an appropriate test surface.
5. Record manual device/XREAL verification when automated tests cannot cover the behavior.

## Milestone 1 - Project Setup

| Task ID | Covers | Task | Completion Test |
| --- | --- | --- | --- |
| SETUP-01 | UC-01 | Create or verify Unity 3D project structure. | Unity project opens without missing package errors. |
| SETUP-02 | UC-03, UC-08 | Set Android as the Unity build target. | Android build target is active in Unity settings. |
| SETUP-03 | UC-03, UC-08 | Import and configure XREAL SDK / NRSDK. | XREAL sample or minimal scene renders to glasses. |
| SETUP-04 | UC-03, UC-06 | Configure permissions for camera, microphone, and USB. | Android manifest includes required runtime permissions. |
| SETUP-05 | UC-03 | Test basic XREAL glasses connection and display output. | Connected glasses show a known test scene or overlay. |

## Milestone 2 - App Shell and Navigation

| Task ID | Covers | Task | Completion Test |
| --- | --- | --- | --- |
| HOME-01 | UC-01 | Build home screen with app logo and name. | Launch opens home screen with expected branding. |
| HOME-02 | UC-02 | Add Procedures button. | Tap opens Procedures page. |
| HOME-03 | UC-11 | Add Procedure Log button. | Tap opens Procedure Log page. |
| HOME-04 | UC-10 | Add Settings button. | Tap opens Settings page. |
| HOME-05 | UC-12 | Add Exit button and exit behavior. | Tap or exit command closes the app cleanly. |
| NAV-01 | UC-04 | Implement voice listener for page navigation. | Voice commands are captured and routed. |
| NAV-02 | UC-04 | Map "Home", "Procedures", "Settings", and "Exit" commands. | Each command navigates to the matching destination. |
| NAV-03 | UC-04 | Add fallback tap or gesture navigation. | All navigation has a non-voice fallback. |
| PROC-01 | UC-02 | Build Procedures page UI. | Page shows Insert, Maintenance, and Remove options. |
| PROC-02 | UC-13, UC-21, UC-26 | Wire procedure buttons to workflow starts. | Each button opens the first step of the matching checklist. |

## Milestone 3 - Reusable Checklist System

| Task ID | Covers | Task | Completion Test |
| --- | --- | --- | --- |
| CHECK-01 | UC-13 through UC-30 | Build reusable step-by-step checklist UI component. | Same component can render Insert, Maintenance, and Remove data. |
| CHECK-02 | UC-17, UC-24, UC-28 | Implement one-step-at-a-time progression logic. | Next action advances exactly one valid step. |
| CHECK-03 | UC-17, UC-24, UC-28 | Add voice command progression for "Next" and "Done". | Voice and tap progression produce the same state transition. |
| CHECK-04 | UC-17, UC-24, UC-28 | Highlight current active step. | Current step is visually distinct in app and HUD. |
| CHECK-05 | UC-16, UC-23, UC-27 | Show checked/unchecked completion state. | Completed steps remain visible as completed. |
| CHECK-06 | UC-16, UC-23, UC-27 | Block skipping steps. | Attempted out-of-order navigation is rejected or ignored. |

## Milestone 4 - Procedure Workflows

| Task ID | Covers | Task | Completion Test |
| --- | --- | --- | --- |
| INSERT-01 | UC-13 | Create insertion checklist data in order. | Insert workflow starts with first insertion step. |
| INSERT-02 | UC-14 | Add sterile field setup verification prompt. | User must confirm sterile field before continuing. |
| INSERT-03 | UC-15 | Add hand hygiene reminder prompt. | Hand hygiene prompt appears and is read aloud. |
| INSERT-04 | UC-16 | Add site prep, gloving, draping, and catheter placement steps. | Insert checklist renders all required steps in sequence. |
| INSERT-05 | UC-18 | Add "Line inserted" voice confirmation trigger. | Confirmation moves workflow into verification phase. |
| INSERT-06 | UC-19 | Add dressing application verification prompt. | Dressing verification is required before completion. |
| INSERT-07 | UC-20 | Add insertion completion screen and save log. | Completion creates a persisted insertion log. |
| MAINT-01 | UC-21 | Create maintenance checklist data in order. | Maintenance workflow starts with first maintenance step. |
| MAINT-02 | UC-22 | Add dressing condition inspection prompt. | Dressing inspection prompt appears before maintenance steps continue. |
| MAINT-03 | UC-23 | Add hand hygiene, dressing change, line flush, and site inspection steps. | Maintenance checklist renders all required steps in sequence. |
| MAINT-04 | UC-25 | Add maintenance completion screen and save log. | Completion creates a persisted maintenance log. |
| REMOVE-01 | UC-26 | Create removal checklist data in order. | Removal workflow starts with first removal step. |
| REMOVE-02 | UC-27 | Add hand hygiene, clamp line, remove catheter, apply pressure, and dress site steps. | Removal checklist renders all required steps in sequence. |
| REMOVE-03 | UC-29 | Add "Line removed" voice confirmation trigger. | Confirmation is required before completion. |
| REMOVE-04 | UC-30 | Add removal completion screen and save log. | Completion creates a persisted removal log. |

## Milestone 5 - Audio, AI, and AR Overlay

| Task ID | Covers | Task | Completion Test |
| --- | --- | --- | --- |
| AUDIO-01 | UC-05 | Integrate text-to-speech for reading steps aloud. | New active step is spoken automatically. |
| AUDIO-02 | UC-05 | Add mute/unmute control for audio prompts. | Muted mode suppresses step speech and persists during session. |
| AI-01 | UC-06 | Set up voice-to-text pipeline for user questions. | Spoken question reaches the AI request path as text. |
| AI-02 | UC-06 | Integrate conversational AI response path. | User receives spoken and/or visible answer. |
| AI-03 | UC-06, UC-07 | Provide AI with sterile technique and CLABSI prevention knowledge. | CLABSI questions return procedural guidance from approved knowledge. |
| AI-04 | UC-07 | Implement real-time safety alerts for missed steps and risk flags. | Safety alert appears when a risk condition is detected. |
| AI-05 | UC-07, UC-11 | Log every AI alert, warning, and suggestion with timestamps. | Procedure log contains timestamped AI events. |
| AR-01 | UC-08 | Render checklist UI on XREAL glasses using NRSDK. | HUD shows the current checklist step. |
| AR-02 | UC-08 | Position overlay in a non-obstructive HUD area. | Overlay remains readable without blocking central view. |
| AR-03 | UC-08 | Display current step text and progress indicator. | HUD step text and progress match app state. |
| AR-04 | UC-07, UC-08 | Display AI alerts as overlay popups. | Alerts appear on HUD and clear according to product rules. |
| AR-05 | UC-08 | Test readability for text size, contrast, and brightness. | Text is readable on glasses in expected lighting conditions. |

## Milestone 6 - Logs, Offline Mode, and Settings

| Task ID | Covers | Task | Completion Test |
| --- | --- | --- | --- |
| LOG-01 | UC-11, UC-20, UC-25, UC-30 | Create local storage for procedure logs. | Logs persist after app restart. |
| LOG-02 | UC-11 | Store procedure type, completed steps, timestamps, AI alerts, warnings, and missed steps. | Log record contains all required fields. |
| LOG-03 | UC-11 | Build Procedure Log page accessible from homepage. | User can open log list from home screen. |
| LOG-04 | UC-11 | List past procedures by date and type. | Log list sorts or groups procedures clearly. |
| LOG-05 | UC-11 | Add full log detail view. | User can open one log and inspect all saved events. |
| OFFLINE-01 | UC-09 | Store all checklist definitions locally. | Procedure flow can start without network. |
| OFFLINE-02 | UC-09 | Ensure TTS works offline. | Step prompts are audible without network. |
| OFFLINE-03 | UC-09 | Cache AI locally or provide graceful fallback when offline. | AI path does not block checklist completion offline. |
| OFFLINE-04 | UC-09 | Test full procedure flow without network. | Start, progress, complete, and log a procedure offline. |
| SETTINGS-01 | UC-10 | Build Settings page UI. | Settings page is reachable from home screen. |
| SETTINGS-02 | UC-10 | Add appearance controls for text size, brightness, and overlay opacity. | Controls affect app/HUD rendering. |
| SETTINGS-03 | UC-10 | Add Terms of Service page. | Terms page is reachable from Settings. |
| SETTINGS-04 | UC-10 | Add Privacy Policy page. | Privacy page is reachable from Settings. |

## Milestone 7 - Verification

| Task ID | Covers | Task | Completion Test |
| --- | --- | --- | --- |
| TEST-01 | UC-01 through UC-12 | Test on Android device without glasses in mobile-only mode. | Core navigation and checklist flow work without glasses. |
| TEST-02 | UC-03, UC-08 | Test with XREAL glasses connected. | HUD overlay mirrors app state. |
| TEST-03 | UC-04, UC-17, UC-24, UC-28 | Test voice navigation end to end. | Voice commands navigate pages and advance steps. |
| TEST-04 | UC-13 through UC-30 | Test each procedure checklist start to finish. | Insert, Maintenance, and Remove can all complete and log. |
| TEST-05 | UC-06, UC-07 | Test AI assistant responses during procedure. | AI answers valid procedural questions and blocks unsafe ones. |
| TEST-06 | UC-11 | Test procedure log saves and displays correctly. | Completed procedure log can be reopened after restart. |
| TEST-07 | UC-09 | Test offline mode. | Core checklist flow works with no network. |
| TEST-08 | UC-12 | Test exit and relaunch state persistence. | App exits cleanly and relaunches into expected state. |

## Definition of Done

- Every implemented feature references one or more UC IDs.
- Each procedure workflow can be completed in order.
- Voice, tap, mobile UI, AR HUD, audio prompt, and log state are consistent.
- AI safety alerts are visible, logged, and bounded to procedural support.
- Offline mode preserves core checklist execution.
- Device/XREAL manual verification is recorded for hardware-only behavior.
