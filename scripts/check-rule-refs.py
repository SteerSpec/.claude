#!/usr/bin/env python3
"""Check that every rule cited in templates/ still says what it did when cited.

Templates cite rules by ID (e.g. NTE-020). Mustache cannot resolve those, and
marker-mode sync expands no variables, so nothing else ties the prose to the
rule. This script does:

  * every cited ID must exist in dev.steerspec.core at the pinned ref,
  * the rule must not be Abandoned, Retired or Terminated (A, R, T),
  * its state and body must match rule-refs.lock.json, so any change to a cited
    rule fails the check until a person re-reads the citing line and runs
    --update,
  * the lock must not carry IDs that no template cites.

Modes:
  (default)   check against the ref pinned in the lock (deterministic, for PRs)
  --latest    check against the latest strspc-rules release (drift, scheduled)
  --update    rewrite the lock from the latest release (review the diff, then
              re-read every citing line)
"""
import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request

REPO = "SteerSpec/strspc-rules"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCK = os.path.join(ROOT, "rule-refs.lock.json")
TEMPLATES = os.path.join(ROOT, "templates")
ID_RE = re.compile(r"\b([A-Z]{2,8})-(\d{3})\b")
DEAD = {"A", "R", "T"}  # Abandoned, Retired, Terminated


def http(url, accept_404=False):
    req = urllib.request.Request(url, headers={"User-Agent": "rule-refs-check"})
    token = os.environ.get("GITHUB_TOKEN")
    if token and url.startswith("https://api.github.com/"):
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        if accept_404 and e.code == 404:
            return None
        raise


def latest_ref():
    data = http(f"https://api.github.com/repos/{REPO}/releases/latest")
    return json.loads(data)["tag_name"]


_families = {}


def family(ref, prefix):
    """Rules of rules/core/<prefix>.json at ref, or None if no such file."""
    key = (ref, prefix)
    if key not in _families:
        raw = http(
            f"https://raw.githubusercontent.com/{REPO}/{ref}/rules/core/{prefix}.json",
            accept_404=True,
        )
        _families[key] = (
            None if raw is None else {r["id"]: r for r in json.loads(raw)["rules"]}
        )
    return _families[key]


def cited_ids():
    found = {}
    for dirpath, _, files in os.walk(TEMPLATES):
        for name in sorted(files):
            path = os.path.join(dirpath, name)
            with open(path, encoding="utf-8") as fh:
                for n, line in enumerate(fh, 1):
                    for m in ID_RE.finditer(line):
                        found.setdefault(m.group(0), []).append(
                            f"{os.path.relpath(path, ROOT)}:{n}"
                        )
    return found


def resolve(ref, cited):
    """(ids -> rule snapshot, problems) for the IDs that belong to a core family."""
    snap, problems = {}, []
    for rid, where in sorted(cited.items()):
        fam = family(ref, rid.split("-")[0])
        if fam is None:
            continue  # not a rule family (SHA-256 style false positive)
        rule = fam.get(rid)
        if rule is None:
            problems.append(f"{rid} ({where[0]}): no such rule at {ref}")
            continue
        if rule["state"] in DEAD:
            problems.append(
                f"{rid} ({where[0]}): rule is {rule['state']} (abandoned/retired/"
                f"terminated) at {ref}; the citing line must change"
            )
        snap[rid] = {
            "state": rule["state"],
            "body_sha256": hashlib.sha256(rule["body"].encode()).hexdigest(),
        }
    return snap, problems


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--latest", action="store_true")
    ap.add_argument("--update", action="store_true")
    args = ap.parse_args()

    cited = cited_ids()
    lock = {}
    if os.path.exists(LOCK):
        with open(LOCK, encoding="utf-8") as fh:
            lock = json.load(fh)

    if args.update:
        ref = latest_ref()
        snap, problems = resolve(ref, cited)
        for p in problems:
            print("error:", p, file=sys.stderr)
        if problems:
            return 1
        with open(LOCK, "w", encoding="utf-8") as fh:
            json.dump({"source": REPO, "ref": ref, "refs": snap}, fh, indent=2)
            fh.write("\n")
        print(f"wrote {os.path.relpath(LOCK, ROOT)} at {ref}: {', '.join(snap) or 'no refs'}")
        return 0

    if not lock:
        print("error: rule-refs.lock.json missing; run with --update", file=sys.stderr)
        return 1
    ref = latest_ref() if args.latest else lock["ref"]
    snap, problems = resolve(ref, cited)
    locked = lock["refs"]
    for rid in sorted(snap):
        if rid not in locked:
            problems.append(f"{rid} ({cited[rid][0]}): cited but not in the lock; run --update")
        elif locked[rid] != snap[rid]:
            problems.append(
                f"{rid} ({cited[rid][0]}): rule changed since it was last reviewed "
                f"(lock {lock['ref']}, checked {ref}); re-read the citing line, then run --update"
            )
    for rid in sorted(set(locked) - set(snap)):
        if rid not in cited:
            problems.append(f"{rid}: in the lock but no template cites it; run --update")
    for p in problems:
        print("error:", p, file=sys.stderr)
    if problems:
        return 1
    print(f"rule references OK at {ref}: {', '.join(sorted(snap)) or 'none cited'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
