"""
Part B: order-of-magnitude annual cost of inaccurate ETAs.

Reproduces the low / base / high scenarios from the write-up and a
one-at-a-time sensitivity check. All inputs are illustrative assumptions.

Run:  python eta_cost_estimate.py
"""

CONTAINERS_PER_YEAR = 400 * 12          # 4,800
CONTAINER_VALUE_USD = 50_000            # average cargo value per container

SCENARIOS = {
    #                   low     base    high
    "buffer_days":     (2,      4,      6),       # days of buffer held against ETA uncertainty
    "carrying_rate":   (0.15,   0.20,   0.25),    # annual inventory carrying cost
    "expedite_share":  (0.02,   0.05,   0.08),    # share of shipments needing expedited recovery
    "expedite_cost":   (3_000,  5_000,  8_000),   # incremental cost per expedite, USD
    "dd_share":        (0.05,   0.10,   0.20),    # share incurring ETA-related detention/demurrage
    "dd_cost":         (800,    1_200,  1_800),   # incremental D&D / warehouse cost, USD
}


def buckets(p: dict) -> dict:
    """Annual cost per bucket, USD. Safety stock is an upper allocation, not a measured cost."""
    return {
        "safety_stock": CONTAINERS_PER_YEAR * CONTAINER_VALUE_USD * p["carrying_rate"] * p["buffer_days"] / 365,
        "expedite": CONTAINERS_PER_YEAR * p["expedite_share"] * p["expedite_cost"],
        "detention_demurrage": CONTAINERS_PER_YEAR * p["dd_share"] * p["dd_cost"],
    }


def scenario(index: int) -> dict:
    return {name: values[index] for name, values in SCENARIOS.items()}


def usd(x: float) -> str:
    sign = "-" if x < 0 else ""
    x = abs(x)
    return f"{sign}${x / 1e6:.2f}M" if x >= 1e6 else f"{sign}${x / 1e3:.0f}K"


def main() -> None:
    print(f"Containers per year: {CONTAINERS_PER_YEAR:,}\n")

    print(f"{'Bucket':<22}{'Low':>10}{'Base':>10}{'High':>10}")
    results = [buckets(scenario(i)) for i in range(3)]
    for bucket in results[1]:
        print(f"{bucket:<22}" + "".join(f"{usd(r[bucket]):>10}" for r in results))
    print(f"{'TOTAL':<22}" + "".join(f"{usd(sum(r.values())):>10}" for r in results))

    # One-at-a-time sensitivity: move each lever from low to high, everything else at base.
    base = scenario(1)
    base_total = sum(buckets(base).values())
    levers = {
        "Expedite share x cost": ["expedite_share", "expedite_cost"],
        "D&D share x cost": ["dd_share", "dd_cost"],
        "Buffer days": ["buffer_days"],
        "Carrying rate": ["carrying_rate"],
    }
    print("\nSensitivity (low -> high, others at base)")
    for label, params in levers.items():
        swings = []
        for i in (0, 2):
            p = dict(base, **{k: SCENARIOS[k][i] for k in params})
            swings.append(sum(buckets(p).values()) - base_total)
        print(f"  {label:<24}{usd(swings[0]):>10} {usd(swings[1]):>10}")


if __name__ == "__main__":
    main()
