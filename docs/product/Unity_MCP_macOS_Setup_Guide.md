# Unity MCP Setup Guide

**macOS — CLABSI AR Project (AR Health)**

---

## Prerequisites

| Requirement | Details |
| :---- | :---- |
| Unity Hub \+ Unity Editor | Any recent LTS version (2022.3+ recommended) |
| Claude Code | Installed and working in your terminal |
| Internet connection | Required for package install |

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

## 3 — Create Your Unity Project

**Step 1 — Open Unity Hub → New Project**

Select the 3D template, name your project (e.g. `CLABSIApp`), and click Create.

**Step 2 — Set build target to Android**

File → Build Settings → select Android → click **Switch Platform**. Wait for Unity to recompile.

---

## 4 — Install the MCP Unity Package

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

## 5 — Start the MCP Server in Unity

**Step 1 — Open the MCP Unity panel**

In Unity's top menu: **Tools → MCP Unity → Start Server**

**Step 2 — Confirm it's running**

The Unity Console should show the server is listening on port **8090**. Leave Unity open while using Claude Code.

---

## 6 — Configure Claude Code

**Step 1 — Find (or create) the config folder**

mkdir \-p \~/.claude

**Step 2 — Open the config file**

nano \~/.claude/claude\_desktop\_config.json

**Step 3 — Find your exact package path**

find \~/YOUR\_PROJECT\_NAME/Library/PackageCache \-name "index.js" | grep mcp-unity

Replace `YOUR_PROJECT_NAME` with your Unity project folder name.

**Step 4 — Add the MCP server config**

Paste the following, updating the path with your actual username, project name, and hash from Step 3:

{

  "mcpServers": {

    "unity": {

      "command": "node",

      "args": \["/Users/YOUR\_USERNAME/YOUR\_PROJECT/Library/PackageCache/com.gamelovers.mcp-unity@HASH/Server\~/build/index.js"\]

    }

  }

}

**Step 5 — Save and exit nano**

Ctrl+O  →  Enter  →  Ctrl+X

**Step 6 — Restart Claude Code**

Fully quit and relaunch Claude Code. Unity should appear as a connected MCP tool.

---

## 7 — Test the Connection

**Step 1 — Make sure Unity is open with the MCP server running**

Tools → MCP Unity → Start Server (if not already started).

**Step 2 — Ask Claude Code to do something in Unity**

Try a simple test:

*"Create a new empty GameObject called HomeScreen in the current scene"*

If a GameObject appears in your Unity Hierarchy panel, the connection is working. ✅

---

## Troubleshooting

| Issue | Fix |
| :---- | :---- |
| Git not found after install | Fully quit Unity Hub from the menu bar (not just close the window), then relaunch |
| Package Manager fails to add URL | Edit `Packages/manifest.json` directly and add the dependency manually, then switch back to Unity |
| npm install fails | Verify Node.js is installed: `node --version`. Must be v18+ |
| Claude Code can't connect | Double-check the `index.js` path in your config. Run the `find` command again to get the exact path including the hash |
| MCP Tools menu missing in Unity | The package may not have compiled yet. Check the Console for errors and wait for Unity to finish importing |

---

*AR Health — CLABSI AR Glasses Project | Chapman University Grand Challenges Initiative | March 2026*  
