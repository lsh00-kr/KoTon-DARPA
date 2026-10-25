# KoTon DARPA TC 데이터 전처리

## 1. 작업 개요

KoTon 프로젝트의 GNN 기반 실시간 이상행위 탐지 시스템 개발을 위한 DARPA 데이터 전처리 작업입니다.

DARPA Transparent Computing E3 THEIA 데이터의 프로세스, 파일, 소켓 정보와 이벤트 관계를 추출하고, 기존 KoTon 프로젝트의 그래프 스키마에 맞춰 변환했습니다.

이번 1차 작업에서는 **원본 데이터 파싱, 그래프 구성, PyTorch Geometric 기반 GNN 입력 데이터 생성 및 검증**까지 진행했습니다.

## 2. 사용 데이터

- **데이터셋:** DARPA Transparent Computing E3 THEIA
- **원본 파일:** `ta1-theia-e3-official-5m.json.tar.gz`
- **데이터 형식:** CDM18 JSONL
- **원본 레코드:** 1,090,138개
- **원본 이벤트:** 915,579개

전체 THEIA 데이터가 아닌 `official-5m` 파일 하나를 대상으로 1차 전처리를 수행했습니다.

## 3. 전처리 결과

| 항목 | 개수 |
|---|---:|
| Process 노드 | 13,916 |
| File 노드 | 20,012 |
| Socket 노드 | 907 |
| **전체 노드** | **34,835** |
| **변환된 정방향 이벤트** | **222,522** |

### 이벤트 관계 변환

현재 KoTon 스키마에서 지원하는 관계를 기준으로 다음 이벤트를 변환했습니다.

- `fork`: 프로세스 생성 및 복제 관계
- `read`: 프로세스의 파일 읽기
- `write`: 프로세스의 파일 쓰기
- `connect`: 프로세스의 네트워크 연결

원본 이벤트 915,579개 중 222,522개를 기존 그래프 스키마에 맞춰 변환했습니다.

지원하지 않는 이벤트 유형은 임의로 다른 관계에 매핑하지 않았으며, 향후 스키마 확장을 통해 추가할 수 있도록 구분했습니다.

## 4. 전처리 코드 및 결과 파일

GitHub 저장소에는 전처리 코드와 작업 설명을 정리했으며, 최종 데이터는 `KoTon_DARPA_final.zip`으로 제공합니다.

ZIP 내부 구성:

```text
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
```

### 주요 파일 설명

| 파일 | 역할 |
|---|---|
| `darpa_loader.py` | DARPA CDM18 원본 JSONL 파싱 및 노드·이벤트 추출 |
| `darpa_converter.py` | 이벤트 관계를 KoTon 스키마에 맞게 변환 |
| `darpa_adapter.py` | 최종 데이터 로딩 및 PyTorch Geometric 그래프 생성 |
| `process_nodes.jsonl` | 프로세스 노드 데이터 |
| `file_nodes.jsonl` | 파일 노드 데이터 |
| `socket_nodes.jsonl` | 소켓 노드 데이터 |
| `events.jsonl` | 변환된 이벤트 관계 데이터 |
| `summary.json` | 전처리 결과 요약 정보 |

원본 DARPA 데이터와 중간 처리 파일은 ZIP에 포함하지 않았습니다. 전체 전처리 과정을 다시 실행하려면 원본 데이터를 별도로 확보하고 입력 경로를 설정해야 합니다.

## 5. 기존 KoTon 프로젝트 적용 방법

본 전처리 결과물은 기존 [KoTon 프로젝트](https://github.com/oknos7f/KoTon)의 그래프 스키마를 기준으로 작성했습니다.

최종 ZIP을 다운로드한 뒤 기존 KoTon 프로젝트 루트에 압축을 해제하면 됩니다.

주요 파일 배치 구조:

```text
KoTon/
  koton/
    data/
      schema.py
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
```

프로젝트 루트에서 다음 Python 코드를 실행하여 그래프를 불러올 수 있습니다.

```python
from koton.data.darpa_adapter import load_koton_graph

graph = load_koton_graph(max_events=None)
print(graph)
```

일부 이벤트만 사용하여 테스트하려면 다음과 같이 실행할 수 있습니다.

```python
graph = load_koton_graph(max_events=1000)
```

실행에는 기존 KoTon 프로젝트의 `schema.py`와 PyTorch, PyTorch Geometric 환경이 필요합니다.

## 6. 검증 결과

전처리 데이터가 기존 KoTon 그래프 스키마와 호환되는지 확인했습니다.

- PyTorch Geometric `HeteroData` 생성 성공
- 전체 노드 34,835개 생성 확인
- 정방향 간선 222,522개 생성 확인
- 역방향 간선 222,522개 생성 확인
- 노드 특성 차원 확인
  - Process: 16차원
  - File: 12차원
  - Socket: 8차원
- 변환된 이벤트의 시간 순서 검사 통과

전체 데이터를 사용한 그래프 생성 테스트를 완료했습니다.

## 7. 후속 개발 및 확장 계획

이번 작업은 GNN 모델에 입력할 수 있는 그래프 데이터 구축을 중심으로 진행한 1차 전처리 결과입니다.

향후 다음 작업을 진행할 계획입니다.

1. **공격 시나리오 및 Ground Truth 연계**  
   사용한 데이터 구간에 해당하는 공격 시나리오와 정답 정보를 확인하고, 실제 공격 이벤트 및 노드와 매칭합니다.

2. **이벤트 관계 확장**  
   현재 스키마에 포함되지 않은 `EVENT_EXECUTE` 등의 이벤트 관계를 검토하고 그래프 표현 범위를 확장합니다.

3. **데이터 범위 확대**  
   THEIA의 추가 데이터 구간을 전처리하여 학습 및 평가에 사용할 데이터 범위를 확대합니다.

4. **GNN 모델 통합 및 검증**  
   전처리 결과를 탐지 모델에 연동하고, 필요한 노드 특성과 이벤트 관계를 개선합니다.

현재 사용한 데이터 구간에서는 공격 정답 라벨을 확인하지 못했으므로, **정상·공격 여부를 임의로 지정하지 않았습니다.** 정답 라벨을 이용한 지도학습 및 탐지 성능 평가는 Ground Truth 매칭 이후 진행해야 합니다.

## 8. 작업 진행 현황

### 1차 완료

- DARPA CDM18 원본 데이터 파싱
- 프로세스·파일·소켓 노드 생성
- 이벤트 관계 변환 및 그래프 구성
- 기존 KoTon 스키마 연동
- 전체 데이터 기반 그래프 생성 및 구조 검증
- 전처리 코드 및 결과 데이터 패키징
- GitHub 결과물 공유

### 후속 진행

- 공격 Ground Truth 확보 및 라벨 매칭
- 추가 이벤트 유형 지원
- 추가 데이터 구간 전처리
- GNN 탐지 모델과의 통합 테스트
