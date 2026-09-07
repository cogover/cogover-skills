#!/usr/bin/env python3
"""Validate the Cogover record-name invariant in an Object-definition workbook."""

from __future__ import annotations

import re
import sys
import zipfile
import posixpath
from pathlib import Path
from xml.etree import ElementTree as ET


MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"m": MAIN_NS, "r": REL_NS, "p": PKG_REL_NS}


def normalize_label(value: object) -> str:
    return re.sub(r"\*$", "", str(value or "").replace('"', "").strip()).lower()


def column_index(reference: str) -> int:
    letters = re.match(r"[A-Z]+", reference)
    if not letters:
        raise ValueError(f"Invalid cell reference: {reference}")
    result = 0
    for character in letters.group(0):
        result = result * 26 + ord(character) - ord("A") + 1
    return result - 1


def shared_strings(archive: zipfile.ZipFile) -> list[str]:
    path = "xl/sharedStrings.xml"
    if path not in archive.namelist():
        return []
    root = ET.fromstring(archive.read(path))
    return ["".join(node.text or "" for node in item.findall(".//m:t", NS)) for item in root.findall("m:si", NS)]


def cell_text(cell: ET.Element, strings: list[str]) -> str:
    cell_type = cell.get("t")
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.findall(".//m:t", NS))
    value_node = cell.find("m:v", NS)
    value = value_node.text if value_node is not None and value_node.text is not None else ""
    if cell_type == "s" and value:
        return strings[int(value)]
    return value


def sheet_rows(archive: zipfile.ZipFile, sheet_path: str, strings: list[str]) -> list[list[str]]:
    root = ET.fromstring(archive.read(sheet_path))
    sparse_rows: dict[int, dict[int, str]] = {}
    max_column = 0
    for cell in root.findall(".//m:sheetData/m:row/m:c", NS):
        reference = cell.get("r", "")
        row_match = re.search(r"\d+$", reference)
        if not row_match:
            continue
        row_number = int(row_match.group(0)) - 1
        col_number = column_index(reference)
        sparse_rows.setdefault(row_number, {})[col_number] = cell_text(cell, strings)
        max_column = max(max_column, col_number)
    if not sparse_rows:
        return []
    rows = []
    for row_number in range(max(sparse_rows) + 1):
        row = [""] * (max_column + 1)
        for col_number, value in sparse_rows.get(row_number, {}).items():
            row[col_number] = value
        rows.append(row)
    return rows


def workbook_sheets(archive: zipfile.ZipFile) -> list[tuple[str, str]]:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    targets = {
        rel.get("Id"): rel.get("Target", "")
        for rel in relationships.findall("p:Relationship", NS)
    }
    result = []
    for sheet in workbook.findall("m:sheets/m:sheet", NS):
        name = sheet.get("name", "")
        relation_id = sheet.get(f"{{{REL_NS}}}id", "")
        target = targets.get(relation_id, "")
        path = target.lstrip("/")
        if not path.startswith("xl/"):
            path = posixpath.normpath(posixpath.join("xl", path))
        result.append((name, path))
    return result


def validate_sheet(sheet_name: str, rows: list[list[str]]) -> list[str]:
    violations = []
    indexes = {}
    for key in ("field name", "data type", "slug"):
        matches = [index for index, row in enumerate(rows) if row and normalize_label(row[0]) == key]
        if len(matches) != 1:
            violations.append(f"{sheet_name}: cần đúng 1 dòng {key}, hiện có {len(matches)}")
        else:
            indexes[key] = matches[0]

    record_rows = [index for index, row in enumerate(rows) if row and normalize_label(row[0]) == "record name field"]
    if len(record_rows) != 1:
        violations.append(f'{sheet_name}: cần đúng 1 dòng "Record name" field, hiện có {len(record_rows)}')
    if violations:
        return violations

    record_row = rows[record_rows[0]]
    record_label = normalize_label(record_row[1] if len(record_row) > 1 else "")
    if not record_label:
        return [f'{sheet_name}: "Record name" field đang trống']

    header = rows[indexes["field name"]]
    matching_columns = [index for index, value in enumerate(header) if index > 0 and normalize_label(value) == record_label]
    if len(matching_columns) != 1:
        return [f'{sheet_name}: record-name "{record_row[1]}" phải khớp đúng 1 field, hiện khớp {len(matching_columns)}']

    slug_row = rows[indexes["slug"]]
    name_columns = [index for index, value in enumerate(slug_row) if index > 0 and str(value).strip() == "name"]
    if len(name_columns) != 1:
        return [f"{sheet_name}: cần đúng 1 field slug name, hiện có {len(name_columns)}"]

    record_column = matching_columns[0]
    if name_columns[0] != record_column:
        violations.append(f"{sheet_name}: field được chọn làm record-name không phải field slug name")

    type_row = rows[indexes["data type"]]
    field_type = normalize_label(type_row[record_column] if record_column < len(type_row) else "")
    if field_type not in {"short text", "auto number"}:
        violations.append(f'{sheet_name}: field slug name có type không hợp lệ "{field_type}"')
    return violations


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/validate_record_name.py <workbook.xlsx>", file=sys.stderr)
        return 2
    workbook_path = Path(sys.argv[1])
    violations = []
    try:
        with zipfile.ZipFile(workbook_path) as archive:
            strings = shared_strings(archive)
            sheets = workbook_sheets(archive)
            for sheet_name, sheet_path in sheets:
                violations.extend(validate_sheet(sheet_name, sheet_rows(archive, sheet_path, strings)))
    except (FileNotFoundError, zipfile.BadZipFile, ET.ParseError, KeyError, ValueError, IndexError) as error:
        print(f"Cannot validate workbook: {error}", file=sys.stderr)
        return 2

    if violations:
        print(f"Record-name validation failed ({len(violations)}):", file=sys.stderr)
        for violation in violations:
            print(f"- {violation}", file=sys.stderr)
        return 1
    print(f"Record-name validation passed: {len(sheets)} sheet(s), mỗi sheet có đúng một field slug name với type Short text/Auto number.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
