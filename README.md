# Portcast Data Analyst Intern: take-home assignment

My submission for the Data Analyst Intern take-home at [Portcast](https://www.portcast.io), a company that predicts and tracks container shipments. The assignment has three self-contained parts:

| Part | Question | My answer in one line |
| --- | --- | --- |
| A. Root cause | Why did a container reach Rotterdam 7 days after its promised ETA? | It left Singapore 7 days late on a different vessel. Ocean transit took exactly as long as planned. |
| B. Guesstimate | What do inaccurate ETAs cost a manufacturer shipping 400 containers a month? | About **$2.3M a year** in the base case, within a range of $0.7M–5.8M. Expedited freight is the biggest lever. |
| C. AI sanity check | Can the team ship an AI-written plan to integrate 50+ tracking feeds in two weeks? | Not as written. It needs source-specific adapters, a data-quality layer and a phased rollout. |

**Full write-up:** [solution/Anubrata_De_Portcast_Take_Home_Solution.pdf](solution/Anubrata_De_Portcast_Take_Home_Solution.pdf)
**Original brief:** [brief/Portcast_DA_Intern_Assignment_Brief.pdf](brief/Portcast_DA_Intern_Assignment_Brief.pdf)

## Part A: root cause analysis

The customer was promised an arrival of 15 April. The container arrived on 22 April, and "ocean delays" no longer convinced them.

| | Booked | Actual |
| --- | --- | --- |
| Shanghai → Singapore | EVER GIVEN, arrives 9 Mar | EVER GIVEN, discharged 10 Mar (+1 day) |
| Leaves Singapore | MSC ANNA, 11 Mar | COSCO PACIFIC, 18 Mar (+7 days) |
| Singapore → Rotterdam transit | 35 days | 35 days (no change) |
| Arrives Rotterdam | 15 Apr | 22 Apr (+7 days) |

- **Cause:** a later connecting departure at Singapore. There's no load event on the booked MSC ANNA, and the container sailed a week later on COSCO PACIFIC, which is consistent with a rollover or missed connection. The first leg ran a day late and squeezed the two-day connection window. That's a plausible reason for missing the cutoff, but the data can't prove it.
- **Ruled out:**
  - **Ocean slippage:** the second leg took the same 35 days as planned.
  - **Singapore congestion:** the data shows *that* the container waited, but nothing about *why*.
- **Early warning:** [`part-a/connection_risk_check.sql`](part-a/connection_risk_check.sql) flags any container with no LOADED event on its booked vessel once that vessel has actually departed. It keys on the vessel's actual departure rather than its booked ETD, joins on voyage ID, and allows 24 hours for data latency. If MSC ANNA sailed on time, this would have raised the alarm around 12 March, about five weeks before the promised ETA.

## Part B: guesstimate

4,800 containers a year, split into three cost buckets. All inputs are illustrative assumptions:

| Bucket | Formula | Base case |
| --- | --- | --- |
| Safety stock (upper allocation) | containers × $50K cargo value × 20% carrying cost × 4/365 buffer days | $526K |
| Expedited freight | containers × 5% expedited × $5,000 each | $1.20M |
| Detention, demurrage and warehouse | containers × 10% affected × $1,200 each | $576K |
| **Total** | | **≈ $2.3M / year** |

The low and high cases flex each assumption, giving **$0.7M–5.8M a year**. The estimate is most sensitive to how often shipments need expediting and what each expedite costs. Moving just those two inputs from low to high swings the total by about $2.8M, more than every other input combined. As a magnitude check, $2.3M is roughly $480 per container, under 1% of the ~$240M of cargo shipped each year.

Reproduce the numbers (Python 3, no dependencies):

```bash
python part-b/eta_cost_estimate.py
```

## Part C: sanity check on an AI-written plan

The plan proposed one universal parser for every feed, no data-quality layer of our own, every event trusted equally, and all 50+ integrations live in two weeks. I'd push back on six claims:

1. **One universal parser:** AIS, carrier APIs, terminal EDI and PDF schedules differ in schema, cadence and failure modes.
2. **"Virtually all carriers have standard real-time APIs":** many still send EDI, CSV, email or proprietary formats.
3. **"Already validated, so no data-quality layer":** sources send duplicate, missing, late and conflicting events.
4. **Every event equally trustworthy:** trust depends on the source and the type of event.
5. **Raw events straight into the customer-facing ETA:** conflicting inputs produce unstable ETAs.
6. **50+ integrations in two weeks:** each one needs credentials, mapping, testing, backfill and monitoring.

Two further problems with the plan:
- **AIS is vessel-level, not container-level.** It has to be joined to containers through a container-to-voyage mapping.
- **PDF schedules are plans, not events.** The schema needs to label every record as planned, estimated or actual.

The recommended architecture is source adapters, then a canonical schema, then a data-quality and reconciliation layer, then a confidence-weighted ETA model. It would roll out in phases, ordered by shipment volume, with measurable go-live gates for match rate, latency and duplicate rate.

## How I used AI

I drafted every part myself, then ran each draft through an AI review and kept only the changes I could justify. The PDF lists exactly which ideas came from review, part by part. Examples: the "1 day + 6 days" breakdown of the delay, the voyage-ID join in the SQL, and the AIS and PDF points in Part C.

## Repository layout

```
brief/      Portcast's original assignment
solution/   my full submission (PDF)
part-a/     early-warning SQL rule
part-b/     script that reproduces the cost estimate
```
