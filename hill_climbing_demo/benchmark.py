#!/usr/bin/env python3
"""
Benchmark: mide tasa de éxito, % de estancamiento, iteraciones y tiempo.
Cada configuración se ejecuta desde N estados iniciales aleatorios (misma semilla
para todas, así la comparación es justa).

  python benchmark.py            # N=500
  python benchmark.py -n 1000
"""
import argparse, csv, json, random, statistics as st

from hc.algorithms import run_metrics
from hc.problem import make_problem

CONFIGS = [  # (etiqueta, variante, mitigación)
    ("Simple HC", "simple", "none"),
    ("Steepest-Ascent", "steepest", "none"),
    ("First-Choice", "first_choice", "none"),
    ("Stochastic HC", "stochastic", "none"),
    ("Steepest + Reinicios aleatorios", "steepest", "restart"),
    ("First-Choice + Reinicios aleatorios", "first_choice", "restart"),
    ("Steepest + Penalizaciones", "steepest", "penalty"),
]


def run(n=500, cases=("A", "B", "C"), seed=2024):
    rows = []
    for case in cases:
        problem = make_problem(case)
        rng = random.Random(seed)
        starts = [problem.random_state(rng) for _ in range(n)]
        for label, variant, mitig in CONFIGS:
            res = [run_metrics(problem, variant, mitig, s, seed=i) for i, s in enumerate(starts)]
            ok = [r for r in res if r["success"]]
            rows.append(dict(
                caso=case, algoritmo=label, n=n,
                exito_pct=100 * len(ok) / n,
                estancado_pct=100 * sum(r["stuck"] for r in res) / n,
                iter_media=st.mean(r["iterations"] for r in res),
                iter_media_exito=st.mean(r["iterations"] for r in ok) if ok else float("nan"),
                reinicios_medios=st.mean(r["restarts"] for r in res),
                tiempo_ms=st.mean(r["time_ms"] for r in res)))
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("-n", type=int, default=500)
    a = ap.parse_args()
    rows = run(a.n)
    with open("results/benchmark.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    json.dump(rows, open("results/benchmark.json", "w"), indent=1)
    for case in ("A", "B", "C"):
        print(f"\nCaso {case}  (N={a.n} inicios aleatorios)")
        print(f"{'Algoritmo':38s} {'Éxito%':>7s} {'Estanc.%':>9s} {'Iter':>7s} {'ms':>7s}")
        for r in [r for r in rows if r['caso'] == case]:
            print(f"{r['algoritmo']:38s} {r['exito_pct']:7.1f} {r['estancado_pct']:9.1f} "
                  f"{r['iter_media']:7.1f} {r['tiempo_ms']:7.3f}")
