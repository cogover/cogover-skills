#!/usr/bin/env python3
"""Validate Cogover implementation artifacts without calling the Workspace API.

The validator intentionally checks deterministic structure and cross-references only.
Business correctness remains the responsibility of the coordinator and independent reviewers.
"""

from __future__ import annotations

import argparse
import json
import posixpath
import re
import sys
import zipfile
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET


VERSION = "1.5.0"
MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"m": MAIN_NS, "r": REL_NS, "p": PKG_REL_NS}

ID_PATTERN = re.compile(r"\b(REQ|Q|DEC|OBJ|REL|FLD|TR|MIG|ISSUE|AUT|GAP|W|T)-\d{3,}\b", re.I)
MARKER_PATTERN = re.compile(r"<!--\s*cogover-table:([a-z0-9-]+)\s*-->", re.I)
PLACEHOLDER_PATTERN = re.compile(r"\b(TBD|UNKNOWN)\b", re.I)
TRUE_VALUES = {"yes", "true", "1", "blocking", "có", "x"}
RESOLVED_VALUES = {"answered", "closed", "resolved", "done", "not blocking", "đã trả lời", "đã xử lý"}
SYSTEM_OBJECTS = {"personnel", "department", "queue"}


TABLE_COLUMNS = {
    "requirements-solutions": 5,
    "questions": 4,
    "object-catalog": 11,
    "relationships": 9,
    "fields": 13,
    "state-transitions": 12,
    "requirement-traceability": 7,
    "work-breakdown": 14,
    "lock-register": 5,
    "test-plan": 7,
    "workbook-scope": 3,
    "execution-checkpoints": 7,
}


@dataclass
class Finding:
    severity: str
    code: str
    artifact: str
    message: str


@dataclass
class MarkdownTable:
    marker: str
    headers: list[str]
    rows: list[list[str]]
    line: int


@dataclass
class WorkbookField:
    name: str
    slug: str
    data_type: str
    required: bool
    lookup_target: str


@dataclass
class WorkbookObject:
    sheet_name: str
    name: str
    record_name_field: str
    fields: list[WorkbookField]
    options: dict[str, list[str]]


class Validator:
    def __init__(self) -> None:
        self.findings: list[Finding] = []
        self.solution_requirements: set[str] = set()
        self.in_scope_requirements: set[str] = set()
        self.design_ids: set[str] = set()
        self.data_objects: dict[str, dict[str, str]] = {}

    def add(self, severity: str, code: str, artifact: str, message: str) -> None:
        self.findings.append(Finding(severity, code, artifact, message))

    def error(self, code: str, artifact: str, message: str) -> None:
        self.add("ERROR", code, artifact, message)

    def warning(self, code: str, artifact: str, message: str) -> None:
        self.add("WARNING", code, artifact, message)

    def validate_solution(self, path: Path) -> None:
        tables = self._load_markdown(path, {"requirements-solutions"})
        if not tables:
            return
        artifact = str(path)
        source = path.read_text(encoding="utf-8")
        if not re.search(r"<!--\s*cogover-api-key-preflight:\s*VERIFIED\s*-->", source, re.I):
            self.error(
                "CREDENTIAL_PREFLIGHT_MISSING",
                artifact,
                "Solution artifact requires <!-- cogover-api-key-preflight:VERIFIED --> before Workspace discovery evidence is used.",
            )
        requirements = self._definition_ids(tables, "requirements-solutions", "REQ", artifact)
        self.solution_requirements = requirements
        requirement_table = first_table(tables, "requirements-solutions")
        allowed_statuses = {"cần làm rõ", "đã rõ", "out_of_scope", "unknown"}
        allowed_dispositions = {
            "REUSE_AS_IS", "CONFIGURE", "EXTEND", "INSTALL_STANDARD_APP", "BUILD_CUSTOM",
            "EXTERNAL_INTEGRATION", "NOT_SUPPORTED", "UNKNOWN",
        }
        expected_questions: dict[str, set[str]] = defaultdict(set)
        has_open_requirements = False
        if requirement_table:
            for number, row in enumerate(requirement_table.rows, requirement_table.line + 2):
                req_id = canonical_id(cell(row, 0))
                status = normalize(cell(row, 2))
                if status not in allowed_statuses:
                    self.error("SOLUTION_CLARITY_STATUS", artifact, f"Requirement line {number} has invalid clarity status {cell(row, 2) or '<empty>'}.")
                if req_id and status != "out_of_scope":
                    self.in_scope_requirements.add(req_id)
                if is_blank(cell(row, 1)):
                    self.error("SOLUTION_REQUIREMENT_DESCRIPTION", artifact, f"Requirement line {number} has no description.")
                solution = cell(row, 4).strip()
                if is_blank(solution):
                    self.error("SOLUTION_MISSING", artifact, f"Requirement line {number} has no preliminary/final solution.")
                elif not any(disposition in solution.upper() for disposition in allowed_dispositions):
                    self.error("SOLUTION_DISPOSITION", artifact, f"Requirement line {number} solution has no supported fit-gap disposition.")
                question_ids = ids_of_type(cell(row, 3), "Q")
                if status == "cần làm rõ":
                    has_open_requirements = True
                    if not question_ids:
                        self.error("SOLUTION_QUESTION_MISSING", artifact, f"Requirement line {number} needs at least one Q-ID.")
                elif question_ids:
                    self.error("SOLUTION_QUESTION_STALE", artifact, f"Requirement line {number} is not open but still lists Q-ID values.")
                for question_id in question_ids:
                    expected_questions[question_id].add(req_id)

        question_table = first_table(tables, "questions")
        if has_open_requirements and not question_table:
            self.error("SOLUTION_QUESTIONS_TABLE_MISSING", artifact, "Open requirements require the questions table.")
        if not has_open_requirements and question_table:
            self.error("SOLUTION_FINAL_HAS_QUESTIONS", artifact, "Final/fully clarified revision must omit the questions table.")
        if question_table:
            defined_questions = self._unique_ids_from_rows(question_table, 0, "Q", artifact, "questions")
            for number, row in enumerate(question_table.rows, question_table.line + 2):
                question_id = canonical_id(cell(row, 0))
                req_ids = ids_of_type(cell(row, 1), "REQ")
                unknown_reqs = req_ids - requirements
                if not req_ids:
                    self.error("SOLUTION_QUESTION_REQ", artifact, f"Question line {number} has no REQ-ID.")
                elif unknown_reqs:
                    self.error("SOLUTION_QUESTION_REQ", artifact, f"Question line {number} references undefined requirements: {join_ids(unknown_reqs)}.")
                if is_blank(cell(row, 2)):
                    self.error("SOLUTION_QUESTION_TEXT", artifact, f"Question line {number} has no question text.")
                expected_reqs = expected_questions.get(question_id, set())
                if expected_reqs and expected_reqs != req_ids:
                    self.error(
                        "SOLUTION_QUESTION_MAPPING",
                        artifact,
                        f"{question_id} maps to {join_ids(expected_reqs)} in Table 1 but {join_ids(req_ids)} in Table 2.",
                    )
            missing_questions = set(expected_questions) - defined_questions
            if missing_questions:
                self.error("SOLUTION_QUESTION_UNDEFINED", artifact, f"Table 1 references undefined questions: {join_ids(missing_questions)}.")
            unreferenced_questions = defined_questions - set(expected_questions)
            if unreferenced_questions:
                self.error("SOLUTION_QUESTION_UNREFERENCED", artifact, f"Table 2 contains questions not referenced by Table 1: {join_ids(unreferenced_questions)}.")

    def validate_data_design(self, path: Path) -> None:
        required = {"object-catalog", "relationships", "fields"}
        tables = self._load_markdown(path, required)
        if not tables:
            return
        artifact = str(path)
        object_ids = self._definition_ids(tables, "object-catalog", "OBJ", artifact)
        relationship_ids = self._definition_ids(tables, "relationships", "REL", artifact)
        field_ids = self._definition_ids(tables, "fields", "FLD", artifact)
        transition_ids = self._definition_ids(tables, "state-transitions", "TR", artifact, required=False)
        self.design_ids = object_ids | relationship_ids | field_ids | transition_ids

        catalog = first_table(tables, "object-catalog")
        slugs: dict[str, str] = {}
        if catalog:
            for number, row in enumerate(catalog.rows, catalog.line + 2):
                obj_id = canonical_id(cell(row, 0))
                name = cell(row, 1).strip()
                slug = cell(row, 2).strip()
                disposition = cell(row, 3).strip().upper()
                reqs = ids_of_type(cell(row, 9), "REQ")
                if not name or not slug:
                    self.error("DATA_OBJECT_REQUIRED", artifact, f"Object line {number} needs both name and slug.")
                slug_key = normalize(slug)
                if slug_key in slugs:
                    self.error("DATA_OBJECT_SLUG_DUPLICATE", artifact, f"Duplicate Object slug {slug!r} at line {number}.")
                elif slug_key:
                    slugs[slug_key] = obj_id
                if disposition not in {"REUSE", "EXTEND", "CREATE"}:
                    self.error("DATA_OBJECT_DISPOSITION", artifact, f"Object line {number} has invalid disposition {disposition or '<empty>'}.")
                self._validate_requirement_refs(reqs, artifact, f"Object line {number}")
                if obj_id:
                    self.data_objects[obj_id] = {"name": name, "slug": slug, "disposition": disposition}

        relationships = all_tables(tables, "relationships")
        for table in relationships:
            for number, row in enumerate(table.rows, table.line + 2):
                self._validate_object_ref(cell(row, 1), object_ids, artifact, f"Relationship line {number} source")
                self._validate_object_ref(cell(row, 2), object_ids, artifact, f"Relationship line {number} target")
                self._validate_requirement_refs(ids_of_type(cell(row, 7), "REQ"), artifact, f"Relationship line {number}")

        seen_field_slugs: set[tuple[str, str]] = set()
        fields = all_tables(tables, "fields")
        for table in fields:
            for number, row in enumerate(table.rows, table.line + 2):
                object_ref = cell(row, 1).strip()
                self._validate_object_ref(object_ref, object_ids, artifact, f"Field line {number} Object")
                slug = cell(row, 3).strip()
                if not cell(row, 2).strip() or not slug or not cell(row, 4).strip():
                    self.error("DATA_FIELD_REQUIRED", artifact, f"Field line {number} needs name, slug and type.")
                key = (normalize(object_ref), normalize(slug))
                if key in seen_field_slugs:
                    self.error("DATA_FIELD_SLUG_DUPLICATE", artifact, f"Duplicate field slug {slug!r} for {object_ref!r} at line {number}.")
                seen_field_slugs.add(key)
                self._validate_requirement_refs(ids_of_type(cell(row, 11), "REQ"), artifact, f"Field line {number}")

        for table in all_tables(tables, "state-transitions"):
            for number, row in enumerate(table.rows, table.line + 2):
                self._validate_requirement_refs(ids_of_type(cell(row, 11), "REQ"), artifact, f"Transition line {number}")

    def validate_workbook(self, path: Path, data_design_path: Path | None) -> None:
        artifact = str(path)
        try:
            objects = read_workbook(path)
        except (FileNotFoundError, zipfile.BadZipFile, ET.ParseError, KeyError, ValueError, IndexError) as error:
            self.error("WORKBOOK_READ", artifact, f"Cannot read workbook: {error}.")
            return
        if not objects:
            self.error("WORKBOOK_EMPTY", artifact, "Workbook contains no Object sheets.")
            return

        names = {normalize(item.name) for item in objects}
        for item in objects:
            if normalize(item.sheet_name) != normalize(item.name):
                self.warning("WORKBOOK_SHEET_NAME", artifact, f"Sheet {item.sheet_name!r} differs from Object name {item.name!r}.")
            slugs = [field.slug for field in item.fields if field.slug]
            duplicates = {slug for slug in slugs if slugs.count(slug) > 1}
            if duplicates:
                self.error("WORKBOOK_FIELD_SLUG_DUPLICATE", artifact, f"{item.name}: duplicate field slugs {sorted(duplicates)}.")
            record_fields = [field for field in item.fields if field.slug == "name"]
            if len(record_fields) != 1:
                self.error("WORKBOOK_RECORD_NAME", artifact, f"{item.name}: expected exactly one field with slug name, found {len(record_fields)}.")
            elif base_type(record_fields[0].data_type) not in {"short text", "auto number"}:
                self.error("WORKBOOK_RECORD_NAME_TYPE", artifact, f"{item.name}: record-name field type must be Short text or Auto number.")
            elif normalize(record_fields[0].name) != normalize(item.record_name_field):
                self.error(
                    "WORKBOOK_RECORD_NAME_POINTER",
                    artifact,
                    f"{item.name}: record-name row points to {item.record_name_field!r}, not field {record_fields[0].name!r} with slug name.",
                )
            for field in item.fields:
                field_type = base_type(field.data_type)
                if field_type in {"normal lookup", "dependency lookup"}:
                    target = normalize(field.lookup_target)
                    if not target:
                        self.error("WORKBOOK_LOOKUP_TARGET", artifact, f"{item.name}.{field.name}: lookup target is empty.")
                    elif target not in names and target not in SYSTEM_OBJECTS:
                        self.error("WORKBOOK_LOOKUP_MISSING", artifact, f"{item.name}.{field.name}: lookup target {field.lookup_target!r} is not a sheet/system Object.")
                if field_type in {"single choice", "multi choices"} and normalize(field.name) not in item.options:
                    self.error("WORKBOOK_OPTIONS_MISSING", artifact, f"{item.name}.{field.name}: selective field has no options table.")

        if data_design_path and self.data_objects:
            self._compare_data_and_workbook(data_design_path, objects)

    def validate_review_workbook(self, path: Path, data_path: Path) -> None:
        """Validate a human review projection, without relaxing import validation."""
        artifact = str(path)
        tables = self._load_markdown(data_path, {"fields", "workbook-scope"})
        definitions = {
            canonical_id(cell(row, 0)): row
            for table in all_tables(tables, "fields") for row in table.rows
        }
        aliases = {}
        for obj_id, obj in self.data_objects.items():
            for alias in (obj_id, obj["name"], obj["slug"]):
                aliases[normalize(alias)] = obj
        scopes = {}
        included_actions = {"NEW", "MODIFY", "IMPORTANT"}
        allowed_actions = included_actions | {"OMIT_EXISTING", "OMIT_SYSTEM"}
        for table in all_tables(tables, "workbook-scope"):
            for row in table.rows:
                field_id = canonical_id(cell(row, 0))
                action = cell(row, 1).upper()
                if field_id not in definitions or field_id in scopes:
                    self.error("REVIEW_SCOPE_ID", artifact, f"Unknown or duplicate scope field {field_id}.")
                if action not in allowed_actions or is_blank(cell(row, 2)) or PLACEHOLDER_PATTERN.search(cell(row, 2)):
                    self.error("REVIEW_SCOPE_ACTION", artifact, f"{field_id}: invalid action or missing rationale/evidence.")
                design = definitions.get(field_id, [])
                obj = aliases.get(normalize(cell(design, 1)), {})
                if action == "OMIT_EXISTING" and obj.get("disposition") == "CREATE":
                    self.error("REVIEW_SCOPE_NEW_OBJECT", artifact, f"{field_id}: CREATE Object cannot omit an existing field.")
                scopes[field_id] = action
        if set(scopes) != set(definitions):
            self.error("REVIEW_SCOPE_COVERAGE", artifact, "Every design field must have exactly one scope row.")
        expected = {key for key, action in scopes.items() if action in included_actions}
        headers = ["Field name", "Field slug", "Data type", "Field ID", "Object slug", "Action", "Request IDs", "Notes"]
        actual = set()
        try:
            with zipfile.ZipFile(path) as archive:
                strings = shared_strings(archive)
                sheets = workbook_sheets(archive)
                if not sheets:
                    self.error("REVIEW_EMPTY", artifact, "Review workbook has no sheets.")
                for sheet_name, sheet_path in sheets:
                    rows = sheet_rows(archive, sheet_path, strings)
                    header = rows[0] if rows else []
                    if cell(header, 0) != "Field name" or any(header.count(h) != 1 for h in headers):
                        self.error("REVIEW_HEADERS", artifact, f"{sheet_name}: required unique headers missing or Field name is not column A.")
                        continue
                    indexes = {h: header.index(h) for h in headers}
                    root = ET.fromstring(archive.read(sheet_path))
                    pane = root.find("m:sheetViews/m:sheetView/m:pane", NS)
                    if pane is None or pane.get("state") != "frozen" or pane.get("xSplit") != "1" or pane.get("ySplit") != "1":
                        self.error("REVIEW_FREEZE", artifact, f"{sheet_name}: freeze column A and header row (B2).")
                    cols = root.findall("m:cols/m:col", NS)
                    # Calibri 11 approximation; visual/font checks remain required.
                    for col in range(1, len(header) + 1):
                        widths = [float(c.get("width", "0")) for c in cols if int(c.get("min", "0")) <= col <= int(c.get("max", "0"))]
                        if not widths or (col == 1 and abs(widths[-1] - 13.57) > 0.2) or (col > 1 and not 0 < widths[-1] <= 22.16):
                            self.warning("REVIEW_WIDTH", artifact, f"{sheet_name}: verify column {col} renders at 100px (A) / <=160px (others) with its font.")
                    sheet_objects = set()
                    for row in rows[1:]:
                        if not any(v.strip() for v in row):
                            continue
                        values = {h: cell(row, i).strip() for h, i in indexes.items()}
                        field_id = values["Field ID"]
                        if field_id in actual or field_id not in expected:
                            self.error("REVIEW_FIELD_SCOPE", artifact, f"Duplicate or out-of-scope review field {field_id}.")
                        actual.add(field_id)
                        design = definitions.get(field_id)
                        if not design:
                            continue
                        obj = aliases.get(normalize(cell(design, 1)))
                        sheet_objects.add(values["Object slug"])
                        if not obj or values["Object slug"] != obj["slug"]:
                            self.error("REVIEW_OBJECT", artifact, f"{field_id}: Object slug differs from design.")
                        for key, index in (("Field name", 2), ("Field slug", 3), ("Data type", 4)):
                            if normalize(values[key]) != normalize(cell(design, index)):
                                self.error("REVIEW_FIELD_MISMATCH", artifact, f"{field_id}: {key} differs from design.")
                        if values["Action"] != scopes.get(field_id):
                            self.error("REVIEW_ACTION", artifact, f"{field_id}: action differs from scope.")
                        reqs = ids_of_type(cell(design, 11), "REQ")
                        if not reqs or ids_of_type(values["Request IDs"], "REQ") != reqs:
                            self.error("REVIEW_REQUESTS", artifact, f"{field_id}: request mapping differs from design or is empty.")
                        explanation = ID_PATTERN.sub("", values["Notes"]).strip(" ,;:-")
                        if not reqs <= ids_of_type(values["Notes"], "REQ") or is_blank(explanation) or PLACEHOLDER_PATTERN.search(explanation):
                            self.error("REVIEW_NOTES", artifact, f"{field_id}: Notes need explanation and request IDs.")
                    if len(sheet_objects) > 1:
                        self.error("REVIEW_SHEET_OBJECTS", artifact, f"{sheet_name}: use one Object per sheet.")
        except (OSError, zipfile.BadZipFile, ET.ParseError, KeyError, ValueError, IndexError) as error:
            self.error("REVIEW_READ", artifact, f"Cannot read review workbook: {error}.")
            return
        if expected - actual:
            self.error("REVIEW_FIELD_MISSING", artifact, f"Review workbook is missing fields: {join_ids(expected - actual)}.")

    def validate_plan(self, path: Path) -> None:
        required = {"requirement-traceability", "work-breakdown", "lock-register", "test-plan"}
        tables = self._load_markdown(path, required)
        if not tables:
            return
        artifact = str(path)
        source = path.read_text(encoding="utf-8")
        gate_matches = re.findall(
            r"<!--\s*cogover-data-model-gate:\s*(APPROVED|DATA_MODEL_NOT_APPLICABLE)\s*-->",
            source,
            re.I,
        )
        if len(gate_matches) != 1:
            self.error(
                "PLAN_DATA_MODEL_GATE",
                artifact,
                "Plan requires exactly one approved data-model gate marker: APPROVED or DATA_MODEL_NOT_APPLICABLE.",
            )
        trace = first_table(tables, "requirement-traceability")
        work = first_table(tables, "work-breakdown")
        tests = first_table(tables, "test-plan")
        locks = first_table(tables, "lock-register")
        if not trace or not work or not tests or not locks:
            return

        trace_requirements = self._unique_ids_from_rows(trace, 0, "REQ", artifact, "traceability")
        work_ids = self._unique_ids_from_rows(work, 0, "W", artifact, "work breakdown")
        test_ids = self._unique_ids_from_rows(tests, 0, "T", artifact, "test plan")

        if self.in_scope_requirements:
            missing = self.in_scope_requirements - trace_requirements
            if missing:
                self.error("PLAN_REQ_COVERAGE", artifact, f"In-scope requirements missing from traceability: {join_ids(missing)}.")

        dependencies: dict[str, set[str]] = defaultdict(set)
        parallel: dict[str, list[tuple[str, str]]] = defaultdict(list)
        work_to_tests: dict[str, set[str]] = {}
        work_to_reqs: dict[str, set[str]] = {}
        for number, row in enumerate(work.rows, work.line + 2):
            work_id = canonical_id(cell(row, 0))
            status = cell(row, 1).strip().upper()
            reqs = ids_of_type(cell(row, 2), "REQ")
            design_refs = {item for item in extract_ids(cell(row, 3)) if item.split("-", 1)[0] in {"OBJ", "REL", "FLD", "TR", "AUT"}}
            deps = ids_of_type(cell(row, 7), "W")
            group = cell(row, 8).strip()
            lock = cell(row, 9).strip()
            linked_tests = ids_of_type(cell(row, 12), "T")
            work_to_tests[work_id] = linked_tests
            work_to_reqs[work_id] = reqs
            if not reqs:
                self.error("PLAN_WORK_REQ", artifact, f"{work_id or f'line {number}'} has no REQ-ID.")
            self._validate_requirement_refs(reqs, artifact, work_id or f"Work line {number}", trace_requirements)
            unknown_design = design_refs - self.design_ids if self.design_ids else set()
            if unknown_design:
                self.error("PLAN_DESIGN_REF", artifact, f"{work_id}: unknown design refs {join_ids(unknown_design)}.")
            unknown_deps = deps - work_ids
            if unknown_deps:
                self.error("PLAN_DEPENDENCY_REF", artifact, f"{work_id}: unknown dependencies {join_ids(unknown_deps)}.")
            if work_id in deps:
                self.error("PLAN_SELF_DEPENDENCY", artifact, f"{work_id} depends on itself.")
            dependencies[work_id] |= deps
            if group and normalize(group) not in {"n/a", "na", "none"}:
                parallel[group].append((work_id, lock))
            unknown_tests = linked_tests - test_ids
            if unknown_tests:
                self.error("PLAN_TEST_REF", artifact, f"{work_id}: unknown tests {join_ids(unknown_tests)}.")
            if status == "READY":
                for column, label in ((4, "delta"), (5, "action"), (9, "lock"), (10, "acceptance"), (11, "postcondition")):
                    value = cell(row, column)
                    if is_blank(value) or PLACEHOLDER_PATTERN.search(value):
                        self.error("PLAN_READY_INCOMPLETE", artifact, f"{work_id}: READY item has incomplete {label}.")
            if side_effect_risk(" ".join((cell(row, 4), cell(row, 5)))) and not risk_controlled(cell(row, 13)):
                self.warning("PLAN_SIDE_EFFECT_CONTROL", artifact, f"{work_id}: risky side effect may lack approval/gate/containment in Risk/rollback.")

        cycle = dependency_cycle(dependencies)
        if cycle:
            self.error("PLAN_DAG_CYCLE", artifact, f"Dependency cycle detected: {' -> '.join(cycle)}.")

        for group, items in parallel.items():
            for index, (left_id, left_lock) in enumerate(items):
                for right_id, right_lock in items[index + 1:]:
                    if locks_overlap(left_lock, right_lock):
                        self.error("PLAN_PARALLEL_LOCK", artifact, f"Parallel group {group}: {left_id} and {right_id} have overlapping locks.")

        for number, row in enumerate(trace.rows, trace.line + 2):
            req_id = canonical_id(cell(row, 0))
            linked_work = ids_of_type(cell(row, 3), "W")
            linked_tests = ids_of_type(cell(row, 4), "T")
            coverage = cell(row, 5).strip().upper()
            reason = cell(row, 6).strip()
            if linked_work - work_ids:
                self.error("PLAN_TRACE_WORK_REF", artifact, f"{req_id}: traceability references unknown work items {join_ids(linked_work - work_ids)}.")
            if linked_tests - test_ids:
                self.error("PLAN_TRACE_TEST_REF", artifact, f"{req_id}: traceability references unknown tests {join_ids(linked_tests - test_ids)}.")
            if not linked_work and coverage not in {"OUT_OF_SCOPE", "DEFERRED", "NOT_SUPPORTED", "UNKNOWN"}:
                self.error("PLAN_TRACE_WORK_MISSING", artifact, f"{req_id or f'line {number}'} has no work item and no valid gap status.")
            if not linked_tests and coverage not in {"OUT_OF_SCOPE", "DEFERRED", "NOT_SUPPORTED", "UNKNOWN"}:
                self.error("PLAN_TRACE_TEST_MISSING", artifact, f"{req_id or f'line {number}'} has no test and no valid gap status.")
            if coverage in {"OUT_OF_SCOPE", "DEFERRED", "NOT_SUPPORTED", "UNKNOWN"} and is_blank(reason):
                self.error("PLAN_TRACE_REASON", artifact, f"{req_id}: coverage {coverage} needs a reason.")

        for number, row in enumerate(tests.rows, tests.line + 2):
            test_id = canonical_id(cell(row, 0))
            reqs = ids_of_type(cell(row, 1), "REQ")
            if not reqs:
                self.error("PLAN_TEST_REQ", artifact, f"{test_id or f'line {number}'} has no REQ-ID.")
            self._validate_requirement_refs(reqs, artifact, test_id or f"Test line {number}", trace_requirements)

        for number, row in enumerate(locks.rows, locks.line + 2):
            lock = cell(row, 0).strip()
            linked_work = ids_of_type(cell(row, 1), "W")
            if not lock or not linked_work:
                self.error("PLAN_LOCK_REGISTER", artifact, f"Lock-register line {number} needs lock key and work item.")
            unknown = linked_work - work_ids
            if unknown:
                self.error("PLAN_LOCK_WORK_REF", artifact, f"Lock-register line {number} references unknown {join_ids(unknown)}.")

        checkpoints = all_tables(tables, "execution-checkpoints")
        if checkpoints:
            statuses = {canonical_id(cell(row, 0)): cell(row, 1).upper() for row in work.rows}
            seen = set()
            for table in checkpoints:
                for row in table.rows:
                    work_id = canonical_id(cell(row, 0))
                    mark = cell(row, 1).lower()
                    if work_id not in work_ids or work_id in seen:
                        self.error("PLAN_CHECKPOINT_ID", artifact, f"Unknown or duplicate checkpoint {work_id}.")
                    seen.add(work_id)
                    if mark not in {"[ ]", "[x]"} or (mark == "[x]") != (statuses.get(work_id) == "DONE"):
                        self.error("PLAN_CHECKPOINT_STATUS", artifact, f"{work_id}: DONE and checkbox disagree.")
                    if statuses.get(work_id) == "DONE":
                        for index in (2, 3, 5):
                            if is_blank(cell(row, index)) or PLACEHOLDER_PATTERN.search(cell(row, index)):
                                self.error("PLAN_CHECKPOINT_EVIDENCE", artifact, f"{work_id}: DONE needs time, agent and evidence.")
            if seen != work_ids:
                self.error("PLAN_CHECKPOINT_COVERAGE", artifact, "Checkpoint table must cover every work item.")

    def _load_markdown(self, path: Path, required: set[str]) -> dict[str, list[MarkdownTable]]:
        artifact = str(path)
        try:
            text = path.read_text(encoding="utf-8")
        except (FileNotFoundError, UnicodeDecodeError, OSError) as error:
            self.error("MARKDOWN_READ", artifact, f"Cannot read Markdown: {error}.")
            return {}
        tables = parse_marked_tables(text)
        for marker in sorted(required):
            if marker not in tables:
                self.error("TABLE_MARKER_MISSING", artifact, f"Missing <!-- cogover-table:{marker} --> table.")
        for marker, instances in tables.items():
            expected = TABLE_COLUMNS.get(marker)
            if expected is None:
                continue
            for table in instances:
                if len(table.headers) != expected:
                    self.error("TABLE_COLUMN_COUNT", artifact, f"{marker} at line {table.line} needs {expected} columns, found {len(table.headers)}.")
                for offset, row in enumerate(table.rows, table.line + 2):
                    if len(row) != expected:
                        self.error("TABLE_ROW_COLUMN_COUNT", artifact, f"{marker} row at line {offset} needs {expected} cells, found {len(row)}.")
        return tables

    def _definition_ids(
        self,
        tables: dict[str, list[MarkdownTable]],
        marker: str,
        prefix: str,
        artifact: str,
        required: bool = True,
    ) -> set[str]:
        instances = all_tables(tables, marker)
        if required and not instances:
            return set()
        result: set[str] = set()
        for table in instances:
            for number, row in enumerate(table.rows, table.line + 2):
                item_id = canonical_id(cell(row, 0))
                if not item_id or not item_id.startswith(prefix + "-"):
                    self.error("STABLE_ID_FORMAT", artifact, f"{marker} line {number} needs a {prefix}-NNN ID.")
                elif item_id in result:
                    self.error("STABLE_ID_DUPLICATE", artifact, f"Duplicate definition {item_id} in {marker}.")
                else:
                    result.add(item_id)
        return result

    def _unique_ids_from_rows(self, table: MarkdownTable, index: int, prefix: str, artifact: str, label: str) -> set[str]:
        result: set[str] = set()
        for number, row in enumerate(table.rows, table.line + 2):
            item_id = canonical_id(cell(row, index))
            if not item_id or not item_id.startswith(prefix + "-"):
                self.error("STABLE_ID_FORMAT", artifact, f"{label} line {number} needs a {prefix}-NNN ID.")
            elif item_id in result:
                self.error("STABLE_ID_DUPLICATE", artifact, f"Duplicate definition {item_id} in {label}.")
            else:
                result.add(item_id)
        return result

    def _validate_requirement_refs(
        self,
        refs: set[str],
        artifact: str,
        context: str,
        fallback: set[str] | None = None,
    ) -> None:
        known = self.solution_requirements or fallback or set()
        if known:
            unknown = refs - known
            if unknown:
                self.error("REQ_REFERENCE", artifact, f"{context} references undefined {join_ids(unknown)}.")

    def _validate_object_ref(self, value: str, object_ids: set[str], artifact: str, context: str) -> None:
        ids = ids_of_type(value, "OBJ")
        if ids and not ids <= object_ids:
            self.error("OBJ_REFERENCE", artifact, f"{context} references undefined {join_ids(ids - object_ids)}.")
        elif not value.strip():
            self.error("OBJ_REFERENCE_EMPTY", artifact, f"{context} is empty.")

    def _compare_data_and_workbook(self, data_path: Path, workbook_objects: list[WorkbookObject]) -> None:
        artifact = str(data_path)
        by_name = {normalize(item.name): item for item in workbook_objects}
        create_names = {normalize(item["name"]) for item in self.data_objects.values() if item["disposition"] == "CREATE"}
        for obj_id, item in self.data_objects.items():
            if item["disposition"] == "CREATE" and normalize(item["name"]) not in by_name:
                self.error("DATA_WORKBOOK_OBJECT_MISSING", artifact, f"{obj_id} CREATE Object {item['name']!r} is missing from workbook.")
        extra = set(by_name) - create_names - {
            normalize(item["name"]) for item in self.data_objects.values() if item["disposition"] in {"EXTEND", "REUSE"}
        }
        if extra:
            self.error("DATA_WORKBOOK_OBJECT_EXTRA", artifact, f"Workbook Objects absent from data design: {', '.join(sorted(extra))}.")

        tables = parse_marked_tables(data_path.read_text(encoding="utf-8"))
        fields_by_object: dict[str, list[list[str]]] = defaultdict(list)
        for table in all_tables(tables, "fields"):
            for row in table.rows:
                fields_by_object[normalize(cell(row, 1))].append(row)
        for obj_id, item in self.data_objects.items():
            workbook_object = by_name.get(normalize(item["name"]))
            if not workbook_object:
                continue
            expected_rows = (
                fields_by_object.get(normalize(obj_id), [])
                + fields_by_object.get(normalize(item["name"]), [])
                + fields_by_object.get(normalize(item["slug"]), [])
            )
            expected = {normalize(cell(row, 3)): row for row in expected_rows if cell(row, 3).strip()}
            actual = {normalize(field.slug): field for field in workbook_object.fields if field.slug}
            for slug, row in expected.items():
                if slug not in actual:
                    self.error("DATA_WORKBOOK_FIELD_MISSING", artifact, f"{item['name']}: field slug {cell(row, 3)!r} is missing from workbook.")
                    continue
                expected_type = base_type(cell(row, 4))
                if expected_type != base_type(actual[slug].data_type):
                    self.error("DATA_WORKBOOK_FIELD_TYPE", artifact, f"{item['name']}.{cell(row, 3)} type differs: design={cell(row, 4)!r}, workbook={actual[slug].data_type!r}.")
                expected_required = required_value(cell(row, 6))
                if expected_required is not None and expected_required != actual[slug].required:
                    self.error("DATA_WORKBOOK_FIELD_REQUIRED", artifact, f"{item['name']}.{cell(row, 3)} required flag differs.")
            if item["disposition"] == "CREATE":
                unexpected = set(actual) - set(expected)
                if unexpected:
                    self.warning("DATA_WORKBOOK_FIELD_EXTRA", artifact, f"{item['name']}: workbook has field slugs not listed in design: {', '.join(sorted(unexpected))}.")


def parse_marked_tables(text: str) -> dict[str, list[MarkdownTable]]:
    lines = text.splitlines()
    result: dict[str, list[MarkdownTable]] = defaultdict(list)
    for index, line in enumerate(lines):
        marker_match = MARKER_PATTERN.search(line)
        if not marker_match:
            continue
        marker = marker_match.group(1).lower()
        table_line = index + 1
        while table_line < len(lines) and not lines[table_line].strip():
            table_line += 1
        if table_line >= len(lines) or not lines[table_line].lstrip().startswith("|"):
            continue
        headers = split_markdown_row(lines[table_line])
        separator_line = table_line + 1
        if separator_line >= len(lines) or not is_separator_row(split_markdown_row(lines[separator_line])):
            continue
        rows: list[list[str]] = []
        cursor = separator_line + 1
        while cursor < len(lines) and lines[cursor].lstrip().startswith("|"):
            rows.append(split_markdown_row(lines[cursor]))
            cursor += 1
        result[marker].append(MarkdownTable(marker, headers, rows, table_line + 1))
    return dict(result)


def split_markdown_row(line: str) -> list[str]:
    content = line.strip()
    if content.startswith("|"):
        content = content[1:]
    if content.endswith("|"):
        content = content[:-1]
    parts = re.split(r"(?<!\\)\|", content)
    return [part.strip().replace("\\|", "|") for part in parts]


def is_separator_row(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", item.replace(" ", "")) for item in cells)


def first_table(tables: dict[str, list[MarkdownTable]], marker: str) -> MarkdownTable | None:
    items = tables.get(marker, [])
    return items[0] if items else None


def all_tables(tables: dict[str, list[MarkdownTable]], marker: str) -> list[MarkdownTable]:
    return tables.get(marker, [])


def cell(row: list[str], index: int) -> str:
    return row[index] if index < len(row) else ""


def normalize(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace('"', "").strip()).lower()


def canonical_id(value: str) -> str:
    match = ID_PATTERN.search(value or "")
    return match.group(0).upper() if match else ""


def extract_ids(value: str) -> set[str]:
    return {match.group(0).upper() for match in ID_PATTERN.finditer(value or "")}


def ids_of_type(value: str, prefix: str) -> set[str]:
    return {item for item in extract_ids(value) if item.startswith(prefix + "-")}


def join_ids(values: Iterable[str]) -> str:
    return ", ".join(sorted(values))


def is_blank(value: str) -> bool:
    return not value.strip() or normalize(value) in {"n/a", "na", "none", "-"}


def base_type(value: str) -> str:
    normalized = normalize(value)
    return re.sub(r"\s*\(.*$", "", normalized).strip()


def required_value(value: str) -> bool | None:
    normalized = normalize(value)
    if normalized in {"", "n/a", "unknown", "tbd"}:
        return None
    if any(token in normalized for token in ("required", "bắt buộc", "yes", "true")):
        return True
    if any(token in normalized for token in ("optional", "không", "no", "false")):
        return False
    return None


def dependency_cycle(graph: dict[str, set[str]]) -> list[str]:
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def visit(node: str) -> list[str]:
        if node in visiting:
            start = stack.index(node)
            return stack[start:] + [node]
        if node in visited:
            return []
        visiting.add(node)
        stack.append(node)
        for dependency in graph.get(node, set()):
            cycle = visit(dependency)
            if cycle:
                return cycle
        stack.pop()
        visiting.remove(node)
        visited.add(node)
        return []

    for candidate in graph:
        cycle = visit(candidate)
        if cycle:
            return cycle
    return []


def locks_overlap(left: str, right: str) -> bool:
    left = left.strip().rstrip("/")
    right = right.strip().rstrip("/")
    if not left or not right or normalize(left) in {"n/a", "na"} or normalize(right) in {"n/a", "na"}:
        return False
    return left == right or left.startswith(right + "/") or right.startswith(left + "/")


def side_effect_risk(value: str) -> bool:
    return bool(re.search(r"\b(delete|destructive|replace|publish|activate|email|message|external|api key|persona|permission|schedule|cleanup)\b", value, re.I))


def risk_controlled(value: str) -> bool:
    return bool(re.search(r"\b(approval|confirm|gate|containment|rollback|restore|snapshot|manual recovery)\b", value, re.I))


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


def cell_text(cell_node: ET.Element, strings: list[str]) -> str:
    cell_type = cell_node.get("t")
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell_node.findall(".//m:t", NS))
    value_node = cell_node.find("m:v", NS)
    value = value_node.text if value_node is not None and value_node.text is not None else ""
    if cell_type == "s" and value:
        return strings[int(value)]
    return value


def sheet_rows(archive: zipfile.ZipFile, sheet_path: str, strings: list[str]) -> list[list[str]]:
    root = ET.fromstring(archive.read(sheet_path))
    sparse_rows: dict[int, dict[int, str]] = {}
    max_column = 0
    for cell_node in root.findall(".//m:sheetData/m:row/m:c", NS):
        reference = cell_node.get("r", "")
        row_match = re.search(r"\d+$", reference)
        if not row_match:
            continue
        row_number = int(row_match.group(0)) - 1
        col_number = column_index(reference)
        sparse_rows.setdefault(row_number, {})[col_number] = cell_text(cell_node, strings)
        max_column = max(max_column, col_number)
    if not sparse_rows:
        return []
    rows: list[list[str]] = []
    for row_number in range(max(sparse_rows) + 1):
        row = [""] * (max_column + 1)
        for col_number, value in sparse_rows.get(row_number, {}).items():
            row[col_number] = value
        rows.append(row)
    return rows


def workbook_sheets(archive: zipfile.ZipFile) -> list[tuple[str, str]]:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    targets = {rel.get("Id"): rel.get("Target", "") for rel in relationships.findall("p:Relationship", NS)}
    result: list[tuple[str, str]] = []
    for sheet in workbook.findall("m:sheets/m:sheet", NS):
        name = sheet.get("name", "")
        relation_id = sheet.get(f"{{{REL_NS}}}id", "")
        target = targets.get(relation_id, "")
        path = target.lstrip("/")
        if not path.startswith("xl/"):
            path = posixpath.normpath(posixpath.join("xl", path))
        result.append((name, path))
    return result


def find_row(rows: list[list[str]], label: str) -> list[str]:
    matches = [row for row in rows if row and normalize(row[0]) == normalize(label)]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one {label!r} row, found {len(matches)}")
    return matches[0]


def read_workbook(path: Path) -> list[WorkbookObject]:
    objects: list[WorkbookObject] = []
    with zipfile.ZipFile(path) as archive:
        strings = shared_strings(archive)
        for sheet_name, sheet_path in workbook_sheets(archive):
            rows = sheet_rows(archive, sheet_path, strings)
            field_names = find_row(rows, "Field name")
            types = find_row(rows, "Data type")
            slugs = find_row(rows, "Slug")
            lookup_rows = [row for row in rows if row and normalize(row[0]) == "lookup to object"]
            lookups = lookup_rows[0] if lookup_rows else []
            object_name_row = find_row(rows, "Object name")
            object_name = cell(object_name_row, 1).strip()
            record_name_row = find_row(rows, "Record name field")
            record_name_field = re.sub(r"\*$", "", cell(record_name_row, 1).strip()).strip()
            fields: list[WorkbookField] = []
            for index in range(1, len(field_names)):
                name = cell(field_names, index).strip()
                if not name:
                    continue
                fields.append(
                    WorkbookField(
                        name=re.sub(r"\*$", "", name).strip(),
                        slug=cell(slugs, index).strip(),
                        data_type=cell(types, index).strip(),
                        required=name.endswith("*"),
                        lookup_target=cell(lookups, index).strip(),
                    )
                )
            options: dict[str, list[str]] = defaultdict(list)
            current = ""
            for row in rows:
                label = normalize(cell(row, 0))
                if label == "selective field":
                    current = normalize(cell(row, 1))
                elif label == "selective field option" and current:
                    options[current].append(cell(row, 1).strip())
            objects.append(WorkbookObject(sheet_name, object_name, record_name_field, fields, dict(options)))
    return objects


def render_json(validator: Validator, inputs: dict[str, str | None]) -> str:
    errors = sum(item.severity == "ERROR" for item in validator.findings)
    warnings = sum(item.severity == "WARNING" for item in validator.findings)
    payload = {
        "validator": "build-cogover-app/validate_artifacts",
        "version": VERSION,
        "status": "PASS" if errors == 0 else "FAIL",
        "errors": errors,
        "warnings": warnings,
        "inputs": {key: value for key, value in inputs.items() if value},
        "findings": [asdict(item) for item in validator.findings],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def render_markdown(validator: Validator, inputs: dict[str, str | None]) -> str:
    errors = sum(item.severity == "ERROR" for item in validator.findings)
    warnings = sum(item.severity == "WARNING" for item in validator.findings)
    status = "PASS" if errors == 0 else "FAIL"
    lines = [
        "# Cogover Artifact Validation",
        "",
        f"- Validator version: `{VERSION}`",
        f"- Result: `{status}`",
        f"- Errors: {errors}",
        f"- Warnings: {warnings}",
        "",
    ]
    if validator.findings:
        lines.extend(["## Findings", "", "| Severity | Code | Artifact | Message |", "|---|---|---|---|"])
        for item in validator.findings:
            values = [item.severity, item.code, item.artifact, item.message]
            lines.append("| " + " | ".join(value.replace("|", "\\|").replace("\n", " ") for value in values) + " |")
    else:
        lines.append("No findings.")
    lines.extend(["", "## Inputs", ""])
    for key, value in inputs.items():
        if value:
            lines.append(f"- {key}: `{value}`")
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solution", type=Path)
    parser.add_argument("--data-design", type=Path)
    parser.add_argument("--workbook", type=Path)
    parser.add_argument("--review-workbook", type=Path, help="Human review workbook; requires --data-design, separate from import --workbook.")
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--version", action="version", version=VERSION)
    args = parser.parse_args(argv)
    if args.review_workbook and (not args.data_design or args.workbook):
        parser.error("--review-workbook requires --data-design and cannot be combined with --workbook")
    if not any((args.solution, args.data_design, args.workbook, args.plan)):
        parser.error("provide at least one artifact input")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    validator = Validator()
    if args.solution:
        validator.validate_solution(args.solution)
    if args.data_design:
        validator.validate_data_design(args.data_design)
    if args.workbook:
        validator.validate_workbook(args.workbook, args.data_design)
    elif args.review_workbook:
        validator.validate_review_workbook(args.review_workbook, args.data_design)
    elif args.data_design:
        validator.warning("DATA_WORKBOOK_NOT_PROVIDED", str(args.data_design), "Workbook consistency was not checked.")
    if args.plan:
        validator.validate_plan(args.plan)

    inputs = {
        "solution": str(args.solution) if args.solution else None,
        "data_design": str(args.data_design) if args.data_design else None,
        "workbook": str(args.workbook) if args.workbook else None,
        "review_workbook": str(args.review_workbook) if args.review_workbook else None,
        "plan": str(args.plan) if args.plan else None,
    }
    json_report = render_json(validator, inputs)
    markdown_report = render_markdown(validator, inputs)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json_report, encoding="utf-8")
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(markdown_report, encoding="utf-8")
    print(markdown_report, end="")
    return 1 if any(item.severity == "ERROR" for item in validator.findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
