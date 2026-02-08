# Project Structure

This is a proposed layout for the TruthStream pipeline. The focus is on clear boundaries between video ingest, detection, interaction logic, semantic reasoning, and outputs.

```
world2data/
  readme.md
  docs/
    ARCHITECTURE.md
    PROJECT_STRUCTURE.md
    TASKS.md
  configs/
    prompts.yaml
    model.yaml
  data/
    raw/
    processed/
    samples/
  notebooks/
    implementation.ipynb
  scripts/
    run_pipeline.ps1
    export_logs.ps1
  src/
    app/
      streamlit_app.py
    ingest/
      video_loader.py
    detection/
      yolo_detector.py
      bytetrack_tracker.py
    interaction/
      iou_trigger.py
      state_memory.py
    semantic/
      vlm_client.py
      sam_segmenter.py
    pipeline/
      truthstream_pipeline.py
    logging/
      json_logger.py
      schema.py
    eval/
      metrics.py
      eval_runner.py
    utils/
      video_utils.py
      viz_utils.py
  tests/
    test_trigger.py
    test_state_memory.py
    test_json_logger.py
```

Notes:
- `notebooks/implementation.ipynb` is the staging area. Implement and validate each module in the notebook first, then move to the matching source file.
- `configs/` holds prompts and model settings so they are easy to tweak without changing code.
- `logging/schema.py` defines the JSON Action Log schema to keep outputs consistent.
