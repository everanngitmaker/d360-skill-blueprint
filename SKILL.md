---
name: d360-blueprint
description: >
  Generates a comprehensive, self-contained HTML Blueprint document from Salesforce Data Cloud metadata.
  Use this skill whenever the user wants to document a Data Cloud org, generate a Data 360 blueprint,
  create a build specification, visualize data streams or identity resolution config, or export
  Data Cloud metadata as HTML. Triggers on phrases like "generate blueprint", "document this org",
  "create html from metadata", "d360 blueprint", or "data cloud documentation".
---

# D360 Blueprint Skill

Generates a fully self-contained HTML documentation file from Salesforce Data Cloud metadata.
The output covers: Data Streams (field tables with formulas and DMO mappings), Identity Resolution
(match rules and reconciliation rules), and Data Graphs (visual card hierarchy with join conditions
and TopK filters).

## Step 1 — Gather inputs

Ask the user for:

1. **Brand name** — used to label the document (e.g. "Acme", "Contoso"). No default.
2. **Metadata source** — one of:
   - **Folder path**: a local folder already containing Salesforce metadata (e.g. `"acme-preview copy"`). The skill will look for `force-app/main/default/` inside it, or treat the folder itself as the metadata root if that subdirectory doesn't exist.
   - **Org alias + manifest**: retrieve live from a connected org. Ask for the org alias (e.g. `acme-dev`) and manifest path (default: `manifests/package.xml`).

Ask all required fields in one message. If the user provides a folder path, skip Step 2. If the user provides an org alias, proceed with Step 2.

## Step 2 — Retrieve metadata (skip if folder path provided)

Run the SF CLI retrieve command from the project root (the directory containing `force-app/`):

```bash
sf project retrieve start \
  --manifest <manifest_path> \
  --target-org <alias> \
  --wait 30
```

If the command fails, surface the error to the user before proceeding.

## Step 3 — Resolve the metadata base path

The parser needs the path to the directory that contains subdirectories like `dataStreamTemplates/`, `dataSourceObjects/`, etc.

- If the user gave a **folder path**: check if `<folder>/force-app/main/default/` exists. If so, use that. Otherwise use `<folder>` directly.
- If metadata was **retrieved from an org**: use `force-app/main/default/` relative to the current working directory.

## Step 4 — Parse metadata

The skill directory is:
```
~/.claude/plugins/marketplaces/my-skills/plugins/my-skills/skills/d360-blueprint/
```

Run the parser:

```bash
python3 ~/.claude/plugins/marketplaces/my-skills/plugins/my-skills/skills/d360-blueprint/scripts/parse_metadata.py \
  --base <resolved_base_path> \
  --output /tmp/<brand_lowercase>_metadata.json
```

The parser prints a summary line (streams, DSOs, mappings, graphs). Share this with the user so they can confirm the metadata was found correctly before generating the HTML.

## Step 5 — Generate HTML Blueprint

```bash
python3 ~/.claude/plugins/marketplaces/my-skills/plugins/my-skills/skills/d360-blueprint/scripts/generate_html.py \
  --data /tmp/<brand_lowercase>_metadata.json \
  --brand "<Brand Name>" \
  --output ./<brand_lowercase>-data360-blueprint.html
```

## Step 6 — Report completion

Tell the user:
- The output file path (e.g. `./acme-data360-blueprint.html`)
- A one-line summary of what's inside (N streams, IR rules, N data graphs)
- That the file is fully self-contained and can be opened in any browser or shared as-is

## Notes

- The HTML is self-contained (all CSS, JS, and images embedded inline). It can be emailed or shared without dependencies.
- If a data model diagram image exists (e.g. a `.jpg` or `.png`), the generate script will embed it automatically if passed via `--diagram <path>`. This is optional.
- If the user wants to re-generate with a different brand name or after metadata changes, skip Steps 2–3 and re-run Steps 4–5.
