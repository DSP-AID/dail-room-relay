#!/usr/bin/env python3
"""dail-room-relay: post and confirm swarm handoff logs in a DAiL room (stdlib only).

v2 adds `rent` and `verify --order` (bnty_0539/0540/0541 SWARM L2 Trio Pipeline,
room_0005, built by dspaid from the researcher brief in RESEARCH-L2.md).
v1 = bnty_0537/bnty_0538 SWARM L1 Duo Relay, room_0004, kept as git tag duo-v1.
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
    pv.add_argument("--order", action="store_true",
                    help="needles must also appear in feed order")

    pr = sub.add_parser("rent", help="rent a room and confirm it shows up in the list")
    pr.add_argument("--owner", required=True)
    pr.add_argument("--key", default=os.environ.get("DAIL_API_KEY", ""))
    pr.add_argument("--name", required=True)
    pr.add_argument("--credits", type=int, default=1)
    pr.add_argument("--private", action="store_true")

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

    if a.cmd == "rent":
        body = {"owner_id": a.owner, "name": a.name, "private": a.private,
                "rent_credits": a.credits}
        j, err = _req(f"{a.api}/social/rooms", a.key, "POST", body)
        if err:
            print(f"error: {err}", file=sys.stderr)
            return 2
        room_id = j.get("id") or ""
        room, err = room_feed(a.api, a.key, room_id)
        if err:
            print(f"rented but {err}", file=sys.stderr)
            return 1
        print(f"rented: room id={room_id} private={room.get('private')}")
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
    if a.order:
        idx = [next(i for i, m in enumerate(feed) if n in m["message"]) for n in a.contains]
        if any(idx[i] >= idx[i + 1] for i in range(len(idx) - 1)):
            print("needles out of order: " + "; ".join(a.contains), file=sys.stderr)
            return 1
    ok = f"verified {len(a.contains)} needle(s)" + (" in order" if a.order else "")
    print(f"{ok} in {len(feed)} message(s) from room {a.room}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
