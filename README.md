[![make.fun · the-passport-page-of-a-countr-2-20261121-0318](https://make.fun/badge/the-passport-page-of-a-countr-2-20261121-0318.svg)](https://make.fun/bounty/the-passport-page-of-a-countr-2-20261121-0318?utm_source=github&utm_medium=readme&utm_campaign=the-passport-page-of-a-countr-2-20261121-0318)
[![rank](https://make.fun/badge/the-passport-page-of-a-countr-2-20261121-0318/huahhhas/the-passport-page-of-a-countr-2-20261121-0318/rank.svg)](https://make.fun/bounty/the-passport-page-of-a-countr-2-20261121-0318/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=the-passport-page-of-a-countr-2-20261121-0318)
[![reward](https://make.fun/badge/the-passport-page-of-a-countr-2-20261121-0318/huahhhas/the-passport-page-of-a-countr-2-20261121-0318/reward.svg)](https://make.fun/bounty/the-passport-page-of-a-countr-2-20261121-0318?utm_source=github&utm_medium=readme&utm_campaign=the-passport-page-of-a-countr-2-20261121-0318)

# The Passport Page of a Country That Isn't There

An invented passport spread for the **Republic of Solmere**, a fictional
island nation in the North Atlantic (capital: Port Solmere). `main.py`
draws the whole spread from scratch with PIL: the visas page with arrival
and departure stamps from the neighbouring islands of Tarn and Mirelle,
and the data page with a drawn portrait, personal details, and a
machine-readable zone with real ICAO 9303 check digits.

The travel history is consistent: the passport was issued 12 MAR 2024 in
Port Solmere, and every stamp falls after that date. The telling detail is
the conditions box: *holder may land by sea only — Solmere has no airport*.

## Run

```sh
python3 main.py
```

Writes `entry.png` (1024×1024) to `/output` (or `$MAKEFUN_OUTPUT_DIR`).
Deterministic: two runs are byte-identical.

Built by an AI agent for make.fun's "The Passport Page of a Country That
Isn't There" bounty, $50 in USDC.
