"""
Hill Climbing y variantes. Todas las funciones son GENERADORES que producen un
objeto `Step` por iteración, lo que permite el modo paso a paso (next(gen)) y
la telemetría en tiempo real.

Variantes:   simple | steepest | first_choice | stochastic
Mitigación:  none | restart (reinicios aleatorios) | penalty (penalización por visitas)
"""
import random
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Iterator, List, Optional, Tuple

from .problem import MazeProblem, State

VARIANTS = ["steepest", "simple", "first_choice", "stochastic"]
MITIGATIONS = ["none", "restart", "penalty"]

STATUS_RUNNING = "running"      # sigue iterando
STATUS_GOAL = "goal"            # terminó: óptimo global
STATUS_LOCAL_MAX = "local_max"  # terminó: atrapado en máximo local
STATUS_RESTART = "restart"      # atrapado, pero se reinicia (mitigación)
STATUS_MAX_ITER = "max_iter"    # terminó: límite de iteraciones


@dataclass
class Step:
    iteration: int
    restart: int
    state: State
    f: float                                   # f(actual)
    f_eff: float                               # f' (con penalización; = f si no hay)
    neighbors: List[Tuple[State, float, float]] = field(default_factory=list)  # (vecino, f, Δf)
    chosen: Optional[State] = None
    status: str = STATUS_RUNNING
    reason: str = ""


def format_step(s: Step) -> str:
    """Texto de telemetría de una iteración."""
    lines = [f"Iteración {s.iteration}" + (f"   (reinicio #{s.restart})" if s.restart else ""),
             f"Estado actual : {s.state}   f = {s.f:.2f}" +
             (f"   f' = {s.f_eff:.2f}" if abs(s.f_eff - s.f) > 1e-9 else "")]
    if s.neighbors:
        lines.append("Vecinos evaluados:")
        for n, fn, d in s.neighbors:
            mark = " <== elegido" if n == s.chosen else ""
            lines.append(f"   {n}  f = {fn:6.2f}   Δf = {d:+.2f}{mark}")
    else:
        lines.append("Vecinos evaluados: (ninguno)")
    import textwrap
    lines.append(textwrap.fill(f"Decisión      : {s.reason}", 58, subsequent_indent=" " * 16))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
def hill_climbing(problem: MazeProblem, start: State, variant: str = "steepest",
                  rng: Optional[random.Random] = None, max_iter: int = 1000,
                  lam: float = 0.0, it0: int = 0, restart: int = 0) -> Iterator[Step]:
    """Una corrida de Hill Climbing desde `start`.

    lam > 0 activa la mitigación por PENALIZACIONES: se optimiza
    f'(s) = f(s) - lam * visitas(s); cuando no hay vecino mejor se penaliza el
    estado actual (el máximo local "se rellena") en lugar de terminar.
    """
    rng = rng or random.Random()
    visits: Dict[State, int] = defaultdict(int)
    f_eff = lambda s: problem.f(s) - lam * visits[s]
    cur, it = start, it0
    while True:
        it += 1
        fc, fc_eff = problem.f(cur), f_eff(cur)

        if problem.is_goal(cur):
            yield Step(it, restart, cur, fc, fc_eff, [], None, STATUS_GOAL,
                       "META alcanzada: f = 0 (óptimo global). Fin.")
            return
        if it - it0 > max_iter:
            yield Step(it, restart, cur, fc, fc_eff, [], None, STATUS_MAX_ITER,
                       f"Se alcanzó el límite de {max_iter} iteraciones. Fin.")
            return

        nbrs = problem.neighbors(cur)
        evaluated: List[Tuple[State, float, float]] = []
        chosen: Optional[State] = None
        why = ""

        if variant == "simple":                       # primer vecino mejor, orden fijo
            for n in nbrs:
                fn = f_eff(n)
                evaluated.append((n, fn, fn - fc_eff))
                if fn > fc_eff:
                    chosen, why = n, "Simple: primer vecino (en orden fijo) con Δf > 0"
                    break
        elif variant == "first_choice":               # primer vecino mejor, orden aleatorio
            order = nbrs[:]
            rng.shuffle(order)
            for n in order:
                fn = f_eff(n)
                evaluated.append((n, fn, fn - fc_eff))
                if fn > fc_eff:
                    chosen, why = n, "First-choice: primer vecino aleatorio con Δf > 0"
                    break
        else:                                         # steepest / stochastic evalúan todos
            evaluated = [(n, f_eff(n), f_eff(n) - fc_eff) for n in nbrs]
            better = [e for e in evaluated if e[2] > 0]
            if better:
                if variant == "stochastic":
                    chosen = rng.choices([e[0] for e in better],
                                         weights=[e[2] for e in better])[0]
                    why = "Stochastic: vecino mejor elegido con prob. ∝ Δf"
                else:
                    chosen = max(better, key=lambda e: e[1])[0]
                    why = "Steepest: el vecino con mayor f (mayor Δf)"

        if chosen is not None:
            d = next(e[2] for e in evaluated if e[0] == chosen)
            yield Step(it, restart, cur, fc, fc_eff, evaluated, chosen, STATUS_RUNNING,
                       f"{why}. Se mueve a {chosen} (Δf = {d:+.2f}).")
            cur = chosen
            continue

        # --- ningún vecino mejora: máximo local (o meseta) --------------------
        if lam > 0:
            visits[cur] += 1
            yield Step(it, restart, cur, fc, fc_eff, evaluated, None, STATUS_RUNNING,
                       f"Sin vecinos mejores → MÁXIMO LOCAL en f'. Penalización: "
                       f"visitas{cur} = {visits[cur]}, f' baja a {f_eff(cur):.2f}. Se reintenta.")
            continue
        yield Step(it, restart, cur, fc, fc_eff, evaluated, None, STATUS_LOCAL_MAX,
                   "Ningún vecino mejora (Δf ≤ 0 para todos) → ATRAPADO en MÁXIMO LOCAL. Fin.")
        return


def random_restart(problem: MazeProblem, start: State, variant: str = "steepest",
                   rng: Optional[random.Random] = None, max_iter: int = 1000,
                   max_restarts: int = 20) -> Iterator[Step]:
    """Random-Restart Hill Climbing: al caer en un máximo local reinicia desde
    un estado aleatorio, hasta `max_restarts` veces."""
    rng = rng or random.Random()
    s, it = start, 0
    for k in range(max_restarts + 1):
        last = None
        for step in hill_climbing(problem, s, variant, rng, max_iter, 0.0, it, k):
            last = step
            it = step.iteration
            if step.status == STATUS_LOCAL_MAX and k < max_restarts:
                s = problem.random_state(rng)
                step.status = STATUS_RESTART
                step.reason = ("Atrapado en MÁXIMO LOCAL → REINICIO ALEATORIO "
                               f"#{k + 1}: nuevo estado inicial {s}.")
            yield step
        if last.status != STATUS_RESTART:
            return


def solve(problem: MazeProblem, variant: str = "steepest", mitigation: str = "none",
          rng: Optional[random.Random] = None, start: Optional[State] = None,
          max_iter: int = 1000, max_restarts: int = 20, lam: float = 1.0) -> Iterator[Step]:
    """Punto de entrada único: variante + técnica de mitigación."""
    rng = rng or random.Random()
    start = start or problem.start
    if mitigation == "restart":
        return random_restart(problem, start, variant, rng, max_iter, max_restarts)
    if mitigation == "penalty":
        return hill_climbing(problem, start, variant, rng, max(max_iter, 5000), lam)
    return hill_climbing(problem, start, variant, rng, max_iter)


def run_metrics(problem: MazeProblem, variant: str, mitigation: str, start: State,
                seed: int = 0, **kw) -> dict:
    """Ejecuta una corrida completa y devuelve métricas."""
    rng = random.Random(seed)
    t0 = time.perf_counter()
    steps = list(solve(problem, variant, mitigation, rng, start, **kw))
    dt = (time.perf_counter() - t0) * 1000
    last = steps[-1]
    return dict(status=last.status, success=last.status == STATUS_GOAL,
                stuck=last.status == STATUS_LOCAL_MAX, iterations=last.iteration,
                restarts=last.restart, time_ms=dt, steps=steps)
