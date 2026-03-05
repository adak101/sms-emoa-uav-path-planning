"""
Główny punkt wejścia do uruchamiania SMS-EMOA.

Użycie:
    python main.py
    python main.py --test-case data/TC-SP/tcGB.json --uavs 5 --eval 20000
    python main.py --pop 200 --eval 50000 --seed 123
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

from src.io.data_loader import load_test_case
from src.io.logger import setup_logging
from src.algorithm.sms_emoa import SmsEmoa, SmsEmoaConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SMS-EMOA UAV Path Optimization")

    parser.add_argument(
        "--test-case",
        type=str,
        default="data/TC-PGI/tcB.json",
        help="Ścieżka do pliku JSON z danymi testowymi (default: data/TC-PGI/tcB.json)",
    )
    parser.add_argument("--uavs", type=int, default=3, help="Liczba dronów (default: 3)")
    parser.add_argument("--pop", type=int, default=100, help="Rozmiar populacji (default: 100)")
    parser.add_argument("--eval", type=int, default=10_000, help="Max ewaluacji (default: 10000)")
    parser.add_argument("--mutation", type=float, default=0.1, help="Mutation rate (default: 0.1)")
    parser.add_argument("--crossover", type=float, default=0.9, help="Crossover prob (default: 0.9)")
    parser.add_argument("--seed", type=int, default=115986, help="Random seed (default: 115986)")
    parser.add_argument("--snapshot", type=int, default=500, help="Snapshot interval (default: 500)")
    parser.add_argument("--no-plots", action="store_true", help="Nie pokazuj wykresów")

    return parser.parse_args()


def plot_results(algo: SmsEmoa, output_dir: Path, show: bool = True) -> None:
    """Generuj wykresy: HV, best f1/f2, front Pareto."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # 1. Hypervolume
    ax = axes[0]
    ax.plot(algo.history["generations"], algo.history["hypervolume"], color="steelblue")
    ax.set_xlabel("Generacja")
    ax.set_ylabel("Hypervolume")
    ax.set_title("Zbieżność Hypervolume")
    ax.grid(True, alpha=0.3)

    # 2. Best f1 / f2
    ax = axes[1]
    ax.plot(algo.history["generations"], algo.history["best_f1"], label="best f1", color="#e74c3c")
    ax.set_xlabel("Generacja")
    ax.set_ylabel("f1")
    ax.set_title("Najlepsze f1 / f2")
    ax.grid(True, alpha=0.3)

    ax2 = ax.twinx()
    ax2.plot(algo.history["generations"], algo.history["best_f2"], label="best f2", color="#2ecc71")
    ax2.set_ylabel("f2")

    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2)

    # 3. Front Pareto
    ax = axes[2]
    arch_f1 = [sol.f1 for sol in algo.archive]
    arch_f2 = [sol.f2 for sol in algo.archive]
    ax.scatter(arch_f1, arch_f2, c="steelblue", edgecolors="black", s=60, zorder=3)
    ax.set_xlabel("f1 — Czas zakończenia misji")
    ax.set_ylabel("f2 — Współczynnik nieodkrytego obszaru")
    ax.set_title(f"Front Pareto ({len(algo.archive)} rozwiązań)")
    ax.grid(True, alpha=0.3)

    fig.suptitle(
        f"SMS-EMOA: {algo.test_case.name}, {algo.config.num_uavs} UAV, "
        f"{algo.config.max_evaluations} ewaluacji, seed={algo.config.seed}",
        fontsize=14,
    )
    fig.tight_layout()

    save_path = output_dir / "results.png"
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    print(f"Wykres: {save_path}")

    if show:
        plt.show()
    plt.close()


def main():
    args = parse_args()

    # Nazwa runu na podstawie parametrów
    tc_name = Path(args.test_case).stem
    seed_str = f"_s{args.seed}" if args.seed is not None else ""
    run_name = f"{tc_name}_u{args.uavs}_p{args.pop}_e{args.eval}{seed_str}"

    # Foldery wynikowe
    output_dir = Path("results/runs") / run_name
    output_dir.mkdir(parents=True, exist_ok=True)

    # Logging
    setup_logging(log_file=output_dir / "log.txt")

    # Załaduj dane
    tc = load_test_case(args.test_case)

    # Konfiguracja
    config = SmsEmoaConfig(
        population_size=args.pop,
        max_evaluations=args.eval,
        num_uavs=args.uavs,
        crossover_prob=args.crossover,
        mutation_rate=args.mutation,
        seed=args.seed,
        snapshot_interval=args.snapshot,
    )

    # Uruchom
    algo = SmsEmoa(config, tc)
    algo.run()

    # Zapisz wyniki
    algo.save_results(output_dir / "results.json")

    # Wykresy
    plot_results(algo, output_dir, show=not args.no_plots)

    print(f"\nWyniki w: {output_dir}")


if __name__ == "__main__":
    main()