from src.ingestion.log_watcher import follow
def test_follow_is_generator():
    assert hasattr(follow, "__call__")
