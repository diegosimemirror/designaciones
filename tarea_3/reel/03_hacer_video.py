# ============================================================
# Reel · Paso 3: armar el video 9:16 (1080 x 1920) con la narración del autor, gráficos animados, subtítulos y música
# Insumos:   reel/voz/narracion_final.wav y reel/voz/palabras_final.json (paso 2); indicadores del script 07/07c;
#            web/data/dashboard.json (red de seguimiento, sin nombres); música "Clean Soul" de Kevin MacLeod (CC BY 4.0)
# Resultado: reel/reel.mp4, reel/subtitulos.srt, reel/portada.png, reel/recursos/ (música y créditos)
# Versión entregada: "corta" (79 s; elegida por el autor el 01/11/2026). "--version completa" genera reel_completa.mp4 (95 s)
# Cada escena empieza cuando el autor empieza la frase correspondiente (tiempos de Whisper, paso 1).
# Todo se dibuja con los datos: no hay nombres de personas (códigos anónimos) ni código en pantalla.
# ============================================================

# --- Paquetes ---
# json, math, random, subprocess, shutil: utilidades (leer JSON, cálculos, orden aleatorio fijo, llamar a ffmpeg y Chrome)
import json
import math
import random
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path
# numpy y pandas: datos de los gráficos
import numpy as np
import pandas as pd
# PIL (Pillow): dibujar cada cuadro del video
from PIL import Image, ImageDraw, ImageFont
# imageio_ffmpeg: trae ffmpeg, que codifica el video y mezcla el audio
import imageio_ffmpeg

CARPETA = Path(__file__).resolve().parent
TAREA = CARPETA.parent
VOZ, REC = CARPETA / "voz", CARPETA / "recursos"
REC.mkdir(exist_ok=True)
IND = TAREA / "datos" / "procesados" / "indicadores"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
W, H, FPS = 1080, 1920, 30
INICIO_VOZ, COLA = 0.4, 1.1
MUSICA = Path(r"C:\Users\Principal\designaciones_cache\musica\Clean Soul.mp3")
URL = "diegosimemirror.github.io/designaciones/tarea_3/web"

# Colores (los mismos del modo oscuro del dashboard y de las infografías)
FONDO, SUPERFICIE = (13, 13, 13), (26, 26, 25)
T1, T2, T3 = (240, 239, 236), (195, 194, 183), (137, 135, 129)
AZUL, NARANJA, VERDE, GRIS = (57, 135, 229), (217, 89, 38), (25, 158, 112), (56, 56, 53)
RAMPA = [(16, 66, 129), (24, 79, 149), (28, 92, 171), (37, 106, 191), (57, 135, 229), (109, 167, 236), (183, 211, 246)]


@lru_cache(maxsize=None)
def fuente(peso, tam):
    """Antes: peso ("b" negrita, "r" normal) y tamaño | Después: la fuente Segoe UI de Windows"""
    return ImageFont.truetype(f"C:/Windows/Fonts/{'segoeuib' if peso == 'b' else 'segoeui'}.ttf", tam)


def suave(x):
    """Curva de animación: arranca rápido y frena al final (x de 0 a 1)"""
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def mezclar(c1, c2, a):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * a) for i in range(3))


def texto(d, xy, t, peso="b", tam=48, color=T1, ancla="la", ancho=None, interlinea=1.22):
    """Escribe un texto; si se da 'ancho', lo parte en varias líneas que no pasen de ese ancho en píxeles"""
    f = fuente(peso, tam)
    if not ancho:
        d.text(xy, t, font=f, fill=color, anchor=ancla)
        return
    lineas, actual = [], ""
    for p in t.split():
        prueba = f"{actual} {p}".strip()
        if d.textlength(prueba, font=f) <= ancho or not actual:
            actual = prueba
        else:
            lineas.append(actual)
            actual = p
    lineas.append(actual)
    for k, l in enumerate(lineas):
        d.text((xy[0], xy[1] + k * tam * interlinea), l, font=f, fill=color, anchor=ancla)


def miles(n):
    return f"{n:,}".replace(",", ".")


# ============================================================
# PASO 3.1: tiempos de la narración y de cada escena
# ============================================================
import sys
# Versión del audio (paso 2): "completa" (todo lo dicho, salvo dos frases completas) o "corta" (además sin la frase de los grafos)
VERSION = sys.argv[sys.argv.index("--version") + 1] if "--version" in sys.argv else "corta"
voz = json.loads((VOZ / f"palabras_{VERSION}.json").read_text(encoding="utf-8"))
DURACION = INICIO_VOZ + voz["duracion"] + COLA
# Restos de palabras cortadas que Whisper ubica en el borde de un corte (no se oyen): fuera de los subtítulos
EXCLUIR = set()          # ya no hay cortes a mitad de frase (criterio revisado con el autor)
palabras = [w for w in voz["palabras"] if not any(abs(w["i_original"] - e) < 0.03 for e in EXCLUIR)]
# Escenas: nombre y segundo del audio ORIGINAL en que empieza la frase
INICIOS = [("gancho", 0), ("alcance", 10.7), ("elenco", 18.46), ("olas", 30.3), ("control", 35.2), ("rotacion", 44.6),
           ("trayectorias", 52.02)]
if VERSION == "completa":       # la red mientras habla de grupos y grafos; el triángulo cuando explica las referencias
    INICIOS += [("grafos", 60.56), ("redes", 78.8)]
else:                           # sin la frase de los grafos: primero el triángulo, luego la red
    INICIOS += [("redes", 60.56), ("grafos", 65.9)]
INICIOS += [("mujeres", 92.0), ("cierre", 100.4)]


def inicio_final(t_original):
    if t_original == 0:
        return 0.0
    w = next(w for w in palabras if w["i_original"] >= t_original - 0.02)
    return INICIO_VOZ + w["i"] - 0.15


ESCENAS = []
for k, (nombre, t0) in enumerate(INICIOS):
    a = inicio_final(t0)
    b = inicio_final(INICIOS[k + 1][1]) if k + 1 < len(INICIOS) else DURACION
    ESCENAS.append((nombre, a, b))
print("Escenas:", [(n, round(a, 1), round(b - a, 1)) for n, a, b in ESCENAS], "| total", round(DURACION, 1), "s")

# ============================================================
# PASO 3.2: subtítulos (bloques de hasta 2 líneas) y archivo .srt
#   Antes: palabras con su tiempo | Después: bloques legibles con inicio y fin
# ============================================================
ARREGLOS = {25.5: "Estado.", 100.4: "Los"}
limpias = []
for w in palabras:
    p = w["p"]
    for t, nuevo in ARREGLOS.items():
        if abs(w["i_original"] - t) < 0.05:
            p = nuevo
    if limpias and p.startswith(".") and limpias[-1]["p"][-1].isdigit():          # "27" + ".000" = "27.000"
        limpias[-1]["p"] += p
        limpias[-1]["f"] = w["f"]
        continue
    if p.lower() == "peruano" and limpias and limpias[-1]["p"].lower() == "el":
        limpias[-1]["p"], p = "El", "Peruano"
    limpias.append({"p": p, "i": w["i"] + INICIO_VOZ, "f": w["f"] + INICIO_VOZ})
bloques, actual = [], []
for w in limpias:
    propuesta = " ".join(x["p"] for x in actual + [w])
    if actual and (len(propuesta) > 64 or w["f"] - actual[0]["i"] > 3.4):
        bloques.append(actual)
        actual = []
    actual.append(w)
    if w["p"].endswith((".", "?")) or (w["p"].endswith(",") and len(" ".join(x["p"] for x in actual)) > 28):
        bloques.append(actual)
        actual = []
if actual:
    bloques.append(actual)
CUES = []
for k, b in enumerate(bloques):
    ini = b[0]["i"] - 0.05
    fin = b[-1]["f"] + 0.25
    if k + 1 < len(bloques):
        fin = min(fin, bloques[k + 1][0]["i"] - 0.05)
    CUES.append((ini, fin, " ".join(x["p"] for x in b)))


def hms(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


(CARPETA / ("subtitulos.srt" if VERSION == "corta" else f"subtitulos_{VERSION}.srt")).write_text("\n".join(f"{k + 1}\n{hms(a)} --> {hms(b)}\n{t}\n" for k, (a, b, t) in enumerate(CUES)),
                                        encoding="utf-8")
print(f"Subtítulos: {len(CUES)} bloques -> reel/subtitulos_{VERSION}.srt")

# ============================================================
# PASO 3.3: datos de cada escena (todos de la base; ninguno con nombres)
# ============================================================
mov = pd.read_csv(TAREA / "datos" / "procesados" / "movimientos_analisis.csv", dtype=str,
                  usecols=["en_analisis_principal", "tipo_movimiento", "fecha_publicacion"])
mov = mov[(mov["en_analisis_principal"] == "True") & mov["tipo_movimiento"].isin(["designación", "nombramiento", "encargatura"])]
pub = pd.to_datetime(mov["fecha_publicacion"], dayfirst=True)
DIA0, DIA1 = pd.Timestamp("2022-11-01"), pd.Timestamp("2026-10-29")
por_dia = pub.dt.normalize().value_counts().reindex(pd.date_range(DIA0, DIA1), fill_value=0)
por_mes = pub[(pub >= DIA0) & (pub <= DIA1)].dt.to_period("M").value_counts().sort_index()
gob = pd.read_csv(IND / "gobiernos.csv", parse_dates=["inicio"])
CORTO = {"CASTILLO": "Castillo", "BOLUARTE": "Boluarte", "JERI": "Jerí", "BALCAZAR": "Balcázar", "FUJIMORI": "Fujimori"}
gob["corto"] = [next((v for k, v in CORTO.items() if k in p), p.title()) for p in gob["presidente"]]
armado = pd.read_csv(IND / "armado_equipo_resumen.csv").set_index("familia")["dias_mediana"]
BARRAS_ARMADO = [("Secretaría general", armado["Secretaría General"]), ("Gabinete de asesores", armado["Gabinete de asesores"]),
                 ("Asesoría jurídica", armado["Asesoría jurídica"]), ("Administración", armado["Administración"]),
                 ("Recursos humanos", armado["Recursos humanos"]), ("Viceministros", armado["Viceministerio"]),
                 ("Planeamiento", armado["Planeamiento y presupuesto"])]
pt = pd.read_csv(IND / "puestos_titulares.csv")
puesto15 = pt[pt["ambito"] != "subprefectos y prefectos"].sort_values("titulares", ascending=False).iloc[0]
per = pd.read_csv(IND / "periodos_titulares.csv", parse_dates=["inicio", "fin"])
PERIODOS15 = per[per["puesto"] == puesto15["puesto"]].sort_values("inicio")[["inicio", "fin"]].values.tolist()
rot = pd.read_csv(IND / "ranking_rotacion.csv").iloc[0]
tray = pd.read_csv(IND / "trayectorias.csv", parse_dates=["inicio", "fin"])
CARGOS_ROT = tray[tray["id_persona"] == rot["id_persona"]].sort_values("inicio")[["inicio", "fin"]].values.tolist()
perm = pd.read_csv(IND / "ranking_permanencia.csv", parse_dates=["inicio", "fin"])
perm = perm[perm["tipo_de_jefe"] == "ministros"].sort_values("jefes_que_llegaron", ascending=False).iloc[0]
lleg = pd.read_csv(IND / "llegadas_ministros.csv", parse_dates=["fecha_ref"])
MINISTROS_PERM = sorted(lleg[(lleg["institucion_del_cargo"] == perm["institucion_del_cargo"]) & (lleg["fecha_ref"] > perm["inicio"])
                             & (lleg["fecha_ref"] < perm["fin"])]["fecha_ref"])
genero = pd.read_csv(IND / "genero_jerarquia.csv").set_index("jerarquia_puesto")["pct_mujeres"]
NIVELES = [("Ministro", "J1"), ("Viceministro", "J2"), ("Secretario general o titular", "J3"), ("Director general", "J4"),
           ("Asesor", "J5"), ("Jefe de unidad", "J6"), ("Subunidad", "J7")]
MUJERES = [(n, float(genero[[i for i in genero.index if i.startswith(j)][0]])) for n, j in NIVELES]
dash = json.loads((TAREA / "web" / "data" / "dashboard.json").read_text(encoding="utf-8"))
RED = dash["red"]
SEG = RED["seg"]
ARRASTRE = RED["resumen"]["arrastre_pct"], RED["resumen"]["arrastre_pct_azar"]
CODIGOS = [n[0] for n in RED["nodos"]]
random.Random(7).shuffle(CODIGOS)
cont = pd.read_csv(IND / "continuidad_gobiernos.csv")
PCT_ELENCO = float(cont[(cont["grupo"] == "todos")].iloc[-1]["pct_con_cargo_previo"])
print(f"Datos: {int((por_dia > 0).sum())} días con designaciones de {len(por_dia)} | normas {dash['meta']['normas']} | "
      f"puesto con {int(puesto15['titulares'])} jefes | rotación {int(rot['cargos_en_12_meses'])} en 12 meses | "
      f"permanencia: {len(MINISTROS_PERM)} ministros | elenco {PCT_ELENCO} % | arrastre {ARRASTRE}")

# Captura del dashboard para el cierre (servidor local; si no está, se usa la que exista)
CAPTURA = REC / "dashboard_movil.png"
if not CAPTURA.exists():
    chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    tmp = REC / "_captura.png"
    subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2",
                    "--virtual-time-budget=9000", "--window-size=500,1100", f"--screenshot={tmp}",
                    "http://127.0.0.1:8765/index.html?tema=oscuro"], capture_output=True)
    if tmp.exists():
        Image.open(tmp).convert("RGB").crop((0, 0, 1000, 2100)).save(CAPTURA)
        tmp.unlink()


# ============================================================
# PASO 3.4: escenas (cada una dibuja un cuadro según el tiempo dentro de la escena)
# ============================================================
def x_fecha(fecha, x0=100, x1=980):
    return x0 + (x1 - x0) * (pd.Timestamp(fecha) - DIA0).days / (DIA1 - DIA0).days


def eje_anios(d, y, x0=100, x1=980):
    for anio in range(2023, 2027):
        x = x_fecha(f"{anio}-01-01", x0, x1)
        d.line([(x, y - 8), (x, y + 8)], fill=T3, width=2)
        texto(d, (x, y + 14), str(anio), "r", 26, T3, "ma")


def escena_gancho(d, t, dur):
    texto(d, (80, 250), "¿Cambia todo para que nada cambie?", "b", 54, T1, ancho=900)
    n = int(suave(t / (dur * 0.85)) * len(por_dia))
    cols, celda, hueco, y0 = 40, 19, 3, 420
    x0 = (W - (cols * (celda + hueco) - hueco)) // 2
    for k, c in enumerate(por_dia.values[:n]):
        fila, col = divmod(k, cols)
        color = (38, 38, 36) if c == 0 else RAMPA[min(6, int(math.log2(c)))]
        x, y = x0 + col * (celda + hueco), y0 + fila * (celda + hueco)
        d.rectangle([x, y, x + celda, y + celda], fill=color)
    texto(d, (x0, y0 - 34), "nov 2022", "r", 24, T3)
    texto(d, (W - x0, y0 + 37 * (celda + hueco) + 8), "oct 2026", "r", 24, T3, "ra")
    if t > dur * 0.35:
        a = suave((t - dur * 0.35) / 0.6)
        texto(d, (W // 2, 1262), "99 de cada 100 días", "b", 72, mezclar(FONDO, T1, a), "ma")
        texto(d, (W // 2, 1350), "hubo designaciones · unas 15 por día", "r", 36, mezclar(FONDO, T2, a), "ma")


def escena_alcance(d, t, dur):
    v = int(suave(t / (dur * 0.6)) * dash["meta"]["normas"])
    texto(d, (W // 2, 330), miles(v), "b", 160, T1, "ma")
    texto(d, (W // 2, 530), "normas de personal de El Peruano", "r", 38, T2, "ma")
    y = 820
    eje_anios(d, y - 60)
    for k, g in gob.iterrows():
        if t < dur * (0.15 + 0.13 * k):
            continue
        a = pd.Timestamp(max(g["inicio"], DIA0))
        b = gob["inicio"].iloc[k + 1] if k + 1 < len(gob) else DIA1
        xa, xb = x_fecha(a), x_fecha(b)
        d.rectangle([xa, y, xb - 2, y + 60], fill=AZUL if k % 2 == 0 else RAMPA[2])
        xm = (xa + xb) / 2
        if xb - xa > 120:
            texto(d, (xm, y + 80), g["corto"], "b", 30, T1, "ma")
        else:                                       # gobiernos cortos: rótulo escalonado con una línea guía
            baja = {0: 70, 2: 70, 3: 120, 4: 170}.get(k, 70)
            d.line([(xm, y + 62), (xm, y + 60 + baja)], fill=T3, width=2)
            ancla = "la" if k == 0 else "ra"
            texto(d, (xm + (6 if k == 0 else 6), y + 64 + baja), g["corto"], "b", 28, T1, ancla)
    if t > dur * 0.5:
        a = suave((t - dur * 0.5) / 0.5)
        texto(d, (W // 2, 1130), "5 presidentes en 4 años", "b", 64, mezclar(FONDO, T1, a), "ma")
        texto(d, (W // 2, 1215), "noviembre de 2022 a octubre de 2026", "r", 36, mezclar(FONDO, T2, a), "ma")


ORDEN_ELENCO = list(range(100))
random.Random(3).shuffle(ORDEN_ELENCO)
DESTINO = list(range(100))
random.Random(11).shuffle(DESTINO)


def escena_elenco(d, t, dur):
    texto(d, (W // 2, 270), f"{round(PCT_ELENCO)} %", "b", 150, NARANJA, "ma")
    texto(d, (W // 2, 455), "de quienes designó el gobierno de julio de 2026", "r", 34, T2, "ma")
    texto(d, (W // 2, 500), "ya había tenido un cargo en el Estado", "b", 36, T1, "ma")
    encendidos = int(suave(t / (dur * 0.45)) * 50)
    ya = set(ORDEN_ELENCO[:50])
    mover = suave((t - dur * 0.55) / (dur * 0.35)) if t > dur * 0.55 else 0
    paso, x0, y0 = 70, W // 2 - 315, 600
    for k in range(100):
        f0, c0 = divmod(k, 10)
        x, y = x0 + c0 * paso, y0 + f0 * paso
        if mover > 0:                                   # "cambian de puesto": todos se reacomodan; los naranjas siguen ahí
            f1, c1 = divmod(DESTINO[k], 10)
            x, y = x + (x0 + c1 * paso - x) * mover, y + (y0 + f1 * paso - y) * mover
        color = NARANJA if (k in ya and ORDEN_ELENCO.index(k) < encendidos) else GRIS
        d.ellipse([x - 24, y - 24, x + 24, y + 24], fill=color)
    if t > dur * 0.55:
        a = suave((t - dur * 0.55) / 0.6)
        texto(d, (W // 2, 1320), "Cambian de puesto, pero se quedan", "b", 52, mezclar(FONDO, T1, a), "ma")


def escena_olas(d, t, dur):
    texto(d, (80, 300), "Designaciones por mes", "b", 46, T1)
    x0, x1, y0, y1 = 100, 980, 420, 1040
    vals = por_mes.values
    vmax = vals.max() * 1.12
    d.line([(x0, y1), (x1, y1)], fill=T3, width=2)
    eje_anios(d, y1 + 4)
    for k, g in gob.iterrows():
        if g["inicio"] > DIA0:
            x = x_fecha(g["inicio"])
            for yy in range(y0, y1, 22):
                d.line([(x, yy), (x, yy + 11)], fill=GRIS, width=2)
    pts = [(x_fecha(p.to_timestamp() + pd.Timedelta(days=14)), y1 - (y1 - y0) * v / vmax) for p, v in zip(por_mes.index, vals)]
    n = suave(t / (dur * 0.8)) * (len(pts) - 1)
    k = int(n)
    visibles = pts[: k + 1]
    if k + 1 < len(pts):
        f = n - k
        visibles.append((pts[k][0] + (pts[k + 1][0] - pts[k][0]) * f, pts[k][1] + (pts[k + 1][1] - pts[k][1]) * f))
    if len(visibles) > 1:
        d.line(visibles, fill=AZUL, width=7, joint="curve")
    picos = sorted(range(len(vals)), key=lambda i: -vals[i])
    elegidos = []
    for i in picos:
        if all(abs(i - j) > 4 for j in elegidos):
            elegidos.append(i)
        if len(elegidos) == 2:
            break
    MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "set", "oct", "nov", "dic"]
    for i in elegidos:
        if i <= k:
            x, y = pts[i]
            d.ellipse([x - 12, y - 12, x + 12, y + 12], fill=NARANJA)
            p = por_mes.index[i]
            texto(d, (x, y - 62), f"{MESES[p.month - 1]}-{p.year}", "b", 30, T1, "ma")
    if t > dur * 0.45:
        a = suave((t - dur * 0.45) / 0.6)
        texto(d, (W // 2, 1160), "Los cambios llegan en olas", "b", 60, mezclar(FONDO, T1, a), "ma")
        texto(d, (W // 2, 1245), "con cada presidente o ministro nuevo", "r", 36, mezclar(FONDO, T2, a), "ma")


def escena_control(d, t, dur):
    texto(d, (80, 290), "Días hasta que cambia cada cargo", "b", 48, T1)
    texto(d, (80, 355), "cuando llega un ministro · mediana de 168 llegadas", "r", 30, T2)
    xb0, xb1, maximo = 470, 900, max(v for _, v in BARRAS_ARMADO)
    for k, (nombre, v) in enumerate(BARRAS_ARMADO):
        y = 460 + k * 100
        a = suave((t - 0.12 * k) / 0.8)
        texto(d, (80, y + 6), nombre, "b" if k == 0 else "r", 34, T1 if k == 0 else T2)
        largo = (xb1 - xb0) * v / maximo * a
        if largo > 2:
            d.rounded_rectangle([xb0, y, xb0 + largo, y + 48], radius=6, fill=NARANJA if k == 0 else AZUL)
        if a > 0.95:
            texto(d, (xb0 + largo + 14, y + 4), f"{v:g}".replace(".", ","), "b", 34, T1)
    if t > dur * 0.5:
        a = suave((t - dur * 0.5) / 0.6)
        texto(d, (W // 2, 1230), "Primero, el control administrativo", "b", 52, mezclar(FONDO, T1, a), "ma")


def escena_rotacion(d, t, dur):
    texto(d, (80, 290), f"Un mismo puesto, {int(puesto15['titulares'])} jefes en 4 años", "b", 52, T1, ancho=900)
    texto(d, (80, 430), "jefatura de una oficina de un ministerio", "r", 32, T2)
    y = 620
    eje_anios(d, y - 50)
    n = int(suave(t / (dur * 0.75)) * len(PERIODOS15))
    for k, (a, b) in enumerate(PERIODOS15[:n]):
        xa, xb = x_fecha(max(a, DIA0)), x_fecha(min(b, DIA1))
        d.rectangle([xa, y, max(xa + 3, xb - 3), y + 110], fill=AZUL if k % 2 == 0 else RAMPA[6])
    texto(d, (W // 2, 790), str(min(n, int(puesto15["titulares"]))), "b", 170, T1, "ma")
    texto(d, (W // 2, 1000), "jefes distintos", "r", 40, T2, "ma")
    if t > dur * 0.4:
        a = suave((t - dur * 0.4) / 0.6)
        texto(d, (W // 2, 1180), "Una alarma para recursos humanos", "b", 56, mezclar(FONDO, NARANJA, a), "ma")


def escena_trayectorias(d, t, dur):
    texto(d, (80, 290), f"Quien más rota: {int(rot['cargos'])} cargos, {int(rot['cargos_en_12_meses'])} en un solo año", "b", 42, T1, ancho=900)
    y = 450
    eje_anios(d, y + 90)
    n = int(suave(t / (dur * 0.5)) * len(CARGOS_ROT))
    for a, b in CARGOS_ROT[:n]:
        xa, xb = x_fecha(max(a, DIA0)), x_fecha(min(b, DIA1))
        d.rounded_rectangle([xa, y, max(xa + 6, xb - 3), y + 70], radius=6, fill=AZUL)
    texto(d, (80, 690), f"Quien más permanece: el mismo puesto, {len(MINISTROS_PERM)} ministros", "b", 42, T1, ancho=900)
    y2 = 850
    eje_anios(d, y2 + 90)
    if t > dur * 0.3:
        a = suave((t - dur * 0.3) / (dur * 0.45))
        xa, xb = x_fecha(max(perm["inicio"], DIA0)), x_fecha(min(perm["fin"], DIA1))
        d.rounded_rectangle([xa, y2, xa + (xb - xa) * a, y2 + 70], radius=6, fill=NARANJA)
        for m in MINISTROS_PERM:                    # cada marca: llegó un ministro nuevo y la persona siguió en su puesto
            xm = x_fecha(m)
            if xm <= xa + (xb - xa) * a:
                d.polygon([(xm - 9, y2 - 26), (xm + 9, y2 - 26), (xm, y2 - 8)], fill=T1)
    if t > dur * 0.6:
        a = suave((t - dur * 0.6) / 0.5)
        texto(d, (W // 2, 1130), "Unos rotan cada pocos meses;", "b", 48, mezclar(FONDO, T1, a), "ma")
        texto(d, (W // 2, 1195), f"otros ven pasar {len(MINISTROS_PERM)} ministros sin moverse", "b", 48, mezclar(FONDO, T1, a), "ma")
        texto(d, (W // 2, 1270), "cada marca blanca: llega un ministro nuevo", "r", 30, mezclar(FONDO, T3, a), "ma")


def flecha(d, a, b, ra, rb, color, ancho, punteada=False):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    p0 = (a[0] + ux * (ra + 8), a[1] + uy * (ra + 8))
    p1 = (b[0] - ux * (rb + 10), b[1] - uy * (rb + 10))
    if punteada:
        largo = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        for s in np.arange(0, largo, 26):
            e = min(s + 14, largo)
            d.line([(p0[0] + ux * s, p0[1] + uy * s), (p0[0] + ux * e, p0[1] + uy * e)], fill=color, width=ancho)
    else:
        d.line([p0, p1], fill=color, width=ancho)
        px, py = -uy, ux
        d.polygon([(p1[0] + ux * 6, p1[1] + uy * 6), (p1[0] - ux * 26 + px * 14, p1[1] - uy * 26 + py * 14),
                   (p1[0] - ux * 26 - px * 14, p1[1] - uy * 26 - py * 14)], fill=color)


def escena_redes(d, t, dur):
    texto(d, (80, 290), "Detrás de cada designación", "b", 54, T1, ancho=900)
    A, B, C, r = (540, 560), (290, 930), (790, 930), 64
    if t > dur * 0.12:
        flecha(d, A, B, r, r, T3, 5, True)
        flecha(d, A, C, r, r, T3, 5, True)
        texto(d, (330, 690), "se conocen", "r", 30, T3, "ma")
        texto(d, (752, 690), "se conocen", "r", 30, T3, "ma")
    if t > dur * 0.35:
        flecha(d, B, C, r, r, T1, 7)
        texto(d, (540, 975), "firma la designación", "b", 32, T1, "ma")
    for p, color, letra, rotulo in [(A, RAMPA[5], "A", "recomienda"), (B, NARANJA, "B", "jefe que firma"), (C, AZUL, "C", "designado")]:
        d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=color)
        texto(d, (p[0], p[1] - 34), letra, "b", 56, (255, 255, 255), "ma")
        texto(d, (p[0], p[1] + r + 14), rotulo, "r", 30, T2, "ma")
    if t > dur * 0.5:
        a = suave((t - dur * 0.5) / 0.6)
        texto(d, (W // 2, 1150), "Detrás suele haber referencias:", "b", 50, mezclar(FONDO, T1, a), "ma")
        texto(d, (W // 2, 1215), "alguien recomienda, otro firma", "b", 50, mezclar(FONDO, NARANJA, a), "ma")
        texto(d, (W // 2, 1295), "La norma solo registra la firma", "r", 32, mezclar(FONDO, T3, a), "ma")


NODOS = {n[0]: n for n in RED["nodos"]}
GRUPOS_ORDEN = sorted({n[3] for n in RED["nodos"]})


def escena_grafos(d, t, dur):
    texto(d, (80, 290), "Grupos que se desplazan juntos", "b", 52, T1, ancho=900)
    asp = RED["aspecto"]
    caja = 720
    ancho = min(900, caja / asp)
    alto = ancho * asp
    zoom = 1 + 0.12 * min(t / dur, 1)
    cx, cy = W / 2, 400 + caja / 2
    def pos(n):
        x = 80 + (W - 160 - ancho) / 2 + n[1] * ancho
        y = 400 + (caja - alto) / 2 + n[2] * ancho
        return cx + (x - cx) * zoom, cy + (y - cy) * zoom
    visibles = set(GRUPOS_ORDEN[: max(1, int(suave(t / (dur * 0.6)) * len(GRUPOS_ORDEN)))])
    for a, b, inst, _ in RED["aristas"]:
        na, nb = NODOS.get(a), NODOS.get(b)
        if na and nb and na[3] == nb[3] and na[3] in visibles:
            d.line([pos(na), pos(nb)], fill=(92, 91, 86), width=2 if inst >= 3 else 1)
    for n in RED["nodos"]:
        if n[3] not in visibles:
            continue
        x, y = pos(n)
        r = 4 + math.sqrt(n[5]) * 2.2 if n[4] == "jefe" else 4
        d.ellipse([x - r, y - r, x + r, y + r], fill={"jefe": NARANJA, "puente": VERDE}.get(n[4], AZUL))
    if t > dur * 0.35:
        a = suave((t - dur * 0.35) / 0.6)
        texto(d, (W // 2, 1250), "1 de cada 6 sigue a su jefe", "b", 54, mezclar(FONDO, T1, a), "ma")
        texto(d, (W // 2, 1325), "cuando él cambia de institución · por azar, 1 de cada 50", "r", 30, mezclar(FONDO, T2, a), "ma")


def escena_mujeres(d, t, dur):
    texto(d, (80, 290), "Mujeres según el nivel del cargo", "b", 50, T1)
    xb0, xb1 = 470, 930
    x50 = xb0 + (xb1 - xb0) * 50 / 60
    for yy in range(410, 1130, 24):
        d.line([(x50, yy), (x50, yy + 12)], fill=T3, width=2)
    texto(d, (x50, 375), "paridad", "r", 26, T3, "ma")
    for k, (nombre, v) in enumerate(MUJERES):
        y = 430 + k * 100
        a = suave((t - 0.06 * k) / 0.6)
        texto(d, (80, y + 4), nombre, "r", 32, T1, ancho=380, interlinea=1.0)
        largo = (xb1 - xb0) * v / 60 * a
        d.rounded_rectangle([xb0, y, xb0 + max(largo, 4), y + 46], radius=6, fill=NARANJA if k == 0 else AZUL)
        if a > 0.95:
            texto(d, (xb0 + largo + 12, y + 2), f"{round(v)} %", "b", 32, T1)
    if t > dur * 0.3:
        a = suave((t - dur * 0.3) / 0.5)
        texto(d, (W // 2, 1200), "Cuanto más alto el cargo,", "b", 52, mezclar(FONDO, T1, a), "ma")
        texto(d, (W // 2, 1268), "menos mujeres", "b", 52, mezclar(FONDO, NARANJA, a), "ma")


CAPTURA_IMG = None
if CAPTURA.exists():
    im = Image.open(CAPTURA).convert("RGB")
    ancho_c = 700
    CAPTURA_IMG = im.resize((ancho_c, int(im.height * ancho_c / im.width)))
    CAPTURA_IMG = CAPTURA_IMG.crop((0, 0, ancho_c, min(CAPTURA_IMG.height, 760)))


def escena_cierre(d, t, dur, lienzo):
    f1, f2 = dur * 0.3, dur * 0.62
    if t < f1:                                        # 1) códigos anónimos en lugar de nombres
        rng = random.Random(int(t * 4))
        for k in range(36):
            f, c = divmod(k, 4)
            a = suave((t - 0.03 * k) / 0.5)
            texto(d, (170 + c * 250, 330 + f * 80), CODIGOS[k], "b", 40, mezclar(FONDO, RAMPA[5] if rng.random() > 0.2 else T3, a), "ma")
        texto(d, (W // 2, 1110), "Nombres anonimizados", "b", 60, T1, "ma")
        texto(d, (W // 2, 1190), "buscamos estructuras y patrones", "r", 40, T2, "ma")
    elif t < f2:                                      # 2) el dashboard y su enlace
        if CAPTURA_IMG is not None:
            x0 = (W - CAPTURA_IMG.width) // 2
            d.rounded_rectangle([x0 - 10, 290, x0 + CAPTURA_IMG.width + 10, 300 + CAPTURA_IMG.height + 10], radius=22, fill=SUPERFICIE)
            lienzo.paste(CAPTURA_IMG, (x0, 300))
        texto(d, (W // 2, 1110), "Explora el tablero", "b", 60, T1, "ma")
        texto(d, (W // 2, 1190), URL, "b", 32, RAMPA[5], "ma")
    else:                                             # 3) créditos
        texto(d, (80, 300), "¿Cambia todo para que nada cambie?", "b", 50, T1, ancho=900)
        lineas = ["Datos: Diario Oficial El Peruano, noviembre de 2022 a octubre de 2026",
                  "Análisis y dashboard: Tarea 3 · Python Intermedio (D2CML)",
                  "Narración: voz propia del autor (no generada con IA)",
                  "Música: «Clean Soul», Kevin MacLeod (incompetech.com) · CC BY 4.0",
                  "Guion del autor; edición y gráficos con apoyo de IA (Claude)",
                  "Personas con códigos anónimos: los patrones no implican irregularidades"]
        y = 470
        for l in lineas:
            texto(d, (80, y), l, "r", 32, T2, ancho=900)
            y += 92
        texto(d, (80, y + 20), URL, "b", 32, RAMPA[5])


DIBUJO = {"gancho": escena_gancho, "alcance": escena_alcance, "elenco": escena_elenco, "olas": escena_olas,
          "control": escena_control, "rotacion": escena_rotacion, "trayectorias": escena_trayectorias,
          "redes": escena_redes, "grafos": escena_grafos, "mujeres": escena_mujeres}


def subtitulo(lienzo, t):
    cue = next((c for c in CUES if c[0] <= t < c[1]), None)
    if not cue:
        return
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dc = ImageDraw.Draw(capa)
    f = fuente("b", 44)
    palabras_c, lineas, actual = cue[2].split(), [], ""
    for p in palabras_c:
        prueba = f"{actual} {p}".strip()
        if dc.textlength(prueba, font=f) <= 860 or not actual:
            actual = prueba
        else:
            lineas.append(actual)
            actual = p
    lineas.append(actual)
    alto_l = 56
    y1 = 1560
    y0 = y1 - alto_l * len(lineas) - 24
    ancho_max = max(dc.textlength(l, font=f) for l in lineas)
    dc.rounded_rectangle([W / 2 - ancho_max / 2 - 24, y0, W / 2 + ancho_max / 2 + 24, y1], radius=14, fill=(0, 0, 0, 185))
    for k, l in enumerate(lineas):
        dc.text((W / 2, y0 + 12 + k * alto_l), l, font=f, fill=(255, 255, 255), anchor="ma")
    lienzo.alpha_composite(capa)


FONDO_IMG = Image.new("RGBA", (W, H), FONDO + (255,))


def cuadro(t):
    """Antes: un instante t (segundos) | Después: la imagen de ese cuadro (escena + rótulo superior + subtítulo)"""
    nombre, a, b = next((e for e in ESCENAS if e[1] <= t < e[2]), ESCENAS[-1])
    capa = FONDO_IMG.copy()
    dc = ImageDraw.Draw(capa)
    if nombre == "cierre":
        escena_cierre(dc, t - a, b - a, capa)
    else:
        DIBUJO[nombre](dc, t - a, b - a)
    entrada = suave((t - a) / 0.3)                     # cada escena aparece con un fundido corto
    lienzo = Image.blend(FONDO_IMG, capa, entrada) if entrada < 1 else capa
    texto(ImageDraw.Draw(lienzo), (80, 200), "DESIGNACIONES EN EL ESTADO PERUANO · 2022-2026", "b", 26, T3)
    subtitulo(lienzo, t)
    return lienzo.convert("RGB")


# Modo de prueba: dos cuadros por escena en una carpeta, sin armar el video
import sys
if "--prueba" in sys.argv:
    destino = Path(sys.argv[sys.argv.index("--prueba") + 1])
    destino.mkdir(parents=True, exist_ok=True)
    for nombre, a, b in ESCENAS:
        for frac in (0.45, 0.95):
            cuadro(a + (b - a) * frac).save(destino / f"{nombre}_{int(frac * 100)}.png")
    print("Cuadros de prueba en", destino)
    raise SystemExit

# ============================================================
# PASO 3.5: audio (voz + música baja) y video
# ============================================================
mezcla = VOZ / f"_mezcla_{VERSION}.wav"
retraso = int(INICIO_VOZ * 1000)
subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(VOZ / f"narracion_{VERSION}.wav"), "-i", str(MUSICA),
                "-filter_complex",
                f"[1:a]atrim=0:{DURACION:.2f},asetpts=PTS-STARTPTS,aresample=48000,loudnorm=I=-16:TP=-2,volume=-17dB,"
                f"afade=t=in:d=1.5,afade=t=out:st={DURACION - 2.5:.2f}:d=2.5[m];"
                f"[0:a]adelay={retraso}|{retraso},apad=whole_dur={DURACION:.2f}[v];"
                f"[v][m]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95[a]",
                "-map", "[a]", "-ar", "48000", "-ac", "2", str(mezcla)], check=True)
# Extracto de la música usada (para el repositorio, con su licencia en recursos/CREDITOS.md)
subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(MUSICA), "-t", f"{DURACION:.2f}", "-c:a", "libmp3lame", "-b:a", "192k",
                str(REC / "musica_clean_soul_extracto.mp3")], check=True)

salida = CARPETA / ("reel.mp4" if VERSION == "corta" else f"reel_{VERSION}.mp4")   # la corta es la entregada
proc = subprocess.Popen([FFMPEG, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                         "-i", "-", "-i", str(mezcla), "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                         "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(salida)], stdin=subprocess.PIPE)
total = int(DURACION * FPS)
for k in range(total):
    t = k / FPS
    im = cuadro(t)
    if k == int(4.2 * FPS):
        im.save(CARPETA / "portada.png")
    proc.stdin.write(im.tobytes())
    if k % (FPS * 10) == 0:
        print(f"  cuadro {k}/{total}")
proc.stdin.close()
proc.wait()
mezcla.unlink()
print("Video:", salida, f"({salida.stat().st_size / 1e6:.1f} MB, {DURACION:.1f} s)")
