"""
Modelado del problema: Escape de un laberinto con trampas.

Espacio de estados  S : celdas libres (fila, columna) de una cuadrícula 2D.
Vecindad         N(s) : las celdas libres a distancia 1 en 4 direcciones
                        (arriba, derecha, abajo, izquierda), sin atravesar muros.
Aptitud          f(s) : f(s) = -h(s, meta)   (se MAXIMIZA; el óptimo global es 0)
                        con h = distancia Manhattan o Euclidiana.
"""
import math
import random
from typing import List, Tuple

State = Tuple[int, int]

# Orden fijo de los movimientos (importante para Simple/Steepest deterministas)
MOVES = [(-1, 0, "arriba"), (0, 1, "derecha"), (1, 0, "abajo"), (0, -1, "izquierda")]


class MazeProblem:
    def __init__(self, name: str, rows: List[str], heuristic: str = "manhattan"):
        self.name = name
        self.rows = rows
        self.n_rows = len(rows)
        self.n_cols = len(rows[0])
        assert all(len(r) == self.n_cols for r in rows), "Filas de distinta longitud"
        self.walls = set()
        self.start = self.goal = None
        for r, line in enumerate(rows):
            for c, ch in enumerate(line):
                if ch == "#":
                    self.walls.add((r, c))
                elif ch == "S":
                    self.start = (r, c)
                elif ch == "G":
                    self.goal = (r, c)
        assert self.start and self.goal, "El laberinto necesita 'S' y 'G'"
        self.heuristic = heuristic
        self.free_cells = [(r, c) for r in range(self.n_rows) for c in range(self.n_cols)
                           if (r, c) not in self.walls]

    # ---- componentes formales -------------------------------------------------
    def neighbors(self, s: State) -> List[State]:
        """Operador de vecindad N(s)."""
        out = []
        for dr, dc, _ in MOVES:
            n = (s[0] + dr, s[1] + dc)
            if 0 <= n[0] < self.n_rows and 0 <= n[1] < self.n_cols and n not in self.walls:
                out.append(n)
        return out

    def h(self, s: State) -> float:
        dr, dc = abs(s[0] - self.goal[0]), abs(s[1] - self.goal[1])
        return dr + dc if self.heuristic == "manhattan" else math.hypot(dr, dc)

    def f(self, s: State) -> float:
        """Función de aptitud (a maximizar)."""
        return -self.h(s) + 0.0

    def is_goal(self, s: State) -> bool:
        return s == self.goal

    def random_state(self, rng: random.Random) -> State:
        return rng.choice([c for c in self.free_cells if c != self.goal])


# ---------------------------------------------------------------------------
# Laberintos de prueba   (# = muro, S = inicio, G = meta)
# ---------------------------------------------------------------------------

# CASO A: obstáculos convexos (aislados). Hill Climbing los rodea sin problema.
MAZE_A = [
    "...............",
    "............G..",
    "..##......#....",
    "..##......#....",
    "...............",
    "##....##.......",
    "......##.......",
    "...............",
    "...###.....##..",
    ".S.............",
    "...............",
]

# CASO B: una "copa" (U invertida) cuyo fondo apunta hacia la meta. El inicio
# está dentro; la esquina superior derecha de la copa es un MÁXIMO LOCAL.
MAZE_B = [
    "...............",
    "..............G",
    "...............",
    "...............",
    "...###########.",
    "...#.........#.",
    "...#.........#.",
    "...#....S....#.",
    "...#.........#.",
    "...#.........#.",
    "...............",
]

# CASO C: dos trampas (más difícil), útil para medir tasas de éxito.
MAZE_C = [
    "....................",
    ".................G..",
    "....................",
    "..#########..#######",
    "..#.......#..#.....#",
    "..#...S...#..#.....#",
    "..#.......#..#.....#",
    "..#.......#..#.....#",
    "....................",
    "....................",
    "....................",
]

MAZES = {
    "A": ("Caso A: obstáculos convexos", MAZE_A),
    "B": ("Caso B: trampa en U (máximo local)", MAZE_B),
    "C": ("Caso C: dos trampas", MAZE_C),
}


def make_problem(case: str, heuristic: str = "manhattan") -> MazeProblem:
    title, rows = MAZES[case.upper()]
    return MazeProblem(title, rows, heuristic)
