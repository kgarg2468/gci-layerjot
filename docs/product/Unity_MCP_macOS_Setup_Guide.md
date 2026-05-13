# Unity MCP Setup Guide

**macOS — CLABSI AR Project (AR Health)**

---

## Prerequisites

| Requirement | Details |
| :---- | :---- |
| Unity Hub \+ Unity Editor | **Unity 6000.4.0f1** specifically — install steps in Section 3 |
| Claude Code | Installed and working in your terminal |
| Internet connection | Required for package install |
| Beam Pro USB cable | For deploying builds to XREAL glasses via ADB |

---

## 1 — Install Git

**Step 1 — Check if Git is already installed**

git \--version

If you see a version number, Git is already installed — skip to Section 2\.

**Step 2 — Install via Homebrew (recommended)**

If you don't have Homebrew yet:

/bin/bash \-c "$(curl \-fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

Then install Git:

brew install git

**Step 3 — Or install via Xcode Command Line Tools**

xcode-select \--install

A dialog will appear — follow the prompts. Verify when done:

git \--version   \# should print git version 2.x.x

⚠ After installing Git, fully quit Unity Hub (menu bar → Unity Hub → Quit) and relaunch it so it picks up the new PATH.

---

## 2 — Install Node.js

**Step 1 — Check if Node.js is already installed**

node \--version   \# needs to be v18 or higher

**Step 2 — Install via Homebrew**

brew install node

**Step 3 — Or download from nodejs.org**

Go to [nodejs.org/en/download](https://nodejs.org/en/download) and download the macOS installer (`.pkg`). Run it with default settings. Verify after install:

node \--version

npm \--version

---

## 3 — Install Unity Editor and Android Modules

This project requires **Unity 6000.4.0f1** with the Android build modules. Whether Unity is already installed or not, follow this section to make sure the right version and modules are present and that `adb` is on your PATH.

**Step 1 — Install Unity Hub (if not already)**

Download from [unity.com/download](https://unity.com/download). Open the `.dmg` and drag Unity Hub to Applications. Sign in or create a free Unity account when prompted.

**Step 2 — Install Unity 6000.4.0f1**

In Unity Hub → **Installs** → **Install Editor** → find `6000.4.0f1` under **Official releases** (or the **Archive** tab if it's not in the current list).

In the modules screen, **check all three** under "Platforms":

* ✅ **Android Build Support**
* ✅ **OpenJDK** (nested under Android Build Support)
* ✅ **Android SDK & NDK Tools** (nested under Android Build Support)

Click Install. This takes 10–15 minutes — Android SDK/NDK is large (~3 GB).

**Step 3 — Verify the modules if Unity is already installed**

In Unity Hub → **Installs** → find `6000.4.0f1`. Hover over its row and click the gear icon (or **⋮** menu) → **Add Modules**.

Confirm the three Android modules listed in Step 2 are checked. If any are unchecked, check them and click Install.

**Step 4 — Verify the ADB path**

Unity bundles ADB inside its Android SDK install. After Step 2 or 3, ADB lives at:

/Applications/Unity/Hub/Editor/6000.4.0f1/PlaybackEngines/AndroidPlayer/SDK/platform-tools/adb

Check it exists:

ls /Applications/Unity/Hub/Editor/6000.4.0f1/PlaybackEngines/AndroidPlayer/SDK/platform-tools/adb

If you see the path printed back, the binary is there.

**Step 5 — Add ADB to your shell PATH**

So `adb` works from any terminal:

echo 'export PATH="$PATH:/Applications/Unity/Hub/Editor/6000.4.0f1/PlaybackEngines/AndroidPlayer/SDK/platform-tools"' \>\> \~/.zshrc
source \~/.zshrc

Verify:

adb version   \# should print "Android Debug Bridge version 1.0.x ..."

If `adb version` errors with "command not found," close and reopen your terminal, then try again.

**Step 6 — Plug in the Beam Pro and confirm**

Plug the Beam Pro into the Mac (glasses-icon USB port on the Beam Pro, not the power-icon port). On the Beam Pro screen, tap **Allow** when the "Allow USB debugging?" prompt appears.

adb devices   \# should list one "device" line (not "unauthorized" or empty)

---

## 4 — Open the Unity Project

**Step 1 — Clone or pull the repo**

If you haven't already cloned the repo on the Mac:

git clone https://github.com/kgarg2468/gci-layerjot.git

If you have, make sure it's up to date:

cd gci-layerjot && git pull

**Step 2 — Open the `unity/` folder in Unity Hub**

Unity Hub → **Open** → navigate to the cloned repo → select the `unity/` folder (not the repo root). Unity Hub will recognize the version (`6000.4.0f1`) and open it.

**Step 3 — Wait for first-time package import**

On first open, Unity regenerates `Library/` cache and imports all packages (TMP, XREAL SDK, etc). Takes **5–10 minutes**. Watch the bottom-right progress bar.

**Step 4 — Set build target to Android**

File → Build Settings → select Android → click **Switch Platform**. Wait for Unity to recompile (a few minutes).

---

## 5 — Install the MCP Unity Package

**Step 1 — Open the Package Manager**

In Unity: Window → Package Manager

**Step 2 — Add the package via Git URL**

Click the **\+** button (top left) → **Add package from git URL**, then paste:

https://github.com/CoderGamester/mcp-unity.git

Click Add and wait for Unity to download and compile the package.

⚠ If you get a "No git executable found" error, fully quit and relaunch Unity Hub after installing Git (Section 1).

**Step 3 — Ignore the meta file warning**

You may see: `"Asset has no meta file, but it's in an immutable folder."` This is harmless — ignore it.

**Step 4 — Verify npm install succeeded**

Check the Unity Console for:

\[MCP Unity\] npm install completed successfully in .../Server\~

This confirms the MCP server backend is ready.

---

## 6 — Start the MCP Server in Unity

**Step 1 — Open the MCP Unity panel**

In Unity's top menu: **Tools → MCP Unity → Start Server**

**Step 2 — Confirm it's running**

The Unity Console should show the server is listening on port **8090**. Leave Unity open while using Claude Code.

---

## 7 — Verify the Claude Code MCP Config

Claude Code (the CLI) reads MCP server configuration from a file named `.mcp.json` in the directory where you launch it. **This file is already committed in this repo's root** — you don't need to create or edit `~/.claude/claude_desktop_config.json` (that's a different file used by the Claude Desktop chat app, not Claude Code).

**Step 1 — Inspect the committed config**

In the repo root on your Mac:

cat .mcp.json

You should see something like:

{
  "mcpServers": {
    "unity": {
      "command": "node",
      "args": \["unity/Library/PackageCache/com.gamelovers.mcp-unity@d50c83a273d8/Server\~/build/index.js"\]
    }
  }
}

**Step 2 — Verify the hash matches your local Unity package cache**

The hash after `mcp-unity@` (e.g. `d50c83a273d8`) is generated by Unity when it imports the package. **It may differ on your Mac.** After Unity finishes its first-time package import (Section 4 Step 3), check what hash you actually have:

ls unity/Library/PackageCache/ | grep mcp-unity

If the output shows a different hash, edit `.mcp.json` and replace the hash to match:

nano .mcp.json

Replace `d50c83a273d8` with the hash you got from the `ls` command. Save with Ctrl+O → Enter → Ctrl+X.

⚠ Do not commit this hash change — it's local to your machine. Use `git update-index --skip-worktree .mcp.json` if you want Git to ignore future edits.

**Step 3 — Confirm Unity's MCP server is running**

In Unity: **Tools → MCP Unity → Start Server** (if not already running). Confirm the Console shows port **8090**.

---

## 8 — Test the Connection

**Step 1 — Launch Claude Code from the repo root**

Open a terminal at the repo root (the folder containing `.mcp.json`, not inside `unity/`):

cd \~/gci-layerjot
claude

When Claude Code starts, it reads `.mcp.json` and connects to Unity's MCP server on port 8090.

**Step 2 — Ask Claude Code to do something in Unity**

Try a simple test:

*"Get the active scene info in Unity"*

Claude Code should call `mcp__unity__get_scene_info` and return details about the currently open scene (name, path, root count). If you see scene info come back, the connection works. ✅

If nothing happens or you get an error like "tool not available," check:

* Unity is open and the MCP server is running (Tools → MCP Unity → Start Server)
* Your terminal is in the **repo root**, not inside `unity/`
* The hash in `.mcp.json` matches the directory in `unity/Library/PackageCache/`

---

## Troubleshooting

| Issue | Fix |
| :---- | :---- |
| Git not found after install | Fully quit Unity Hub from the menu bar (not just close the window), then relaunch |
| Package Manager fails to add URL | Edit `Packages/manifest.json` directly and add the dependency manually, then switch back to Unity |
| npm install fails | Verify Node.js is installed: `node --version`. Must be v18+ |
| Claude Code can't connect | Confirm you launched `claude` from the repo root (the folder with `.mcp.json`), not inside `unity/`. Check the hash in `.mcp.json` matches what's in `unity/Library/PackageCache/`. Make sure Unity is open with the MCP server started. |
| MCP Tools menu missing in Unity | The package may not have compiled yet. Check the Console for errors and wait for Unity to finish importing |

---

*AR Health — CLABSI AR Glasses Project | Chapman University Grand Challenges Initiative | March 2026*  
