#!/usr/bin/env python3
"""Smoke test for scheduled-team-workflow: runs make_job_kit.py on sample configs.

Usage:
  python evals/smoke_test.py

Checks the worked example, a single-agent job, a three-agent job with a mapped
folder, the refusal to overwrite, and config validation. Everything is written
to a temporary folder; nothing is written inside the skill folder.
"""

import sys

sys.dont_write_bytecode = True

import json  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
from pathlib import Path  # noqa: E402

SKILL = Path(__file__).resolve().parent.parent
SCRIPT = SKILL / "scripts" / "make_job_kit.py"
EXAMPLE = SKILL / "assets" / "job-kit.example.json"

failures = []


def check(condition, message):
    if not condition:
        failures.append(message)
    return condition


def run(args):
    proc = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def no_markup(folder: Path):
    for path in folder.rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            check("{{" not in text and "}}" not in text, f"template markup left in {path.name}")
            check("\n\n\n" not in text, f"triple blank line in {path.name}")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)

        # 1. --example prints valid JSON
        code, out, _ = run(["--example"])
        check(code == 0, "--example failed")
        try:
            json.loads(out)
        except json.JSONDecodeError:
            failures.append("--example output is not valid JSON")

        # 2. worked example: two agents with peer learning
        kit = tmp / "kit-two"
        code, _, err = run([str(EXAMPLE), "-o", str(kit)])
        if check(code == 0, f"example config failed: {err}"):
            for name in ["PROTOCOL.md", "PEER.md", "prompts/agent-A.md", "prompts/agent-B.md",
                         "prompts/setup-B.md", "prompts/verify-B.md", "schedule.md", "folders.txt", "NEXT-STEPS.md"]:
                check((kit / name).is_file(), f"two-agent kit missing {name}")
            no_markup(kit)
            a = (kit / "prompts/agent-A.md").read_text(encoding="utf-8")
            check("YOU ARE AGENT A" in a, "agent-A prompt lacks its identity")
            check("at most 2 units" in a, "agent-A prompt lacks the per-run cap")
            check("PROTOCOL.md" in a and "TASK.md" in a, "agent-A prompt doesn't point to TASK.md and PROTOCOL.md")
            check("pre-approved" in a, "agent-A prompt lacks pre-approval")
            check("questions/" in a, "agent-A prompt lacks the questions rule")
            check("DONE.md" in a, "agent-A prompt lacks the stop condition")
            check("/Claude Products/Skills/skills/farsi-scifi-builder/" in a, "agent-A prompt lacks the skill fallback")
            setup = (kit / "prompts/setup-B.md").read_text(encoding="utf-8")
            check("YOU ARE AGENT B" in setup, "setup-B doesn't contain B's prompt")
            check("approval" in setup, "setup-B doesn't ask about the approval setting")
            check("CRON_TZ=Pacific/Auckland 30 * * * *" in setup, "setup-B lacks B's cron")
            protocol = (kit / "PROTOCOL.md").read_text(encoding="utf-8")
            check("| **A** |" in protocol and "| **B** |" in protocol, "PROTOCOL.md agents table incomplete")
            check("PEER.md" in protocol and "`retro`" in protocol, "PROTOCOL.md doesn't link peer learning")
            check("status file has not been updated in the last hour" in protocol, "PROTOCOL.md lacks the liveness rule")
            check("Check that the claim is really yours" in protocol, "PROTOCOL.md lacks the claim check")
            check("This overrides TASK.md's \"no unit left\" rule" in protocol, "PROTOCOL.md lacks the done guard")
            check("PAUSE.md" in protocol, "PROTOCOL.md lacks the pause switch")
            check(protocol.startswith("# Coordination protocol for parallel runs (v1)"), "PROTOCOL.md title lacks the version")
            check("since your previous run started" in (kit / "PEER.md").read_text(encoding="utf-8"), "PEER.md lacks the overlap-safe cut-off")
            check("PAUSE.md" in a, "agent-A prompt lacks the pause switch")
            check('pause this scheduled task ("Had-e Momken Persian adaptation")' in a, "agent-A prompt lacks the self-pause")
            b_prompt = (kit / "prompts/agent-B.md").read_text(encoding="utf-8")
            check('("Had-e Momken – Persian adaptation (hourly)")' in b_prompt, "agent-B prompt doesn't pause its own task by name")
            peer = (kit / "PEER.md").read_text(encoding="utf-8")
            check("«ترجیح‌های نویسنده»" in peer, "PEER.md lacks the configured authority files")
            check("OrisonVoice" in peer, "PEER.md lacks the configured review checks")
            folders = (kit / "folders.txt").read_text(encoding="utf-8").split("\n")
            check(folders.index("/Novel/Farsi Novel/Had-e Momken/had-e-momken/peer")
                  < folders.index("/Novel/Farsi Novel/Had-e Momken/had-e-momken/peer/retro"),
                  "folders.txt doesn't list parents first")

        # 3. refuses to overwrite without --force, replaces with --force
        code, _, _ = run([str(EXAMPLE), "-o", str(kit)])
        check(code == 3, f"expected exit 3 when kit files exist, got {code}")
        code, _, _ = run([str(EXAMPLE), "-o", str(kit), "--force"])
        check(code == 0, "--force didn't replace the kit")

        # 4. single agent: no protocol, no peer file, no agent identity
        single = tmp / "single.json"
        single.write_text(json.dumps({
            "job_name": "coding the Coastal Interviews transcripts",
            "job_folder": "/Research/Coastal Interviews",
            "owner": "the researcher",
            "unit": {"singular": "transcript", "plural": "transcripts"},
            "units_per_run": 1,
            "outputs_folder": "coded",
            "self_pause": False,
            "agents": [{"id": "A", "minute": 10}],
            "peer_learning": {"enabled": True},
        }), encoding="utf-8")
        code, _, err = run([str(single)])
        kit1 = tmp / "single-kit"
        if check(code == 0, f"single-agent config failed: {err}"):
            check(not (kit1 / "PROTOCOL.md").exists(), "single-agent kit should have no PROTOCOL.md")
            check(not (kit1 / "PEER.md").exists(), "single-agent kit should have no PEER.md")
            prompt = (kit1 / "prompts/agent-A.md").read_text(encoding="utf-8")
            check("AGENT" not in prompt, "single-agent prompt shouldn't name an agent")
            check("at most 1 transcript." in prompt, "single-agent prompt uses the wrong unit word")
            check("TASK.md allows" in prompt, "single-agent prompt grammar")
            check("peer learning needs at least two agents" in err, "no note about skipped peer learning")
            check("list_triggers" not in prompt and prompt.rstrip().endswith("don't start any work, and stop."),
                  "self_pause: false should leave the plain stop line")
            check("/Research/Coastal Interviews/coded" in (kit1 / "folders.txt").read_text(encoding="utf-8"),
                  "folders.txt lacks the outputs folder")
            no_markup(kit1)

        # 5. three agents, one with an unknown folder, one mapped
        three = tmp / "three.json"
        three.write_text(json.dumps({
            "job_name": "the Persian translation of the lab manual",
            "job_folder": "/Lab Manual/fa-translation",
            "unit": {"singular": "chapter", "plural": "chapters"},
            "skill": {"name": "persian-technical-style", "dropbox_path": "/Skills/persian-technical-style/"},
            "dropbox_email": "owner@example.org",
            "agents": [{"id": "A", "minute": 20}, {"id": "B", "minute": 40}, {"id": "C", "minute": 50, "job_folder": "/fa-translation"}],
        }), encoding="utf-8")
        kit3 = tmp / "kit-three"
        code, _, err = run([str(three), "-o", str(kit3)])
        if check(code == 0, f"three-agent config failed: {err}"):
            b = (kit3 / "prompts/agent-B.md").read_text(encoding="utf-8")
            check("<JOB FOLDER>" in b, "agent-B prompt should carry the folder placeholder")
            check("search this Dropbox" in b, "agent-B prompt lacks the search fallback")
            check("agent A" in b and "agent C" in b, "agent-B prompt doesn't name both other agents")
            c = (kit3 / "prompts/agent-C.md").read_text(encoding="utf-8")
            check("JOB FOLDER: /fa-translation" in c, "agent-C prompt lacks its mapped folder")
            setup_b = (kit3 / "prompts/setup-B.md").read_text(encoding="utf-8")
            check("replaced with the path you found" in setup_b, "setup-B should ask for the placeholder to be replaced")
            check("It should be signed in as owner@example.org" in setup_b, "setup-B lacks the email gate")
            check("holds SKILL.md" in setup_b, "setup-B doesn't check the skill folder")
            check("start its first run now" in setup_b, "setup-B doesn't start the first run")
            check(not (kit3 / "PEER.md").exists(), "PEER.md written although peer learning is off")
            protocol = (kit3 / "PROTOCOL.md").read_text(encoding="utf-8")
            check("Three scheduled tasks" in protocol, "PROTOCOL.md agent count")
            check("PEER.md" not in protocol and "`retro`" not in protocol, "PROTOCOL.md mentions peer learning while it's off")
            no_markup(kit3)

        # 6. validation errors exit 2
        bad = tmp / "bad.json"
        bad.write_text(json.dumps({"job_name": "x", "job_folder": "/x",
                                   "agents": [{"id": "A"}, {"id": "A"}]}), encoding="utf-8")
        code, _, err = run([str(bad)])
        check(code == 2 and "twice" in err, "duplicate agent ids not rejected")
        bad.write_text(json.dumps({"job_name": "x", "job_folder": "relative/path", "agents": [{"id": "A"}]}),
                       encoding="utf-8")
        code, _, _ = run([str(bad)])
        check(code == 2, "relative job folder not rejected")
        bad.write_text(json.dumps({"job_name": "x", "job_folder": "/x", "agents": [{"id": "A", "minute": 75}]}),
                       encoding="utf-8")
        code, _, _ = run([str(bad)])
        check(code == 2, "minute out of range not rejected")

    if failures:
        print(f"FAILED: {len(failures)} check(s)", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1
    print("smoke test passed", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
