from src.interaction.state_memory import StateMemory


def test_state_memory_transitions():
    memory = StateMemory()
    assert memory.get_state("door_1") == "unknown"

    updated = memory.update_state("door_1", "closed", frame_idx=1, reason="init")
    assert updated is True

    updated = memory.update_state("door_1", "closed", frame_idx=2, reason="noop")
    assert updated is False

    updated = memory.update_state("door_1", "open", frame_idx=3, reason="interaction")
    assert updated is True

    history = memory.history
    assert len(history) == 2
    assert history[0].before == "unknown"
    assert history[0].after == "closed"
    assert history[1].before == "closed"
    assert history[1].after == "open"
