#!/usr/bin/env python3
"""
parse_metadata.py — Parses Salesforce Data Cloud metadata from force-app/main/default/
and outputs a structured JSON payload used by the HTML generator.

Usage:
  python3 parse_metadata.py --base <force-app/main/default path> --output <out.json>
"""

import argparse, json, os, xml.etree.ElementTree as ET
from collections import defaultdict

NS = 'http://soap.sforce.com/2006/04/metadata'

def t(tag): return f'{{{NS}}}{tag}'

def parse_xml(path):
    try:
        tree = ET.parse(path)
        return tree.getroot()
    except Exception:
        return None

def children_dict(el):
    d = {}
    for child in el:
        local = child.tag.split('}')[-1]
        d[local] = child.text
    return d

# ── Data Stream Templates ─────────────────────────────────────────────────────

def parse_stream_templates(base):
    streams = []
    d = os.path.join(base, 'dataStreamTemplates')
    if not os.path.isdir(d): return streams
    for fn in sorted(os.listdir(d)):
        if not fn.endswith('.xml'): continue
        root = parse_xml(os.path.join(d, fn))
        if root is None: continue
        m = children_dict(root)
        cat = m.get('objectCategory', '')
        cat_short = cat.split('.')[-1] if '.' in cat else cat
        streams.append({
            'label':   m.get('masterLabel', ''),
            'bundle':  m.get('dataSourceBundleDefinition', ''),
            'refresh': m.get('refreshMode', ''),
            'category': cat_short,
            'dso':     m.get('dataSourceObject', ''),
        })
    return streams

# ── Data Source Objects ───────────────────────────────────────────────────────

DTYPE_MAP = {'S':'String','N':'Number','D':'Date','F':'DateTime','B':'Boolean','E':'Email','I':'Integer'}

def dtype_label(d): return DTYPE_MAP.get(d, d or '?')

def parse_dso(path):
    root = parse_xml(path)
    if root is None: return None
    fields = []
    data_source = None
    for el in root:
        local = el.tag.split('}')[-1]
        if local == 'dataSource':
            data_source = el.text
        elif local == 'dataSourceFields':
            m = children_dict(el)
            fields.append({
                'name':        m.get('fullName', ''),
                'label':       m.get('masterLabel', m.get('fullName', '')),
                'datatype':    dtype_label(m.get('datatype', '')),
                'isFormula':   m.get('isFormula') == 'true',
                'formula':     m.get('fieldFormula', ''),
                'kq':          m.get('srcKeyQualifier'),
                'required':    m.get('isDataRequired') == 'true',
                'recMod':      m.get('isRecordModified') == 'true',
                'primaryIdx':  m.get('primaryIndexOrder'),
            })
    # derive DLO name from file path
    fn = os.path.basename(path)
    dso_name = fn.replace('.dataSourceObject-meta.xml', '')
    return {
        'dsoName': dso_name,
        'dataSource': data_source,
        'fields': fields,
    }

def parse_all_dsos(base):
    result = {}
    d = os.path.join(base, 'dataSourceObjects')
    if not os.path.isdir(d): return result
    for fn in sorted(os.listdir(d)):
        if not fn.endswith('.xml'): continue
        key = fn.replace('.dataSourceObject-meta.xml', '')
        data = parse_dso(os.path.join(d, fn))
        if data:
            result[key] = data
    return result

# ── Field Mappings ────────────────────────────────────────────────────────────

def parse_field_mappings(base):
    """Returns dict: dso_key -> list of {src_field, dmo, dmo_field}"""
    result = defaultdict(list)
    d = os.path.join(base, 'dataSrcDataModelFieldMaps')
    if not os.path.isdir(d): return result
    for fn in sorted(os.listdir(d)):
        if not fn.endswith('.xml'): continue
        root = parse_xml(os.path.join(d, fn))
        if root is None: continue
        m = children_dict(root)
        src = m.get('sourceField', '')
        tgt = m.get('targetField', '')
        if '.' not in src or '.' not in tgt: continue
        dso_key = src.split('.')[0]
        src_field = src.split('.')[-1].replace('__c', '')
        tgt_parts = tgt.split('.')
        dmo = tgt_parts[0]
        dmo_field = tgt_parts[-1].replace('__c', '').replace('ssot__', '') if len(tgt_parts) > 1 else ''
        result[dso_key].append({'src_field': src_field, 'dmo': dmo, 'dmo_field': dmo_field})
    return dict(result)

# ── Identity Resolution ───────────────────────────────────────────────────────

def parse_identity_resolution(base):
    d = os.path.join(base, 'dataKitObjectTemplates')
    if not os.path.isdir(d): return None
    # Look for Individual.dataKitObjectTemplate-meta.xml
    path = os.path.join(d, 'Individual.dataKitObjectTemplate-meta.xml')
    if not os.path.isfile(path): return None
    root = parse_xml(path)
    if root is None: return None
    payload_text = None
    for el in root.iter():
        if el.tag.split('}')[-1] == 'entityPayload':
            payload_text = el.text
            break
    if not payload_text: return None
    try:
        payload = json.loads(payload_text)
    except Exception:
        return None

    match_rules = []
    for rule in payload.get('matchRules', []):
        for c in rule.get('criteria', []):
            mr = {
                'label':       rule.get('label', ''),
                'dmo':         c.get('entityName', ''),
                'field':       c.get('fieldName', ''),
                'matchType':   c.get('matchMethodType', ''),
                'caseSensitive': c.get('caseSensitiveMatch', False),
                'matchOnBlank':  c.get('shouldMatchOnBlank', False),
            }
            if c.get('partyIdentificationInfo'):
                mr['partyType'] = c['partyIdentificationInfo'].get('partyType', '')
                mr['partyName'] = c['partyIdentificationInfo'].get('partyName', '')
            match_rules.append(mr)

    recon_rules = []
    for rule in payload.get('reconciliationRules', []):
        sources = [s.get('name', '') for s in rule.get('sources', [])]
        recon_rules.append({
            'sourceDmo':    rule.get('entityName', ''),
            'unifiedDmo':   rule.get('unifiedDmoName', ''),
            'strategy':     rule.get('ruleType', ''),
            'ignoreEmpty':  rule.get('shouldIgnoreEmptyValue', False),
            'sources':      sources,
        })

    return {
        'matchRules': match_rules,
        'reconRules': recon_rules,
        'doesRunAutomatically': payload.get('doesRunAutomatically', False),
    }

# ── Data Graphs ───────────────────────────────────────────────────────────────

def parse_data_graph(path):
    root = parse_xml(path)
    if root is None: return None
    payload_text = None
    for el in root.iter():
        if el.tag.split('}')[-1] == 'entityPayload':
            payload_text = el.text
            break
    if not payload_text: return None
    try:
        payload = json.loads(payload_text)
    except Exception:
        return None

    graph_meta = {
        'type':              payload.get('type', ''),
        'cacheDuration':     payload.get('cacheDurationInDays'),
        'maxRecords':        payload.get('maxRecordsCached'),
        'fullRefreshFreq':   None,
    }
    fc = payload.get('fullRefreshConfig', {})
    if fc and fc.get('schedule'):
        sched = fc['schedule']
        graph_meta['fullRefreshFreq'] = f"every {sched.get('frequency')} {sched.get('timeGranularity','')}"

    def topk_str(node):
        tkf = node.get('topKFilterCriteria') or {}
        if not tkf: return None
        limit = tkf.get('limit')
        orders = tkf.get('orderCriteria', [])
        if orders:
            o = orders[0]
            return f"TopK={limit} ORDER BY {o.get('fieldApiName')} {o.get('sortOrder','')}"
        return f"TopK={limit}" if limit else None

    def parse_node(node, depth=0):
        name = node.get('projectedName') or node.get('name') or '?'
        paths = node.get('path', [])
        join = None
        if paths:
            p = paths[0]
            join = f"{p.get('parentFieldName')} → {p.get('fieldName')}"
        fields = [f.get('fieldName', '').replace('__c', '')
                  for f in node.get('fields', []) if f.get('fieldName')]
        children = [parse_node(c, depth+1) for c in node.get('relatedObjects', [])]
        return {
            'name': name,
            'join': join,
            'topk': topk_str(node),
            'fields': fields,
            'children': children,
        }

    src = payload.get('sourceObject', {})
    return {**graph_meta, 'root': parse_node(src)}

def parse_all_graphs(base):
    d = os.path.join(base, 'dataKitObjectTemplates')
    result = {}
    if not os.path.isdir(d): return result
    for fn in sorted(os.listdir(d)):
        if not fn.endswith('.xml'): continue
        if 'DataGraph' not in fn and 'dataGraph' not in fn and 'data_graph' not in fn.lower(): continue
        key = fn.replace('.dataKitObjectTemplate-meta.xml', '')
        data = parse_data_graph(os.path.join(d, fn))
        if data:
            result[key] = data
    return result

# ── Bundle grouping ───────────────────────────────────────────────────────────

def group_streams_by_bundle(streams):
    bundles = defaultdict(list)
    for s in streams:
        bundles[s['bundle']].append(s)
    return dict(bundles)

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', required=True, help='Path to force-app/main/default')
    parser.add_argument('--output', required=True, help='Output JSON path')
    args = parser.parse_args()

    base = args.base
    print(f"Parsing metadata from: {base}")

    streams     = parse_stream_templates(base)
    dsos        = parse_all_dsos(base)
    mappings    = parse_field_mappings(base)
    ir          = parse_identity_resolution(base)
    graphs      = parse_all_graphs(base)
    bundles     = group_streams_by_bundle(streams)

    output = {
        'streams':  streams,
        'bundles':  bundles,
        'dsos':     dsos,
        'mappings': mappings,
        'ir':       ir,
        'graphs':   graphs,
    }

    with open(args.output, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"✓ Parsed: {len(streams)} streams, {len(dsos)} DSOs, "
          f"{sum(len(v) for v in mappings.values())} mappings, "
          f"{len(graphs)} graphs")
    print(f"✓ Output written to: {args.output}")

if __name__ == '__main__':
    main()
