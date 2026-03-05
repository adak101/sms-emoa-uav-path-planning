# Multi-Objective UAV Path Planning with SMS-EMOA

Master's thesis project — implementation of the SMS-EMOA (S-Metric Selection Evolutionary Multi-Objective Algorithm) for optimizing UAV flight paths in disaster response scenarios.

## Problem

In disaster response, drones (UAVs) must survey affected areas to locate victims as quickly as possible. This creates a multi-objective optimization problem with competing goals:

- **f₁ — Mission completion time**: the maximum departure time across all UAVs (the slowest drone determines when the mission ends)
- **f₂ — Undiscovered area coefficient**: `f₂ = 1 - ∫V(t)dt / (V_total × T_cut)`, where V(t) is the cumulative number of discovered victims at time t

These objectives conflict — a fast route may miss victim clusters, while thorough coverage takes longer. The algorithm produces a **Pareto front** of non-dominated solutions representing optimal trade-offs.

## Method

**SMS-EMOA** is a steady-state evolutionary algorithm that uses the **hypervolume indicator** as its selection criterion. Each generation:

1. Select two parents randomly
2. Apply **Order Crossover (OX)** adapted for multi-UAV paths (concat → OX → restore splits)
3. Apply mutation (weighted random choice of: invert, swap, transfer, insert, exchange)
4. Evaluate offspring with both objective functions
5. Add offspring to population (μ → μ+1)
6. Remove the individual with the **least hypervolume contribution** from the worst front (μ+1 → μ)

### Population initialization

The initial population is generated using a hybrid strategy for diversity:

| Strategy | Share | Description |
|----------|-------|-------------|
| Nearest-neighbor | 20% | Greedy path construction by closest region |
| Cluster-based | 10% | Group regions by reach time, assign to UAVs |
| Victim-priority | 10% | High-population regions distributed round-robin |
| Balanced random | 60% | Random assignment with balanced path lengths |

## Usage

```bash
# Default run
python main.py

# Custom parameters
python main.py --test-case data/TC-SP/tcGB.json --uavs 5 --eval 20000 --seed 123

# All options
python main.py --test-case data/TC-PGI/tcB.json \
               --uavs 3 \
               --pop 100 \
               --eval 10000 \
               --mutation 0.1 \
               --crossover 0.9 \
               --seed 115986 \
               --snapshot 500
```

Results (JSON, logs, plots) are saved to `results/runs/<run_name>/`.

## Project structure

```
├── main.py                          # Entry point, argument parsing, plotting
├── src/
│   ├── algorithm/
│   │   ├── sms_emoa.py              # SMS-EMOA main loop, non-dominated sorting, hypervolume
│   │   ├── operators.py             # Crossover (OX) and mutations (swap, insert, invert, transfer, exchange)
│   │   └── initializers.py          # Population initialization strategies
│   ├── model/
│   │   ├── individual.py            # Solution representation (multi-UAV paths)
│   │   └── objectives.py            # Objective functions f1, f2, flight schedule builder
│   └── io/
│       ├── data_loader.py           # JSON test case loading
│       └── logger.py                # Logging configuration
├── data/                            # Test case JSONs (not included, see below)
├── results/
│   ├── plots/
│   └── runs/                        # Experiment outputs (JSON, logs, plots)
└── tests/
```

## Output

Each run generates:
- **results.json** — full history (hypervolume convergence, best f1/f2 per generation, Pareto archive)
- **results.png** — three-panel plot: hypervolume convergence, best objectives over time, final Pareto front
- **log.txt** — detailed execution log

## Tech stack

- Python 3.11+
- NumPy
- Matplotlib (visualization)
- PyYAML (configuration)

## Data format

Test case files are JSON with the following structure:

```json
{
  "node-count": 20,
  "node-population": [12, 0, 5, ...],
  "time-process-node": [3.2, 2.8, ...],
  "time-process_edge": [[0, 1.5, ...], ...],
  "time-reach-node": [0.5, 1.2, ...]
}
```

| Field | Description |
|-------|-------------|
| `node-count` | Number of regions in the disaster area |
| `node-population` | Victim count per region |
| `time-process-node` | Scan/processing time per region |
| `time-process_edge` | Flight time matrix between regions |
| `time-reach-node` | Time to reach each region from the base |

> **Note:** Test case data used in this project is confidential and not included in the repository. To run the algorithm, provide your own JSON file following the format above.

## Context

Master's thesis in Computer Science at Cardinal Stefan Wyszyński University (UKSW), Warsaw.
Supervisor: Dr. Krzysztof Trojanowski.

## References

- Beume, N., Naujoks, B., & Emmerich, M. (2007). SMS-EMOA: Multiobjective selection based on dominated hypervolume. *European Journal of Operational Research*, 181(3), 1653–1669.
- Deb, K., et al. (2002). A fast and elitist multiobjective genetic algorithm: NSGA-II. *IEEE Transactions on Evolutionary Computation*, 6(2), 182–197.

## Author

Adam Waśko
