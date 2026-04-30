# Phase 1 Build Session — 2026-04-27

**Working directory at start:** `C:/Users/zaara/CLABSIApp1/`
**Unity project root (after refactor):** `C:/Users/zaara/CLABSIApp1/unity/`
**Active scene:** `unity/Assets/Scenes/SampleScene.unity`
**Driver of the session:** Zaara
**Goal:** Complete Phase 1 of the CLABSI AR app (UI shell, checklists, TTS, voice nav, log) per `docs/product/CLABSI_AR_Build_Guide_v2.md`.

---

## TL;DR

By end of session, Phase 1 is **8 of 8 priorities done** and the app is **running on the XREAL Beam Pro Android device** (model `XREAL X4000`, package `com.layerjot.clabsiar`, version `0.1.0`):

- Five screens: Home, Procedures, StepChecklist, Log, Settings — all wired through a single `ScreenManager` on the Canvas.
- All three procedure JSON files (Insert, Maintenance, Remove) loaded via `ProcedureLoader.Resources.Load`.
- Step-by-step procedure flow with no-skip enforcement and a working "Done" completion path that writes to the log.
- TTS reads each step aloud on device (via Android `TextToSpeech` JNI; respects `SettingsStore.IsMuted`).
- Voice commands work end-to-end on device via Android `SpeechRecognizer` JNI; 9 phrases recognized; orange Mic button on every screen for push-to-talk.
- Editor keyboard fallback (N/D/H/P/L/S/I/M/R) for testing dispatch without speaking.
- Procedure completion log persisted at `Application.persistentDataPath/procedure_log.json`.
- Settings (Mute toggle) persisted via `PlayerPrefs`.

Nothing has been committed to git yet — `.git` is initialized but the tree is uncommitted.

---

## What was already in place at session start

- A boilerplate Unity 6 project (Unity 6000.4.0f1, Android target, IL2CPP, URP) with only `SampleScene.unity` (empty) and the standard `Readme.cs` template asset.
- The MCP Unity server already configured at port 8090 (`com.gamelovers.mcp-unity`) with `.mcp.json` launching it.
- The build guide at `docs/product/CLABSI_AR_Build_Guide_v2.md` (the master reference for all 5 phases).
- An old-style `claude.md` with placeholders, no actual conventions filled in.

---

## Inputs Zaara gave, in order — and what was done in response

### 1. `claude init` — "create the CLAUDE.md"

Explored the codebase and rewrote `CLAUDE.md` with: the actual Unity version, MCP server context, build-and-test commands, the system architecture diagram, the `action_cmd` Phase 4 schema, folder conventions, the procedure-step counts table, and a "current state" callout. Replaced the placeholder `[fill in yours]` with the real `6000.4.0f1`.

### 2. "let's start building. what should we build first?"

Recommended the **data layer first** (JSON + C# model) because every later system depends on it. Got approval and built:
- `Assets/Scripts/Data/ProcedureData.cs` — `StepData` and `ProcedureData` `[Serializable]` classes for `JsonUtility`.
- `Assets/Scripts/Data/ProcedureLoader.cs` — static `Load(procedureId)` calling `Resources.Load<TextAsset>`.
- `Assets/Resources/Checklists/insert.json` (9 steps), `maintenance.json` (6 steps), `remove.json` (7 steps).
- Note: had to use `Resources/Checklists/` (not `Data/Checklists/` as originally proposed) because `Resources.Load` only works from a folder named `Resources`.

### 3. "what are the pros/cons of the two approaches?" (Home screen via MCP vs code-only)

Explained tradeoffs, recommended **hybrid** — controller in code (testable, diff-able), scene authored via MCP (visual, follows Unity conventions). Zaara picked hybrid.

### 4. "go with hybrid"

Wrote `HomeScreenController.cs`, expanded `.claude/settings.local.json` to allow scene-write MCP tools, and built the Home screen:
- Canvas (ScreenSpaceOverlay + CanvasScaler scale-with-screen-size 1080×1920) + EventSystem.
- HomeScreen panel with 5 buttons (Procedures, Log, Settings, Exit) in a `VerticalLayoutGroup`.
- Title text "CLABSI AR".
- Button auto-wiring via `transform.Find` by name in `Start()` (no inspector wiring needed).

Hit the **first Play Mode error** here — the EventSystem had `StandaloneInputModule` (legacy) but the project uses the new Input System. Replaced with `InputSystemUIInputModule` and disabled the legacy module.

### 5. "how do i play test it?"

Walked through Editor Play Mode + Console; user confirmed home buttons logged correctly.

### 6. "everything plays well… what next?"

Recommended **Procedures page + ScreenManager** (the navigation system). Built:
- `ScreenManager.cs` — singleton on Canvas, `Show(name)` toggles which child screen is active.
- `ProceduresPageController.cs` — wires Insert/Maintenance/Remove/Back buttons.
- Updated `HomeScreenController` to call `ScreenManager.Instance.Show(...)` on each click.
- ProceduresPage scene panel (mirrors HomeScreen layout) with 3 procedure buttons + a gray Back button. Inactive at startup.

**Discovered the MCP "asset refresh" gotcha:** new `.cs` files written via the Write tool don't get a `.meta` file automatically — Unity skips them at compile time. Found by getting a `CS0103: ScreenManager not found` error. Fix: call `mcp__unity__execute_menu_item("Assets/Refresh")` before `recompile_scripts` whenever new files are added. **Saved as memory** (`mcp_unity_workflow.md`) so future sessions don't re-hit it.

### 7. "everything worked. let's move to next thing. where will this json live?"

Clarified the JSON is already at `Assets/Resources/Checklists/`. Then built the **StepChecklist screen** — the meaty one:
- `StepChecklistController.cs` — finds children (Title, ProgressIndicator, StepCard, BottomBar buttons) via `transform.Find` in `Awake`. Public `Begin(ProcedureData)` method. Tracks `currentStepIndex`, renders one step, on Next advances or completes (writing log entry), on Back clears and returns. No-skip enforced at the controller level.
- ProceduresPageController updated to load JSON via `ProcedureLoader`, find StepChecklistController via `FindAnyObjectByType(FindObjectsInactive.Include)`, call `Begin`.
- Built the StepChecklistScreen scene: dark `StepCard` background, Title at top, ProgressIndicator ("Step X of N"), StepTitle (bold) + StepInstruction (multi-line wrapped), BottomBar with Back (gray) + Next (green, label flips to "Done" on last step). Inactive at start.

### 8. "everything plays well and i see the .json file with the log" (after Log feature)

For the **procedure log**, built:
- `ProcedureLogEntry.cs` — serializable: procedureId, procedureName, completedAtIso (UTC), stepsCompleted, totalSteps.
- `ProcedureLogStore.cs` — static, reads/writes `Application.persistentDataPath/procedure_log.json` via `JsonUtility`. In-memory cache.
- StepChecklistController writes a log entry on completion (last step + Next).
- `LogPageController.cs` — on enable, clears prior clones, loads entries, clones an `EntryTemplate` per entry (newest first), shows `EmptyState` text when empty. Back returns home.
- LogPage scene with Title, EntriesContainer (`VerticalLayoutGroup`), EntryTemplate (inactive, used as clone source), EmptyState text, BackButton.

### 9. "let's finish the settings"

Built the **Settings page**:
- `SettingsStore.cs` — static; `IsMuted` getter/setter backed by `PlayerPrefs`.
- `SettingsPageController.cs` — auto-wires MuteButton (toggles + flips label "Audio: On" / "Audio: Muted") and BackButton.
- SettingsPage scene mirrors HomeScreen/ProceduresPage layout. Inactive at start.

User confirmed the mute setting **persisted across sessions** as expected.

### 10. "what next?" → TTS plan agreed → "go ahead"

Built **TtsService** with platform branching:
- Editor: just `Debug.Log($"[TTS] Speaking: {text}")`.
- Android: `AndroidJavaObject` for `android.speech.tts.TextToSpeech` + `AndroidJavaProxy` listener for `OnInitListener`. Queues speech if init isn't complete; drains queue once `setLanguage(Locale.US)` returns.
- `Speak()` early-outs on `SettingsStore.IsMuted`.
- `Stop()` cancels in-flight speech.
- StepChecklistController calls `Speak(title + ". " + instruction)` in `Render()` and `Stop()` on Back / completion.
- Attached as a component to Canvas.

### 11. "i want to test on android but confused how i would command the app with my voice"

Explained push-to-talk model (tap Mic, say one command), the Mic button location (initially only on StepChecklist, in BottomBar), and that Phase 4 will add wake word for true hands-free. Then:

### 12. "extend parser, then i will test"

Extended voice command set from 4 to **9 phrases** (the original Next/Done/Home/Procedures plus Log/Settings/Insert/Maintenance/Remove). Updated `VoiceCommand` enum, `VoiceCommandRouter.Parse` (with synonyms — "forward", "continue", "complete", "finish", "maintain", "removal", etc.), and `Dispatch` (Insert/Maintenance/Remove start the corresponding procedure from any screen).

Added Editor keyboard shortcuts: `N D H P L S I M R`.

### 13. "yes, i want to simulate the stt for all the commands"

Made all 5 screens voice-ready:
- New `MicButtonBinder.cs` — generic component that wires its own `Button.onClick` to `VoiceService.Instance.StartListening()`.
- Added orange floating MicButton (220×220, bottom-right anchor) to HomeScreen, ProceduresPage, LogPage, SettingsPage.
- Attached `MicButtonBinder` to all of them, including the existing one on StepChecklist's BottomBar (replaces the old StepChecklist mic-wiring).

### 14. "tell me how i can [test on android]" → "i don't see Identification in Player Settings" → "should this be under the project hierarchy?" → "i don't see Window → Analysis → Android Logcat"

Walked through:
- Enabling Developer Options + USB debugging on the phone.
- Player Settings → Other Settings → Identification (which is **nested**, not top-level).
- Build And Run; APK location convention (anywhere outside `Assets/`).
- Installing the Android Logcat package via Package Manager → Unity Registry.

### 15. "i am getting a no android device connected" → "nothing shows up in `adb devices`" → "i don't see where developer options are" → "i changed cables and turned on dev options" → "there are two ports… i plugged into the other one and it worked"

Diagnosed and resolved:
- USB-debug-cable not the same as charging-cable (PS5 controllers work with charging-only cables).
- Build-number-tap-7-times to unlock Developer Options.
- And the **Beam Pro USB-port quirk:** the **glasses-icon port** is the one that does ADB; the **power-icon port is charge-only**. Counterintuitive — saved as memory `beam_pro_usb_ports.md` after we got the labels right (initially had it backwards).

### 16. "i had to refactor the folder structure of the project. can you make sure you can still connect to unity via mcp?"

Verified MCP still talks to Unity (`get_scene_info` returned the scene). Confirmed the new layout: workspace root has top-level `unity/`, `backend/`, `AI/`, `docs/`, etc. All 16 `.cs` files intact at `unity/Assets/Scripts/...`. Going forward, all file paths in this conversation use full absolute paths.

### 17. "i did the build run but don't know how to run the app"

Explained app drawer / icon location.

### 18. "DeploymentOperationFailedException: No activity in the manifest with action MAIN and category LAUNCHER"

Root cause: the `Assets/Plugins/Android/AndroidManifest.xml` I had created earlier (to declare `RECORD_AUDIO`) had **replaced** Unity's full manifest, leaving no launcher activity. Fix: deleted the custom manifest entirely and wrote `Assets/Editor/AndroidManifestPostProcessor.cs` — implements `IPostGenerateGradleAndroidProject` to **inject** RECORD_AUDIO permission and the `<queries>` block for `android.speech.RecognitionService` into Unity's auto-generated manifest, surgically. Survives Unity manifest changes.

### 19. "it deployed and app seems to be working… i clicked mic… i don't hear any sound or me speaking into it doesn't take any action"

Two separate issues. Started with STT.

### 20. Logcat: `[Voice] Listen failed: SpeechRecognizer should be used only from the application's main thread`

Root cause: Android `SpeechRecognizer` requires the **Android UI main thread**, which is not the same as Unity's main thread. Fix: wrapped the `Listen()` body and `OnDestroy` `destroy()` call in `mainActivity.Call("runOnUiThread", new AndroidJavaRunnable(...))`. STT then worked end-to-end on device.

### 21. "mic is working, but i don't hear anything when i take actions or when i navigate menus"

Clarified that menu navigation is silent by design — only StepChecklist triggers TTS. Then asked for logcat to diagnose TTS.

### 22. Logcat showed TTS init succeeded but no `Speaking:` lines

Root cause: my `Debug.Log("[TTS] Speaking: ...")` was inside the `#else` (Editor) branch only — on Android it was silent. Added explicit logs on the Android path: log `Speaking:` before the JNI call, log `setLanguage` return value, log `speak()` return value.

### 23. New logcat: `setLanguage(US) returned 1`, `Speaking: Sterile Field Setup…`, no `speak() returned non-success`

Engine accepted the speech requests but no audio reached Zaara's ear. Suggested three checks: media volume, audio routing (Beam Pro routes audio through the glasses by default; built-in speaker is small), and an OS-level TTS smoke test.

### 24. "it works now."

Phase 1 done. 🎉

---

## Final scene hierarchy

```
Canvas (+ ScreenManager + TtsService + VoiceService)
├── HomeScreen        Title + ButtonsPanel(Procedures, Log, Settings, Exit) + MicButton
├── ProceduresPage    Title + ButtonsPanel(Insert, Maintenance, Remove, Back) + MicButton          (inactive at start)
├── StepChecklistScreen
│   ├── Title, ProgressIndicator
│   ├── StepCard (StepTitle, StepInstruction)
│   └── BottomBar [Back] [Next/Done] [Mic]                                                          (inactive at start)
├── LogPage           Title + EntriesContainer(EntryTemplate) + EmptyState + BackButton + MicButton (inactive at start)
└── SettingsPage      Title + ButtonsPanel(MuteButton, BackButton) + MicButton                      (inactive at start)
EventSystem (with InputSystemUIInputModule, NOT StandaloneInputModule)
```

## Code structure under `unity/Assets/`

```
Assets/
├── Editor/
│   └── AndroidManifestPostProcessor.cs  ← injects RECORD_AUDIO + queries into manifest
├── Plugins/Android/                     ← (empty; no custom manifest)
├── Resources/Checklists/
│   ├── insert.json
│   ├── maintenance.json
│   └── remove.json
├── Scenes/
│   └── SampleScene.unity                ← only scene, holds everything
└── Scripts/
    ├── Audio/
    │   └── TtsService.cs
    ├── Data/
    │   ├── ProcedureData.cs             ← StepData + ProcedureData
    │   ├── ProcedureLoader.cs           ← Resources.Load<TextAsset>
    │   ├── ProcedureLogEntry.cs
    │   ├── ProcedureLogStore.cs         ← persistentDataPath/procedure_log.json
    │   └── SettingsStore.cs             ← PlayerPrefs IsMuted
    ├── UI/
    │   ├── HomeScreenController.cs
    │   ├── ProceduresPageController.cs
    │   ├── ScreenManager.cs             ← singleton on Canvas, Show(name)
    │   ├── StepChecklistController.cs
    │   ├── LogPageController.cs
    │   └── SettingsPageController.cs
    └── Voice/
        ├── VoiceCommand.cs              ← enum
        ├── VoiceCommandRouter.cs        ← Parse + Dispatch
        ├── VoiceService.cs              ← Editor keyboard + Android SpeechRecognizer
        └── MicButtonBinder.cs           ← reusable Mic button → StartListening
```

## Voice command map

| Phrase (and synonyms) | Editor key | Action |
|---|---|---|
| Next / forward / continue | `N` | Advance one step |
| Done / complete / finish | `D` | Advance (or completes on last step) |
| Home | `H` | Show HomeScreen |
| Procedures | `P` | Show ProceduresPage |
| Log | `L` | Show LogPage |
| Settings | `S` | Show SettingsPage |
| Insert | `I` | Start Insert procedure (works from any screen) |
| Maintenance / maintain | `M` | Start Maintenance procedure |
| Remove / removal | `R` | Start Remove procedure |

---

## Gotchas hit (and recorded as memory where relevant)

1. **Play Mode revert trap.** Scene edits made via MCP while Unity is in Play Mode are silently reverted when Play stops. `save_scene` errors with "This cannot be used during play mode" but by then half a batch may already be lost. Always confirm Play is stopped before scene/component edits. (Memory: `mcp_unity_play_mode.md`.)
2. **New `.cs` files need `Assets/Refresh` before recompile.** When you write a fresh `.cs` via the Write tool, Unity hasn't imported it and `recompile_scripts` excludes it. Call `mcp__unity__execute_menu_item("Assets/Refresh")` first. (Memory: `mcp_unity_workflow.md`.)
3. **Beam Pro USB ports — counterintuitively, the GLASSES-icon port is the data port** (ADB / Build And Run). The power-icon port is charging-only. (Memory: `beam_pro_usb_ports.md`.)
4. **Do not ship a custom `AndroidManifest.xml`** — Unity replaces its full manifest with whatever you put there. Use a build post-processor (`IPostGenerateGradleAndroidProject`) to surgically inject permissions instead.
5. **Android `SpeechRecognizer` insists on the Android UI main thread,** which is not Unity's main thread. Wrap any `recognizer.*` calls in `mainActivity.Call("runOnUiThread", new AndroidJavaRunnable(...))`.
6. **`UnityEngine.Input` is unavailable** when the new Input System is enabled. The legacy `StandaloneInputModule` on EventSystem will throw `InvalidOperationException` on first click. Use `InputSystemUIInputModule` and disable the legacy one. For keyboard shortcuts, use `Keyboard.current.<key>.wasPressedThisFrame` from `UnityEngine.InputSystem`.
7. **Beam Pro audio routes through the glasses by default.** When glasses aren't connected, the small built-in speaker may be quiet. Verify with media-volume slider and an OS-level TTS smoke test before assuming the app is broken.
8. **Logging on Android sometimes hides the message line in Unity Logcat package** but `adb logcat -s Unity:I` from terminal shows it correctly.
9. **`Application.identifier` on Beam Pro:** the device model string is `XREAL X4000`.

---

## What is NOT done yet

- **Git commits.** Repo is initialized but no commits exist. Worth a checkpoint commit now.
- **Workspace-root `CLAUDE.md`.** There's a `unity/CLAUDE.md` but no top-level orientation file pointing at `unity/`, `backend/`, `AI/`, `docs/`, etc.
- **Phase 2 (XREAL glasses integration)** — NRSDK setup, port the Canvas to WorldSpace, route the camera/mic through the glasses hardware, AR HUD overlay. The current build is the foundation to port from.
- **Phase 3+** — Mac FastAPI backend, LangChain agent, ChromaDB, GPT-4o (teammate's responsibility per the build guide).
- **Custom app icon.** Currently shows the default Unity icon on the phone.
- **Procedure-start commands' procedure names are hardcoded** in the Router — could refactor to use `ProcedureLoader` for dynamic lists when more procedures are added.

---

## Suggested next steps

1. **Make a checkpoint commit** so this session's work is saved.
2. **Add a workspace-root CLAUDE.md** that describes the multi-folder layout (`unity/`, `backend/`, etc.).
3. **Phase 2 kickoff:** import NRSDK, set up the Beam Pro pairing, port the existing Canvas to a `WorldSpace` canvas anchored to the right lens of the glasses.
4. **Add a Mic button to the procedure-start commands' source screen visually** — currently the procedure-start voice commands work from the Mic on Home, but the Home Mic icon doesn't hint at which commands are valid. Could surface the command list in the UI (like a "Try saying: Next, Done, Home, Procedures, Log, Settings, Insert, Maintenance, Remove" tooltip near the Mic).

---

## References

- Master build guide: `docs/product/CLABSI_AR_Build_Guide_v2.md`
- Use cases: `docs/product/use-cases.md`
- App build checklist: `docs/product/app-build-checklist.md`
- System diagram: `docs/product/clabsi_ar_system_diagram.svg`
- Unity-side per-project notes: `unity/CLAUDE.md`
- Memory accumulated this session: `~/.claude/projects/C--Users-zaara-CLABSIApp1/memory/` (mcp_unity_workflow.md, mcp_unity_play_mode.md, beam_pro_usb_ports.md)
