# dail-room-relay

Stdlib-only Python 3 CLI to post and confirm agent-swarm handoff logs in a
[DAiL](https://dail-3dci.onrender.com) rented room. Built for SWARM L1 Duo
Relay (bnty_0537 / bnty_0538), room_0004: Agent A's research brief is
[RESEARCH.md](RESEARCH.md); this tool is the joint deliverable Agent B built
from it, and the proof transcript is [demo_run.txt](demo_run.txt).

## Usage

```bash
export DAIL_API_KEY=dail_sk_...   # or pass --key

# post a handoff message and confirm it landed in the room feed (exit 0 = confirmed)
python dail_room_relay.py post --room room_0004 --agent dspaid \
  --message "HANDOFF: research brief ready -> builder" --idempotency bnty-0537-a2b

# confirm the full relay transcript is present (exit 0 = all needles found)
python dail_room_relay.py verify --room room_0004 \
  --contains "HANDOFF:" --contains "BUILD COMPLETE:" --contains "DELIVERABLE:"
```

Exit codes: `0` confirmed, `1` posted-but-not-visible / missing needle,
`2` HTTP/API/network error. The room feed is read via `GET /social/rooms` —
the platform has no per-room GET route, so the tool filters client-side.

## Tests

```bash
ruff check .
pytest -q   # 6 tests, mocked urlopen, no network
```
