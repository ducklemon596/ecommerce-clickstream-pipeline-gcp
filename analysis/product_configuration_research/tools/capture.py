"""Capture redacted research evidence over the existing authorized SSH access."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys


def remote_command(script: str, config: str, user: str, size: int, ids: list[str] | None = None) -> str:
    """Build a secret-free command; the VM reads its own protected YAML file.

    Inputs are research JS, authorized config path, MongoDB user and pool size.
    Returns shell-quoted Python invocation. Requires VM Python/PyYAML/mongosh.
    """
    wrapper = (
        "import os,pathlib,subprocess,yaml; "
        f"settings=yaml.safe_load(pathlib.Path({config!r}).expanduser().read_text()); "
        "environment=os.environ.copy(); "
        "environment['RESEARCH_MONGO_PASSWORD']=str(settings['password']); "
        f"environment['RESEARCH_MONGO_USER']={user!r}; "
        f"environment['RESEARCH_SAMPLE_SIZE']={str(size)!r}; "
        f"environment['RESEARCH_TARGET_IDS']={json.dumps(ids or [])!r}; "
        f"subprocess.run(['mongosh','--nodb','--quiet','--eval',{script!r}],env=environment,check=True)"
    )
    return "python3 -c " + shlex.quote(wrapper)


def capture(args: argparse.Namespace) -> None:
    """Stream a bounded, redacted pool to a new private JSONL evidence file.

    Uses explicit gcloud coordinates and creates no MongoDB collections. Fails
    on command errors, incomplete output, or existing output; partial files are
    retained with a .partial suffix and must not be treated as complete samples.
    """
    script_path = args.script or Path(__file__).with_name("sample.mjs")
    script = "console.error('Research: capture started');\n" + script_path.read_text()
    command = remote_command(script, args.config, args.mongo_user, args.size, args.id)
    output = args.output
    output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if output.exists():
        raise FileExistsError(output)
    partial = output.with_suffix(output.suffix + ".partial")
    descriptor = os.open(partial, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        process = subprocess.Popen([
            "gcloud", "compute", "ssh", f"{args.ssh_user}@{args.vm}",
            f"--project={args.project}", f"--zone={args.zone}",
            "--command", command,
        ], stdout=subprocess.PIPE, text=True)
        try:
            assert process.stdout is not None
            for line in process.stdout:
                if line.startswith("Research:"):
                    print(line.rstrip(), file=sys.stderr)
                    continue
                stream.write(line)
            if process.wait():
                raise subprocess.CalledProcessError(process.returncode, process.args)
        finally:
            if process.stdout is not None:
                process.stdout.close()
    rows = 0
    completed = None
    with partial.open() as stream:
        for line in stream:
            record = json.loads(line)
            if "_completed" in record:
                completed = record["_completed"]["emitted"]
            elif "_metadata" not in record:
                rows += 1
    if rows != args.size or completed != rows:
        raise ValueError(f"incomplete sample: {rows} rows; completion={completed}")
    os.rename(partial, output)
    print(f"Captured {rows:,} redacted events: {output}")


def main() -> None:
    """Parse explicit infrastructure settings and capture research evidence."""
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("project", "zone", "vm", "ssh-user", "mongo-user"):
        parser.add_argument("--" + flag, required=True)
    parser.add_argument("--config", required=True, help="Authorized VM-side YAML password file")
    parser.add_argument("--size", type=int, default=300000)
    parser.add_argument("--id", action="append", default=[], help="Exact source ObjectId to verify; replaces random sampling")
    parser.add_argument("--script", type=Path, help="Alternative read-only research probe")
    parser.add_argument("--ids-file", type=Path, help="Research cohort JSON with anchors containing _id")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.ids_file:
        args.id.extend(item["_id"] for item in json.loads(args.ids_file.read_text())["anchors"])
    if args.id:
        import re
        if any(not re.fullmatch(r"[0-9a-f]{24}", value) for value in args.id):
            parser.error("--id must be an exact lowercase 24-hex source ObjectId")
        args.id = list(dict.fromkeys(args.id))
        args.size = len(args.id)
    if not 1 <= args.size <= 500000:
        parser.error("research pool size must be between 1 and 500000")
    capture(args)


if __name__ == "__main__":
    main()
