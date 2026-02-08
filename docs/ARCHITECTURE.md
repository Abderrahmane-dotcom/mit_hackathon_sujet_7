# Architecture

This diagram shows the event-triggered pipeline from video ingest to JSON Action Logs.

```mermaid
flowchart LR
  A[Video Ingest] --> B[YOLOv8 Detector]
  B --> C[ByteTrack Tracker]
  C --> D{Interaction Trigger IoU}
  D -- no --> C
  D -- yes --> E[LFM VLM Query]
  E --> F[State Memory]
  F --> G[JSON Action Log]
  E --> H[SAM Segmenter]
  H --> G
  G --> I[Streamlit App]

  subgraph Configs
    P[Prompt Templates]
    M[Model Settings]
  end
  P --> E
  M --> B
  M --> E
  M --> H
```

Key ideas:
- Fast detection and tracking runs continuously; semantic reasoning is event-triggered.
- State memory records transitions across time, enabling causal logs.
- Logs power the real-time visualization and downstream learning.
