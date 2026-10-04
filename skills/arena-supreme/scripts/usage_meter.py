#!/usr/bin/env python3
"""ArenaSupreme: cost-weighted token usage for this session and its helpers, read from the host's
transcripts (Claude Code / Cowork keep them under ~/.claude/projects/<project>/<session>.jsonl and
<session>/subagents/agent-*.jsonl). Weights: cache read 0.1x, cache write 2x, output 5x, input 1x.
Transcripts under-record output tokens, so true totals run a little higher.
Usage: python3 usage_meter.py [--session-file PATH] [--since 2026-10-04T00:22]   (UTC ISO prefix)"""
import argparse, glob, json, os
ap = argparse.ArgumentParser(); ap.add_argument("--session-file"); ap.add_argument("--since", default="")
a = ap.parse_args()
base = os.path.expanduser(os.environ.get("CLAUDE_CONFIG_DIR", "~/.claude")) + "/projects/"
main = a.session_file or max(glob.glob(base + "*/*.jsonl"), key=os.path.getmtime)
subdir = main[:-6] + "/subagents/"
def cost(path):
    seen, tot, steps, first = set(), 0.0, 0, None
    for line in open(path):
        try: r = json.loads(line)
        except Exception: continue
        first = first or r.get("timestamp")
        m = r.get("message") if r.get("type") == "assistant" else None
        if not isinstance(m, dict) or m.get("id") in seen: continue
        seen.add(m.get("id")); u = m.get("usage") or {}; steps += 1
        tot += u.get("input_tokens", 0) + 2 * u.get("cache_creation_input_tokens", 0) + 0.1 * u.get("cache_read_input_tokens", 0) + 5 * u.get("output_tokens", 0)
    return tot, steps, first or ""
t, s, _ = cost(main); print(f"main session ({os.path.basename(main)}): {t:,.0f} over {s} steps")
ht = 0
for f in sorted(glob.glob(subdir + "agent-*.jsonl")):
    c, st, fi = cost(f)
    if a.since and fi < a.since: continue
    ht += c; print(f"  helper {os.path.basename(f)[6:14]} started {fi[:16]}  steps {st:3d}  cost {c:11,.0f}")
print(f"helpers: {ht:,.0f}   total: {ht + t:,.0f}")
