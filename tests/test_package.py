"""Basic import test for the openrun package."""


def test_import():
    """Test that the main package imports successfully."""
    import openrun

    # Core types should be available
    assert openrun.Flow is not None
    assert openrun.Step is not None
    assert openrun.StateContainer is not None

    # Steps should be available
    assert openrun.TriggerWebhook is not None
    assert openrun.StepDelay is not None
    assert openrun.StepRequest is not None
