import json, pathlib
def test_cookie_file():
    c = pathlib.Path("profiles/niijima_cookies.json")
    cookies = json.loads(c.read_text())
    assert isinstance(cookies, list)
    for ck in cookies:
        for key in ("name", "value", "domain", "path"):
            assert key in ck
