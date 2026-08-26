"""
API tests for Linklet URL shortener.
Fixtures (clean_db, sys.path setup, TEST_DATABASE_URL) live in conftest.py.
"""
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from main import app

client = TestClient(app, follow_redirects=False)


def test_shorten_valid_url():
    res = client.post("/shorten", json={"long_url": "https://www.google.com"})
    assert res.status_code == 201
    data = res.json()
    assert len(data["short_code"]) == 7
    assert data["long_url"] == "https://www.google.com"
    assert data["short_url"].endswith(data["short_code"])


def test_shorten_custom_alias():
    res = client.post("/shorten", json={"long_url": "https://github.com", "custom_alias": "mygit"})
    assert res.status_code == 201
    data = res.json()
    assert data["short_code"] == "mygit"
    assert data["long_url"] == "https://github.com"


def test_shorten_duplicate_alias():
    client.post("/shorten", json={"long_url": "https://example.com", "custom_alias": "dupalias"})
    res = client.post("/shorten", json={"long_url": "https://another.com", "custom_alias": "dupalias"})
    assert res.status_code == 409


def test_shorten_invalid_url():
    res = client.post("/shorten", json={"long_url": "not-a-url"})
    assert res.status_code == 422


def test_redirect_and_click_tracking():
    client.post("/shorten", json={"long_url": "https://news.ycombinator.com", "custom_alias": "hn"})
    redir = client.get("/hn", headers={"referer": "https://twitter.com"})
    assert redir.status_code == 302
    assert redir.headers["location"] == "https://news.ycombinator.com"

    stats = client.get("/api/links/hn/stats").json()
    assert stats["click_count"] == 1
    assert stats["recent_clicks"][0]["referrer"] == "https://twitter.com"


def test_list_links():
    headers = {"X-Client-Id": "device-alpha"}
    client.post("/shorten", json={"long_url": "https://news.ycombinator.com", "custom_alias": "hn"}, headers=headers)
    res = client.get("/api/links", headers=headers)
    assert res.status_code == 200
    links = res.json()
    assert any(l["short_code"] == "hn" for l in links)


def test_device_history_isolation():
    client_a_headers = {"X-Client-Id": "device-a-uuid"}
    client_b_headers = {"X-Client-Id": "device-b-uuid"}

    # Device A creates a link
    res_a = client.post("/shorten", json={"long_url": "https://site-a.com", "custom_alias": "link-a"}, headers=client_a_headers)
    assert res_a.status_code == 201

    # Device B creates a link
    res_b = client.post("/shorten", json={"long_url": "https://site-b.com", "custom_alias": "link-b"}, headers=client_b_headers)
    assert res_b.status_code == 201

    # Device A should only see link-a
    links_a = client.get("/api/links", headers=client_a_headers).json()
    assert len(links_a) == 1
    assert links_a[0]["short_code"] == "link-a"

    # Device B should only see link-b
    links_b = client.get("/api/links", headers=client_b_headers).json()
    assert len(links_b) == 1
    assert links_b[0]["short_code"] == "link-b"

    # Unauthenticated / headerless request should see no history
    links_anon = client.get("/api/links").json()
    assert len(links_anon) == 0


def test_soft_delete():
    headers = {"X-Client-Id": "device-test"}
    client.post("/shorten", json={"long_url": "https://reddit.com", "custom_alias": "redd"}, headers=headers)
    res = client.delete("/api/links/redd", headers=headers)
    assert res.status_code == 200
    assert client.get("/redd").status_code == 404


def test_expired_link():
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    client.post("/shorten", json={"long_url": "https://wikipedia.org", "custom_alias": "old", "expires_at": past})
    assert client.get("/old").status_code == 404
