# mcp-appstore

Claude Code plugin wrapper for [appreply-co/mcp-appstore](https://github.com/appreply-co/mcp-appstore) — an MCP server that scrapes the **Google Play Store** and **Apple App Store** for ASO research.

## What you get

Tools exposed to Claude (no auth required, public data only):

- `search_app` — search by term + platform (ios/android)
- `get_app_details` — full metadata for an app
- `fetch_reviews` / `analyze_reviews` — pull and summarize reviews
- `analyze_top_keywords` / `get_keyword_scores` — keyword competitiveness
- `get_similar_apps` — discovery / competitor mapping
- `get_developer_info`, `get_pricing_details`, `get_version_history`, `get_android_categories`

Perfect for: competitor analysis, keyword research, review mining, ASO audits.

## Install

```bash
/plugin marketplace add saroby/saroby-marketplace
/plugin install mcp-appstore@saroby-marketplace
```

## How the wrapper works

The first time the MCP server starts, it:

1. Clones `appreply-co/mcp-appstore` to `$HOME/.cache/claude-mcp-appstore`
2. Runs `npm install --omit=dev` once
3. Boots `node server.js` via stdio

Subsequent launches reuse the cached install (instant). Override the cache location with `MCP_APPSTORE_DIR=/your/path`.

## Requirements

- `node` >= 18
- `git`
- `npm`

## Not affiliated with

Apple, Google, or AppReply.co. This is a community wrapper around an open-source MCP server. Use scraped data responsibly and within the target store's terms.
