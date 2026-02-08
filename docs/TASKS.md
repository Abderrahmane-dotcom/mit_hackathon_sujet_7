# Task Split (4 People)

Reminder: implement and validate each piece in `notebooks/implementation_{task_i}.ipynb` before creating the matching source file.

## Person 1: Ingest + Detection

- Notebook: prototype video loading and frame sampling.
- Implement:
  - `src/ingest/video_loader.py` (load video, frame iterator, timestamps)
  - `src/detection/yolo_detector.py` (wrap YOLOv8 inference)
  - `src/detection/bytetrack_tracker.py` (track IDs across frames)
- Configs:
  - `configs/model.yaml` (detector and tracker settings)

## Person 2: Interaction + State Tracking

- Notebook: validate IoU trigger and state transitions on sample clips.
- Implement:
  - `src/interaction/iou_trigger.py` (IoU spike detection + event window)
  - `src/interaction/state_memory.py` (per-object state machine)
  - `src/pipeline/truthstream_pipeline.py` (orchestrate steps)
- Tests:
  - `tests/test_trigger.py`
  - `tests/test_state_memory.py`

## Person 3: Semantic + Segmentation

- Notebook: prompt the VLM on cropped interactions; test SAM boundaries.
- Implement:
  - `src/semantic/vlm_client.py` (LiquidAI LFM request wrapper)
  - `src/semantic/sam_segmenter.py` (affordance segmentation)
- Configs:
  - `configs/prompts.yaml` (prompt templates for door state)

## Person 4: Logging + App + Eval

- Notebook: validate JSON schema and visualization with sample events.
- Implement:
  - `src/logging/schema.py` (Action Log schema)
  - `src/logging/json_logger.py` (write logs + versioning)
  - `src/app/streamlit_app.py` (real-time visualization)
  - `src/eval/metrics.py`, `src/eval/eval_runner.py` (basic metrics)
- Tests:
  - `tests/test_json_logger.py`
