# d360-blueprint

A Claude Code skill that generates a fully self-contained HTML documentation file from Salesforce Data Cloud metadata.

## What it documents

- **Data Streams** — field tables with formulas and DMO mappings
- **Identity Resolution** — match rules and reconciliation rules
- **Data Graphs** — card hierarchy with join conditions and TopK filters

The output is a single `.html` file with all CSS, JS, and images embedded inline — shareable by email or link, no dependencies.

## Usage

Invoke in Claude Code with phrases like:

- "generate blueprint"
- "document this org"
- "create html from metadata"
- "d360 blueprint"

Claude will ask for a **brand name** and a **metadata source** (local folder path or org alias), then run the pipeline automatically.

## How it works

1. Optionally retrieves metadata from a connected Salesforce org via `sf project retrieve`
2. Parses metadata with `scripts/parse_metadata.py`
3. Generates the HTML document with `scripts/generate_html.py`

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/parse_metadata.py` | Reads `force-app/main/default/` and outputs a structured JSON file |
| `scripts/generate_html.py` | Takes the JSON and renders a self-contained HTML blueprint |

## Installation

This skill is part of the [my-skills](https://github.com/everanngitmaker) plugin collection. Copy the skill directory into your Claude Code skills folder:

```bash
cp -r d360-blueprint ~/.claude/plugins/marketplaces/my-skills/plugins/my-skills/skills/
```
