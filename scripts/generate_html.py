#!/usr/bin/env python3
"""
generate_html.py — Generates the Data 360 Blueprint HTML from parsed metadata JSON.

Usage:
  python3 generate_html.py --data <metadata.json> --brand <BrandName> --output <out.html>
"""

import argparse, json, html as H, re
from collections import defaultdict
from datetime import date

def e(s): return H.escape(str(s) if s else '')

# ── CSS ───────────────────────────────────────────────────────────────────────

CSS = """
  :root {
    --blue:#0070d2;--blue-dark:#005ba1;--green:#2e844a;--orange:#e65c00;
    --purple:#7526e3;--gray1:#f3f3f3;--gray2:#e0e0e0;--gray3:#706e6b;
    --formula-bg:#1e1e2e;--formula-fg:#cdd6f4;
  }
  * { box-sizing:border-box; }
  body { font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;margin:0;color:#1a1a1a;font-size:14px; }
  h1 { font-size:2rem;margin:0 0 .5rem; }
  h2 { font-size:1.4rem;border-bottom:3px solid var(--blue);padding-bottom:.4rem;margin-top:2rem; }
  h3 { font-size:1.1rem;color:var(--blue-dark);margin:1.5rem 0 .5rem; }
  h4 { font-size:.95rem;margin:1rem 0 .3rem;color:#333; }
  a  { color:var(--blue);text-decoration:none; }
  a:hover { text-decoration:underline; }
  #sidebar {
    position:fixed;top:0;left:0;width:220px;height:100vh;
    overflow-y:auto;background:#16325c;color:#fff;padding:1rem .75rem;
    font-size:12px;z-index:100;
  }
  #sidebar h2 { color:#fff;border-color:rgba(255,255,255,.3);font-size:.9rem;margin:1rem 0 .4rem; }
  #sidebar a  { color:#b0cff5;display:block;padding:.15rem 0; }
  #sidebar a:hover { color:#fff; }
  #sidebar .nav-group { margin-bottom:.5rem; }
  #sidebar .nav-sub   { padding-left:.8rem; }
  #main { margin-left:220px;padding:2rem;max-width:1200px; }
  table { border-collapse:collapse;width:100%;margin:.75rem 0 1.5rem;font-size:13px; }
  th { background:var(--blue);color:#fff;padding:.5rem .75rem;text-align:left;white-space:nowrap; }
  tr:nth-child(even) td { background:#f7f9fc; }
  td { padding:.4rem .75rem;vertical-align:top;border-bottom:1px solid var(--gray2); }
  .tbl-wide th,.tbl-wide td { padding:.35rem .5rem;font-size:12px; }
  .badge { display:inline-block;padding:.15rem .5rem;border-radius:12px;font-size:11px;font-weight:600;white-space:nowrap; }
  .badge-upsert  { background:#d4edda;color:#155724; }
  .badge-partial { background:#fff3cd;color:#856404; }
  .badge-profile { background:#d1ecf1;color:#0c5460; }
  .badge-related { background:#e2d9f3;color:#6f42c1; }
  .badge-formula { background:#fde8d8;color:#9e2f00; }
  .badge-field   { background:#e8f4e8;color:#1a5c1a; }
  .badge-kq      { background:#e8d5f5;color:#5b1fa8;font-size:10px; }
  .badge-req     { background:#ffd6d6;color:#8b0000;font-size:10px; }
  .badge-recmod  { background:#ffe4b5;color:#7a4900;font-size:10px; }
  .badge-idx     { background:#d0e8ff;color:#003d7a;font-size:10px; }
  .formula-cell { max-width:500px; }
  pre.formula {
    background:var(--formula-bg);color:var(--formula-fg);
    padding:.6rem .8rem;border-radius:6px;overflow-x:auto;
    font-size:11px;line-height:1.5;margin:.25rem 0;
    white-space:pre-wrap;word-break:break-all;
  }
  .explain { color:#444;font-size:12px;margin-top:.3rem;font-style:italic; }
  .card { border:1px solid var(--gray2);border-radius:8px;padding:1rem;margin-bottom:1.5rem; }
  .card-header {
    background:var(--gray1);border-radius:6px;padding:.5rem .75rem;
    margin-bottom:.75rem;display:flex;gap:.5rem;align-items:center;flex-wrap:wrap;
  }
  .card-header strong { font-size:1rem; }
  .section-note { background:#fffbf0;border-left:4px solid #f0ad00;padding:.5rem .75rem;margin:.5rem 0 1rem;font-size:12px;border-radius:0 4px 4px 0; }
  .warn { background:#fff0f0;border-left:4px solid #c00; }
  /* Matrix */
  .matrix-wrap { overflow-x:auto;margin:1rem 0 2rem; }
  .matrix { border-collapse:collapse;font-size:11px; }
  .matrix th { padding:0; }
  .matrix td { padding:0;border:1px solid #e0e0e0; }
  .matrix .stream-label {
    text-align:right;padding:.25rem .5rem .25rem .25rem;
    font-size:11px;white-space:nowrap;font-weight:600;
    border:none;border-right:2px solid #ccc;width:1px;
  }
  .matrix .dmo-header-wrap {
    writing-mode:vertical-rl;transform:rotate(180deg);
    white-space:nowrap;padding:.5rem .3rem;
    font-size:10px;font-weight:600;height:160px;
    vertical-align:bottom;text-align:left;display:block;
  }
  .matrix .dot-cell { width:28px;height:28px;text-align:center;vertical-align:middle; }
  .matrix .dot { width:14px;height:14px;border-radius:50%;display:inline-block; }
  .matrix .group-header { padding:0;height:6px; }
  .matrix .stream-group-spacer { height:6px;background:#f5f5f5; }
  .matrix-legend { display:flex;gap:1.5rem;flex-wrap:wrap;margin-bottom:1rem;font-size:12px;align-items:center; }
  .matrix-legend-item { display:flex;align-items:center;gap:.4rem; }
  .matrix-legend-dot { width:12px;height:12px;border-radius:50%;display:inline-block; }
  /* Data graph nodes */
  .dg-tree { padding:1.5rem 1rem; }
  .dg-node {
    border:2px solid #ccc;border-radius:8px;padding:.6rem .9rem;
    display:block;font-size:12px;font-family:"SF Mono",monospace;
    font-weight:700;white-space:nowrap;overflow-x:auto;
  }
  .dg-node-root   { border-color:var(--blue-dark);background:#e8f0fe;color:var(--blue-dark); }
  .dg-node-bridge { border-color:var(--purple);background:#f3ebff;color:var(--purple); }
  .dg-node-std    { border-color:var(--green);background:#e8f5ea;color:var(--green); }
  .dg-node-custom { border-color:var(--orange);background:#fff0e0;color:var(--orange); }
  .dg-node-label  { font-size:10px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;opacity:.7;display:block;margin-bottom:2px; }
  .dg-node-name   { font-size:13px; }
  .dg-node-meta   { font-size:11px;font-weight:400;color:#555;margin-top:.35rem;border-top:1px solid #ddd;padding-top:.35rem;white-space:nowrap;overflow-x:auto; }
  .dg-node-meta code { background:rgba(0,0,0,.06);padding:0 3px;border-radius:3px;font-size:10px; }
  .dg-node-filter { font-size:11px;font-weight:400;color:#555;margin-top:.3rem;white-space:nowrap;overflow-x:auto; }
  .dg-node-fields { font-size:10px;font-weight:400;color:#444;margin-top:.3rem;line-height:1.6;white-space:nowrap;overflow-x:auto; }
  .dg-node-fields code { background:rgba(0,0,0,.06);padding:0 2px;border-radius:2px; }
  .dg-children { margin-left:2.5rem;border-left:2px solid #ddd;padding-left:1rem;margin-top:.5rem; }
  .dg-child-row { margin-bottom:.75rem; }
  .dg-child-row:last-child { margin-bottom:0; }
"""

# ── Formula explanations (generic patterns) ──────────────────────────────────

def explain_formula(name, formula):
    """Generate a human-readable explanation for common formula patterns."""
    f = formula or ''
    if 'NOW()' in f:
        return 'Captures the current ingestion timestamp.'
    if re.match(r'^"[^"]+"$', f.strip()):
        return 'Hardcoded constant string value.'
    if 'CONCAT(' in f and ('|' in f or "'|'" in f):
        return 'Composite primary key built by concatenating key fields with a "|" separator.'
    if 'LOWER(' in f and 'TRIM(' in f and 'SELECT(' in f and 'A-Za-z0-9' in f and '@' in f:
        return 'Extracts and normalises an email address using regex validation. Returns empty string if not a valid email.'
    if re.match(r"^IF\(.*=='null'", f) or re.match(r"^IF\(sourceField\['.+'\]=='null'", f):
        return 'Null-guard: returns empty string if the value is the literal "null" or blank; otherwise passes through the source value.'
    if 'LOWER(' in f and 'sourceField' in f and 'TRIM' not in f and 'SELECT' not in f:
        return 'Lowercase version of the source field for case-insensitive search.'
    if 'FIND(' in f and 'delete' in f.lower():
        return 'Soft-delete detection: returns true if the changeType field contains "delete" (case-insensitive).'
    if 'REPLACE(' in f and 'COALESCE(' in f:
        return 'Returns source value, substituting a default when the value is null or the literal string "null".'
    if 'E164' in name.upper() or ('SUBSTRING(' in f and 'FIND(' in f and 'phones_number' in f):
        return 'Normalises phone number to E.164 format: strips extension, removes spaces/leading zeros, validates US format, prepends +1 or +.'
    if 'REPLACE(' in f and '[^a-zA-Z0-9]' in f and 'SELECT' not in f:
        return 'Strips all non-alphanumeric characters for fuzzy search matching.'
    if 'LEFT(' in f and 'postalCode' in f.lower():
        return 'Extracts 5-digit ZIP for US, or strips non-alphanumeric for non-US postal codes. Used for fuzzy address search.'
    if 'ISEMPTY(' in f and 'preferred' in f.lower():
        return 'Returns true if the "preferred" flag is set and truthy, false otherwise.'
    if 'IF(' in f and (',true,' in f or ',false,' in f):
        return 'Converts a boolean source field to a true/false string value.'
    if f.startswith('"test"') or f == '"test"':
        return '⚠️ Hardcoded placeholder value — appears to be a test/stub, not a real value.'
    if 'RIGHT(' in f and '@' in f:
        return 'Extracts the domain portion of an email address (everything after "@"), lowercased.'
    return ''

# ── HTML generation helpers ───────────────────────────────────────────────────

def badge(cls, text):
    return f'<span class="badge {cls}">{e(text)}</span>'

def field_row(f):
    name     = f.get('name', '')
    dtype    = f.get('datatype', '')
    is_form  = f.get('isFormula', False)
    formula  = f.get('formula', '')
    kq       = f.get('kq')
    required = f.get('required', False)
    rec_mod  = f.get('recMod', False)
    pidx     = f.get('primaryIdx')
    label    = f.get('label', name)

    flags = []
    if kq:       flags.append(badge('badge-kq',     f'kq: {kq}'))
    if required: flags.append(badge('badge-req',    'required'))
    if rec_mod:  flags.append(badge('badge-recmod', 'recordModified'))
    if pidx:     flags.append(badge('badge-idx',    'primary key'))

    kind_badge = badge('badge-formula', 'Formula') if is_form else badge('badge-field', 'Source')

    row = f'<tr><td><code>{e(name)}</code></td><td>{e(dtype)}</td><td>{kind_badge}</td>'
    if is_form:
        expl = explain_formula(name, formula)
        row += f'<td class="formula-cell"><pre class="formula">{e(formula)}</pre>'
        if expl: row += f'<div class="explain">{e(expl)}</div>'
        row += '</td>'
    else:
        row += f'<td>{e(label)}</td>'
    row += f'<td>{" ".join(flags)}</td></tr>'
    return row

def fields_table(fields):
    rows = ''.join(field_row(f) for f in fields)
    return (
        '<table class="tbl-wide"><thead>'
        '<tr><th>Field Name</th><th>Type</th><th>Kind</th><th>Formula / Label</th><th>Flags</th></tr>'
        f'</thead><tbody>{rows}</tbody></table>'
    )

def mapping_table(mappings):
    """Group by DMO and render tables."""
    by_dmo = defaultdict(list)
    for m in mappings:
        by_dmo[m['dmo']].append((m['src_field'], m['dmo_field']))
    parts = []
    for dmo in sorted(by_dmo):
        parts.append(f'<h4>{e(dmo)}</h4>')
        parts.append('<table class="tbl-wide"><thead><tr><th>Source Field (DSO)</th><th>DMO Field</th></tr></thead><tbody>')
        for sf, df in sorted(by_dmo[dmo]):
            parts.append(f'<tr><td><code>{e(sf)}</code></td><td><code>{e(df)}</code></td></tr>')
        parts.append('</tbody></table>')
    return '\n'.join(parts) if parts else '<p><em>No mappings found.</em></p>'

def stream_card(stream, dso_data, stream_mappings, brand):
    label    = stream['label']
    refresh  = stream['refresh']
    category = stream['category']
    dso_key  = stream['dso']

    refresh_badge  = badge('badge-upsert', refresh) if refresh == 'UPSERT' else badge('badge-partial', refresh)
    category_badge = badge('badge-profile', category) if category == 'Profile' else badge('badge-related', category)

    slug = label.replace(' ', '-').replace('_', '-').lower()
    anchor = f'stream-{slug}'

    parts = [f'<div class="card" id="{anchor}">']
    parts.append(f'<div class="card-header"><strong>{e(label)}</strong> {refresh_badge} {category_badge} '
                 f'<span style="color:#555;font-size:12px">DSO: <code>{e(dso_key)}</code></span></div>')

    # Detect unmapped / typo fields
    if dso_data:
        mapped_src_fields = {m['src_field'] for m in stream_mappings}
        for f in dso_data.get('fields', []):
            # Check for obvious typos: field not mapped and name looks like a duplicate with slight difference
            if f['name'] not in mapped_src_fields and not f.get('isFormula'):
                parts.append(f'<div class="section-note warn">⚠️ Field <code>{e(f["name"])}</code> is present in the DSO but not mapped to any DMO.</div>')

    # Fields table
    if dso_data:
        parts.append('<h4>Fields</h4>')
        parts.append(fields_table(dso_data.get('fields', [])))

    # Mappings
    parts.append('<h4>DMO Mappings</h4>')
    parts.append(mapping_table(stream_mappings))

    parts.append('</div>')
    return '\n'.join(parts)

# ── Matrix ────────────────────────────────────────────────────────────────────

def build_matrix(streams, mappings, dsos):
    """Build stream→DMO mapping matrix."""
    # Determine all DMOs
    all_dmos = set()
    stream_dmo_map = {}
    for s in streams:
        dso_key = s['dso']
        dmo_set = {m['dmo'] for m in mappings.get(dso_key, [])}
        stream_dmo_map[s['label']] = (dso_key, dmo_set)
        all_dmos.update(dmo_set)

    # Classify DMOs
    def classify_dmo(name):
        if 'Extended_Search' in name or 'Search__dlm' in name: return 'search'
        if name.startswith('ssot__'): return 'profile'
        return 'event'

    grp_colors = {'profile': '#0070d2', 'search': '#7526e3', 'event': '#e65c00'}
    grp_labels = {'profile': 'Standard Profile DMOs', 'search': 'Extended Search DMOs', 'event': 'Business Event DMOs'}
    grp_tints  = {'profile': '#e8f0fe', 'search': '#f3ebff', 'event': '#fff0e0'}

    # Sort DMOs: profile first, then search, then event
    dmo_order = {'profile': 0, 'search': 1, 'event': 2}
    sorted_dmos = sorted(all_dmos, key=lambda d: (dmo_order[classify_dmo(d)], d))

    # Stream group colors (assign by bundle)
    bundle_colors = {}
    color_cycle = ['#0c7abf', '#2e844a', '#e65c00', '#7526e3', '#b36800', '#c23934',
                   '#0d7356', '#8b2fc9', '#c4711c', '#2055a5']
    bundles_seen = {}
    for s in streams:
        b = s['bundle']
        if b not in bundles_seen:
            bundles_seen[b] = color_cycle[len(bundles_seen) % len(color_cycle)]
        bundle_colors[s['label']] = bundles_seen[b]

    # Header row: colored group bars
    group_row = '<tr><th class="stream-label"></th>'
    dmo_row   = '<tr><th class="stream-label"></th>'
    for dmo in sorted_dmos:
        grp   = classify_dmo(dmo)
        color = grp_colors[grp]
        tint  = grp_tints[grp]
        # Short label
        short = dmo.replace('ssot__','').replace('__dlm','').replace('_All_Sites','').replace('_',' ')
        group_row += f'<th class="group-header" style="background:{color}"></th>'
        dmo_row   += f'<th style="background:{tint}"><div class="dmo-header-wrap" style="color:{color}">{e(short)}</div></th>'
    group_row += '</tr>'
    dmo_row   += '</tr>'

    # Data rows, with spacers between bundles
    rows = [group_row, dmo_row]
    prev_bundle = None
    for s in streams:
        if prev_bundle and s['bundle'] != prev_bundle:
            rows.append(f'<tr class="stream-group-spacer"><td colspan="{len(sorted_dmos)+1}"></td></tr>')
        prev_bundle = s['bundle']

        color = bundle_colors[s['label']]
        _, dmo_set = stream_dmo_map[s['label']]
        row = f'<tr><td class="stream-label" style="border-left:3px solid {color}">{e(s["label"])}</td>'
        for dmo in sorted_dmos:
            grp = classify_dmo(dmo)
            if dmo in dmo_set:
                row += f'<td class="dot-cell"><span class="dot" style="background:{grp_colors[grp]}"></span></td>'
            else:
                row += '<td class="dot-cell"></td>'
        row += '</tr>'
        rows.append(row)

    matrix_html = f'<div class="matrix-wrap"><table class="matrix">\n{"".join(rows)}\n</table></div>'

    # Legend: stream bundles + DMO types
    legend = '<div class="matrix-legend"><strong style="font-size:12px">Streams:</strong>'
    for bundle, color in bundles_seen.items():
        legend += f'<span class="matrix-legend-item"><span class="matrix-legend-dot" style="background:{color};border-radius:2px;width:14px;height:10px"></span>{e(bundle)}</span>'
    legend += '&nbsp;&nbsp;<strong style="font-size:12px">DMOs:</strong>'
    for grp in ['profile', 'search', 'event']:
        legend += f'<span class="matrix-legend-item"><span class="matrix-legend-dot" style="background:{grp_colors[grp]}"></span>{grp_labels[grp]}</span>'
    legend += '</div>'

    return legend + matrix_html

# ── Data Graph node rendering ─────────────────────────────────────────────────

def node_type(name, depth):
    """Heuristic to classify graph nodes."""
    if depth == 0: return 'root',    'dg-node-root',   'Root'
    if 'IdentityLink' in name or 'Bridge' in name: return 'bridge', 'dg-node-bridge', 'Bridge'
    if name.startswith('ssot__'): return 'std', 'dg-node-std', 'Standard'
    return 'custom', 'dg-node-custom', 'Custom'

def render_graph_node(node, depth=0):
    name   = node.get('name', '?')
    join   = node.get('join')
    topk   = node.get('topk')
    fields = node.get('fields', [])
    children = node.get('children', [])

    _, css_class, type_label = node_type(name, depth)

    parts = [f'<div class="dg-node {css_class}">']
    parts.append(f'<span class="dg-node-label">{type_label}</span>')
    parts.append(f'<span class="dg-node-name">{e(name)}</span>')
    if join:
        parts.append(f'<div class="dg-node-meta">Join: <code>{e(join)}</code></div>')
    if topk:
        parts.append(f'<div class="dg-node-filter">Filter: {e(topk)}</div>')
    if fields:
        field_codes = ' '.join(f'<code>{e(f)}</code>' for f in fields)
        parts.append(f'<div class="dg-node-fields">Fields: {field_codes}</div>')
    parts.append('</div>')

    html = '\n'.join(parts)

    if children:
        child_html = '\n'.join(
            f'<div class="dg-child-row">{render_graph_node(c, depth+1)}</div>'
            for c in children
        )
        html += f'\n<div class="dg-children">{child_html}</div>'

    return html

def render_graph(key, graph):
    meta_items = []
    if graph.get('type'):        meta_items.append(badge('badge-upsert', graph['type']))
    if graph.get('cacheDuration'): meta_items.append(f'<span style="color:#555;font-size:12px">cacheDurationInDays: {graph["cacheDuration"]}</span>')
    if graph.get('maxRecords'):  meta_items.append(f'<span style="color:#555;font-size:12px">maxRecordsCached: {graph["maxRecords"]:,}</span>')
    if graph.get('fullRefreshFreq'): meta_items.append(f'<span style="color:#555;font-size:12px">fullRefresh: {e(graph["fullRefreshFreq"])}</span>')

    parts = [f'<div class="card"><div class="card-header"><strong>{e(key)}</strong> {" ".join(meta_items)}</div></div>']
    root_node = graph.get('root')
    if root_node:
        parts.append(f'<div class="dg-tree"><div class="dg-child-row">{render_graph_node(root_node)}</div></div>')
    return '\n'.join(parts)

# ── Sidebar ───────────────────────────────────────────────────────────────────

def build_sidebar(brand, bundles, graphs):
    parts = [
        f'<nav id="sidebar">',
        f'<div style="font-weight:700;font-size:1rem;color:#fff;margin-bottom:1rem">{e(brand)} Data 360 Blueprint</div>',
        '<div class="nav-group"><h2>Overview</h2>',
        '<a href="#overview">Solution Summary</a>',
        '<a href="#overview-matrix">Stream → DMO Matrix</a>',
        '<a href="#overview-diagram">Data Model Overview</a>',
        '</div>',
        '<div class="nav-group"><h2>Data Streams</h2>',
    ]
    for bundle, streams in sorted(bundles.items()):
        b_slug = bundle.replace(' ', '-').lower()
        parts.append(f'<a href="#bundle-{b_slug}">{e(bundle)}</a>')
        parts.append('<div class="nav-sub">')
        for s in streams:
            slug = s['label'].replace(' ', '-').replace('_', '-').lower()
            parts.append(f'<a href="#stream-{slug}">↳ {e(s["label"])}</a>')
        parts.append('</div>')
    parts.append('</div>')
    parts.append('<div class="nav-group"><h2>Identity Resolution</h2>')
    parts.append('<a href="#ir-match">Match Rules</a>')
    parts.append('<a href="#ir-recon">Reconciliation Rules</a>')
    parts.append('</div>')
    parts.append('<div class="nav-group"><h2>Data Graphs</h2>')
    for gkey in sorted(graphs.keys()):
        slug = gkey.replace(' ', '-').replace('_', '-').lower()
        parts.append(f'<a href="#dg-{slug}">{e(gkey)}</a>')
    parts.append('</div>')
    parts.append('</nav>')
    return '\n'.join(parts)

# ── Full document ─────────────────────────────────────────────────────────────

def generate_html(data, brand):
    streams  = data.get('streams', [])
    bundles  = data.get('bundles', {})
    dsos     = data.get('dsos', {})
    mappings = data.get('mappings', {})
    ir       = data.get('ir')
    graphs   = data.get('graphs', {})

    out = []

    # Head
    out.append(f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(brand)} Data 360 Blueprint</title>
<style>
{CSS}
</style>
</head>
<body>''')

    # Sidebar
    out.append(build_sidebar(brand, bundles, graphs))

    # Main
    out.append('<main id="main">')
    out.append(f'<h1>{e(brand)} Data 360 Blueprint</h1>')

    # ── Section 1: Solution Overview
    out.append('<h2 id="overview">1. Solution Overview</h2>')
    n_streams = len(streams)
    n_bundles = len(bundles)
    out.append(f'<p>The solution consists of <strong>Data Streams</strong> ({n_streams} streams across {n_bundles} source bundles), <strong>Identity Resolution</strong>, and <strong>Data Graphs</strong> ({len(graphs)} graphs).</p>')

    out.append('<h3 id="overview-matrix">Stream → Data Model Object Mapping</h3>')
    out.append('<p>Each filled dot indicates that the stream contributes data to that DMO. Streams are grouped by source bundle; DMO columns are grouped by type.</p>')
    out.append(build_matrix(streams, mappings, dsos))

    out.append('<h3 id="overview-diagram">Data Model Overview</h3>')
    out.append('<p><em>To include a data model diagram, embed an image here.</em></p>')

    # ── Section 2: Data Streams
    out.append('<h2 id="data-streams">2. Data Streams</h2>')
    out.append('<p>Each stream ingests data from a source system into a Data Lake Object (DLO), then maps fields to one or more Data Model Objects (DMOs). '
               f'Fields marked {badge("badge-formula","Formula")} are computed; fields marked {badge("badge-field","Source")} are pass-through from the source.</p>')

    for bundle, bundle_streams in sorted(bundles.items()):
        b_slug = bundle.replace(' ', '-').lower()
        refresh = bundle_streams[0]['refresh'] if bundle_streams else ''
        cat     = bundle_streams[0]['category'] if bundle_streams else ''
        refresh_badge = badge('badge-upsert', refresh) if refresh == 'UPSERT' else badge('badge-partial', refresh)
        cat_badge     = badge('badge-profile', cat) if cat == 'Profile' else badge('badge-related', cat)
        out.append(f'<h2 id="bundle-{b_slug}">Bundle: {e(bundle)}</h2>')
        out.append(f'<p>{refresh_badge} {cat_badge}</p>')

        for s in bundle_streams:
            dso_key   = s['dso']
            dso_data  = dsos.get(dso_key)
            stream_mappings = mappings.get(dso_key, [])
            out.append(stream_card(s, dso_data, stream_mappings, brand))

    # ── Section 3: Identity Resolution
    out.append('<h2 id="identity-resolution">3. Identity Resolution</h2>')
    if ir:
        auto = 'Yes' if ir.get('doesRunAutomatically') else 'No'
        out.append(f'<div class="card"><div class="card-header"><strong>Individual</strong> '
                   f'<span class="badge badge-profile">IdentityResolution</span> '
                   f'<span style="color:#555;font-size:12px">Auto-runs: {auto}</span></div>'
                   f'<p>Unifies guest records across data sources into a single <code>UnifiedIndividual__dlm</code>.</p>'
                   f'</div>')

        # Match rules
        out.append('<h3 id="ir-match">Match Rules</h3>')
        out.append('<table><thead><tr><th>#</th><th>Rule Label</th><th>DMO</th><th>Field</th>'
                   '<th>Match Type</th><th>Case Sensitive</th><th>Match on Blank</th><th>Filters</th></tr></thead><tbody>')
        for i, mr in enumerate(ir.get('matchRules', []), 1):
            filters = ''
            if mr.get('partyType'): filters = f'partyIdentificationTypeId = "{e(mr["partyType"])}", name = "{e(mr.get("partyName",""))}"'
            out.append(f'<tr><td>{i}</td><td><strong>{e(mr["label"])}</strong></td>'
                       f'<td><code>{e(mr["dmo"])}</code></td><td><code>{e(mr["field"])}</code></td>'
                       f'<td>{e(mr["matchType"])}</td><td>{"Yes" if mr["caseSensitive"] else "No"}</td>'
                       f'<td>{"Yes" if mr["matchOnBlank"] else "No"}</td><td>{filters}</td></tr>')
        out.append('</tbody></table>')

        # Reconciliation rules
        out.append('<h3 id="ir-recon">Reconciliation Rules</h3>')
        out.append('<table><thead><tr><th>Source DMO</th><th>Unified DMO</th><th>Strategy</th>'
                   '<th>Ignore Empty</th><th>Notes</th></tr></thead><tbody>')
        for rr in ir.get('reconRules', []):
            notes = ''
            if rr['strategy'] == 'SourceSequence':
                srcs = ', '.join(f'<code>{e(s)}</code>' for s in rr.get('sources', []))
                notes = f'Preferred source(s): {srcs}. Values from this source always win over others in the sequence.'
                notes += ('<br><br><strong>Recommendation:</strong> Use LastUpdated / Ignore Empty Values to allow '
                          'the Unified Individual record to be updated in real-time.')
            elif rr['strategy'] == 'MostFrequent':
                notes = 'The value that appears most often across all matched source records wins.'
            elif rr['strategy'] == 'LastUpdated':
                notes = 'The most recently updated source record\'s value wins.'
            out.append(f'<tr><td><code>{e(rr["sourceDmo"])}</code></td>'
                       f'<td><code>{e(rr["unifiedDmo"])}</code></td>'
                       f'<td><strong>{e(rr["strategy"])}</strong></td>'
                       f'<td>{"Yes" if rr["ignoreEmpty"] else "No"}</td>'
                       f'<td>{notes}</td></tr>')
        out.append('</tbody></table>')

        out.append('''<div class="section-note">
<strong>Strategy definitions:</strong><br>
<strong>SourceSequence</strong> — a ranked list of data sources; the first with a non-empty value wins.<br>
<strong>MostFrequent</strong> — the value appearing most often across matched records wins.<br>
<strong>LastUpdated</strong> — the value from the most recently updated source record wins.
</div>''')
    else:
        out.append('<p><em>No Identity Resolution configuration found in metadata.</em></p>')

    # ── Section 4: Data Graphs
    out.append('<h2 id="data-graphs">4. Data Graphs</h2>')
    out.append('<p>Data Graphs pre-compute and cache related data around a root DMO for real-time API access. '
               'Each node defines its join path, a TopK limit for related records, and projected fields.</p>')
    if graphs:
        for gkey, graph in sorted(graphs.items()):
            slug = gkey.replace(' ', '-').replace('_', '-').lower()
            out.append(f'<h3 id="dg-{slug}">{e(gkey)}</h3>')
            out.append(render_graph(gkey, graph))
    else:
        out.append('<p><em>No Data Graph configurations found in metadata.</em></p>')

    # Footer
    today = date.today().strftime('%Y-%m-%d')
    out.append(f'<hr style="margin-top:3rem;border-color:#ddd">')
    out.append(f'<p style="color:#888;font-size:12px;text-align:center">{e(brand)} Data 360 Blueprint &mdash; {today}</p>')
    out.append('</main></body></html>')

    return '\n'.join(out)

# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data',   required=True, help='Path to parsed metadata JSON')
    parser.add_argument('--brand',  required=True, help='Brand name (e.g. Acme)')
    parser.add_argument('--output', required=True, help='Output HTML path')
    args = parser.parse_args()

    with open(args.data) as f:
        data = json.load(f)

    html = generate_html(data, args.brand)

    with open(args.output, 'w') as f:
        f.write(html)

    print(f'✓ HTML written to: {args.output}')

if __name__ == '__main__':
    main()
