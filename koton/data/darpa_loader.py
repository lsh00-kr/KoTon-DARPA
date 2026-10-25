
import json
from pathlib import Path
from collections import Counter

PROJECT_DIR = Path(__file__).resolve().parents[2]

INPUT_PATH = (
    PROJECT_DIR
    / "data"
    / "raw"
    / "ta1-theia-e3-official-5m.json"
    / "ta1-theia-e3-official-5m.json"
)

OUTPUT_DIR = PROJECT_DIR / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 원본 파일 전체 처리
MAX_RECORDS = None

FILE_NAMES = {
    "Subject": "processes.jsonl",
    "FileObject": "files.jsonl",
    "NetFlowObject": "sockets.jsonl",
    "Event": "events.jsonl",
}

def unwrap(value):
    """Avro JSON의 {"string": ...}, {"long": ...} 구조 해제"""
    if isinstance(value, dict) and len(value) == 1:
        key, inner = next(iter(value.items()))
        if key in ("string", "long", "int", "com.bbn.tc.schema.avro.cdm18.UUID"):
            return inner
    return value

def transform(record_type, data):
    if record_type == "Subject":
        props = (data.get("properties") or {}).get("map") or {}
        cmdline = unwrap(data.get("cmdLine")) or ""
        path = props.get("path") or ""
        return {
            "key": data.get("uuid"),
            "pid": data.get("cid"),
            "name": Path(path).name if path else "",
            "cmdline": cmdline,
            "path": path,
            "principal_id": data.get("localPrincipal"),
            "timestamp": (data.get("startTimestampNanos") or 0) / 1e9,
        }

    if record_type == "FileObject":
        props = ((data.get("baseObject") or {}).get("properties") or {}).get("map") or {}
        path = props.get("filename") or ""
        return {
            "key": data.get("uuid"),
            "path": path,
            "extension": Path(path).suffix,
        }

    if record_type == "NetFlowObject":
        return {
            "key": data.get("uuid"),
            "ip": data.get("remoteAddress") or "",
            "port": data.get("remotePort"),
            "protocol": data.get("ipProtocol") or "",
        }

    if record_type == "Event":
        return {
            "key": data.get("uuid"),
            "timestamp": (data.get("timestampNanos") or 0) / 1e9,
            "relation": data.get("type"),
            "subject_key": unwrap(data.get("subject")),
            "object_key": unwrap(data.get("predicateObject")),
        }

    return None

def main():
    counts = Counter()
    handles = {}

    try:
        for record_type, filename in FILE_NAMES.items():
            handles[record_type] = (
                OUTPUT_DIR / filename
            ).open("w", encoding="utf-8")

        with INPUT_PATH.open("r", encoding="utf-8") as source:
            for index, line in enumerate(source):
                if MAX_RECORDS is not None and index >= MAX_RECORDS:
                    break

                if not line.strip():
                    continue

                record = json.loads(line)
                datum = record.get("datum") or {}
                if not datum:
                    continue

                full_type, data = next(iter(datum.items()))
                record_type = full_type.split(".")[-1]

                if record_type not in FILE_NAMES:
                    continue

                result = transform(record_type, data)
                if result is None:
                    continue

                handles[record_type].write(
                    json.dumps(result, ensure_ascii=False) + "\n"
                )
                counts[record_type] += 1

    finally:
        for handle in handles.values():
            handle.close()

    print("전처리 완료!")
    for record_type, filename in FILE_NAMES.items():
        print(f"{filename}: {counts[record_type]:,}건")
    print("저장 위치:", OUTPUT_DIR)

if __name__ == "__main__":
    main()

