#!/usr/bin/env python3
"""Generate topic pages and lookup tables from docs/reference.md (stdlib only)."""

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/reference.md"

PAGES = [
    ("1. Address and naming conventions", "address-conventions"),
    ("2. Native functions and callable signatures", "native-functions"),
    ("3. Hook sites, byte signatures and detours", "hooks"),
    ("4. Engine globals and structure layouts", "structures"),
    ("5. Load, link and execution sequence", "execution"),
    ("6. Memory ownership and the script arena", "memory"),
    ("7. Compiler, package format and VM dispatch", "compiler-and-vm"),
    ("8. PRX/GSC communication", "communication"),
    ("9. Restarts, updates, disarming and unloading", "lifecycle"),
    ("10. Failure and diagnostic reference", "diagnostics"),
    ("11. Legacy modes and scope boundaries", "scope"),
    ("12. Source map and evidence", "evidence"),
    ("Appendix A. Complete active console builtin mapping", "builtins"),
    ("Appendix B. Accepted opcode widths and native dispatch anchors", "opcodes"),
    ("Appendix C. Source fingerprints", "fingerprints"),
]

TABLES = [
    ("loader-functions", "Engine role / conventional description", "RVA", "Neutral typedef / call label", "Use"),
    ("dvar-functions", "Role", "RVA", "Existing PRX contract"),
    ("native-signatures", "Manifest label", "RVA", "Bytes", "Length"),
    ("engine-globals", "RVA", "Access width / interpretation", "Use in this implementation or observed engine path"),
    ("zone-globals", "Global RVA", "Width", "Observed use"),
    ("builtins", "GSC binding", "Console ID", "Kind", "Native RVA", "Registration RVA", "Flags"),
    ("opcodes", "Opcode", "Profile name", "Width", "Kind", "Handler RVA"),
    ("source-fingerprints", "Evidence component", "SHA-256"),
]


def slug(heading):
    return re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")


def cells(line):
    return [cell.strip().replace("`", "") for cell in line.strip().strip("|").split("|")]


def table(source, headers):
    lines = source.splitlines()
    matches = [i for i, line in enumerate(lines) if line.startswith("|") and cells(line) == list(headers)]
    if len(matches) != 1:
        raise ValueError(f"Expected one table with headers {headers!r}, found {len(matches)}")
    i = matches[0]
    if not re.fullmatch(r"[| :\-]+", lines[i + 1]):
        raise ValueError(f"Missing table separator after {headers!r}")
    rows = []
    for line in lines[i + 2:]:
        if not line.startswith("|"):
            break
        values = cells(line)
        if len(values) != len(headers):
            raise ValueError(f"Wrong column count: {line}")
        rows.append(dict(zip(headers, values)))
    if not rows:
        raise ValueError(f"Empty table: {headers!r}")
    return rows


def generate():
    raw = SOURCE.read_bytes()
    source = raw.decode("utf-8")
    headings = list(re.finditer(r"^## (.+)$", source, re.M))
    sections = {
        match.group(1): source[match.start():headings[i + 1].start() if i + 1 < len(headings) else len(source)].strip()
        for i, match in enumerate(headings)
    }
    output = {}
    for title, filename in PAGES:
        nav = f"[Repository](../README.md) · [Complete reference](reference.md#{slug(title)})"
        note = "<!-- Generated from docs/reference.md by tools/build_reference.py. -->"
        output[f"docs/{filename}.md"] = f"{nav}\n\n{note}\n\n{sections[title]}\n"

    datasets = {}
    contracts = {
        match.group(2): re.sub(r"\s+", " ", match.group(0)).strip()
        for match in re.finditer(r"typedef\s+([^;]+?)\(\*(\w+)\)\s*\(([^;]*?)\);", source)
    }
    for filename, *headers in TABLES:
        rows = table(source, headers)
        if filename == "loader-functions":
            for row in rows:
                label = row["Neutral typedef / call label"].split(",")[0]
                row["PRX typedef contract"] = contracts[label]
        datasets[filename] = rows
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        output[f"data/{filename}.csv"] = stream.getvalue()

    image = {row["Property"]: row["Value"] for row in table(source, ("Property", "Value"))}
    combined = {
        "schema_version": 1,
        "source": "docs/reference.md",
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "image_identity": image,
        "interpretation": [
            "All table values are strings; hexadecimal addresses and IDs preserve source notation.",
            "RVAs are relative to the target engine image; script handles use the VM program base.",
            "Local labels are descriptive, not recovered original engine symbols.",
            "Typedefs are contracts used by the reviewed PRX, not a reconstructed original SDK.",
            "Builtin callbacks use VM argument state; opcode handlers are internal interpreter labels.",
            "The tables are an index. Read the corresponding reference section for qualifications.",
        ],
        "tables": datasets,
    }
    output["data/reference.json"] = json.dumps(combined, ensure_ascii=False, indent=2) + "\n"
    index = [
        "# Lookup tables", "",
        "Generated from [the complete reference](../docs/reference.md). All CSV and JSON field values are strings, including hexadecimal RVAs, IDs, lengths and flags. The JSON contains image identity and the SHA-256 of its source document.", "",
        "| Dataset | Records |", "|---|---:|",
    ]
    for name, rows in datasets.items():
        index.append(f"| [{name}.csv]({name}.csv) | {len(rows)} |")
    index.extend([
        "", "[Combined JSON](reference.json) contains the same records.", "",
        "Native addresses are engine RVAs. Script handles are offsets from the VM program base. Builtin entries are VM callbacks, and opcode handler entries are internal interpreter destinations. Neither table establishes an ordinary C prototype for every row.", "",
        "Edit `docs/reference.md`, then run `python3 tools/build_reference.py` from the repository root. Use `python3 tools/build_reference.py --check` to detect stale generated files and broken local Markdown links.", "",
    ])
    output["data/README.md"] = "\n".join(index)
    return output


def prose_lines(path):
    inside = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("```"):
            inside = not inside
        elif not inside:
            yield line
    if inside:
        raise ValueError(f"Unclosed code fence: {path.relative_to(ROOT)}")


def check_links():
    errors = []
    for path in ROOT.rglob("*.md"):
        for line in prose_lines(path):
            for href in re.findall(r"\[[^\]]*\]\(([^)]+)\)", line):
                url = urlsplit(href)
                if url.scheme or url.netloc:
                    continue
                target = (path.parent / unquote(url.path)).resolve() if url.path else path
                if not target.is_relative_to(ROOT) or not target.exists():
                    errors.append(f"{path.relative_to(ROOT)}: missing target {href}")
                elif url.fragment and target.suffix == ".md":
                    anchors = {slug(re.sub(r"^#+ ", "", item)) for item in prose_lines(target) if item.startswith("#")}
                    if unquote(url.fragment) not in anchors:
                        errors.append(f"{path.relative_to(ROOT)}: missing anchor {href}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate generated files without writing them")
    args = parser.parse_args()
    output = generate()
    stale = []
    for name, content in output.items():
        path = ROOT / name
        if args.check:
            if not path.exists() or path.read_bytes() != content.encode("utf-8"):
                stale.append(name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content.encode("utf-8"))
    errors = [f"Stale generated file: {name}" for name in stale] + check_links()
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    action = "Checked" if args.check else "Generated"
    print(f"{action} {len(output)} files; local Markdown links and code fences are valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
