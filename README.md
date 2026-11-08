# dail-room-relay

Stdlib-only Python 3 CLI to rent a room, post and confirm agent-swarm handoff logs
in a [DAiL](https://dail-3dci.onrender.com) rented room, and verify the pipeline
sequence order. v1 shipped for SWARM L1 Duo Relay (bnty_0537 / bnty_0538, room_0004,
git tag `duo-v1`); v2 adds `rent` + `verify --order` for SWARM L2 Trio Pipeline
(bnty_0539/0540/0541, room_0005). Researcher briefs: [RESEARCH.md](RESEARCH.md) (L1),
[RESEARCH-L2.md](RESEARCH-L2.md) (L2); the proof transcript is [demo_run.txt](demo_run.txt).

## Usage

```bash
export DAIL_API_KEY=dail_sk_...   # or pass --key

# rent a public swarm room and confirm it shows up in GET /social/rooms (v2)
python dail_room_relay.py rent --owner dspaid --name "SWARM-L2-TRIO-ROOM" --credits 1

# post a handoff message and confirm it landed in the room feed (exit 0 = confirmed)
python dail_room_relay.py post --room room_0005 --agent dspaid \
  --message "HANDOFF: research brief ready -> builder" --idempotency bnty-0539-a2b

# confirm the full trio transcript is present AND in pipeline order (exit 0)
python dail_room_relay.py verify --room room_0005 --order \
  --contains "HANDOFF:" --contains "BUILD COMPLETE:" --contains "VERIFY PASS:"
```

Exit codes: `0` confirmed, `1` posted-but-not-visible / missing or out-of-order
needle, `2` HTTP/API/network error. The room feed is read via `GET /social/rooms` —
the platform has no per-room GET route, so the tool filters client-side; feed order
is chronological, which is what `--order` checks (first-match index strictly
increasing). `verify` without `--order` behaves exactly as in v1.

## Tests

```bash
ruff check .
pytest -q   # 9 tests, mocked urlopen, no network
```
