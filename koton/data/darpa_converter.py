
import json
from pathlib import Path
from collections import Counter

PROJECT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_DIR / "data" / "processed"
OUTPUT_FILE = DATA_DIR / "koton_events.jsonl"

# 첫 테스트에서는 1,000건만 변환
MAX_EVENTS = None

# KoTon에서 지원하는 관계
RELATIONS = {
    "EVENT_FORK": ("fork", "process"),
    "EVENT_CLONE": ("fork", "process"),
    "EVENT_READ": ("read", "file"),
    "EVENT_WRITE": ("write", "file"),
    "EVENT_CONNECT": ("connect", "socket"),
}

def load_keys(filename):
    with (DATA_DIR / filename).open(encoding="utf-8") as f:
        return {json.loads(line)["key"] for line in f}

def main():
    process_keys = load_keys("processes.jsonl")
    file_keys = load_keys("files.jsonl")
    socket_keys = load_keys("sockets.jsonl")

    node_keys = {
        "process": process_keys,
        "file": file_keys,
        "socket": socket_keys,
    }

    counts = Counter()

    with (DATA_DIR / "events.jsonl").open(encoding="utf-8") as source, \
         OUTPUT_FILE.open("w", encoding="utf-8") as output:

        for index, line in enumerate(source):
            if MAX_EVENTS is not None and index >= MAX_EVENTS:
                break

            event = json.loads(line)
            original_relation = event["relation"]
            counts["total"] += 1

            if original_relation not in RELATIONS:
                counts["unsupported_relation"] += 1
                continue

            relation, dst_type = RELATIONS[original_relation]
            src_key = event["subject_key"]
            dst_key = event["object_key"]

            if src_key not in process_keys:
                counts["missing_process"] += 1
                continue

            if dst_key not in node_keys[dst_type]:
                counts["wrong_or_missing_target"] += 1
                continue

            converted = {
                "timestamp": event["timestamp"],
                "src_type": "process",
                "src_key": src_key,
                "relation": relation,
                "dst_type": dst_type,
                "dst_key": dst_key,
                "metadata": {
                    "original_event": original_relation,
                    "event_uuid": event["key"],
                },
            }

            # 공격 라벨은 아직 확보하지 않았으므로 넣지 않음
            output.write(json.dumps(converted) + "\n")
            counts["converted"] += 1

    print("변환 테스트 완료!")
    for key, value in counts.items():
        print(f"{key}: {value:,}")
    print("결과 파일:", OUTPUT_FILE)

if __name__ == "__main__":
    main()
