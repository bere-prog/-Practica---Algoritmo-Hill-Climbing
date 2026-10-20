# Hill Climbing – Escape de un laberinto con trampas (Python)

Demostración de **Hill Climbing** con telemetría paso a paso, casos de éxito y de
atrapamiento en máximo local, y dos mecanismos de mitigación.

## Instalación
    pip install -r requirements.txt

## Uso
    python main.py                      # ventana interactiva: Paso / Auto / Reiniciar + selector de caso y algoritmo
    python main.py --cli --case B       # consola paso a paso (ENTER avanza, q sale)
    python main.py --cli --case A --auto
    python main.py --cli --case B --mitigation restart --auto
    python main.py --cli --case B --mitigation penalty --auto --quiet
    python main.py --cli --case A --heuristic euclidean --auto --quiet
    python benchmark.py -n 500          # métricas (éxito %, estancamiento %, iteraciones, tiempo)
    python make_figures.py && python make_report.py   # regenera figuras y PDF

## Casos
| Caso | Descripción | Resultado (Steepest, inicio fijo) |
|------|-------------|-----------------------------------|
| A | Obstáculos convexos | Éxito en 20 iteraciones |
| B | Una trampa en U | Atrapado en (5,12), f = -6 |
| C | Dos trampas en U | Atrapado, f = -11 |

## Modelo
- Estado: celda libre (fila, columna). Vecindad: 4 direcciones sin muros.
- Aptitud: f(s) = -h(s, meta), con h Manhattan o Euclidiana (maximizar; óptimo = 0).
- Variantes: `simple`, `steepest`, `first_choice`, `stochastic`.
- Mitigaciones: `restart` (reinicios aleatorios) y `penalty` (f' = f - λ·visitas).

## Estructura
    hc/problem.py     laberintos, vecindad y f
    hc/algorithms.py  variantes + mitigaciones (generadores que emiten un Step por iteración)
    hc/visual.py      dibujo y demo interactiva (matplotlib)
    main.py           CLI / lanzador de la ventana
    benchmark.py      tabla de métricas (semilla fija, reproducible)
    make_figures.py, make_report.py   figuras y reporte PDF
