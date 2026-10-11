#!/usr/bin/env python3
"""Read-only BPMN connection checks; Python standard library, no API calls."""

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
from xml.parsers import expat

MODEL = "http://www.omg.org/spec/BPMN/20100524/MODEL"
DI = "http://www.omg.org/spec/BPMN/20100524/DI"
DC = "http://www.omg.org/spec/DD/20100524/DC"
WAYPOINT = "{http://www.omg.org/spec/DD/20100524/DI}waypoint"


def local(element):
    return element.tag.rsplit("}", 1)[-1]


def extract_xml(text):
    """Accept XML, a process payload, or a public API response envelope."""
    value = text
    for _ in range(8):
        if isinstance(value, str):
            if value.lstrip().startswith("<"):
                return value
            value = json.loads(value)
        elif isinstance(value, dict):
            if "r" in value and value["r"] != 0:
                raise ValueError("API response is not successful")
            if "xmlString" in value:
                value = value["xmlString"]
            elif "body" in value:
                value = value["body"]
            else:
                value = value.get("data")
        else:
            break
    raise ValueError("Expected BPMN XML or a process with xmlString")


def outline(node, bounds):
    """Task bounds, gateway diamond, event ellipse (128-segment approximation)."""
    x, y, w, h = (float(bounds[k]) for k in ("x", "y", "width", "height"))
    if not all(math.isfinite(v) for v in (x, y, w, h)) or w <= 0 or h <= 0:
        raise ValueError("Invalid node bounds")
    cx, cy = x + w / 2, y + h / 2
    kind = local(node)
    if kind.endswith("Gateway"):
        return [(cx, y), (x + w, cy), (cx, y + h), (x, cy)]
    if kind.endswith("Event"):
        return [(cx + w / 2 * math.cos(i * math.tau / 128),
                 cy + h / 2 * math.sin(i * math.tau / 128)) for i in range(128)]
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def sides(polygon):
    return zip(polygon, polygon[1:] + polygon[:1])


def boundary_distance(point, polygon):
    distances = []
    for a, b in sides(polygon):
        dx, dy = b[0] - a[0], b[1] - a[1]
        t = max(0, min(1, ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy)
                       / (dx * dx + dy * dy)))
        distances.append(math.hypot(point[0] - a[0] - t * dx, point[1] - a[1] - t * dy))
    return min(distances)


def crosses_interior(start, end, polygon, tolerance):
    """Clip a segment to the inset convex polygon; ignore boundary touches."""
    lower, upper = 0.0, 1.0
    vx, vy = end[0] - start[0], end[1] - start[1]
    for a, b in sides(polygon):
        dx, dy = b[0] - a[0], b[1] - a[1]
        offset = dx * (start[1] - a[1]) - dy * (start[0] - a[0]) - tolerance * math.hypot(dx, dy)
        slope = dx * vy - dy * vx
        if abs(slope) < 1e-12:
            if offset <= 0:
                return False
        elif slope > 0:
            lower = max(lower, -offset / slope)
        else:
            upper = min(upper, -offset / slope)
        if upper <= lower:
            return False
    return (upper - lower) * math.hypot(vx, vy) > tolerance


def validate(text, mode="request", tolerance=1.0):
    errors, warnings = [], []
    counts = {}

    def error(code, **details):
        errors.append(dict(code=code, **details))

    def result():
        return dict(ok=not errors, counts=counts, errors=errors, warnings=warnings)

    if mode not in ("request", "response") or not math.isfinite(tolerance) or tolerance <= 0:
        error("INVALID_OPTIONS")
        return result()
    try:
        xml = extract_xml(text)
        if re.search(r"<!\s*(DOCTYPE|ENTITY)\b", xml, re.I):
            raise ValueError("DTD/entity declarations are unsupported")
        # A response may contain an undeclared bpmn alias. Repair only a parsing copy.
        if mode == "response" and re.search(r"</?bpmn:", xml) and not re.search(r"xmlns:bpmn\s*=", xml):
            xml, replaced = re.subn(r"(<(?:\w+:)?definitions)(?=[\s>])",
                                   rf'\1 xmlns:bpmn="{MODEL}"', xml, count=1)
            if replaced:
                warnings.append(dict(code="RESPONSE_BPMN_ALIAS", message="Namespace added only to parsing copy"))
        root = ET.fromstring(xml)
    except (ValueError, ET.ParseError, TypeError):
        error("INVALID_INPUT", message="Cannot parse BPMN XML/process JSON; check namespaces and envelope")
        return result()
    if mode == "request":
        # Check actual element prefixes, including locally scoped/default namespaces.
        parser = expat.ParserCreate(namespace_separator="|")
        parser.namespace_prefixes = True
        wrong_prefix = []

        def check_prefix(name, _attributes):
            parts = name.split("|")
            if parts[0] == MODEL and (len(parts) != 3 or parts[2] != "bpmn2"):
                wrong_prefix.append(name)

        parser.StartElementHandler = check_prefix
        parser.Parse(xml, True)
        if wrong_prefix:
            error("REQUEST_BPMN_PREFIX", message="Use bpmn2 for BPMN model elements in generated requests")
    processes = list(root.iter("{" + MODEL + "}process"))
    if len(processes) != 1 or any(local(e) == "subProcess" and e.find("{" + MODEL + "}startEvent") is not None for e in root.iter()):
        error("UNSUPPORTED_STRUCTURE", message="Expected one flat process; nested BPMN subprocesses need separate review")
        return result()
    process = processes[0]
    all_ids = Counter(e.get("id") for e in root.iter() if e.get("id"))
    for identifier, count in all_ids.items():
        if count > 1:
            error("DUPLICATE_ID", elementId=identifier)
    nodes, flows = {}, {}
    for element in process:
        if local(element) in ("documentation", "extensionElements"):
            continue
        identifier = element.get("id")
        if not identifier:
            error("MISSING_ID", elementType=local(element))
            continue
        if element.tag == "{" + MODEL + "}sequenceFlow":
            flows[identifier] = element
        elif local(element).endswith(("Task", "Event", "Gateway")) or any(
                e.get("renderKey") for e in element.iter()):
            nodes[identifier] = element
        else:
            error("UNSUPPORTED_NODE", nodeId=identifier, elementType=local(element))
    if not nodes or not flows:
        error("EMPTY_GRAPH")
    shape_elements = list(root.iter("{" + DI + "}BPMNShape"))
    edge_elements = list(root.iter("{" + DI + "}BPMNEdge"))
    counts.update(nodes=len(nodes), flows=len(flows), shapes=len(shape_elements), edges=len(edge_elements))

    def index_di(elements, expected, kind):
        index = {}
        for element in elements:
            ref = element.get("bpmnElement")
            if ref not in expected:
                error("UNKNOWN_DI_REFERENCE", kind=kind, elementId=ref)
            if ref in index:
                error("DUPLICATE_DI_REFERENCE", kind=kind, elementId=ref)
            index[ref] = element
        for ref in expected.keys() - index.keys():
            error("MISSING_DI", kind=kind, elementId=ref)
        return index

    shapes = index_di(shape_elements, nodes, "shape")
    edges = index_di(edge_elements, flows, "edge")
    polygons = {}
    for nid, node in nodes.items():
        shape = shapes.get(nid)
        if shape is not None:
            try:
                bounds = shape.findall("{" + DC + "}Bounds")
                if len(bounds) != 1:
                    raise ValueError("Expected one bounds element")
                polygons[nid] = outline(node, bounds[0].attrib)
            except (ValueError, KeyError):
                error("INVALID_BOUNDS", nodeId=nid)
        for direction, ref in (("incoming", "targetRef"), ("outgoing", "sourceRef")):
            declared = Counter(e.text for e in node if e.tag == "{" + MODEL + "}" + direction)
            expected = Counter(fid for fid, flow in flows.items() if flow.get(ref) == nid)
            if declared != expected:
                error("FLOW_DECLARATION_MISMATCH", nodeId=nid, direction=direction)
    for fid, flow in flows.items():
        for ref in ("sourceRef", "targetRef"):
            if flow.get(ref) not in nodes:
                error("UNKNOWN_NODE_REFERENCE", flowId=fid, reference=ref)
        edge = edges.get(fid)
        if edge is None:
            continue
        try:
            points = [(float(e.attrib["x"]), float(e.attrib["y"])) for e in edge if e.tag == WAYPOINT]
            if len(points) < 2 or not all(math.isfinite(v) for p in points for v in p):
                raise ValueError("Invalid waypoints")
        except (ValueError, KeyError):
            error("INVALID_WAYPOINTS", flowId=fid)
            continue
        for ref, point in (("sourceRef", points[0]), ("targetRef", points[-1])):
            nid = flow.get(ref)
            if nid in polygons and boundary_distance(point, polygons[nid]) > tolerance:
                error("ENDPOINT_OFF_NODE", flowId=fid, nodeId=nid, endpoint=ref, point=point)
        for i, (start, end) in enumerate(zip(points, points[1:])):
            if math.dist(start, end) < 1e-9:
                error("ZERO_LENGTH_SEGMENT", flowId=fid, segment=i)
            for nid, polygon in polygons.items():
                if crosses_interior(start, end, polygon, tolerance):
                    error("SEGMENT_THROUGH_NODE", flowId=fid, nodeId=nid, segment=i)
    return result()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", default="-", help="XML/JSON file, or - for stdin")
    parser.add_argument("--mode", choices=("request", "response"), default="request")
    parser.add_argument("--tolerance", type=float, default=1.0, help="Coordinate tolerance in pixels (default: 1)")
    args = parser.parse_args()
    try:
        text = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8")
        report = validate(text, args.mode, args.tolerance)
    except (OSError, UnicodeError):
        report = dict(ok=False, errors=[dict(code="INPUT_READ_ERROR")], warnings=[])
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
