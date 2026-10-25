# KoTon DARPA TC 데이터 전처리 결과

## 1. 작업 개요

KoTon 프로젝트의 GNN 기반 이상행위 탐지를 위한 데이터 전처리 작업입니다.

DARPA Transparent Computing E3 THEIA 원본 데이터를 분석하여 프로세스, 파일, 소켓 및 이들 사이의 이벤트 관계를 그래프 형태로 변환했습니다.

현재 결과물은 **GNN 입력용 그래프 생성까지 검증된 상태**이며, 공격 정답 라벨은 아직 확보되지 않았습니다.

## 2. 사용 데이터

- 데이터셋: DARPA Transparent Computing E3 THEIA
- 원본 파일: `ta1-theia-e3-official-5m.json.tar.gz`
- 데이터 형식: CDM18 JSONL
- 원본 레코드: 1,090,138개

전체 THEIA 데이터가 아닌 일부 구간을 사용했습니다.

## 3. 전처리 결과

| 항목 | 개수 |
|---|---:|
| Process 노드 | 13,916 |
| File 노드 | 20,012 |
| Socket 노드 | 907 |
| 전체 노드 | 34,835 |
| 변환된 정방향 이벤트 | 222,522 |

변환된 이벤트 관계는 `fork`, `read`, `write`, `connect`이며, 기존 KoTon 스키마에 맞춰 역방향 간선도 생성할 수 있습니다.

원본 이벤트 915,579개 중 기존 스키마에서 지원하는 관계를 중심으로 222,522개를 변환했습니다. 지원하지 않는 이벤트를 임의로 다른 관계에 매핑하지 않았습니다.

4. 전달 파일

KoTon_DARPA_final.zip 구성:

README_DARPA.md
koton/
  data/
    darpa_loader.py
    darpa_converter.py
    darpa_adapter.py
data/
  processed/
    koton_ready/
      process_nodes.jsonl
      file_nodes.jsonl
      socket_nodes.jsonl
      events.jsonl
      summary.json

darpa_loader.py: DARPA CDM18 원본 JSONL을 노드 및 이벤트 데이터로 변환

darpa_converter.py: 원본 이벤트 관계를 KoTon 스키마에 맞게 변환

darpa_adapter.py: 최종 데이터 로딩 및 PyTorch Geometric 그래프 생성

koton_ready/: 전처리 완료된 그래프 입력 데이터

원본 DARPA 파일은 ZIP에 포함되지 않았습니다. 전처리 코드를 처음부터 재실행하려면 원본 데이터를 별도로 확보하고 입력 경로를 맞춰야 합니다.

## 5. 프로젝트 적용 방법

기존 KoTon 프로젝트 루트 기준으로 파일을 다음 위치에 배치합니다.

```text
KoTon/
  koton/
    data/
      schema.py
      darpa_adapter.py

  data/
    processed/
      koton_ready/
        process_nodes.jsonl
        file_nodes.jsonl
        socket_nodes.jsonl
        events.jsonl
        summary.json
```

프로젝트 루트에서 Python으로 실행합니다.

```python
from koton.data.darpa_adapter import load_koton_graph

graph = load_koton_graph(max_events=None)
print(graph)
```

실행에는 기존 프로젝트의 `schema.py`, PyTorch, PyTorch Geometric 환경이 필요합니다.

`max_events=1000`처럼 지정하면 일부 이벤트만 사용하여 테스트할 수 있습니다.

## 6. 검증 결과

- 기존 KoTon 스키마 기반 `HeteroData` 생성 성공
- 전체 노드 34,835개 생성 확인
- 정방향 간선 222,522개 생성 확인
- 역방향 간선 222,522개 생성 확인
- 노드 특성 차원 확인: Process 16, File 12, Socket 8
- 변환된 이벤트의 시간 순서 검사 통과

## 7. 현재 한계 및 후속 작업

1. **공격 정답 라벨 미확보:** 노드와 이벤트의 실제 공격 여부는 확인되지 않았습니다. 따라서 현재 결과물은 정답 라벨을 사용하는 지도학습용 완성 데이터가 아닙니다.
2. **일부 이벤트 유형 제외:** `EVENT_EXECUTE`는 원본에서 프로세스→파일 관계이지만, 기존 KoTon 스키마는 프로세스→프로세스 관계로 정의되어 있어 제외했습니다.
3. **일부 원본 정보 미포함:** 메모리 관련 이벤트 등은 현재 노드·간선 스키마에 포함되지 않았습니다.
4. **데이터 범위 제한:** THEIA 전체가 아닌 `official-5m` 파일 하나를 사용했습니다.

향후 공격 Ground Truth 자료 확보 및 매칭, 이벤트 관계 확장, 추가 데이터 구간 전처리가 필요합니다.

## 8. 작업 상태

**완료:** 원본 데이터 파싱, 노드·이벤트 변환, KoTon 스키마 연동, 그래프 생성 검증

**진행 예정:** 공격 라벨 확보, 추가 이벤트 유형 지원, 학습용 데이터 확장
