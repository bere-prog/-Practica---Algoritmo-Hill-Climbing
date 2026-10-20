#!/usr/bin/env python3
"""
Hill Climbing – demostración (laberinto con trampas).

Ejemplos:
  python main.py                         # ventana interactiva (botones Paso / Auto)
  python main.py --cli --case B          # consola, paso a paso (ENTER avanza)
  python main.py --cli --case B --auto   # consola, sin pausas
  python main.py --cli --case B --algo steepest --mitigation restart --auto
  python main.py --cli --case B --mitigation penalty --auto --quiet
"""
import argparse
import random

from hc.algorithms import MITIGATIONS, VARIANTS, format_step, solve
from hc.problem import MAZES, make_problem


def run_cli(args):
    problem = make_problem(args.case, args.heuristic)
    print(f"\n=== {problem.name} | variante={args.algo} | mitigación={args.mitigation} "
          f"| heurística={args.heuristic} ===")
    print(f"Inicio {problem.start}  f={problem.f(problem.start):.2f}   Meta {problem.goal}\n")
    gen = solve(problem, args.algo, args.mitigation, random.Random(args.seed))
    last = None
    for step in gen:
        last = step
        if not args.quiet:
            print(format_step(step)); print("-" * 60)
            if not args.auto:
                if input("[ENTER = siguiente paso | q = salir] ").strip().lower() == "q":
                    return
    print(f"\n>>> RESULTADO: {last.status.upper()} | iteraciones={last.iteration} "
          f"| reinicios={last.restart} | estado final={last.state} f={last.f:.2f}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--cli", action="store_true", help="modo consola (sin ventana)")
    ap.add_argument("--case", default="B", choices=list(MAZES))
    ap.add_argument("--algo", default="steepest", choices=VARIANTS)
    ap.add_argument("--mitigation", default="none", choices=MITIGATIONS)
    ap.add_argument("--heuristic", default="manhattan", choices=["manhattan", "euclidean"])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--auto", action="store_true", help="CLI: no pedir ENTER en cada paso")
    ap.add_argument("--quiet", action="store_true", help="CLI: solo imprime el resultado final")
    args = ap.parse_args()
    if args.cli:
        run_cli(args)
    else:
        from hc.visual import InteractiveDemo
        InteractiveDemo(args.case, seed=args.seed).show()


if __name__ == "__main__":
    main()
