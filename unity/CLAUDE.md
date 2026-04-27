# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Unity Android app for CLABSI prevention, targeting XREAL AR glasses.  
Chapman University Grand Challenges Initiative, in partnership with LayerJot.  
Unity version: **6000.4.0f1** — Build target: **Android** (IL2CPP, C# 9.0) — Rendering: **URP**

Full build guide: `../docs/product/CLABSI_AR_Build_Guide_v2.md` — read this before starting any phase.

Note:  This is not a production ready application.  So, let's keep it simple as it's just a demonstration of what is possible.  
---

## MCP / Unity Server

The MCP Unity server runs on **port 8090** and auto-starts when Unity is open. Claude Code connects through it to manipulate the Unity Editor directly. Config lives in `ProjectSettings/McpUnitySettings.json` (this folder) and `../.mcp.json` (repo root).

Before using any `mcp__unity__*` tools that write to the scene, make sure Unity Editor is open and the project is loaded.

Currently permitted MCP operations are listed in `.claude/settings.local.json` (per-developer, not committed). Expand that list as needed when adding write operations.

### MCP server path

`../.mcp.json` points at the MCP Unity server inside Unity's package cache:
`unity/Library/PackageCache/com.gamelovers.mcp-unity@<hash>/Server~/build/index.js`. The hash (`d50c83a273d8` at time of writing) is content-derived from the package version, so it should match across machines on the same package — but `Library/` is regenerated when Unity opens the project, so first-time setup is: clone repo → open `unity/` in Unity Hub → wait for package import → start Claude Code. If the hash differs locally, update the path in `../.mcp.json`.

---

## Build Commands

Unity builds are driven through the Editor or via command-line batch mode:

```bash
# Android build (command-line, replace path as needed)
"C:/Program Files/Unity/Hub/Editor/6000.4.0f1/Editor/Unity.exe" \
  -batchmode -quit \
  -projectPath "C:/Users/zaara/CLABSIApp1" \
  -buildTarget Android \
  -executeMethod BuildScript.BuildAndroid \
  -logFile build.log

# Run Unity Test Framework (Edit Mode tests)
"C:/Program Files/Unity/Hub/Editor/6000.4.0f1/Editor/Unity.exe" \
  -batchmode -quit \
  -projectPath "C:/Users/zaara/CLABSIApp1" \
  -runTests -testPlatform EditMode \
  -logFile test.log
```

For interactive development, build/run directly from **File → Build Settings → Build And Run** inside Unity Editor.

---

## Architecture

The system has two independent workstreams meeting at a WebSocket boundary in Phase 4:

```
XREAL Glasses → Mic → Porcupine wake word → Android STT → ContextManager
  → NativeWebSocket client (Unity/Android)
    → FastAPI WebSocket server (Mac/Python)
      → LangChain agent (Intent Router → Safety Gate → Tool Executor)
        → GPT-4o + ChromaDB RAG
          → { action_cmd, spoken_response } JSON
            → Android TTS + Unity AR overlay
```

**Zaara owns:** Phases 1, 2, 4-Unity — Unity app, Android, XREAL/NRSDK, WebSocket client  
**Teammate owns:** Phases 3, 4-Backend — FastAPI, LangChain, ChromaDB, GPT-4o

### WebSocket action_cmd Schema (Phase 4 contract)

```json
{
  "action_cmd": "show_alert",
  "parameters": { "severity": "warning", "message": "..." },
  "spoken_response": "Please confirm hand hygiene was performed."
}
```

Supported `action_cmd` values: `next_step`, `prev_step`, `show_alert`, `read_step`, `flag_breach`, `end_procedure`, `navigate_home`

---

## Folder Conventions

```
Assets/Scripts/          ← All custom C# MonoBehaviours
Assets/Scenes/           ← Unity scenes
Assets/Prefabs/UI/       ← Reusable UI prefabs
Assets/Data/Checklists/  ← JSON procedure data
```

- **Namespace:** `CLABSIApp` on all custom scripts
- **Naming:** PascalCase MonoBehaviours, matching filename to class name
- **Step skipping:** Hard-blocked at the controller level — never rely on UI alone

---

## Phase 1 Checklist Data

Three procedures stored as JSON in `Assets/Data/Checklists/`:

| Procedure | Steps |
|---|---|
| Insert | sterile field setup → hand hygiene → site prep → gloving → draping → catheter placement → line confirmation → dressing verification → completion (9 steps) |
| Maintenance | dressing inspection → hand hygiene → dressing change → line flush → site inspection → completion (6 steps) |
| Remove | hand hygiene → clamp line → remove catheter → apply pressure → dress site → line removed confirmation → completion (7 steps) |

---

## Current State

Phase 1 is in progress. No custom C# scripts or UI prefabs exist yet. The only scene is `Assets/Scenes/SampleScene.unity` (empty). All Phase 1 work starts from scratch in `Assets/Scripts/`, `Assets/Data/`, and `Assets/Prefabs/`.

Key packages already installed: `com.unity.inputsystem@1.19.0`, `com.unity.render-pipelines.universal@17.4.0`, `com.gamelovers.mcp-unity`. Phase 2 adds NRSDK; Phase 4 adds NativeWebSocket.
