from src.interaction.iou_trigger import RollingSpikeTrigger


def test_spike_trigger_basic():
    trigger = RollingSpikeTrigger(
        baseline_window=3,
        spike_delta=0.2,
        min_iou=0.01,
        cooldown_frames=3,
        event_window=4,
    )

    series = [0.0, 0.05, 0.0, 0.6]
    fired = []
    for idx, value in enumerate(series):
        step = trigger.step(idx, value)
        fired.append(step.triggered)

    assert fired == [False, False, False, True]


def test_trigger_cooldown_blocks():
    trigger = RollingSpikeTrigger(
        baseline_window=2,
        spike_delta=0.1,
        min_iou=0.01,
        cooldown_frames=5,
        event_window=3,
    )

    series = [0.0, 0.0, 0.5, 0.6, 0.7, 0.8]
    fired = []
    for idx, value in enumerate(series):
        step = trigger.step(idx, value)
        fired.append(step.triggered)

    assert fired[2] is True
    assert any(fired[3:]) is False


def test_in_window_after_trigger():
    trigger = RollingSpikeTrigger(
        baseline_window=2,
        spike_delta=0.2,
        min_iou=0.01,
        cooldown_frames=1,
        event_window=3,
    )

    # Trigger fires at idx=2 (spike from 0→0.5).
    # event_window=3 → window covers frames {2, 3, 4}, i.e. [2, 2+3).
    series = [0.0, 0.0, 0.5, 0.1, 0.1, 0.1]
    in_window = []
    for idx, value in enumerate(series):
        step = trigger.step(idx, value)
        in_window.append(step.in_window)

    assert in_window[2] is True   # trigger frame
    assert in_window[3] is True   # in window
    assert in_window[4] is True   # last frame in window
    assert in_window[5] is False  # window expired
