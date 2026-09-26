"""Download the show recording from the repo's draft release into footage/.

    python tools/fetch_footage.py [--repo millernl/tdf] [--tag footage]

Draft releases are visible only to collaborators, so the footage never goes public.
Uses curl (for the proxy/CA setup of the environment it runs in).
"""
import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def api(url, accept="application/vnd.github+json"):
    out = subprocess.run(["curl", "-sSL", "-H", f"Accept: {accept}", url], capture_output=True, check=True)
    return json.loads(out.stdout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="millernl/tdf")
    ap.add_argument("--tag", default="footage")
    args = ap.parse_args()
    releases = api(f"https://api.github.com/repos/{args.repo}/releases?per_page=50")
    if isinstance(releases, dict):
        raise SystemExit(f"GitHub API: {releases.get('message')}")
    rel = next((r for r in releases if r.get("tag_name") == args.tag or "footage" in (r.get("name") or "").lower()),
               None)
    if not rel:
        raise SystemExit(f"no release tagged '{args.tag}' (drafts included) — has the upload been saved?")
    dest = ROOT / "footage"
    dest.mkdir(exist_ok=True)
    for a in rel["assets"]:
        path = dest / a["name"]
        if path.exists() and path.stat().st_size == a["size"]:
            print(f"  have {a['name']}")
            continue
        print(f"  downloading {a['name']} ({a['size'] / 1e9:.2f} GB)…", flush=True)
        subprocess.run(["curl", "-sSL", "--retry", "4", "-H", "Accept: application/octet-stream", "-o", str(path),
                        f"https://api.github.com/repos/{args.repo}/releases/assets/{a['id']}"], check=True)
        if path.stat().st_size != a["size"]:
            raise SystemExit(f"size mismatch on {a['name']}")
    print(f"{len(rel['assets'])} file(s) in {dest}")


if __name__ == "__main__":
    main()
