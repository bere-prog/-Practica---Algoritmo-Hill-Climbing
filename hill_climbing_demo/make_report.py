#!/usr/bin/env python3
"""Genera Reporte_Hill_Climbing.pdf  (python make_report.py).
Requiere haber corrido antes benchmark.py y make_figures.py."""
import json
import os

import matplotlib
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, Preformatted,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

from hc.algorithms import run_metrics
from hc.problem import make_problem

R = "results"
OUT = "Reporte_Hill_Climbing.pdf"

# ---- fuentes (DejaVu incluye Δ, ∈, ≤, →, ∇ ...) --------------------------------
fd = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")
for name, f in [("DV", "DejaVuSans.ttf"), ("DV-B", "DejaVuSans-Bold.ttf"),
                ("DV-I", "DejaVuSans-Oblique.ttf"), ("DV-BI", "DejaVuSans-BoldOblique.ttf"),
                ("DVM", "DejaVuSansMono.ttf")]:
    pdfmetrics.registerFont(TTFont(name, os.path.join(fd, f)))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DV-B", italic="DV-I", boldItalic="DV-BI")

NAVY = colors.HexColor("#1f3a5f")
body = ParagraphStyle("body", fontName="DV", fontSize=9.2, leading=13.4, alignment=TA_JUSTIFY, spaceAfter=5)
h1 = ParagraphStyle("h1", fontName="DV-B", fontSize=14.5, leading=18, textColor=NAVY, spaceBefore=10, spaceAfter=6)
h2 = ParagraphStyle("h2", fontName="DV-B", fontSize=11, leading=14, textColor=NAVY, spaceBefore=8, spaceAfter=4)
cap = ParagraphStyle("cap", fontName="DV-I", fontSize=8, leading=10.5, alignment=TA_CENTER, textColor=colors.HexColor("#444444"), spaceAfter=8)
cell = ParagraphStyle("cell", fontName="DV", fontSize=8, leading=10)
cellb = ParagraphStyle("cellb", parent=cell, fontName="DV-B", textColor=colors.white)
code = ParagraphStyle("code", fontName="DVM", fontSize=7.8, leading=10, backColor=colors.HexColor("#f3f5f8"),
                      borderPadding=5, leftIndent=6, rightIndent=6, spaceBefore=3, spaceAfter=8)
title = ParagraphStyle("title", fontName="DV-B", fontSize=24, leading=30, textColor=NAVY, alignment=TA_CENTER)
sub = ParagraphStyle("sub", fontName="DV", fontSize=12, leading=17, alignment=TA_CENTER, textColor=colors.HexColor("#333333"))

refst = ParagraphStyle("ref", parent=body, leftIndent=14, firstLineIndent=-14, alignment=0)
P = lambda t, s=body: Paragraph(t, s)
BUL = lambda t: Paragraph(t, body, bulletText="•")


def img(name, width_cm):
    path = f"{R}/{name}"
    w, h = PILImage.open(path).size
    return Image(path, width=width_cm * cm, height=width_cm * cm * h / w)


def fig(name, width_cm, caption):
    return KeepTogether([img(name, width_cm), P(caption, cap)])


def table(rows, widths, header=True, zebra=True):
    data = [[Paragraph(str(c), cellb if (header and i == 0) else cell) for c in row] for i, row in enumerate(rows)]
    t = Table(data, colWidths=[w * cm for w in widths], repeatRows=1 if header else 0)
    st = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b8c2cc")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if header:
        st.append(("BACKGROUND", (0, 0), (-1, 0), NAVY))
    if zebra:
        for i in range(1 if header else 0, len(rows)):
            if i % 2 == 0:
                st.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#eef2f7")))
    t.setStyle(TableStyle(st))
    return t


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("DV", 7.5)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(2 * cm, 1.2 * cm, "Búsqueda Local con Hill Climbing – Reporte técnico")
    canvas.drawRightString(letter[0] - 2 * cm, 1.2 * cm, f"Página {doc.page}")
    canvas.restoreState()


# ---- datos --------------------------------------------------------------------
bench = json.load(open(f"{R}/benchmark.json"))
N = bench[0]["n"]
B = lambda case, algo: next(r for r in bench if r["caso"] == case and r["algoritmo"] == algo)
pB = B("B", "Steepest-Ascent")["exito_pct"] / 100          # prob. de éxito de una corrida (caso B)
exp_restarts = (1 - pB) / pB
meas_restarts = B("B", "Steepest + Reinicios aleatorios")["reinicios_medios"]

fixed = []
for case in "ABC":
    p = make_problem(case)
    for label, v, m, seed in [("Steepest-Ascent", "steepest", "none", 0),
                              ("Steepest + Reinicios aleatorios", "steepest", "restart", 1),
                              ("Steepest + Penalizaciones", "steepest", "penalty", 0)]:
        r = run_metrics(p, v, m, p.start, seed=seed)
        last = r["steps"][-1]
        res = {"goal": "Éxito (óptimo global)", "local_max": "Atrapado en máximo local"}.get(r["status"], r["status"])
        fixed.append([case, label, res, str(r["iterations"]), str(r["restarts"]),
                      f"{last.state}", f"{last.f:.0f}"])

# ---- contenido ----------------------------------------------------------------
S = []
# 1. Portada e introducción -------------------------------------------------------
S += [Spacer(1, 2.2 * cm), P("Búsqueda Local con el Algoritmo<br/>Hill Climbing (Ascenso de Colina)", title),
      Spacer(1, 0.5 * cm), P("Fundamentos, variantes, patologías y demostración práctica:<br/>escape de un laberinto con trampas", sub),
      Spacer(1, 1.0 * cm),
      P("<b>Asignatura:</b> Fundamentos de Inteligencia Artificial / Algoritmos de Optimización<br/>"
        "<b>Equipo:</b> [Nombres de los integrantes]<br/><b>Profesor/a:</b> [Nombre]<br/>"
        "<b>Fecha:</b> [dd/mm/aaaa]", sub),
      Spacer(1, 0.8 * cm)]
S += [P("1. Introducción", h1),
      P("En Inteligencia Artificial, muchos problemas no se resuelven encontrando un <i>camino</i> desde un estado "
        "inicial hasta una meta, sino encontrando un <i>estado</i> que sea bueno según algún criterio: el "
        "acomodo de N reinas sin ataques, la ruta más corta de un viajante o los parámetros que maximizan el "
        "rendimiento de un modelo. En estos casos el camino recorrido es irrelevante y lo único que importa es la "
        "calidad del estado final. Los algoritmos de <b>búsqueda local</b> aprovechan esa propiedad: mantienen "
        "únicamente un estado actual y lo mejoran iterativamente moviéndose a estados vecinos, por lo que usan "
        "memoria constante y pueden encontrar soluciones aceptables en espacios enormes o continuos donde la "
        "búsqueda sistemática es inviable (Russell y Norvig, 2020)."),
      P("<b>Hill Climbing</b> es el algoritmo de búsqueda local más sencillo: en cada iteración se desplaza al vecino "
        "que mejora la función de evaluación y se detiene cuando ninguno la mejora. Su analogía es la de un alpinista "
        "con niebla espesa que solo percibe el terreno inmediato a sus pies. Es rápido y simple, pero es "
        "<i>miope</i>: puede quedar atrapado en máximos locales, mesetas o crestas."),
      P("Este reporte documenta (i) el marco teórico del algoritmo, sus variantes y sus patologías, y (ii) una "
        "demostración en <b>Python</b> que resuelve el <b>escape de un laberinto con trampas cóncavas</b>, "
        "mostrando paso a paso con telemetría tanto un caso de éxito como un caso de atrapamiento en un máximo "
        "local, y evaluando dos técnicas de mitigación: <i>reinicios aleatorios</i> y <i>penalizaciones</i>.")]
S.append(PageBreak())

# 2. Marco teórico ----------------------------------------------------------------
S += [P("2. Marco teórico", h1), P("2.1 Búsqueda local frente a búsqueda informada global", h2),
      P("Los algoritmos como A* o Dijkstra exploran el espacio de forma <i>sistemática</i>: guardan en memoria una "
        "frontera de nodos (un árbol o grafo de búsqueda) y los expanden en orden de costo. Así garantizan "
        "completitud y, con una heurística admisible, optimalidad del camino, pero su memoria crece como "
        "O(b<super>d</super>) en el peor caso. La búsqueda local, en cambio, conserva solo el estado actual (y "
        "evalúa temporalmente a sus vecinos), con lo que la memoria es <b>O(1)</b> respecto al tamaño del espacio."),
      table([["Criterio", "A* / Dijkstra (global)", "Hill Climbing (local)"],
             ["Qué almacena", "Frontera + conjunto de explorados (árbol/grafo)", "Solo el estado actual"],
             ["Memoria", "O(b<super>d</super>) en el peor caso", "O(1)"],
             ["Resultado", "Camino de costo mínimo (con heurística admisible)", "Un estado; el camino no importa"],
             ["Completitud / optimalidad", "Sí (grafos finitos / h admisible)", "No: puede detenerse en un óptimo local"],
             ["Uso típico", "Navegación, planificación de rutas", "Optimización: N-reinas, TSP, ajuste de parámetros"]],
            [3.6, 6.7, 6.7]), Spacer(1, 6),
      P("2.2 Componentes formales", h2),
      BUL("<b>Espacio de estados S:</b> conjunto de configuraciones posibles. Un estado s ∈ S representa una solución "
          "candidata completa; la solución buscada es s* ∈ S con la mejor aptitud."),
      BUL("<b>Operador de vecindad N(s) ⊆ S:</b> reglas que generan los estados adyacentes a s mediante una pequeña "
          "modificación (mover una pieza, intercambiar dos aristas, desplazarse una celda)."),
      BUL("<b>Función de evaluación f: S → ℝ:</b> cuantifica la calidad. En <i>maximización</i> se busca "
          "s* = argmax f(s); un problema de <i>minimización</i> de un costo c(s) se convierte en maximización con "
          "f(s) = −c(s). Se define Δf(n) = f(n) − f(s) para n ∈ N(s)."),
      P("Un estado s es un <b>máximo local</b> si ∀ n ∈ N(s): f(n) ≤ f(s); es un <b>máximo global</b> si "
        "∀ s′ ∈ S: f(s′) ≤ f(s). Todo máximo global es local, pero no al revés; Hill Climbing solo puede "
        "garantizar llegar a un máximo <i>local</i>."),
      P("2.3 Pseudocódigo", h2),
      Preformatted("SIMPLE HILL CLIMBING                    STEEPEST-ASCENT HILL CLIMBING\n"
                   "s ← estado_inicial                       s ← estado_inicial\n"
                   "repetir:                                 repetir:\n"
                   "  mejoró ← falso                           V ← N(s)\n"
                   "  para cada n en N(s) (orden fijo):        n* ← argmax_{n ∈ V} f(n)\n"
                   "     si f(n) > f(s):                       si f(n*) ≤ f(s):\n"
                   "        s ← n ; mejoró ← verdadero            devolver s   # máx. local\n"
                   "        romper                             s ← n*\n"
                   "  si no mejoró: devolver s", code),
      P("La diferencia clave: Simple Hill Climbing acepta el <i>primer</i> vecino que mejora (evalúa pocos vecinos "
        "por iteración), mientras que Steepest-Ascent evalúa <i>todo</i> el vecindario y toma el de mayor "
        "pendiente (más costo por iteración, pasos de mejor calidad).")]

S += [KeepTogether([P("2.4 Estudio comparativo de variantes", h2),
      table([["Variante", "Selección del vecino", "Ventaja", "Desventaja"],
             ["Simple", "Primer vecino mejor en orden fijo", "Muy barata por iteración", "Sesgada por el orden; mismo problema de óptimos locales"],
             ["Steepest-Ascent", "Mejor vecino (máx. Δf)", "Menos pasos hasta el óptimo local", "Evalúa todo N(s): costosa si |N(s)| es grande"],
             ["Stochastic", "Aleatoria entre los mejores, P(n) = Δf(n) / Σ Δf(m)", "Menos determinista; explora distintas rutas de ascenso", "Convergencia más lenta; sigue sin escapar de máximos locales"],
             ["First-Choice", "Vecinos generados al azar; el primero que mejora", "Ideal cuando |N(s)| es enorme", "Puede requerir muchas pruebas cerca del óptimo"],
             ["Random-Restart", "Repite el algoritmo desde estados aleatorios", "Completo con probabilidad 1 si hay tiempo ilimitado", "Costo total depende de la tasa de éxito p de cada corrida"]],
            [2.5, 4.6, 4.8, 5.1])]),
      Spacer(1, 5),
      P(f"<b>Análisis de Random-Restart.</b> Si cada corrida alcanza el óptimo global con probabilidad p, el número esperado "
        f"de corridas es 1/p y el de <i>reinicios</i> es (1 − p)/p. Con las corridas de Steepest-Ascent del caso B "
        f"(p = {pB:.3f}, Sección 4) se predicen {exp_restarts:.2f} reinicios en promedio, y se midieron "
        f"{meas_restarts:.2f}: la teoría concuerda con el experimento."),
      P("2.5 Patologías del paisaje de búsqueda", h2),
      fig("fig_landscape.png", 11, "Figura 1. Paisaje unidimensional: máximo local, meseta, hombro y máximo global."),
      BUL("<b>Máximo local:</b> ∃ s ≠ s* tal que ∀ n ∈ N(s): Δf(n) ≤ 0 pero f(s) < f(s*). El algoritmo termina con "
          "una solución subóptima. En el laberinto ocurre cuando los movimientos que acercan a la meta están "
          "bloqueados por muros."),
      BUL("<b>Meseta (plateau) y hombro (shoulder):</b> región donde Δf = 0 para todos los vecinos (∇f ≈ 0). Sin "
          "gradiente el algoritmo no distingue direcciones. Si la meseta es un <i>hombro</i> tiene una salida "
          "ascendente; si es un máximo plano no. Se mitiga con <i>movimientos laterales</i> limitados: en el "
          "problema de las 8 reinas, Steepest-Ascent resuelve ≈14 % de las instancias, y permitir hasta 100 "
          "movimientos laterales sube el éxito a ≈94 % (Russell y Norvig, 2020)."),
      BUL("<b>Cresta (ridge):</b> secuencia de máximos locales cuya dirección de ascenso es diagonal respecto a los "
          "movimientos permitidos. Para f(x, y) = x + y − 5|x − y| el punto (4, 4) tiene f = 8 y sus cuatro "
          "vecinos ortogonales tienen f = 4 o f = 2; el algoritmo se detiene aunque f crece a lo largo de la "
          "diagonal (Figura 2)."),
      fig("fig_ridge.png", 6.6, "Figura 2. Cresta: movimientos ortogonales no pueden subir por la diagonal.")]

# 3. Modelado ---------------------------------------------------------------------
S += [P("3. Modelado del problema implementado: escape de un laberinto con trampas", h1),
      P("Se eligió el problema recomendado: navegación en una cuadrícula 2D con muros que forman trampas cóncavas. "
        "Se implementó en Python 3 (matplotlib para la visualización)."),
      P("3.1 Definición formal del estado", h2),
      P("Un laberinto es una cuadrícula de n × m celdas con un conjunto de muros W, una celda inicial s<sub>0</sub> y una "
        "meta g. Un <b>estado</b> es la celda ocupada por el agente: s = (r, c) con 0 ≤ r &lt; n, 0 ≤ c &lt; m y "
        "(r, c) ∉ W. El espacio de estados es S = {celdas libres}. La <b>solución</b> es el estado s = g."),
      P("3.2 Generación del vecindario", h2),
      P("N(s) = { (r + Δr, c + Δc) : (Δr, Δc) ∈ {(−1,0), (0,1), (1,0), (0,−1)} } ∩ S, es decir, las celdas libres "
        "adyacentes en cuatro direcciones (arriba, derecha, abajo, izquierda), sin atravesar muros ni salir del "
        "tablero. El orden fijo anterior se usa en Simple y Steepest para desempates deterministas."),
      P("3.3 Función de aptitud", h2),
      P("Se <b>maximiza</b> el negativo de la distancia a la meta:"),
      P("<b>f(s) = − h(s, g),&nbsp;&nbsp; h<sub>Manhattan</sub> = |r − r<sub>g</sub>| + |c − c<sub>g</sub>|,"
        "&nbsp;&nbsp; h<sub>Euclidiana</sub> = √((r − r<sub>g</sub>)² + (c − c<sub>g</sub>)²)</b>", cap),
      P("El óptimo global es f(g) = 0. Con distancia Manhattan, cada movimiento cambia f exactamente en ±1, por "
        "lo que en este modelo no hay mesetas: toda celda sin vecino mejor es un máximo local. Una celda s ≠ g "
        "es máximo local si y solo si todas las direcciones que reducen h (hacia la meta en filas y columnas) "
        "están bloqueadas por muros o por el borde. Una <b>trampa cóncava</b> (U) con el fondo hacia la meta "
        "genera exactamente esta situación (Figura 3)."),
      fig("fig_fmap.png", 14, "Figura 3. Mapa de aptitud f(s) en los casos B y C: los muros crean cuencas donde subir lleva a un callejón sin salida."),
      P("3.4 Casos de prueba y mitigaciones", h2),
      table([["Caso", "Descripción", "Resultado esperado"],
             ["A", "Cuadrícula 11×15, obstáculos convexos aislados", "Convergencia al óptimo global"],
             ["B", "Una copa en U (11×15); el inicio está dentro de ella", "Atrapamiento en el máximo local (5, 12), f = −6"],
             ["C", "Dos copas en U (11×20); el inicio está dentro de la izquierda", "Atrapamiento; sirve para medir tasas de éxito"]],
            [1.4, 9.0, 6.6]), Spacer(1, 5),
      BUL("<b>Reinicios aleatorios:</b> al terminar en un máximo local se elige una celda libre al azar como nuevo "
          "estado inicial (hasta 20 reinicios)."),
      BUL("<b>Penalizaciones:</b> se optimiza f′(s) = f(s) − λ·v(s), donde v(s) cuenta cuántas veces se "
          "penalizó la celda s (λ = 1). Cuando ningún vecino mejora f′, en lugar de detenerse se incrementa v(s) y se "
          "reevalúa: el máximo local se «rellena» progresivamente hasta que algún vecino resulta mejor y el agente puede "
          "salir de la cuenca. No requiere teletransportarse a otro estado."),
      P("3.5 Arquitectura del software", h2),
      P("<font name='DVM'>hc/problem.py</font> (estados, vecindad y f), <font name='DVM'>hc/algorithms.py</font> "
        "(variantes como <i>generadores</i> que emiten un objeto <i>Step</i> por iteración), "
        "<font name='DVM'>hc/visual.py</font> (demo interactiva), <font name='DVM'>main.py</font> (consola paso a paso), "
        "<font name='DVM'>benchmark.py</font> (métricas). Cada <i>Step</i> contiene la telemetría exigida: estado "
        "actual, f(actual), lista de vecinos con f(vecino) y Δf, vecino elegido y razón de la decisión o de "
        "terminación. La interfaz tiene botones <i>Paso</i>, <i>Auto</i> y <i>Reiniciar</i>, y selectores de caso y "
        "algoritmo (Figura 4)."),
      fig("fig_ui.png", 13, "Figura 4. Interfaz de la demostración: modo paso a paso con telemetría (caso B, Steepest-Ascent, iteración 7).")]

# 4. Resultados -------------------------------------------------------------------
S += [P("4. Análisis de resultados", h1),
      P("4.1 Comparación del algoritmo simple frente a las trampas", h2),
      fig("fig_cases.png", 17, "Figura 5. Steepest-Ascent desde el inicio fijo: éxito en el caso A (a) y atrapamiento en los máximos locales de los casos B (b) y C (c). "
          "Los recuadros naranja/verde son los vecinos evaluados con su Δf; ningún vecino tiene Δf &gt; 0."),
      P("En el caso A, el algoritmo avanza con Δf = +1 en cada paso rodeando los obstáculos y llega a la meta en 20 "
        "iteraciones. En el caso B, las iteraciones 1 a 6 son ascensos legítimos, pero en la iteración 7 el agente "
        "llega a (5, 12) con f = −6: su vecino superior y el derecho son muros y los otros dos tienen Δf = −1. "
        "La meta está a solo 6 celdas, pero alcanzarla exige <i>empeorar</i> temporalmente (bajar a la salida de la "
        "copa, donde f baja hasta −11), algo que Hill Climbing nunca hace."),
      fig("fig_trap_sequence.png", 17, "Figura 6. Caso B: iteraciones 1, 4 y 7 (atrapamiento)."),
      KeepTogether([P("4.2 Resultados con mitigaciones (inicio fijo)", h2),
      table([["Caso", "Algoritmo", "Resultado", "Iter.", "Reinicios", "Estado final", "f final"]] + fixed,
            [1.3, 5.0, 4.2, 1.2, 2.0, 2.3, 1.5])]), Spacer(1, 5),
      fig("fig_mitigation.png", 12.5, "Figura 7. Caso B con mitigaciones: tras un reinicio aleatorio (izq.) y con penalizaciones (der.), donde el agente «rellena» la cuenca hasta poder salir."),
      P(f"4.3 Tabla de métricas (N = {N} estados iniciales aleatorios por caso)", h2),
      P("Tasa de éxito = % de corridas que alcanzan la meta; estancamiento = % que terminan en un máximo local; las "
        "iteraciones y el tiempo son promedios por corrida (en las variantes con reinicios incluyen todos los reinicios). "
        "El tiempo incluye generar la telemetría, por lo que solo debe usarse para comparar entre algoritmos.")]
for case, nm in [("A", "Caso A (obstáculos convexos)"), ("B", "Caso B (una trampa en U)"), ("C", "Caso C (dos trampas)")]:
    rows = [["Algoritmo", "Éxito (%)", "Estancado (%)", "Iter. medias", "Reinicios medios", "Tiempo (ms)"]]
    for r in [r for r in bench if r["caso"] == case]:
        rows.append([r["algoritmo"], f"{r['exito_pct']:.1f}", f"{r['estancado_pct']:.1f}", f"{r['iter_media']:.1f}",
                     f"{r['reinicios_medios']:.2f}", f"{r['tiempo_ms']:.3f}"])
    S += [KeepTogether([P(f"<b>{nm}</b>", body), table(rows, [5.9, 1.9, 2.4, 2.2, 2.7, 2.1]), Spacer(1, 6)])]
S += [fig("fig_bars.png", 14.5, "Figura 8. Tasa de éxito por algoritmo y caso."),
      P("<b>Observaciones.</b>"),
      BUL("Sin mitigación, la tasa de éxito depende del <i>inicio</i>: ≈59 % en el caso B y ≈50 % en el C; el resto de las "
          "corridas termina atrapado en una de las cuencas."),
      BUL("Simple y Steepest alcanzan la misma tasa de éxito porque, con Manhattan, todo movimiento que mejora vale +1; difieren en "
          "el trabajo por iteración (Simple evalúa menos vecinos). First-Choice y Stochastic cambian la <i>ruta</i> de ascenso, "
          "lo que puede llevar a cuencas distintas, pero no eliminan los máximos locales."),
      BUL("<b>Reinicios aleatorios</b> llevan el éxito a 100 % con un costo moderado (≈1.7× las iteraciones en el caso B), "
          "porque cada reinicio es un nuevo intento independiente con probabilidad p de éxito."),
      BUL("<b>Penalizaciones</b> también alcanzan 100 % y no necesitan acceso aleatorio al espacio de estados, pero "
          "cuestan más iteraciones (≈7× en B y ≈20× en C) porque deben rellenar la cuenca antes de salir; su costo crece con la "
          "profundidad y el área de la trampa."),
      BUL("Incluso en el caso A, ≈3–6 % de los inicios aleatorios quedan atrapados en las concavidades que forman los "
          "bordes de los obstáculos: los máximos locales aparecen aunque no se diseñen trampas.")]

# 5. Conclusiones -------------------------------------------------------------------
S += [P("5. Conclusiones y discusión", h1),
      P("<b>Idoneidad en el mundo real.</b> Hill Climbing es la elección adecuada cuando (i) el espacio es enorme y solo se "
        "necesita una solución buena, no la óptima, (ii) la memoria es limitada, (iii) el paisaje es poco rugoso o "
        "casi unimodal, o (iv) se usa como <i>refinamiento local</i> final dentro de otro método. Es muy rápido, fácil de "
        "implementar y no requiere almacenar el espacio. Su principal debilidad, demostrada en los casos B y C, es la "
        "dependencia total del estado inicial y de la geometría local: sin garantías de optimalidad, puede fallar "
        "en ≈40–50 % de los inicios incluso en un problema tan pequeño."),
      P("<b>Cuándo sustituirlo:</b>"),
      table([["Situación", "Alternativa", "Justificación"],
             ["Muchos máximos locales; se acepta cierto costo computacional", "Simulated Annealing", "Acepta movimientos que empeoran con probabilidad e<super>Δf/T</super>; al enfriar T converge. Escapa de las trampas sin reiniciar (Kirkpatrick et al., 1983)."],
             ["Paisaje deceptivo o multimodal, soluciones combinables", "Algoritmos Genéticos", "Mantienen una <i>población</i>; el cruce combina buenas partes y la mutación explora (Holland, 1975)."],
             ["Se requiere el camino óptimo garantizado (navegación real)", "A* / Dijkstra", "Completos y óptimos; el costo de memoria es aceptable en mapas moderados."],
             ["Mesetas extensas", "HC con movimientos laterales, Tabú o Guided Local Search", "Permiten recorrer zonas planas y penalizan lo ya visitado (Voudouris y Tsang, 1999)."]],
            [4.8, 3.6, 8.6]), Spacer(1, 6),
      P("<b>Aprendizajes.</b> (1) Que la heurística sea buena no basta: Manhattan es admisible, pero como función de "
        "<i>aptitud local</i> engaña en presencia de muros. (2) La mitigación tiene un costo: los reinicios cuestan "
        "iteraciones extras y las penalizaciones aún más, pero ambas convierten un algoritmo incompleto en uno que "
        "converge con alta probabilidad. (3) La telemetría paso a paso (vecinos, Δf y razón de decisión) hace "
        "visible el momento exacto en que se produce el atrapamiento: ∀ n ∈ N(s), Δf ≤ 0. "
        "<b>Limitaciones:</b> los laberintos son pequeños y los tiempos medidos (&lt; 3 ms) son del orden de la sobrecarga de "
        "Python; las conclusiones sobre el <i>costo relativo</i> son más fiables que los valores absolutos."),
      P("6. Referencias bibliográficas", h1)]
for ref in [
    "Russell, S. y Norvig, P. (2020). <i>Artificial Intelligence: A Modern Approach</i> (4.ª ed.). Pearson. (Cap. 4: Search in Complex Environments.)",
    "Hoos, H. H. y Stützle, T. (2004). <i>Stochastic Local Search: Foundations and Applications</i>. Morgan Kaufmann.",
    "Kirkpatrick, S., Gelatt, C. D. y Vecchi, M. P. (1983). Optimization by Simulated Annealing. <i>Science</i>, 220(4598), 671–680.",
    "Holland, J. H. (1975). <i>Adaptation in Natural and Artificial Systems</i>. University of Michigan Press.",
    "Voudouris, C. y Tsang, E. (1999). Guided local search and its application to the traveling salesman problem. <i>European Journal of Operational Research</i>, 113(2), 469–499.",
    "Hart, P. E., Nilsson, N. J. y Raphael, B. (1968). A Formal Basis for the Heuristic Determination of Minimum Cost Paths. <i>IEEE Transactions on Systems Science and Cybernetics</i>, 4(2), 100–107."]:
    S.append(Paragraph(ref, refst))

S += [P("Anexo: reproducción de resultados", h2),
      Preformatted("pip install -r requirements.txt\n"
                   "python main.py                              # demo interactiva (Paso / Auto / Reiniciar)\n"
                   "python main.py --cli --case B               # consola, ENTER = siguiente paso\n"
                   "python main.py --cli --case B --mitigation restart --auto\n"
                   "python benchmark.py -n 500                  # tabla de métricas (semilla fija)\n"
                   "python make_figures.py && python make_report.py", code)]

doc = SimpleDocTemplate(OUT, pagesize=letter, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm,
                        bottomMargin=1.9 * cm, title="Búsqueda Local con Hill Climbing", author="Equipo")
doc.build(S, onFirstPage=footer, onLaterPages=footer)
print("Generado", OUT)
