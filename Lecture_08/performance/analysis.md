# Product Listing API — Performance Analysis

## Setup
We tested GET /api/v1/products?page=1&per_page=10 using
Locust against Flask's development server and a SQLite database
containing 1,000 seeded products. Each simulated user paused
1–3 seconds between requests. Response checks verified HTTP 200,
10 returned products, and a total count of 1,000.

## Results

| Scenario | Users | Spawn rate | Duration | Requests | p95 | p99 | Failure rate | RPS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A: Baseline | 10 | 2/s | 30s | 139 | 6 ms | 9 ms | 0% | 4.84 |
| B: Normal load | 50 | 5/s | 60s | 1,392 | 6 ms | 10 ms | 0% | 23.44 |
| C: Spike | 200 | 50/s | 30s | 2,866 | 40 ms | 69 ms | 0% | 98.16 |

## Interpretation
Scenarios A and B had the same p95 latency of 6 ms.
Scenario C increased p95 to 40 ms and average latency from
approximately 3.9 ms in B to 8.2 ms. This suggests increased
resource contention under higher concurrency, although these
measurements do not identify a specific bottleneck.

Throughput increased with user count, and no request or response
validation failures were recorded. These runs did not establish
the service's maximum capacity.

## Proposed SLO
For this prototype, we propose p95 response time below 300 ms
and a failure rate below 1% at the expected load of 50 simulated
users, with 1–3-second pauses.

A product listing supports interactive browsing, so the API
should respond promptly while leaving time for network transfer
and interface rendering. The 300 ms threshold is an initial
design target requiring team validation, rather than a limit
derived solely from current performance.

All three measured scenarios met both targets. For an initial
CI performance check, repeat scenario B with the same dataset
and environment, checking p95 < 300 ms and zero unexpected
failures.

## Limitations
These are short local tests, including ramp-up time, using a
small dataset and Flask's development server. They repeatedly
request the same first page and do not cover filtering, writes,
authentication, real network conditions, or sustained traffic.
Zero observed failures does not establish long-term reliability.
Production deployment requires representative workloads,
deployment infrastructure, and longer repeated tests.