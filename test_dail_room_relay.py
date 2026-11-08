import io
import json
import urllib.error

import dail_room_relay as r


class FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()
        return False


def patch(monkeypatch, rooms_payload=None, post_status=200):
    calls = []

    def fake_urlopen(req, timeout=None):
        calls.append((req.method, req.full_url, req.data))
        if req.method == "POST":
            if post_status != 200:
                raise urllib.error.HTTPError(req.full_url, post_status, "err", {}, io.BytesIO(b"boom"))
            return FakeResp(b'{"ok": true}')
        return FakeResp(json.dumps(rooms_payload).encode())

    monkeypatch.setattr(r.urllib.request, "urlopen", fake_urlopen)
    return calls


ROOMS = {"rooms": [{"id": "room_x", "messages": [
    {"id": "m1", "from_id": "dspaid", "message": "HANDOFF: spec ready", "created_at": "2026-11-08T00:00:00Z"},
]}]}


def test_post_happy(monkeypatch, capsys):
    calls = patch(monkeypatch, ROOMS)
    rc = r.main(["post", "--room", "room_x", "--agent", "dspaid", "--key", "k",
                 "--message", "HANDOFF: spec ready"])
    assert rc == 0
    assert "confirmed" in capsys.readouterr().out
    assert calls[0][0] == "POST" and "/social/rooms/message" in calls[0][1]


def test_post_not_visible(monkeypatch, capsys):
    patch(monkeypatch, {"rooms": [{"id": "room_x", "messages": []}]})
    rc = r.main(["post", "--room", "room_x", "--agent", "dspaid", "--key", "k", "--message", "nope"])
    assert rc == 1
    assert "not visible" in capsys.readouterr().err


def test_verify_missing(monkeypatch, capsys):
    patch(monkeypatch, ROOMS)
    rc = r.main(["verify", "--room", "room_x", "--key", "k", "--contains", "HANDOFF",
                 "--contains", "BUILD COMPLETE"])
    assert rc == 1
    assert "BUILD COMPLETE" in capsys.readouterr().err


def test_verify_ok(monkeypatch, capsys):
    patch(monkeypatch, ROOMS)
    rc = r.main(["verify", "--room", "room_x", "--key", "k", "--agent", "dspaid",
                 "--contains", "HANDOFF"])
    assert rc == 0
    assert "verified" in capsys.readouterr().out


def test_http_error_exit2(monkeypatch, capsys):
    patch(monkeypatch, ROOMS, post_status=403)
    rc = r.main(["post", "--room", "room_x", "--agent", "dspaid", "--key", "k", "--message", "x"])
    assert rc == 2
    assert "HTTP 403" in capsys.readouterr().err


def test_room_not_found_exit2(monkeypatch, capsys):
    patch(monkeypatch, ROOMS)
    rc = r.main(["verify", "--room", "room_missing", "--key", "k", "--contains", "x"])
    assert rc == 2
    assert "not found" in capsys.readouterr().err
