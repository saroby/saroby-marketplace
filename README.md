# saroby-marketplace

Claude Code marketplace for saroby's plugins.

## Install

```bash
/plugin marketplace add saroby/saroby-marketplace
```

Then install individual plugins:

```bash
/plugin install codex-util@saroby-marketplace
```

## Plugins

| Plugin | Description | Source |
|---|---|---|
| `codex-util` | Use Codex AI features via the ChatGPT subscription path (no Platform API key) | [saroby/codex-util](https://github.com/saroby/codex-util) |
| `nanobanana-mcp` | Google Gemini image generation MCP server (Nano Banana) — flash and pro modes | [saroby/nanobanana-mcp](https://github.com/saroby/nanobanana-mcp) |
| `andrej-karpathy-skills` | Behavioral guidelines to reduce common LLM coding mistakes | [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills) |
| `cc-plugin-codex` | Run Claude Code and Claude models inside Codex for review, rescue, and tracked background workflows | [sendbird/cc-plugin-codex](https://github.com/sendbird/cc-plugin-codex) |
| `design-prototype` | Build working clickable product prototypes for co-design — `product.html` (real interactions) + `design.html` (ClaudeDesign panel), iterate via the Claude terminal | local |
| `balsamiq-mockups-mcp` | MCP server that lets Claude create and edit Balsamiq Wireframes (.bmpr) files programmatically | [saroby/BalsamiqMockupsMCP](https://github.com/saroby/BalsamiqMockupsMCP) |
| `mcp-appstore` | MCP server for Google Play / Apple App Store scraping — ASO research (search, reviews, keywords, similar apps), auto-installs on first launch | [appreply-co/mcp-appstore](https://github.com/appreply-co/mcp-appstore) (wrapper: local) |
| `app-store-connect-cli-skills` | Agent Skills for the `asc` CLI — TestFlight, builds, submissions, metadata sync, screenshots, signing, IAP/subscriptions automation for your own apps | [rorkai/app-store-connect-cli-skills](https://github.com/rorkai/app-store-connect-cli-skills) |
