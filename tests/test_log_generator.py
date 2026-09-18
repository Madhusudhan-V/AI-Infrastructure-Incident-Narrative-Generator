from pathlib import Path
def test_sample_log_exists():
    assert Path("data/sample_logs/application.log").exists()
