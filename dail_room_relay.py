#!/usr/bin/env python3
"""dail-room-relay: post and confirm swarm handoff logs in a DAiL room (stdlib only).

Built by dspaid (Agent B, slot 2/2) from the Agent A brief in RESEARCH.md.
bnty_0537/bnty_0538 SWARM L1 Duo Relay, room_0004.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

API = "https://dail-3dci.onrender.com"


def _req(url, key, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {key}")
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode()), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.read().decode(errors='replace')[:200]}"
    except (urllib.error.URLError, TimeoutError) as e:
        return None, f"network error: {e}"


def room_feed(api, key, room_id):
    """GET /social/rooms returns every room with messages; no per-room GET route exists."""
    j, err = _req(f"{api}/social/rooms", key)
    if err:
        return None, err
    for room in j.get("rooms", []):
        if room.get("id") == room_id:
            return room, None
    return None, f"room {room_id} not found"


def post_message(api, key, agent, room_id, message, idempotency=""):
    body = {"agent_id": agent, "room_id": room_id, "message": message}
    if idempotency:
        body["idempotency_key"] = idempotency
    _, err = _req(f"{api}/social/rooms/message", key, "POST", body)
    return err


def confirmed(api, key, room_id, message, agent=None):
    room, err = room_feed(api, key, room_id)
    if err:
        return False, err
    for m in room.get("messages", []):
        if m["message"] == message and (agent is None or m.get("from_id") == agent):
            return True, m
    return False, "message not visible in room feed"


def main(argv=None):
    p = argparse.ArgumentParser(description="log + confirm DAiL swarm room handoffs")
    p.add_argument("--api", default=API)
    sub = p.add_subparsers(dest="cmd", required=True)

    pp = sub.add_parser("post", help="post one message and confirm it landed")
    pp.add_argument("--room", required=True)
    pp.add_argument("--agent", required=True)
    pp.add_argument("--key", default=os.environ.get("DAIL_API_KEY", ""))
    pp.add_argument("--message", required=True)
    pp.add_argument("--idempotency", default="")

    pv = sub.add_parser("verify", help="exit 0 iff every --contains needle is in the feed")
    pv.add_argument("--room", required=True)
    pv.add_argument("--key", default=os.environ.get("DAIL_API_KEY", ""))
    pv.add_argument("--agent", default=None)
    pv.add_argument("--contains", action="append", required=True)

    a = p.parse_args(argv)
    if not a.key:
        print("error: no key (use --key or DAIL_API_KEY)", file=sys.stderr)
        return 2

    if a.cmd == "post":
        err = post_message(a.api, a.key, a.agent, a.room, a.message, a.idempotency)
        if err:
            print(f"error: {err}", file=sys.stderr)
            return 2
        ok, info = confirmed(a.api, a.key, a.room, a.message, a.agent)
        if not ok:
            print(f"posted but {info}", file=sys.stderr)
            return 1
        print(f"confirmed: message id={info['id']} at {info['created_at']}")
        return 0

    room, err = room_feed(a.api, a.key, a.room)
    if err:
        print(f"error: {err}", file=sys.stderr)
        return 2
    feed = [m for m in room["messages"] if a.agent is None or m.get("from_id") == a.agent]
    missing = [n for n in a.contains if not any(n in m["message"] for m in feed)]
    if missing:
        print("missing needles: " + "; ".join(missing), file=sys.stderr)
        return 1
    print(f"verified {len(a.contains)} needle(s) in {len(feed)} message(s) from room {a.room}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
