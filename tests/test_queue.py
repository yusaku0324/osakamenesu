import yaml, pathlib
def test_queue_file():
    q = pathlib.Path("queue/queue_now.yaml")
    data = yaml.safe_load(q.read_text())
    assert isinstance(data, list)
    for item in data:
        assert "text" in item
