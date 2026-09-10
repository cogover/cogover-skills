"""Synthetic regression tests for review workbooks and execution checkpoints."""

import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

from validate_artifacts import (
    MAIN_NS, REL_NS, PKG_REL_NS, Validator, WorkbookObject, parse_args,
)


HEADERS = ["Field name", "Field slug", "Data type", "Field ID", "Object slug", "Action", "Request IDs", "Notes"]


def table(marker, width, rows):
    return "\n".join([
        f"<!-- cogover-table:{marker} -->",
        "| " + " | ".join(f"Column {i}" for i in range(width)) + " |",
        "| " + " | ".join("---" for _ in range(width)) + " |",
        *("| " + " | ".join(row) + " |" for row in rows), "",
    ])


def write_review(path, rows, freeze=True):
    """Minimal OOXML fixture for parser checks, not a rendered deliverable."""
    ns = f"{{{MAIN_NS}}}"
    root = ET.Element(ns + "worksheet")
    views = ET.SubElement(root, ns + "sheetViews")
    view = ET.SubElement(views, ns + "sheetView", workbookViewId="0")
    if freeze:
        ET.SubElement(view, ns + "pane", xSplit="1", ySplit="1", state="frozen", topLeftCell="B2")
    cols = ET.SubElement(root, ns + "cols")
    ET.SubElement(cols, ns + "col", min="1", max="1", width="13.57")
    ET.SubElement(cols, ns + "col", min="2", max="8", width="22.14")
    sheet = ET.SubElement(root, ns + "sheetData")
    for index, values in enumerate([HEADERS] + rows, 1):
        row = ET.SubElement(sheet, ns + "row", r=str(index))
        for col, value in enumerate(values):
            cell = ET.SubElement(row, ns + "c", r=f"{chr(65 + col)}{index}", t="inlineStr")
            inline = ET.SubElement(cell, ns + "is")
            ET.SubElement(inline, ns + "t").text = value
    workbook = ET.Element(ns + "workbook")
    sheets = ET.SubElement(workbook, ns + "sheets")
    ET.SubElement(sheets, ns + "sheet", name="Equipment", sheetId="1", attrib={f"{{{REL_NS}}}id": "rId1"})
    relations = ET.Element(f"{{{PKG_REL_NS}}}Relationships")
    ET.SubElement(relations, f"{{{PKG_REL_NS}}}Relationship", Id="rId1", Target="worksheets/sheet1.xml")
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("xl/workbook.xml", ET.tostring(workbook))
        archive.writestr("xl/_rels/workbook.xml.rels", ET.tostring(relations))
        archive.writestr("xl/worksheets/sheet1.xml", ET.tostring(root))


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def review(self, rows=None, disposition="EXTEND", scope_action="MODIFY", freeze=True):
        data = self.root / "data-design-v1.md"
        fields = [
            ["FLD-001", "OBJ-001", "Warranty", "warranty", "numeric", "1", "No", "vi-VN", "N/A", "Staff", "N/A", "REQ-001", "Warranty reporting"],
            ["FLD-002", "OBJ-001", "Old code", "old_code", "short_text", "1", "No", "vi-VN", "N/A", "Staff", "N/A", "REQ-001", "Existing unchanged field"],
        ]
        data.write_text(
            table("object-catalog", 11, [["OBJ-001", "Equipment", "equipment", disposition, "Master", "Manage equipment", "name", "Staff", "N/A", "REQ-001", "Verified schema"]])
            + table("relationships", 9, [])
            + table("fields", 13, fields)
            + table("workbook-scope", 3, [["FLD-001", scope_action, "Warranty requirement"], ["FLD-002", "OMIT_EXISTING", "Existing unchanged field in verified schema"]]),
            encoding="utf-8",
        )
        if rows is None:
            rows = [["Warranty", "warranty", "numeric", "FLD-001", "equipment", scope_action, "REQ-001", "REQ-001: Ghi thời hạn để nhân viên kiểm tra điều kiện bảo hành."]]
        workbook = self.root / "review.xlsx"
        write_review(workbook, rows, freeze=freeze)
        validator = Validator()
        validator.validate_data_design(data)
        validator.validate_review_workbook(workbook, data)
        return validator

    @staticmethod
    def errors(validator):
        return {f.code for f in validator.findings if f.severity == "ERROR"}

    def test_existing_unchanged_field_can_be_omitted(self):
        self.assertEqual(self.errors(self.review()), set())

    def test_new_modified_and_important_fields_cannot_be_missing(self):
        for action in ("NEW", "MODIFY", "IMPORTANT"):
            with self.subTest(action=action):
                self.assertIn("REVIEW_FIELD_MISSING", self.errors(self.review(rows=[], scope_action=action)))

    def test_new_object_cannot_claim_omitted_existing_field(self):
        self.assertIn("REVIEW_SCOPE_NEW_OBJECT", self.errors(self.review(disposition="CREATE")))

    def test_duplicate_fields_are_rejected(self):
        row = ["Warranty", "warranty", "numeric", "FLD-001", "equipment", "MODIFY", "REQ-001", "REQ-001: Explain warranty."]
        self.assertIn("REVIEW_FIELD_SCOPE", self.errors(self.review(rows=[row, row])))

    def test_type_request_and_notes_errors_are_detected(self):
        row = ["Warranty", "warranty", "short_text", "FLD-001", "equipment", "MODIFY", "REQ-999", "REQ-001"]
        errors = self.errors(self.review(rows=[row]))
        self.assertTrue({"REVIEW_FIELD_MISMATCH", "REVIEW_REQUESTS", "REVIEW_NOTES"} <= errors)

    def test_frozen_name_column_is_required(self):
        self.assertIn("REVIEW_FREEZE", self.errors(self.review(freeze=False)))

    def test_import_profile_still_requires_record_name(self):
        validator = Validator()
        with patch("validate_artifacts.read_workbook", return_value=[WorkbookObject("Equipment", "Equipment", "Name", [], {})]):
            validator.validate_workbook(self.root / "import.xlsx", None)
        self.assertIn("WORKBOOK_RECORD_NAME", self.errors(validator))

    def test_review_cli_requires_data_design(self):
        with self.assertRaises(SystemExit):
            parse_args(["--review-workbook", "review.xlsx"])

    def plan(self, mark="[x]", evidence="Read-back and test passed", checkpoint_id="W-001"):
        path = self.root / "implementation-plan-v1.md"
        path.write_text(
            "<!-- cogover-data-model-gate:APPROVED -->\n"
            + table("requirement-traceability", 7, [["REQ-001", "N/A", "N/A", "W-001", "T-001", "COVERED", "N/A"]])
            + table("work-breakdown", 14, [["W-001", "DONE", "REQ-001", "N/A", "Add field", "Create field", "object-info", "N/A", "N/A", "object/equipment", "Field exists", "Read field", "T-001", "Snapshot"]])
            + table("lock-register", 5, [["object/equipment", "W-001", "coordinator", "N/A", "No"]])
            + table("test-plan", 7, [["T-001", "REQ-001", "Read field", "Object exists", "Read schema", "Field exists", "Read-back"]])
            + table("execution-checkpoints", 7, [[checkpoint_id, mark, "2026-09-11T10:00:00Z", "executor", "equipment.warranty", evidence, "N/A"]]),
            encoding="utf-8",
        )
        validator = Validator()
        validator.validate_plan(path)
        return validator

    def test_done_checkpoint_with_evidence(self):
        self.assertEqual(self.errors(self.plan()), set())

    def test_done_checkbox_disagreement_and_missing_evidence(self):
        errors = self.errors(self.plan(mark="[ ]", evidence="TBD"))
        self.assertTrue({"PLAN_CHECKPOINT_STATUS", "PLAN_CHECKPOINT_EVIDENCE"} <= errors)

    def test_unknown_checkpoint_cannot_replace_known_work(self):
        errors = self.errors(self.plan(checkpoint_id="W-999"))
        self.assertTrue({"PLAN_CHECKPOINT_ID", "PLAN_CHECKPOINT_COVERAGE"} <= errors)


if __name__ == "__main__":
    unittest.main()
