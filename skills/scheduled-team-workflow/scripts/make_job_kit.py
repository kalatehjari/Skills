#!/usr/bin/env python3
"""Generate a consistent coordination kit for a scheduled-team job.

Reads a job config (JSON) and writes these files into a new folder:

  PROTOCOL.md            coordination rules (two or more agents)
  PEER.md                peer-learning rules (two or more agents, peer_learning.enabled)
  prompts/agent-<X>.md   the scheduled-task prompt for each agent
  prompts/setup-<X>.md   a message to paste into each other account's Claude
  prompts/verify-<X>.md  a verification prompt for each other account
  schedule.md            task names and cron expressions
  folders.txt            folders to create in the job folder, parents first
  NEXT-STEPS.md          what to do with each file

Examples:
  python make_job_kit.py job.json              # writes job-kit/ next to job.json
  python make_job_kit.py job.json -o kit/
  python make_job_kit.py --example > job.json  # start from the worked example

The script never overwrites its input, and refuses to write into a folder
that already holds kit files unless --force is given.
"""

import sys

sys.dont_write_bytecode = True

import argparse  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
from pathlib import Path  # noqa: E402

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_DIR / "assets" / "templates"
EXAMPLE = SKILL_DIR / "assets" / "job-kit.example.json"

EXIT_CONFIG = 2
EXIT_EXISTS = 3

ID_RE = re.compile(r"^[A-Z][A-Z0-9]{0,3}$")
SECTION_RE = re.compile(r"\{\{([#^])([A-Za-z_][A-Za-z0-9_]*)\}\}(.*?)\{\{/\2\}\}", re.S)
VAR_RE = re.compile(r"\{\{([A-Za-z_][A-Za-z0-9_]*)\}\}")
NUMBER_WORDS = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six"}

DEFAULT_REVIEW_CHECKS = [
    "Content against the source: all present / missing: …",
    "Terms and names against the reference files: OK / …",
    "Format and layout against the approved example: OK / …",
    "The checks TASK.md requires: pass / …",
]
DEFAULT_AUTHORITY = [
    "every file in `reference/`",
    "the approved examples TASK.md names",
]


class ConfigError(Exception):
    pass


# ---------------------------------------------------------------- rendering

def render(text: str, ctx: dict) -> str:
    """Tiny mustache-like renderer: {{var}}, {{#flag}}…{{/flag}}, {{^flag}}…{{/flag}}."""

    def section(match: re.Match) -> str:
        kind, name, inner = match.group(1), match.group(2), match.group(3)
        if name not in ctx:
            raise ConfigError(f"template uses unknown flag '{name}'")
        truthy = bool(ctx[name])
        return inner if (truthy if kind == "#" else not truthy) else ""

    previous = None
    while previous != text:
        previous = text
        text = SECTION_RE.sub(section, text)

    def var(match: re.Match) -> str:
        name = match.group(1)
        if name not in ctx:
            raise ConfigError(f"template uses unknown value '{name}'")
        return str(ctx[name])

    text = VAR_RE.sub(var, text)
    leftover = re.search(r"\{\{|\}\}", text)
    if leftover:
        start = max(0, leftover.start() - 40)
        raise ConfigError(f"unrendered template markup near: {text[start:leftover.end() + 40]!r}")
    text = "\n".join(line.rstrip() for line in text.splitlines())
    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
    return text


def template(name: str) -> str:
    path = TEMPLATES / name
    if not path.is_file():
        raise ConfigError(f"missing template {path}")
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------- config

def load_config(path: Path) -> dict:
    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ConfigError(f"config not found: {path}")
    except json.JSONDecodeError as exc:
        raise ConfigError(f"config is not valid JSON ({exc})")
    if not isinstance(cfg, dict):
        raise ConfigError("config must be a JSON object")
    return normalise(cfg)


def capitalise(text: str) -> str:
    return text[:1].upper() + text[1:]


def normalise(cfg: dict) -> dict:
    def need(key):
        if not cfg.get(key):
            raise ConfigError(f"config needs '{key}'")
        return cfg[key]

    job_folder = str(need("job_folder")).rstrip("/")
    if not job_folder.startswith("/"):
        raise ConfigError("job_folder must be a full Dropbox path starting with '/'")
    agents = need("agents")
    if not isinstance(agents, list):
        raise ConfigError("agents must be a list")

    seen = set()
    clean_agents = []
    for i, agent in enumerate(agents):
        if not isinstance(agent, dict):
            raise ConfigError(f"agent {i + 1} must be an object")
        aid = str(agent.get("id", "")).strip()
        if not ID_RE.match(aid):
            raise ConfigError(f"agent {i + 1}: id must be 1–4 capital letters or digits, starting with a letter (got {aid!r})")
        if aid in seen:
            raise ConfigError(f"agent id {aid} is used twice")
        seen.add(aid)
        minute = agent.get("minute", 0)
        if not isinstance(minute, int) or not 0 <= minute <= 59:
            raise ConfigError(f"agent {aid}: minute must be a whole number from 0 to 59")
        folder = agent.get("job_folder")
        if i == 0 or folder == "same":
            folder = job_folder
        elif folder:
            folder = str(folder).rstrip("/")
            if not folder.startswith("/"):
                raise ConfigError(f"agent {aid}: job_folder must start with '/', be \"same\", or be left out")
        else:
            folder = None
        clean_agents.append({
            "id": aid,
            "account": agent.get("account") or ("owner's Claude account" if i == 0 else f"Claude account {i + 1}"),
            "minute": minute,
            "task_name": agent.get("task_name"),
            "job_folder": folder,
        })

    units_per_run = cfg.get("units_per_run", 1)
    if not isinstance(units_per_run, int) or units_per_run < 1:
        raise ConfigError("units_per_run must be a whole number of at least 1")
    stale = cfg.get("stale_hours", 3)
    if not isinstance(stale, (int, float)) or stale <= 0:
        raise ConfigError("stale_hours must be a positive number")

    unit = cfg.get("unit") or {}
    singular = unit.get("singular", "unit") if isinstance(unit, dict) else str(unit)
    plural = unit.get("plural", singular + "s") if isinstance(unit, dict) else singular + "s"

    skill = cfg.get("skill") or None
    if skill is not None:
        if not isinstance(skill, dict) or not skill.get("name"):
            raise ConfigError("skill must be an object with at least a 'name'")

    peer = cfg.get("peer_learning") or {}
    if isinstance(peer, bool):
        peer = {"enabled": peer}
    peer_enabled = bool(peer.get("enabled")) and len(clean_agents) > 1

    owner = cfg.get("owner", "the owner")
    return {
        "job_name": str(need("job_name")),
        "task_name": cfg.get("task_name") or capitalise(str(cfg["job_name"])),
        "job_folder": job_folder,
        "owner": owner,
        "unit": singular,
        "units": plural,
        "units_per_run": units_per_run,
        "stale_hours": stale,
        "done_file": cfg.get("done_file", "DONE.md"),
        "proposals_folder": str(cfg.get("proposals_folder", "additions")).strip("/"),
        "outputs_folder": str(cfg.get("outputs_folder", "")).strip("/"),
        "version": str(cfg.get("version", "v1")),
        "self_pause": bool(cfg.get("self_pause", True)),
        "dropbox_email": str(cfg.get("dropbox_email", "")),
        "timezone": cfg.get("timezone", ""),
        "timezone_label": cfg.get("timezone_label", cfg.get("timezone", "UTC")),
        "skill": skill,
        "agents": clean_agents,
        "peer_enabled": peer_enabled,
        "peer_requested": bool(peer.get("enabled")),
        "notes_language": peer.get("notes_language", "English"),
        "authority_files": peer.get("authority_files") or DEFAULT_AUTHORITY,
        "review_checks": peer.get("review_checks") or DEFAULT_REVIEW_CHECKS,
        "retro_words": peer.get("retro_words", 250),
        "review_words": peer.get("review_words", 350),
        "digest_lessons": peer.get("digest_lessons", 25),
        "digest_after": peer.get("digest_after", 6),
    }


# ---------------------------------------------------------------- contexts

def cron_for(cfg: dict, minute: int) -> str:
    base = f"{minute} * * * *"
    return f"CRON_TZ={cfg['timezone']} {base}" if cfg["timezone"] else base


def describe(agent: dict) -> str:
    return f"agent {agent['id']} ({agent['account']})"


def join_words(items: list) -> str:
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def base_ctx(cfg: dict) -> dict:
    multi = len(cfg["agents"]) > 1
    rows = []
    for agent in cfg["agents"]:
        when = f"hourly at :{agent['minute']:02d}"
        if cfg["timezone_label"]:
            when += f" {cfg['timezone_label']}"
        rows.append(f"| **{agent['id']}** | {agent['account']} | {when} |")
    owner = cfg["owner"]
    return {
        "job_name": cfg["job_name"],
        "job_folder": cfg["job_folder"],
        "job_folder_name": cfg["job_folder"].rstrip("/").split("/")[-1],
        "owner": owner,
        "owner_cap": capitalise(owner),
        "unit": cfg["unit"],
        "units": cfg["units"],
        "units_per_run": cfg["units_per_run"],
        "units_per_run_word": cfg["unit"] if cfg["units_per_run"] == 1 else cfg["units"],
        "stale_hours": f"{cfg['stale_hours']:g}",
        "done_file": cfg["done_file"],
        "proposals_folder": cfg["proposals_folder"],
        "timezone_label": cfg["timezone_label"],
        "version": cfg["version"],
        "self_pause": cfg["self_pause"],
        "dropbox_email": cfg["dropbox_email"],
        "multi": multi,
        "peer": cfg["peer_enabled"],
        "agent_count_word": NUMBER_WORDS.get(len(cfg["agents"]), str(len(cfg["agents"]))),
        "agents_table": "\n".join(rows),
        "notes_language": cfg["notes_language"],
        "authority_list": "\n".join(f"  - {item}" for item in cfg["authority_files"]),
        "review_checks_list": "\n".join(f"- {item}" for item in cfg["review_checks"]),
        "retro_words": cfg["retro_words"],
        "review_words": cfg["review_words"],
        "digest_lessons": cfg["digest_lessons"],
        "digest_after": cfg["digest_after"],
    }


def agent_ctx(cfg: dict, index: int) -> dict:
    ctx = base_ctx(cfg)
    agent = cfg["agents"][index]
    others = [describe(a) for i, a in enumerate(cfg["agents"]) if i != index]
    if not others:
        others_sentence = ""
    elif len(others) == 1:
        others_sentence = (f"Another scheduled task, {others[0]}, works on this job at the same time "
                           "from the same Dropbox folder.")
    else:
        others_sentence = (f"Other scheduled tasks, {join_words(others)}, work on this job at the same time "
                           "from the same Dropbox folder.")
    folder = agent["job_folder"] or "<JOB FOLDER>"
    mapped = folder != cfg["job_folder"]
    skill = cfg["skill"]
    fallback = ""
    if skill:
        path = skill.get("dropbox_path")
        if not path:
            fallback = (f"If it isn't installed in this account, write that in questions/ for {cfg['owner']} "
                        "and do the work as well as you can without it.")
        elif not mapped:
            fallback = f"If it isn't installed in this account, read its files from {path} in Dropbox."
        else:
            fallback = (f"If it isn't installed in this account, read its files from Dropbox. In the owner's "
                        f"Dropbox they are in {path}; if that path doesn't exist here, search this Dropbox for "
                        f"a folder named \"{skill['name']}\" that contains SKILL.md.")
    task_name = agent["task_name"] or (cfg["task_name"] if index == 0 else f"{cfg['task_name']} (agent {agent['id']})")
    skill_path_here = ""
    if skill and skill.get("dropbox_path"):
        skill_path_here = skill["dropbox_path"] if not mapped else (
            f"the {skill['name']} folder (in the owner's Dropbox: {skill['dropbox_path']})")
    ctx.update({
        "agent_id": agent["id"],
        "account": agent["account"],
        "others_sentence": others_sentence,
        "agent_job_folder": folder,
        "mapped": mapped,
        "known_folder": agent["job_folder"] is not None,
        "skill": bool(skill),
        "skill_name": skill["name"] if skill else "",
        "skill_fallback_sentence": fallback,
        "skill_path": bool(skill_path_here),
        "skill_path_here": skill_path_here,
        "task_name": task_name,
        "minute_padded": f"{agent['minute']:02d}",
        "cron": cron_for(cfg, agent["minute"]),
    })
    return ctx


# ---------------------------------------------------------------- outputs

def folder_list(cfg: dict) -> list:
    names = ([cfg["outputs_folder"]] if cfg["outputs_folder"] else []) + ["claims", "questions", cfg["proposals_folder"]]
    if len(cfg["agents"]) > 1:
        names += ["status", "log", "messages"]
    if cfg["peer_enabled"]:
        names += ["peer", "peer/retro", "peer/review", "peer/digest"]
    return [f"{cfg['job_folder']}/{name}" for name in names]


def schedule_md(cfg: dict) -> str:
    lines = [
        f"# Schedule: {cfg['task_name']}",
        "",
        "| Agent | Account | Task name | Runs | cron_expression |",
        "|---|---|---|---|---|",
    ]
    for i, agent in enumerate(cfg["agents"]):
        ctx = agent_ctx(cfg, i)
        when = f"hourly at :{agent['minute']:02d} {cfg['timezone_label']}".rstrip()
        lines.append(f"| {agent['id']} | {agent['account']} | {ctx['task_name']} | {when} | `{ctx['cron']}` |")
    lines += [
        "",
        "Create each task in its own account, in the cloud (requires_local_device: false), with the prompt in "
        "prompts/agent-<id>.md. Leave the approval setting to the server and check what it got: runs must "
        "approve automatically, or they stall at the first file save.",
    ]
    return "\n".join(lines) + "\n"


def next_steps_md(cfg: dict) -> str:
    multi = len(cfg["agents"]) > 1
    first = cfg["agents"][0]["id"]
    steps = [f"# Next steps for {cfg['task_name']}", ""]
    n = 1
    steps.append(f"{n}. Create the folders in folders.txt, parents first (create_folder fails if a folder exists; that's fine).")
    n += 1
    if multi:
        upload = "PROTOCOL.md and PEER.md" if cfg["peer_enabled"] else "PROTOCOL.md"
        steps.append(f"{n}. Upload {upload} into {cfg['job_folder']} with create_file. If an older PROTOCOL.md is there, "
                     "delete it and create the new one straight away, at a time when no run is about to start.")
        n += 1
    steps.append(f"{n}. In this account (agent {first}): create the scheduled task, or update the existing one with "
                 f"update_trigger, using prompts/agent-{first}.md and the settings in schedule.md.")
    n += 1
    for agent in cfg["agents"][1:]:
        steps.append(f"{n}. Give the user prompts/setup-{agent['id']}.md to paste into the Claude of the "
                     f"{agent['account']} (agent {agent['id']}). Ask them to paste back the reply.")
        n += 1
        steps.append(f"{n}. Its reply reports the Dropbox email and TASK.md's path and file id. Compare them with "
                     "who_am_i and get_file_metadata here. A different email means a shared folder: check it with a "
                     f"canary file (references/parallel-agents.md) before trusting it. Keep prompts/verify-{agent['id']}.md "
                     "for a later re-check.")
        n += 1
    if multi:
        steps.append(f"{n}. If you changed the rules while tasks were running, add an owner log event "
                     "(log/<time>_owner_setup_-.md) saying what changed, so runs don't mistake the switch-over for errors.")
        n += 1
        steps.append(f"{n}. After the next runs, check claims/ (claims carry an agent line), status/ and log/. "
                     "Offer the user a check-in (send_later) after the first coordinated runs.")
    else:
        steps.append(f"{n}. Offer to start the first run now (fire_trigger), then check claims/ for its claim, "
                     "and offer a check-in (send_later) after the first runs.")
    return "\n".join(steps) + "\n"


def build(cfg: dict) -> dict:
    files = {}
    multi = len(cfg["agents"]) > 1
    if multi:
        files["PROTOCOL.md"] = render(template("PROTOCOL.md.tmpl"), base_ctx(cfg))
    if cfg["peer_enabled"]:
        files["PEER.md"] = render(template("PEER.md.tmpl"), base_ctx(cfg))
    for i, agent in enumerate(cfg["agents"]):
        ctx = agent_ctx(cfg, i)
        prompt = render(template("agent-prompt.md.tmpl"), ctx)
        files[f"prompts/agent-{agent['id']}.md"] = prompt
        if i > 0:
            ctx["agent_prompt"] = prompt.strip()
            files[f"prompts/setup-{agent['id']}.md"] = render(template("setup-other-account.md.tmpl"), ctx)
            files[f"prompts/verify-{agent['id']}.md"] = render(template("verify-other-account.md.tmpl"), ctx)
    files["schedule.md"] = schedule_md(cfg)
    files["folders.txt"] = "\n".join(folder_list(cfg)) + "\n"
    files["NEXT-STEPS.md"] = next_steps_md(cfg)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate PROTOCOL.md, PEER.md, prompts and a folder list for a scheduled-team job.")
    parser.add_argument("config", nargs="?", type=Path, help="job config (JSON); see assets/job-kit.example.json")
    parser.add_argument("-o", "--out", type=Path, help="output folder (default: <config name>-kit next to the config)")
    parser.add_argument("--force", action="store_true", help="replace kit files already in the output folder")
    parser.add_argument("--example", action="store_true", help="print the worked example config and exit")
    args = parser.parse_args()

    if args.example:
        sys.stdout.write(EXAMPLE.read_text(encoding="utf-8"))
        return 0
    if not args.config:
        parser.error("give a config file, or --example to print one")

    try:
        cfg = load_config(args.config)
        files = build(cfg)
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_CONFIG

    out = args.out or args.config.resolve().parent / f"{args.config.stem}-kit"
    out = out.resolve()
    config_path = args.config.resolve()
    targets = {name: out / name for name in files}
    if config_path in targets.values():
        print("error: an output file would overwrite the config; choose another output folder", file=sys.stderr)
        return EXIT_CONFIG
    existing = [str(p) for p in targets.values() if p.exists()]
    if existing and not args.force:
        print("error: kit files already exist (use --force to replace them):\n  " + "\n  ".join(existing),
              file=sys.stderr)
        return EXIT_EXISTS

    for name, path in targets.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(files[name], encoding="utf-8")

    agents = ", ".join(a["id"] for a in cfg["agents"])
    print(f"Wrote {len(files)} files to {out}", file=sys.stderr)
    print(f"  agents: {agents}; {cfg['units_per_run']} {cfg['units'] if cfg['units_per_run'] > 1 else cfg['unit']} per run",
          file=sys.stderr)
    if cfg["peer_requested"] and not cfg["peer_enabled"]:
        print("  note: peer learning needs at least two agents, so PEER.md was not written", file=sys.stderr)
    for name in files:
        print(f"  {name}", file=sys.stderr)
    print("  next: follow NEXT-STEPS.md", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
