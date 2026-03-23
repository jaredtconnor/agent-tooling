---
name: install-linctl
description: Install and configure linctl, a fast Linear CLI tool for managing issues, projects, and comments. Use when the user mentions linctl, wants to set up Linear CLI access, needs Linear integration without MCP, or says "install linctl".
version: 1.0.0
---
# Install linctl

Install [linctl](https://github.com/dorkitude/linctl) — a Linear CLI built for agents and humans. Significantly faster than the Linear MCP for issue management.

## Detection

Check if already installed:

```
linctl --version
```

If installed, check auth:

```
linctl auth status
```

If both pass, tell the user linctl is ready and skip installation.

## Installation

### macOS / Linux (Homebrew)

```bash
brew tap dorkitude/linctl
brew install linctl
```

### Windows (from GitHub release)

1. Detect latest release tag:

```powershell
$release = Invoke-RestMethod -Uri "https://api.github.com/repos/dorkitude/linctl/releases/latest"
$tag = $release.tag_name
```

2. Download the Windows binary:

```powershell
$url = "https://github.com/dorkitude/linctl/releases/download/$tag/linctl-windows-amd64.exe"
$dest = "$env:LOCALAPPDATA\Programs\linctl"
New-Item -ItemType Directory -Path $dest -Force | Out-Null
Invoke-WebRequest -Uri $url -OutFile "$dest\linctl.exe"
```

3. Add to PATH if not already present:

```powershell
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($currentPath -notlike "*$dest*") {
    [Environment]::SetEnvironmentVariable("Path", "$currentPath;$dest", "User")
    $env:Path = "$env:Path;$dest"
}
```

4. Verify:

```powershell
linctl --version
```

### From Source (any platform with Go installed)

```bash
git clone https://github.com/dorkitude/linctl.git
cd linctl
make deps
make build
make install
```

## Authentication

After installation, ask the user how they want to authenticate:

**Option A — Interactive auth (recommended):**

Run `linctl auth` which prompts for a Linear API key interactively. Tell the user:
- Go to Linear Settings > API > Personal API keys
- Create a new key
- Paste it when prompted

**Option B — Direct API key (if user provides one):**

If the user provides an API key directly, set it via environment variable:

```bash
# Unix
export LINCTL_API_KEY="lin_api_..."
```

```powershell
# Windows
$env:LINCTL_API_KEY = "lin_api_..."
```

Then run `linctl auth status` to verify.

**Option C — Environment variable (for CI or persistent use):**

Add `LINCTL_API_KEY` to shell profile for persistence. The env var takes precedence over stored credentials.

## Verification

After install and auth, run:

```
linctl whoami
```

This confirms both installation and authentication are working. Show the output to the user.

## Quick Reference

After successful setup, inform the user of key commands:

| Command | Purpose |
|---------|---------|
| `linctl issue get XXX-123 --json` | Get issue details |
| `linctl issue list --team ENG --json` | List team issues |
| `linctl issue create --title "..." --team ENG` | Create issue |
| `linctl issue update XXX-123 --state "Done"` | Update issue state |
| `linctl comment create XXX-123 --body "..."` | Add comment |
| `linctl project list --json` | List projects |
| `linctl issue search "query" --json` | Search issues |

Always use `--json` flag when calling from agents for structured output.
