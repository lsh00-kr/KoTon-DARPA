# KoTon - THEIA E3 Graph Data Delivery

Date: 2026-11-23
Purpose: November 2026 interim deliverable for GNN integration.

## Files

- 6r_attack_graph_delivery.pt: THEIA E3 6r graph
- attack_evidence_nodes.csv: Eight attack-related evidence nodes
- 5m_comparison_graph.pt: Comparison graph (not verified benign)

## Graph Structure

Format: PyTorch Geometric HeteroData

| Node Type | 6r | 5m | Feature Dimensions |
| --- | ---: | ---: | ---: |
| Process | 173 | 13916 | 16 |
| File | 1215 | 20012 | 12 |
| Socket | 5 | 907 | 8 |

6r: 1393 nodes, 13 edge types.
5m: 34835 nodes, 10 edge types.

Feature dimensions match, but feature semantics and normalization
consistency have not been fully verified.

## Attack-Related Evidence

Eight evidence nodes in 6r:
- 3 process nodes
- 1 file node
- 4 socket nodes

Evidence includes Firefox shellcode-related connections,
execution of /home/admin/clean, and Drakon-related network endpoints.

The attack_candidate_mask marks evidence-based candidates,
not confirmed binary ground-truth labels or model predictions.

## Labeling Limitations

All node labels remain y = -1 (unknown).
Neither graph is ready for supervised benign/malicious training.
5m must not be assumed benign, and 6r must not be assumed
entirely malicious.

The attack_candidate_network edges are auxiliary candidate relations
and must not be interpreted as distinct confirmed attacks.

## Verification

6r:
- Node and edge index integrity checks passed.
- Evidence CSV UUID/index correspondence: 8/8 passed.
- Delivery graph reload and candidate mask checks passed.

5m:
- File loaded and node/edge counts inspected.
- Full edge index integrity check not yet performed.

HGT/RGCN forward tests passed previously.
No detection accuracy or model training performance is claimed.

## Integration Notes

- Check PyTorch/PyG environment compatibility.
- Verify feature preprocessing consistency.
- Establish a valid labeling or anomaly-detection strategy.
- Keep candidate masks separate from supervised training labels.
