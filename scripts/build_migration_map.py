#!/usr/bin/env python3
"""Build references/migration-map.json from the public migration guide's
API correspondence appendix (Markdown tables), then check every VisioOne
symbol it cites against the TypeScript declarations of the targeted
@visioglobe/visioone version.

Usage:
  build_migration_map.py <correspondance-api.md> <visioone package dir> <output.json>

Exit code 1, without writing the output, if a cited VisioOne symbol is not
declared in the package.
"""
import json
import re
import sys
from pathlib import Path

SDK_HEADINGS = {
    "VisioWeb": "visioweb",
    "VisioWeb Essential": "visioweb-essential",
    "VisioMoveEssential V2 (iOS / Android)": "visiomove-essential-v2",
}
STATUS = {
    "✅": "direct",
    "🔁": "different",
    "🛠️": "workaround",
    "❌": "none",
    "➖": "not-applicable",
}
GUIDE_REF = re.compile(r"\*([^*]+)\*,?\s*(§\d+(?:\.\d+)*|fiche \d+)", re.IGNORECASE)
CODE = re.compile(r"`([^`]+)`")
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def split_row(line):
    """Split a Markdown table row on unescaped pipes that are outside backticks."""
    cells, cur, in_code = [], "", False
    for ch in line.strip().strip("|"):
        if ch == "`":
            in_code = not in_code
        if ch == "|" and cur.endswith("\\"):  # escaped pipe: literal
            cur = cur[:-1] + ch
        elif ch == "|" and not in_code:
            cells.append(cur.strip())
            cur = ""
        else:
            cur += ch
    cells.append(cur.strip())
    return cells


def parse(md_text):
    entries, sdk, section = [], None, None
    for line in md_text.splitlines():
        if line.startswith("## "):
            sdk = SDK_HEADINGS.get(line[3:].strip())
            section = None
        elif line.startswith("### "):
            section = line[4:].strip()
        elif sdk and line.startswith("|") and not line.startswith("|---"):
            cells = split_row(line)
            if len(cells) < 4 or cells[0].startswith("API "):
                continue
            legacy, visioone, status_cell, note = cells[:4]
            status = next((v for k, v in STATUS.items() if status_cell.startswith(k)), None)
            if status is None:
                continue
            refs = ["{} {}".format(m.group(1).strip(), m.group(2)) for m in GUIDE_REF.finditer(note)]
            entries.append({
                "sdk": sdk,
                "section": section,
                "legacy": legacy.replace("`", ""),
                "visioone": None if visioone in ("—", "") else visioone.replace("`", ""),
                "status": status,
                "note": note,
                "guide": refs,
                "_code": CODE.findall(visioone),
            })
    return entries


COMMENT = re.compile(r"/\*.*?\*/|//[^\n]*", re.DOTALL)


def declared_identifiers(package_dir):
    """Identifiers and string literals of the declarations, comments excluded
    (a word that only appears in a JSDoc comment is not declared)."""
    names = set()
    for f in Path(package_dir).rglob("*.d.ts"):
        text = COMMENT.sub(" ", f.read_text(encoding="utf-8"))
        names.update(IDENT.findall(text))
        # string literal types: event names, enum-like values
        names.update(re.findall(r"'([A-Za-z0-9_-]+)'", text))
        names.update(re.findall(r'"([A-Za-z0-9_-]+)"', text))
    return names


# Identifiers that are not VisioOne API: variable names from the guide's
# conventions, JS keywords and standard browser APIs.
IGNORED = {
    "visioOne", "venue", "view", "options", "event", "container",
    "new", "await", "true", "false", "null", "undefined", "const", "of",
    "try", "URLSearchParams", "addEventListener", "removeEventListener", "dispatchEvent", "once",
    "Promise", "then", "catch", "Array", "filter", "find", "map", "some", "length",
    "latitude", "longitude", "altitude", "x", "y",
    # placeholder names used in the appendix examples
    "p", "c", "cb", "e", "i", "s", "trace", "params", "valeur", "autrePoi", "poiOuId", "message",
    "token", "visible",
    # standard JS / native APIs (mobile WebView shell)
    "constructor", "flatMap", "requestAnimationFrame", "WebView", "WKWebView", "onPause", "onResume",
    # wildcard prefixes: `goTo*` stands for goToFloor, goToPOI, goToViewpoint…,
    # `minimum*`/`maximum*` for the camera limits, `update*` for updateSurface, updateLabel…
    "goTo", "minimum", "maximum", "update",
}


def check(entries, names):
    """Only VisioOne symbols written as code (`...`) in the VisioOne column are checked."""
    missing = {}
    for e in entries:
        for ident in (i for span in e["_code"] for i in IDENT.findall(span)):
            if ident in IGNORED or ident in names:
                continue
            missing.setdefault(ident, []).append("{} / {}".format(e["sdk"], e["legacy"]))
    return missing


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    md, pkg, out = sys.argv[1:]
    entries = parse(Path(md).read_text(encoding="utf-8"))
    missing = check(entries, declared_identifiers(pkg))
    version = json.loads((Path(pkg) / "package.json").read_text())["version"]
    if missing:
        # Fail before writing: never leave unverified mappings in the output.
        for ident, where in sorted(missing.items()):
            print("NOT DECLARED in {}: {}  ({} uses, e.g. {})".format(version, ident, len(where), where[0]))
        sys.exit(1)
    for e in entries:
        del e["_code"]
    Path(out).write_text(json.dumps({
        "visioone": version,
        "source": "VisioOne migration guide, API correspondence appendix",
        "entries": entries,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = {}
    for e in entries:
        counts.setdefault(e["sdk"], 0)
        counts[e["sdk"]] += 1
    print("entries:", len(entries), counts)


if __name__ == "__main__":
    main()
