# T5: cross-system comparison at batch 8 and 32 (2026-10-28)

One small-batch protocol for every method (JHQ's harness's): floor(nq/b) synchronous host-to-host calls of b queries, QPS = queries / summed call time, recall over the queries used; E1's environment (workspace pools). JHQ = v69, scheduled path unless marked G=0. Ratios > 1 favour JHQ.

## vogue-768, batch 8

| target | JHQ kQPS | JHQ G=0 kQPS | CAGRA fp32 kQPS | CAGRA int8 kQPS | IVF-RaBitQ kQPS | JHQ/CAGRA fp32 | JHQ/CAGRA int8 | JHQ/IVF-RaBitQ |
|---|---|---|---|---|---|---|---|---|
| 0.9 | 34.1 | 12.9 | — | 27.1 | 29.5 | — | 1.26 | 1.15 |
| 0.92 | 32.2 | 11.8 | — | 26.8 | 28.4 | — | 1.20 | 1.13 |
| 0.94 | 29.5 | 9.6 | 26.5 | 24.4 | 26.2 | 1.12 | 1.21 | 1.13 |
| 0.95 | 28.3 | 9.0 | 26.4 | — | 25.2 | 1.07 | — | 1.12 |
| 0.96 | 26.1 | 7.6 | 26.2 | — | 24.5 | 1.00 | — | 1.06 |
| 0.97 | 23.3 | 6.2 | 26.1 | — | 24.2 | 0.89 | — | 0.96 |
| 0.98 | 19.9 | 4.8 | 25.4 | — | 23.9 | 0.78 | — | 0.83 |

Max measured recall: JHQ 0.9907, CAGRA fp32 0.9983, CAGRA int8 0.9451, IVF-RaBitQ 0.9926.  Null-call median latency (harness floor): CAGRA fp32 0.026 ms, CAGRA int8 0.027 ms, IVF-RaBitQ 0.012 ms.

## vogue-768, batch 32

| target | JHQ kQPS | JHQ G=0 kQPS | CAGRA fp32 kQPS | CAGRA int8 kQPS | IVF-RaBitQ kQPS | JHQ/CAGRA fp32 | JHQ/CAGRA int8 | JHQ/IVF-RaBitQ |
|---|---|---|---|---|---|---|---|---|
| 0.9 | 110.0 | 43.7 | — | — | 85.5 | — | — | 1.29 |
| 0.92 | 103.8 | 39.9 | — | 101.5 | 83.7 | — | 1.02 | 1.24 |
| 0.94 | 94.3 | 32.7 | 95.9 | 82.5 | 80.0 | 0.98 | 1.14 | 1.18 |
| 0.95 | 89.7 | 30.6 | 93.8 | — | 78.2 | 0.96 | — | 1.15 |
| 0.96 | 82.9 | 26.3 | 91.7 | — | 74.8 | 0.90 | — | 1.11 |
| 0.97 | 73.1 | 21.9 | 84.6 | — | 69.7 | 0.86 | — | 1.05 |
| 0.98 | 61.4 | 17.2 | 70.5 | — | 57.8 | 0.87 | — | 1.06 |

Max measured recall: JHQ 0.9907, CAGRA fp32 0.9985, CAGRA int8 0.9453, IVF-RaBitQ 0.9921.  Null-call median latency (harness floor): CAGRA fp32 0.029 ms, CAGRA int8 0.030 ms, IVF-RaBitQ 0.018 ms.

## arxiv-768, batch 8

| target | JHQ kQPS | JHQ G=0 kQPS | CAGRA fp32 kQPS | CAGRA int8 kQPS | IVF-RaBitQ kQPS | JHQ/CAGRA fp32 | JHQ/CAGRA int8 | JHQ/IVF-RaBitQ |
|---|---|---|---|---|---|---|---|---|
| 0.9 | 43.7 | 24.7 | 29.1 | 29.6 | 28.4 | 1.50 | 1.48 | 1.54 |
| 0.92 | 36.8 | 19.1 | 28.9 | 29.4 | 27.9 | 1.27 | 1.25 | 1.32 |
| 0.94 | 25.3 | 13.5 | 28.7 | 29.1 | 26.6 | 0.88 | 0.87 | 0.95 |
| 0.95 | 24.8 | 12.2 | 28.6 | 28.9 | 25.8 | 0.87 | 0.86 | 0.96 |
| 0.96 | 21.5 | 10.9 | 28.4 | 27.7 | 24.9 | 0.76 | 0.78 | 0.86 |
| 0.97 | 19.7 | 9.0 | 28.3 | — | 23.2 | 0.70 | — | 0.85 |
| 0.98 | 16.4 | 6.1 | 28.2 | — | 21.7 | 0.58 | — | 0.76 |

Max measured recall: JHQ 0.9903, CAGRA fp32 0.9997, CAGRA int8 0.9621, IVF-RaBitQ 0.9942.  Null-call median latency (harness floor): CAGRA fp32 0.027 ms, CAGRA int8 0.027 ms, IVF-RaBitQ 0.012 ms.

## arxiv-768, batch 32

| target | JHQ kQPS | JHQ G=0 kQPS | CAGRA fp32 kQPS | CAGRA int8 kQPS | IVF-RaBitQ kQPS | JHQ/CAGRA fp32 | JHQ/CAGRA int8 | JHQ/IVF-RaBitQ |
|---|---|---|---|---|---|---|---|---|
| 0.9 | 135.7 | 87.5 | 112.0 | 116.4 | 77.7 | 1.21 | 1.17 | 1.75 |
| 0.92 | 114.6 | 68.7 | 110.4 | 115.8 | 67.6 | 1.04 | 0.99 | 1.69 |
| 0.94 | 77.1 | 49.0 | 108.8 | 114.6 | 64.1 | 0.71 | 0.67 | 1.20 |
| 0.95 | 75.3 | 44.5 | 108.0 | 112.8 | 63.0 | 0.70 | 0.67 | 1.20 |
| 0.96 | 68.6 | 39.8 | 104.5 | 94.5 | 54.6 | 0.66 | 0.73 | 1.26 |
| 0.97 | 62.2 | 33.3 | 100.0 | — | 53.7 | 0.62 | — | 1.16 |
| 0.98 | 54.1 | 23.1 | 92.6 | — | 52.9 | 0.58 | — | 1.02 |

Max measured recall: JHQ 0.9902, CAGRA fp32 0.9995, CAGRA int8 0.9621, IVF-RaBitQ 0.9942.  Null-call median latency (harness floor): CAGRA fp32 0.029 ms, CAGRA int8 0.029 ms, IVF-RaBitQ 0.018 ms.

## openai3-1536, batch 8

| target | JHQ kQPS | JHQ G=0 kQPS | CAGRA fp32 kQPS | CAGRA int8 kQPS | IVF-RaBitQ kQPS | JHQ/CAGRA fp32 | JHQ/CAGRA int8 | JHQ/IVF-RaBitQ |
|---|---|---|---|---|---|---|---|---|
| 0.9 | 36.9 | 17.8 | 25.3 | 28.1 | 19.3 | 1.46 | 1.32 | 1.92 |
| 0.92 | 33.3 | 13.7 | 25.2 | 27.9 | 18.5 | 1.32 | 1.19 | 1.80 |
| 0.94 | 26.8 | 9.6 | 25.2 | 27.7 | 17.1 | 1.07 | 0.97 | 1.57 |
| 0.95 | 23.3 | 7.4 | 25.0 | 27.4 | 16.5 | 0.93 | 0.85 | 1.41 |
| 0.96 | 19.5 | 5.9 | 25.0 | 26.8 | 15.8 | 0.78 | 0.73 | 1.24 |
| 0.97 | 15.7 | 4.4 | 24.5 | — | 15.4 | 0.64 | — | 1.02 |
| 0.98 | 11.8 | 2.9 | 23.4 | — | 14.6 | 0.50 | — | 0.81 |

Max measured recall: JHQ 0.9862, CAGRA fp32 0.9947, CAGRA int8 0.9681, IVF-RaBitQ 0.9871.  Null-call median latency (harness floor): CAGRA fp32 0.027 ms, CAGRA int8 0.028 ms, IVF-RaBitQ 0.014 ms.

## openai3-1536, batch 32

| target | JHQ kQPS | JHQ G=0 kQPS | CAGRA fp32 kQPS | CAGRA int8 kQPS | IVF-RaBitQ kQPS | JHQ/CAGRA fp32 | JHQ/CAGRA int8 | JHQ/IVF-RaBitQ |
|---|---|---|---|---|---|---|---|---|
| 0.9 | 115.6 | 65.0 | 90.7 | 107.9 | 51.8 | 1.27 | 1.07 | 2.23 |
| 0.92 | 103.7 | 50.6 | 87.8 | 107.7 | 49.8 | 1.18 | 0.96 | 2.08 |
| 0.94 | 88.0 | 36.5 | 84.3 | 104.2 | 41.9 | 1.04 | 0.84 | 2.10 |
| 0.95 | 79.1 | 29.0 | 78.4 | 102.7 | 38.5 | 1.01 | 0.77 | 2.06 |
| 0.96 | 67.8 | 23.0 | 73.0 | 80.8 | 35.4 | 0.93 | 0.84 | 1.92 |
| 0.97 | 55.8 | 16.8 | 59.5 | — | 33.6 | 0.94 | — | 1.66 |
| 0.98 | 42.1 | 11.9 | 41.8 | — | 31.0 | 1.01 | — | 1.36 |

Max measured recall: JHQ 0.9862, CAGRA fp32 0.9957, CAGRA int8 0.9682, IVF-RaBitQ 0.9870.  Null-call median latency (harness floor): CAGRA fp32 0.035 ms, CAGRA int8 0.036 ms, IVF-RaBitQ 0.027 ms.

## openai3-3072, batch 8

| target | JHQ kQPS | JHQ G=0 kQPS | CAGRA fp32 kQPS | CAGRA int8 kQPS | IVF-RaBitQ kQPS | JHQ/CAGRA fp32 | JHQ/CAGRA int8 | JHQ/IVF-RaBitQ |
|---|---|---|---|---|---|---|---|---|
| 0.9 | 23.4 | 11.7 | — | — | 11.2 | — | — | 2.08 |
| 0.92 | 22.1 | 8.9 | — | — | 10.7 | — | — | 2.06 |
| 0.94 | 18.7 | 6.2 | 18.4 | 22.4 | 10.1 | 1.02 | 0.83 | 1.84 |
| 0.95 | 17.4 | 5.3 | 18.2 | 21.8 | 9.8 | 0.96 | 0.80 | 1.77 |
| 0.96 | 14.8 | 3.6 | 18.0 | 21.6 | 9.5 | 0.82 | 0.68 | 1.55 |
| 0.97 | 12.6 | 3.0 | 17.4 | — | 9.1 | 0.72 | — | 1.38 |
| 0.98 | 9.1 | 2.1 | 15.5 | — | 8.4 | 0.59 | — | 1.08 |

Max measured recall: JHQ 0.9853, CAGRA fp32 0.9935, CAGRA int8 0.9694, IVF-RaBitQ 0.9838.  Null-call median latency (harness floor): CAGRA fp32 0.035 ms, CAGRA int8 0.030 ms, IVF-RaBitQ 0.018 ms.

## openai3-3072, batch 32

| target | JHQ kQPS | JHQ G=0 kQPS | CAGRA fp32 kQPS | CAGRA int8 kQPS | IVF-RaBitQ kQPS | JHQ/CAGRA fp32 | JHQ/CAGRA int8 | JHQ/IVF-RaBitQ |
|---|---|---|---|---|---|---|---|---|
| 0.9 | 71.4 | 44.0 | 56.9 | — | 24.2 | 1.26 | — | 2.95 |
| 0.92 | 61.6 | 34.0 | 53.6 | 81.6 | 22.8 | 1.15 | 0.76 | 2.70 |
| 0.94 | 49.5 | 24.1 | 48.6 | 78.8 | 21.1 | 1.02 | 0.63 | 2.35 |
| 0.95 | 44.7 | 20.6 | 43.1 | 73.5 | 20.0 | 1.04 | 0.61 | 2.23 |
| 0.96 | 37.4 | 16.6 | 37.8 | 52.1 | 18.7 | 0.99 | 0.72 | 2.00 |
| 0.97 | 30.2 | 12.5 | 30.0 | — | 17.0 | 1.01 | — | 1.77 |
| 0.98 | 21.0 | 8.2 | 21.0 | — | 15.2 | 1.00 | — | 1.38 |

Max measured recall: JHQ 0.9855, CAGRA fp32 0.9941, CAGRA int8 0.9690, IVF-RaBitQ 0.9841.  Null-call median latency (harness floor): CAGRA fp32 0.072 ms, CAGRA int8 0.052 ms, IVF-RaBitQ 0.049 ms.

