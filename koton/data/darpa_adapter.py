
import json
from pathlib import Path
from collections import Counter

# 프로젝트 폴더를 기준으로 데이터 경로 설정
PROJECT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_DIR / "data" / "processed"
OUTPUT_DIR = DATA_DIR / "koton_ready"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

NODE_FILES = {
    "process": "processes.jsonl",
    "file": "files.jsonl",
    "socket": "sockets.jsonl",
}

REQUIRED_FIELDS = {
    "process": ("key", "pid", "name", "cmdline", "path", "timestamp"),
    "file": ("key", "path"),
    "socket": ("key", "ip", "port"),
}

VALID_RELATIONS = {
    ("process", "fork", "process"),
    ("process", "exec", "process"),
    ("process", "read", "file"),
    ("process", "write", "file"),
    ("process", "connect", "socket"),
}


def read_jsonl(path):
    with path.open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"{path.name}:{line_number} JSON 오류: {exc}"
                ) from exc


def normalize_node(node_type, raw):
    key = raw.get("key")
    if not isinstance(key, str) or not key:
        raise ValueError(f"{node_type}: UUID 누락")

    node = {
        field: raw.get(field)
        for field in REQUIRED_FIELDS[node_type]
    }

    if node_type == "process":
        node["pid"] = int(node["pid"]) if node["pid"] is not None else 0
        node["name"] = node["name"] or "unknown"
        node["cmdline"] = node["cmdline"] or ""
        node["path"] = node["path"] or ""
        node["timestamp"] = float(node["timestamp"] or 0)
        node["uid"] = None

    elif node_type == "file":
        node["path"] = node["path"] or ""
        node["extension"] = raw.get("extension") or Path(node["path"]).suffix
        node["timestamp"] = float(raw.get("timestamp") or 0)

    elif node_type == "socket":
        node["ip"] = node["ip"] or ""
        node["port"] = int(node["port"]) if node["port"] is not None else 0
        node["protocol"] = raw.get("protocol") or "unknown"
        node["timestamp"] = float(raw.get("timestamp") or 0)

    node["label"] = None
    node["is_anomaly"] = None
    node["anomaly_score"] = None
    node["node_type"] = node_type

    return node


def main():
    stats = Counter()
    nodes = {}

    for node_type, filename in NODE_FILES.items():
        records = {}
        for raw in read_jsonl(DATA_DIR / filename):
            node = normalize_node(node_type, raw)
            key = node["key"]

            if key in records:
                stats[f"{node_type}_duplicates"] += 1

            records[key] = node

        nodes[node_type] = records
        stats[f"{node_type}_nodes"] = len(records)

        output_path = OUTPUT_DIR / f"{node_type}_nodes.jsonl"
        with output_path.open("w", encoding="utf-8") as output:
            for node in records.values():
                output.write(json.dumps(node, ensure_ascii=False) + "\n")

    with (OUTPUT_DIR / "events.jsonl").open(
        "w", encoding="utf-8"
    ) as output:
        for event in read_jsonl(DATA_DIR / "koton_events.jsonl"):
            stats["input_events"] += 1

            relation = (
                event.get("src_type"),
                event.get("relation"),
                event.get("dst_type"),
            )

            if relation not in VALID_RELATIONS:
                stats["invalid_relation"] += 1
                continue

            src_key = event.get("src_key")
            dst_key = event.get("dst_key")

            if src_key not in nodes[relation[0]]:
                stats["missing_source"] += 1
                continue

            if dst_key not in nodes[relation[2]]:
                stats["missing_target"] += 1
                continue

            converted = {
                "timestamp": float(event["timestamp"]),
                "src_type": relation[0],
                "src_key": src_key,
                "relation": relation[1],
                "dst_type": relation[2],
                "dst_key": dst_key,
                "is_attack": None,
                "metadata": event.get("metadata") or {},
            }

            output.write(json.dumps(converted, ensure_ascii=False) + "\n")
            stats["valid_events"] += 1

    summary = {
        "dataset": "DARPA TC E3 THEIA",
        "source": "ta1-theia-e3-official-5m.json",
        "statistics": dict(stats),
        "labels_available": False,
        "uid_available": False,
        "notes": [
            "Node and event UUID references have been validated.",
            "Unknown attack labels are represented as null.",
            "Unknown process UIDs are represented as null.",
            "Unknown network protocols are represented as unknown.",
            "The output is not yet a PyTorch Geometric graph.",
            "Supervised training requires verified attack labels.",
        ],
    }

    with (OUTPUT_DIR / "summary.json").open(
        "w", encoding="utf-8"
    ) as output:
        json.dump(summary, output, ensure_ascii=False, indent=2)

    print("KoTon 전처리 완료")
    for key, value in stats.items():
        print(f"{key}: {value:,}")
    print("결과 폴더:", OUTPUT_DIR)


def load_koton_graph(max_events=1000):
    from koton.data.schema import (
        ProcessNode,
        FileNode,
        SocketNode,
        ProvenanceEvent,
        build_hetero_data,
    )

    processes = {}
    files = {}
    sockets = {}

    for raw in read_jsonl(OUTPUT_DIR / "process_nodes.jsonl"):
        processes[raw["key"]] = ProcessNode(
            key=raw["key"],
            pid=raw["pid"],
            name=raw["name"],
            cmdline=raw["cmdline"],
            path=raw["path"],
            uid=-1,
            timestamp=raw["timestamp"],
            label=-1,
        )

    for raw in read_jsonl(OUTPUT_DIR / "file_nodes.jsonl"):
        files[raw["key"]] = FileNode(
            key=raw["key"],
            path=raw["path"],
            extension=raw["extension"],
            timestamp=raw["timestamp"],
            label=-1,
        )

    for raw in read_jsonl(OUTPUT_DIR / "socket_nodes.jsonl"):
        sockets[raw["key"]] = SocketNode(
            key=raw["key"],
            ip=raw["ip"],
            port=raw["port"],
            protocol=raw["protocol"],
            timestamp=raw["timestamp"],
            label=-1,
        )

    events = []

    for raw in read_jsonl(OUTPUT_DIR / "events.jsonl"):
        if max_events is not None and len(events) >= max_events:
            break

        events.append(
            ProvenanceEvent(
                timestamp=raw["timestamp"],
                src_type=raw["src_type"],
                src_key=raw["src_key"],
                relation=raw["relation"],
                dst_type=raw["dst_type"],
                dst_key=raw["dst_key"],
                is_attack=False,
                metadata={
                    **raw.get("metadata", {}),
                    "label_status": "unknown",
                },
            )
        )

    graph = build_hetero_data(
        processes=processes,
        files=files,
        sockets=sockets,
        events=events,
    )

    # DARPA 원본에 공격 정답 라벨이 없으므로 -1로 유지
    for node_type in graph.node_types:
        graph[node_type].y.fill_(-1)

    return graph

if __name__ == "__main__":
    main()
