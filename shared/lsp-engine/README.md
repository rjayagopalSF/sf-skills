# LSP Engine for sf-skills

Language Server Protocol integration for Salesforce development skills in Claude Code.

## Overview

This module provides a shared LSP engine that enables real-time validation of Salesforce files during Claude Code authoring sessions. Currently supports:

- **Agent Script** (`.agent` files) - via Salesforce VS Code extension
- **Apex** (`.cls`, `.trigger` files) - via Salesforce Apex extension

## Prerequisites

### For Agent Script (.agent files)

1. **VS Code with Agent Script Extension**
   - Open VS Code
   - Go to Extensions (Cmd+Shift+X)
   - Search: "Agent Script" by Salesforce
   - Install

2. **Node.js 18+**
   - Required by the LSP server
   - Check: `node --version`

### For Apex (.cls, .trigger files)

1. **VS Code with Salesforce Extension Pack**
   - Open VS Code
   - Go to Extensions (Cmd+Shift+X)
   - Search: "Salesforce Extension Pack"
   - Install

2. **Java 11+ (Adoptium/OpenJDK recommended)**
   - Required by the Apex LSP server
   - Check: `java --version`
   - Download: https://adoptium.net/temurin/releases/

## Usage

### In Hooks (Recommended)

```python
#!/usr/bin/env python3
import sys
import json
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared" / "lsp-engine"))

from lsp_client import get_diagnostics
from diagnostics import format_diagnostics_for_claude

# Read hook input
hook_input = json.load(sys.stdin)
file_path = hook_input.get("tool_input", {}).get("file_path", "")

# Validate .agent files
if file_path.endswith(".agent"):
    result = get_diagnostics(file_path)
    output = format_diagnostics_for_claude(result)
    if output:
        print(output)
```

### Standalone CLI

```bash
# Test LSP validation
python3 lsp_client.py /path/to/file.agent
```

## Module Structure

```
lsp-engine/
├── __init__.py              # Package exports
├── agentscript_wrapper.sh   # Shell wrapper for Agent Script LSP
├── apex_wrapper.sh          # Shell wrapper for Apex LSP
├── lsp_client.py            # Python LSP client (multi-language)
├── diagnostics.py           # Diagnostic formatting
└── README.md               # This file
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LSP_LOG_FILE` | Path to log file | `/dev/null` |
| `NODE_PATH` | Custom Node.js path (Agent Script) | Auto-detected |
| `JAVA_HOME` | Custom Java path (Apex) | Auto-detected |
| `APEX_LSP_MEMORY` | JVM heap size in MB (Apex) | 2048 |

## Troubleshooting

### Agent Script Issues

#### "LSP server not found"

The VS Code Agent Script extension is not installed:
1. Install from VS Code Marketplace
2. Verify: `ls ~/.vscode/extensions/salesforce.agent-script-*`

#### "Node.js not found"

Install Node.js 18+:
- macOS: `brew install node`
- Or download from https://nodejs.org

#### "Node.js version too old"

Upgrade to Node.js 18+:
- macOS: `brew upgrade node`

### Apex Issues

#### "Apex Language Server not found"

The VS Code Salesforce Extension Pack is not installed:
1. Install from VS Code Marketplace: "Salesforce Extension Pack"
2. Verify: `ls ~/.vscode/extensions/salesforce.salesforcedx-vscode-apex-*`
3. Check JAR exists: `ls ~/.vscode/extensions/salesforce.salesforcedx-vscode-apex-*/dist/apex-jorje-lsp.jar`

#### "Java not found"

Install Java 11+:
- macOS: `brew install openjdk@11`
- Or download from https://adoptium.net/temurin/releases/

#### "Java version too old"

Upgrade to Java 11+:
- macOS: `brew install openjdk@21`
- Set JAVA_HOME: `export JAVA_HOME=/opt/homebrew/opt/openjdk@21`

## How It Works

```
1. Hook triggers after Write/Edit on .agent file
         │
         ▼
2. lsp_client.py discovers VS Code extension
         │
         ▼
3. Spawns LSP server via agentscript_wrapper.sh
         │
         ▼
4. Sends textDocument/didOpen with file content
         │
         ▼
5. Parses textDocument/publishDiagnostics response
         │
         ▼
6. Formats errors for Claude → Auto-fix loop
```

## License

MIT - See LICENSE file in repository root.
