#!/usr/bin/env python3
"""Genera todas las figuras del reporte en results/ (python make_figures.py)."""
import json
import os
import random

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from hc.algorithms import run_metrics
from hc.problem import make_problem
from hc.visual import InteractiveDemo, draw_maze

OUT = "results"
os.makedirs(OUT, exist_ok=True)
DPI = 170


def save(fig, name):
    fig.savefig(f"{OUT}/{name}", dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ---------------------------------------------------------------- teoría ------
def fig_landscape():
    kx = [0, 2.5, 4.5, 7.5, 9, 10.5, 12]
    ky = [0.3, 3.0, 1.0, 1.0, 2.2, 2.2, 4.6]
    x = np.linspace(0, 12, 600)
    y = np.interp(x, kx, ky)
    y = np.convolve(np.pad(y, 15, mode="edge"), np.ones(31) / 31, mode="valid")
    fig, ax = plt.subplots(figsize=(8, 3.6))
    ax.plot(x, y, color="#1f4e79", lw=2.5)
    ax.fill_between(x, y, -0.2, color="#cfe2f3", alpha=.6)
    at = lambda v: float(np.interp(v, x, y))
    ann = [("Máximo local", 2.5, (2.5, 3.9), "#c0392b"),
           ("Meseta (plateau)\nΔf = 0: sin gradiente", 6.0, (6.0, 2.3), "#8e44ad"),
           ("Hombro (shoulder)\nΔf = 0, pero sube después", 9.75, (8.4, 3.7), "#d35400"),
           ("Máximo global", 12, (10.6, 4.9), "#27ae60")]
    for t, px, (tx, ty), col in ann:
        ax.annotate(t, (px, at(px)), xytext=(tx, ty), ha="center", fontsize=9, color=col,
                    fontweight="bold", arrowprops=dict(arrowstyle="->", color=col, lw=1.4))
    ax.set_xlabel("espacio de estados  s"); ax.set_ylabel("aptitud  f(s)")
    ax.set_ylim(-0.2, 5.6); ax.set_xticks([]); ax.set_yticks([])
    ax.set_title("Paisaje de búsqueda unidimensional y sus patologías", fontsize=10)
    save(fig, "fig_landscape.png")


def fig_ridge():
    n = 11
    X, Y = np.meshgrid(np.arange(n), np.arange(n))
    Z = X + Y - 5 * np.abs(X - Y)
    fig, ax = plt.subplots(figsize=(5.2, 4.6))
    cs = ax.contourf(X, Y, Z, 16, cmap="viridis")
    ax.plot([0, n - 1], [0, n - 1], "w--", lw=1)
    p = (4, 4)
    ax.scatter(*p, s=140, color="red", zorder=5, edgecolors="white")
    ax.text(p[0] - .35, p[1] + .55, f"s={p}  f={4 + 4}", color="white", fontsize=8, ha="right")
    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        q = (p[0] + dx, p[1] + dy)
        fq = q[0] + q[1] - 5 * abs(q[0] - q[1])
        ax.annotate("", q, p, arrowprops=dict(arrowstyle="->", color="orange", lw=1.6))
        ax.text(q[0] + .15 * dx + .1, q[1] + .15 * dy + .25, f"{fq}", color="orange", fontsize=8, fontweight="bold")
    ax.annotate("", (7.2, 7.2), (4.4, 4.4), arrowprops=dict(arrowstyle="->", color="white", lw=2.2))
    ax.text(0.3, 7.6, "flecha blanca: dirección de ascenso\n(diagonal; no es un movimiento\nválido de la vecindad)", color="white", fontsize=7.5)
    ax.set_title("Cresta: f(x,y) = x + y − 5|x − y|", fontsize=9)
    ax.set_xlabel("x"); ax.set_ylabel("y"); ax.set_aspect("equal")
    fig.colorbar(cs, ax=ax, label="f(x,y)", shrink=.8)
    save(fig, "fig_ridge.png")


# ---------------------------------------------------------- laberinto ---------
def run_steps(case, variant="steepest", mitig="none", seed=0, start=None):
    p = make_problem(case)
    r = run_metrics(p, variant, mitig, start or p.start, seed=seed)
    return p, r["steps"]


def fig_cases():
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.6))
    p, s = run_steps("A")
    draw_maze(axs[0], p, s, title=f"(a) Caso A – Steepest: ÉXITO en {s[-1].iteration} it.", annotate_neighbors=False)
    p, s = run_steps("B")
    draw_maze(axs[1], p, s, title=f"(b) Caso B – Steepest: ATRAPADO en {s[-1].iteration} it. (f = {s[-1].f:.0f})", annotate_neighbors=True)
    p, s = run_steps("C")
    draw_maze(axs[2], p, s, title=f"(c) Caso C – Steepest: ATRAPADO en {s[-1].iteration} it. (f = {s[-1].f:.0f})", annotate_neighbors=True)
    fig.tight_layout()
    save(fig, "fig_cases.png")


def fig_trap_sequence():
    p, s = run_steps("B")
    picks = [0, 3, len(s) - 1]
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.6))
    for ax, k in zip(axs, picks):
        st = s[k]
        draw_maze(ax, p, s[:k + 1], title=f"Iteración {st.iteration}: estado {st.state}, f = {st.f:.0f}")
    fig.tight_layout()
    save(fig, "fig_trap_sequence.png")


def fig_mitigation():
    fig, axs = plt.subplots(1, 2, figsize=(10.5, 4.6))
    p, s = run_steps("B", "steepest", "restart", seed=1)
    draw_maze(axs[0], p, s, title=f"Reinicios aleatorios: ÉXITO ({s[-1].iteration} it., {s[-1].restart} reinicios)", annotate_neighbors=False)
    p, s = run_steps("B", "steepest", "penalty")
    draw_maze(axs[1], p, s, title=f"Penalizaciones f' = f − λ·visitas: ÉXITO ({s[-1].iteration} it.)", annotate_neighbors=False)
    fig.tight_layout()
    save(fig, "fig_mitigation.png")


def fig_ui():
    d = InteractiveDemo("B", "Steepest-Ascent")
    for _ in range(7):
        d.step()
    d.fig.savefig(f"{OUT}/fig_ui.png", dpi=110, facecolor="white")
    plt.close(d.fig)


def fig_bars():
    rows = json.load(open(f"{OUT}/benchmark.json"))
    algos = []
    for r in rows:
        if r["algoritmo"] not in algos:
            algos.append(r["algoritmo"])
    fig, ax = plt.subplots(figsize=(10, 4.2))
    w = 0.26
    for i, (case, col) in enumerate(zip("ABC", ["#74a9cf", "#d95f0e", "#756bb1"])):
        vals = [next(r["exito_pct"] for r in rows if r["caso"] == case and r["algoritmo"] == a) for a in algos]
        b = ax.bar(np.arange(len(algos)) + (i - 1) * w, vals, w, label=f"Caso {case}", color=col)
        ax.bar_label(b, fmt="%.0f", fontsize=7)
    ax.set_xticks(range(len(algos)))
    ax.set_xticklabels([a.replace(" + ", "\n+ ").replace("First-Choice", "First-\nChoice") for a in algos], fontsize=7.5)
    ax.set_ylabel("Tasa de éxito (%)"); ax.set_ylim(0, 112); ax.legend(ncol=3, fontsize=8, loc="lower right")
    ax.set_title("Tasa de éxito desde estados iniciales aleatorios", fontsize=10)
    save(fig, "fig_bars.png")


def fig_landscape_f():
    fig, axs = plt.subplots(1, 2, figsize=(10.5, 4.4))
    for ax, case in zip(axs, "BC"):
        p = make_problem(case)
        draw_maze(ax, p, None, title=f"Mapa de aptitud f(s) = −h(s, meta) – {p.name}")
    fig.tight_layout()
    save(fig, "fig_fmap.png")


if __name__ == "__main__":
    for fn in (fig_landscape, fig_ridge, fig_cases, fig_trap_sequence, fig_mitigation,
               fig_ui, fig_landscape_f):
        fn()
    if os.path.exists(f"{OUT}/benchmark.json"):
        fig_bars()
    print("Figuras generadas en", OUT)
