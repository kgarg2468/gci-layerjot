# CLABSI AR AI Action Contract

This is the shared Phase 4 contract between Unity/XREAL and the Mac FastAPI backend.

## Backend to Unity

Every `ai_response` keeps the legacy MVP `payload` and also emits the build-guide fields Unity should prefer:

```json
{
  "type": "ai_response",
  "schema_version": "clabsi-ar.v1",
  "session_id": "sess-001",
  "timestamp": "2026-04-29T10:00:00Z",
  "action_cmd": "show_alert",
  "parameters": {
    "severity": "warning",
    "message": "Please confirm hand hygiene before continuing."
  },
  "spoken_response": "Please confirm hand hygiene before continuing.",
  "payload": {
    "intent": "safety_block",
    "spoken_response": "Please confirm hand hygiene before continuing.",
    "action": null
  }
}
```

Supported `action_cmd` values:

- `next_step`: Unity advances the active checklist by one step.
- `prev_step`: Unity moves back one checklist step.
- `show_alert`: Unity displays a HUD alert and speaks `spoken_response`.
- `read_step`: Unity speaks `spoken_response`; optional `parameters.screen` may carry legacy navigation context.
- `flag_breach`: Unity displays a breach advisory, speaks the response, and logs the AI event.
- `end_procedure`: Unity stores the AI summary/compliance data and displays the summary.
- `navigate_home`: Unity navigates to the home screen.

## Unity to Backend

Natural-language request:

```json
{
  "type": "ai_request",
  "session_id": "sess-001",
  "timestamp": "2026-04-29T10:00:00Z",
  "payload": {
    "transcript": "can I move to gloving now",
    "context": {
      "session_id": "sess-001",
      "patient_id": "PAT-123",
      "current_screen": "StepChecklistScreen",
      "procedure_active": true,
      "procedure_id": "insert",
      "procedure_name": "Central Line Insertion",
      "current_step_id": 4,
      "current_step_title": "Gloving",
      "total_steps": 9,
      "completed_step_ids": [1, 2, 3]
    }
  }
}
```

Camera advisory frame:

```json
{
  "type": "camera_frame",
  "session_id": "sess-001",
  "timestamp": "2026-04-29T10:00:00Z",
  "payload": {
    "image_jpeg_base64": "...",
    "context": { "procedure_id": "insert", "current_step_id": 4 },
    "metadata": { "simulated_breach": false }
  }
}
```

Procedure completion:

```json
{
  "type": "procedure_complete",
  "session_id": "sess-001",
  "timestamp": "2026-04-29T10:00:00Z",
  "payload": {
    "procedure_id": "insert",
    "procedure_name": "Central Line Insertion",
    "started_at": "2026-04-29T10:00:00Z",
    "completed_at": "2026-04-29T10:12:00Z",
    "total_steps": 9,
    "completed_step_ids": [1, 2, 3, 4, 5, 6, 7, 8, 9],
    "ai_events": []
  }
}
```

## Safety Boundary

The assistant is advisory. It must not diagnose, recommend medication dosing, or override clinician judgment. Camera detections are advisory until a clinician verifies them.
