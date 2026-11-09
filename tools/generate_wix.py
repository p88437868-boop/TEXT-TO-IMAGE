from __future__ import annotations

import argparse
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path


NAMESPACE = uuid.UUID("8a3f7e2b-0e57-4e18-9d63-4c4f2a6d8b10")


def stable_id(prefix: str, relative: str) -> str:
    token = uuid.uuid5(NAMESPACE, relative.replace("\\", "/")).hex[:12]
    return f"{prefix}_{token}"


def component_guid(relative: str) -> str:
    return "{" + str(uuid.uuid5(NAMESPACE, "component/" + relative.replace("\\", "/"))).upper() + "}"


def add_directories(root: ET.Element, files: list[Path], dist: Path) -> dict[str, str]:
    parent_ids: dict[str, str] = {"": "INSTALLFOLDER"}
    directories: dict[str, Path] = {}
    for path in files:
        relative_parent = path.relative_to(dist).parent
        if str(relative_parent) == ".":
            continue
        current = Path()
        for part in relative_parent.parts:
            current /= part
            key = current.as_posix()
            if key in directories:
                continue
            directories[key] = current
    ordered = sorted(directories.items(), key=lambda item: len(item[1].parts))
    for key, relative in ordered:
        parent = relative.parent
        parent_key = "" if str(parent) == "." else parent.as_posix()
        parent_id = parent_ids[parent_key]
        directory_id = stable_id("dir", key)
        if parent_id == "INSTALLFOLDER":
            parent_node = root
        else:
            parent_node = root.find(f".//Directory[@Id='{parent_id}']")
        if parent_node is None:
            raise RuntimeError(f"Could not find parent directory for {relative}")
        ET.SubElement(
            parent_node,
            "Directory",
            {"Id": directory_id, "Name": relative.name},
        )
        parent_ids[key] = directory_id
    return parent_ids


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    dist = Path(args.dist).resolve()
    out = Path(args.out).resolve()
    if not dist.is_dir():
        raise SystemExit(f"Distribution folder not found: {dist}")

    files = sorted(path for path in dist.rglob("*") if path.is_file())
    ET.register_namespace("", "http://wixtoolset.org/schemas/v4/wxs")

    root = ET.Element(
        "Wix",
        {"xmlns": "http://wixtoolset.org/schemas/v4/wxs"},
    )
    fragment = ET.SubElement(root, "Fragment")
    directory_ref = ET.SubElement(fragment, "DirectoryRef", {"Id": "INSTALLFOLDER"})
    parent_ids = add_directories(directory_ref, files, dist)

    group_fragment = ET.SubElement(root, "Fragment")
    group = ET.SubElement(group_fragment, "ComponentGroup", {"Id": "AppFiles"})

    for path in files:
        relative = path.relative_to(dist)
        key = relative.as_posix()
        parent = relative.parent
        parent_key = "" if str(parent) == "." else parent.as_posix()
        directory_id = parent_ids[parent_key]
        component_id = stable_id("cmp", key)
        if key.lower() == "textpicstudio.exe":
            component_id = "MainExecutableComponent"
            file_id = "TextPicStudioExe"
        else:
            file_id = stable_id("fil", key)
        component = ET.SubElement(
            group,
            "Component",
            {
                "Id": component_id,
                "Directory": directory_id,
                "Guid": component_guid(key),
            },
        )
        ET.SubElement(
            component,
            "File",
            {
                "Id": file_id,
                "Source": f"$(var.DistDir)\\{str(relative)}",
            },
        )

    ET.indent(root, space="  ")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        + ET.tostring(root, encoding="unicode")
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(files)} files to {out}")


if __name__ == "__main__":
    main()
