"""
Visualización con matplotlib.

  draw_maze(...)        dibuja el laberinto, el mapa de calor de f, el camino y los vecinos.
  InteractiveDemo       ventana con botones: Paso, Auto, Reiniciar + selección de caso y algoritmo.
"""
import random
from typing import List, Optional

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.widgets import Button, RadioButtons

from .algorithms import (STATUS_GOAL, STATUS_LOCAL_MAX, STATUS_MAX_ITER, STATUS_RESTART,
                         Step, format_step, solve)
from .problem import MAZES, MazeProblem, make_problem

# etiqueta del menú -> (variante, mitigación)
ALGOS = {
    "Steepest-Ascent": ("steepest", "none"),
    "Simple HC": ("simple", "none"),
    "First-Choice": ("first_choice", "none"),
    "Stochastic HC": ("stochastic", "none"),
    "Steepest + Reinicios": ("steepest", "restart"),
    "Steepest + Penalizac.": ("steepest", "penalty"),
}


def draw_maze(ax, problem: MazeProblem, steps: Optional[List[Step]] = None,
              show_f: bool = True, title: str = "", annotate_neighbors: bool = True):
    """Dibuja el estado actual de la búsqueda (último Step de `steps`)."""
    ax.clear()
    R, C = problem.n_rows, problem.n_cols
    F = np.full((R, C), np.nan)
    W = np.zeros((R, C))
    for r in range(R):
        for c in range(C):
            if (r, c) in problem.walls:
                W[r, c] = 1
            else:
                F[r, c] = problem.f((r, c))
    ax.imshow(F, cmap="YlGn", vmin=np.nanmin(F) - 3, vmax=0, interpolation="nearest")
    wall_layer = np.ma.masked_where(W == 0, W)
    ax.imshow(wall_layer, cmap=ListedColormap(["#2f2f2f"]), interpolation="nearest")

    if show_f:
        for r in range(R):
            for c in range(C):
                if not np.isnan(F[r, c]):
                    ax.text(c, r, f"{F[r, c]:.0f}", ha="center", va="center",
                            fontsize=6, color="white" if F[r, c] > -10 else "#3d5a3d", alpha=0.8)

    ax.scatter(*problem.start[::-1], marker="s", s=250, facecolors="none",
               edgecolors="#1f5fbf", linewidths=2, zorder=3)
    ax.text(problem.start[1], problem.start[0] - 0.62, "S", color="#1f5fbf",
            ha="center", fontsize=9, fontweight="bold")
    ax.scatter(*problem.goal[::-1], marker="*", s=420, color="gold",
               edgecolors="black", linewidths=1, zorder=4)

    if steps:
        # camino recorrido (los saltos de reinicio se dibujan punteados)
        xs, ys, prev_restart = [], [], steps[0].restart
        for s in steps:
            if s.restart != prev_restart and xs:
                ax.plot(xs, ys, "-", color="#d62728", lw=2, alpha=0.8, zorder=2)
                xs, ys, prev_restart = [], [], s.restart
            xs.append(s.state[1]); ys.append(s.state[0])
        ax.plot(xs, ys, "-o", color="#d62728", lw=2, ms=3.5, alpha=0.85, zorder=2)

        last = steps[-1]
        if annotate_neighbors:
            for n, fn, d in last.neighbors:
                ok = last.chosen == n
                ax.add_patch(plt.Rectangle((n[1] - .45, n[0] - .45), .9, .9, fill=False,
                                           ec="#2ca02c" if ok else "#ff7f0e", lw=2.2, zorder=3))
                ax.text(n[1], n[0] + 0.33, f"{d:+.0f}", ha="center", va="center",
                        fontsize=6.5, color="#2ca02c" if d > 0 else "#c0392b",
                        fontweight="bold", zorder=5)
        col = {STATUS_GOAL: "#2ca02c", STATUS_LOCAL_MAX: "#c0392b"}.get(last.status, "#d62728")
        ax.scatter(*last.state[::-1], s=180, color=col, edgecolors="white",
                   linewidths=1.5, zorder=6)
        if last.status == STATUS_LOCAL_MAX:
            ax.annotate("MÁXIMO LOCAL", last.state[::-1], xytext=(0, -22),
                        textcoords="offset points", ha="center", color="#c0392b",
                        fontsize=9, fontweight="bold",
                        bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#c0392b", alpha=0.95),
                        arrowprops=dict(arrowstyle="->", color="#c0392b"), zorder=8)

    ax.set_xticks(np.arange(-.5, C, 1), minor=True)
    ax.set_yticks(np.arange(-.5, R, 1), minor=True)
    ax.grid(which="minor", color="white", lw=0.8)
    ax.tick_params(which="both", length=0, labelbottom=False, labelleft=False)
    ax.set_title(title, fontsize=10)


class InteractiveDemo:
    """Demo interactiva: avanza con 'Paso', corre sola con 'Auto'."""

    def __init__(self, case: str = "B", algo: str = "Steepest-Ascent", seed: int = 0):
        self.case, self.algo, self.seed = case, algo, seed
        self.fig = plt.figure(figsize=(12.5, 7))
        self.fig.canvas.manager.set_window_title("Hill Climbing – demostración interactiva")
        self.ax = self.fig.add_axes([0.02, 0.17, 0.52, 0.76])
        self.txt = self.fig.add_axes([0.56, 0.17, 0.42, 0.76]); self.txt.axis("off")
        self.timer = self.fig.canvas.new_timer(interval=250)
        self.timer.add_callback(self._tick)
        self.running = False
        self._build_widgets()
        self.reset()

    # -- widgets ---------------------------------------------------------------
    def _build_widgets(self):
        f = self.fig
        self.b_step = Button(f.add_axes([0.03, 0.04, 0.10, 0.07]), "Paso")
        self.b_auto = Button(f.add_axes([0.14, 0.04, 0.10, 0.07]), "Auto")
        self.b_reset = Button(f.add_axes([0.25, 0.04, 0.12, 0.07]), "Reiniciar")
        self.b_step.on_clicked(lambda e: self.step())
        self.b_auto.on_clicked(lambda e: self.toggle_auto())
        self.b_reset.on_clicked(lambda e: self.reset())
        ax_case = f.add_axes([0.40, 0.01, 0.17, 0.13])
        self.r_case = RadioButtons(ax_case, [f"{k}" for k in MAZES], active=list(MAZES).index(self.case))
        ax_case.set_title("Caso", fontsize=8)
        self.r_case.on_clicked(self._set_case)
        ax_algo = f.add_axes([0.60, 0.01, 0.38, 0.14])
        self.r_algo = RadioButtons(ax_algo, list(ALGOS), active=list(ALGOS).index(self.algo))
        for lbl in self.r_algo.labels:
            lbl.set_fontsize(7.5)
        self.r_algo.on_clicked(self._set_algo)

    def _set_case(self, label): self.case = label; self.reset()
    def _set_algo(self, label): self.algo = label; self.reset()

    # -- lógica -----------------------------------------------------------------
    def reset(self):
        self.timer.stop(); self.running = False
        self.problem = make_problem(self.case)
        variant, mitig = ALGOS[self.algo]
        self.gen = solve(self.problem, variant, mitig, random.Random(self.seed))
        self.steps: List[Step] = []
        self.done = False
        self._render(initial=True)

    def step(self):
        if self.done:
            return
        try:
            s = next(self.gen)
        except StopIteration:
            self.done = True; return
        self.steps.append(s)
        if s.status in (STATUS_GOAL, STATUS_LOCAL_MAX, STATUS_MAX_ITER):
            self.done = True; self.timer.stop(); self.running = False
        self._render()

    def toggle_auto(self):
        self.running = not self.running
        (self.timer.start if self.running else self.timer.stop)()

    def _tick(self):
        self.step()

    def _render(self, initial=False):
        draw_maze(self.ax, self.problem, self.steps,
                  title=f"{self.problem.name}  |  {self.algo}")
        self.txt.clear(); self.txt.axis("off")
        if initial:
            msg = ("TELEMETRÍA\n\nPulsa «Paso» para avanzar una iteración\n"
                   "o «Auto» para ejecutar de forma continua.\n\n"
                   f"Estado inicial: {self.problem.start}   f = {self.problem.f(self.problem.start):.2f}\n"
                   f"Meta: {self.problem.goal}   (f = 0 es el óptimo global)")
        else:
            msg = format_step(self.steps[-1])
            if self.done:
                msg += f"\n\n>>> TERMINADO: {self.steps[-1].status.upper()} en {self.steps[-1].iteration} iteraciones"
        self.txt.text(0.0, 1.0, msg, va="top", ha="left", family="monospace", fontsize=8.5,
                      transform=self.txt.transAxes, wrap=True)
        self.fig.canvas.draw_idle()

    def show(self):
        plt.show()
