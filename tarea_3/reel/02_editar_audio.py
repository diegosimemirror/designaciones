# ============================================================
# Reel · Paso 2: editar la narración para que entre en 75 segundos (requisito del issue: 45 a 75 s)
# Insumo:    reel/voz/relato.wav (voz propia del autor) y reel/voz/transcripcion.json (paso 1)
# Resultado: reel/voz/narracion_<version>.wav (voz editada, 48 kHz) y reel/voz/palabras_<version>.json (cada palabra con su
#            tiempo en el audio editado, para los subtítulos y para sincronizar las escenas)
# Método:
#   1) Cortes de contenido acordados (frases que pasan a la pantalla como texto).
#   2) Pausas largas (silencios de más de 0,55 s, medidos por la energía de la señal) se acortan a 0,4 s.
#   3) Todo un 8 % más rápido con ffmpeg "atempo" (cambia la velocidad sin cambiar el tono de la voz).
#   4) Volumen parejo para redes (-16 LUFS, filtro "loudnorm" de ffmpeg).
# ============================================================

# --- Paquetes ---
# json: leer la transcripción y guardar los tiempos nuevos
import json
# subprocess: llamar a ffmpeg (velocidad y volumen)
import subprocess
# pathlib: rutas
from pathlib import Path
# numpy: medir la energía del audio y cortar tramos
import numpy as np
# soundfile: leer y escribir archivos WAV
import soundfile as sf
# imageio_ffmpeg: trae el programa ffmpeg
import imageio_ffmpeg

CARPETA = Path(__file__).resolve().parent
VOZ = CARPETA / "voz"
# Criterio (revisado con el autor el 01/11/2026): solo se cortan FRASES COMPLETAS entre dos pausas naturales, nunca a
# mitad de frase; las pausas largas quedan en 0,4 s (ritmo natural). Dos versiones: "completa" y "corta".
import sys
VERSION = sys.argv[sys.argv.index("--version") + 1] if "--version" in sys.argv else "corta"   # versión entregada: corta
TEMPO = 1.08
PAUSA_MAX, PAUSA_DEJAR = 0.55, 0.40

# ============================================================
# Paso 2.1: leer el audio y la transcripción
#   Antes: WAV estéreo de 114,6 s | Después: señal mono (una sola voz) y la lista de palabras con sus tiempos
# ============================================================
audio, sr = sf.read(VOZ / "relato.wav", dtype="float32")
mono = audio.mean(axis=1) if audio.ndim == 2 else audio
palabras = [w for s in json.loads((VOZ / "transcripcion.json").read_text(encoding="utf-8"))["segmentos"] for w in s["palabras"]]

# ============================================================
# Paso 2.2: cortes de contenido (tiempos del audio original, en segundos)
# ============================================================
# Solo frases completas, con pausa natural antes y después (bordes en silencio, medidos por energía)
CORTES = [
    (48.55, 51.95, "Una alarma para cualquier área de recursos humanos. (frase completa; pasa a la pantalla)"),
    (98.20, 100.30, "Como se puede ver, (al inicio de la frase, después de una pausa)"),
]
if VERSION == "corta":
    # Frase completa entre dos pausas: "Se intentó representar esta dinámica a través de grafos en vista que el sistema de
    # referencias es el más usado cuando solamente se accede a través de designaciones a estos puestos." (pasa a la pantalla)
    CORTES.append((72.30, 91.40, "Se intentó representar esta dinámica ... a estos puestos."))
# Donde un corte une dos frases sin silencio natural entre ellas, se inserta una pausa (segundos, en el tiempo original)
PAUSA_INSERTADA = {}
inicio_voz, fin_voz = palabras[0]["i"] - 0.25, palabras[-1]["f"] + 0.5

# ============================================================
# Paso 2.3: pausas largas por energía (ventanas de 20 ms)
#   Antes: silencios de hasta 2,4 s entre frases | Después: cada silencio largo se recorta a 0,4 s
# ============================================================
ventana = int(0.02 * sr)
n = len(mono) // ventana
rms_db = 20 * np.log10(np.sqrt((mono[: n * ventana].reshape(n, ventana) ** 2).mean(axis=1)) + 1e-9)
umbral = np.percentile(rms_db, 10) + 10          # piso de ruido de la grabación + 10 dB
silencio = rms_db < umbral
tramos, k = [], 0
while k < n:
    if silencio[k]:
        j = k
        while j < n and silencio[j]:
            j += 1
        a, b = k * 0.02, j * 0.02
        if b - a > PAUSA_MAX:
            tramos.append((a + PAUSA_DEJAR / 2, b - PAUSA_DEJAR / 2, "pausa"))
        k = j
    else:
        k += 1
print(f"Umbral de silencio: {umbral:.1f} dB | pausas largas: {len(tramos)} (suman {sum(b - a for a, b, _ in tramos):.1f} s a recortar)")

# Unir todos los cortes y quedarse con lo que se conserva
cortes = sorted([(a, b) for a, b, _ in CORTES] + [(a, b) for a, b, _ in tramos if inicio_voz < a < fin_voz])
unidos = []
for a, b in cortes:
    if unidos and a <= unidos[-1][1]:
        unidos[-1] = (unidos[-1][0], max(unidos[-1][1], b))
    else:
        unidos.append((a, b))
conservar, t = [], inicio_voz
for a, b in unidos:
    if a > t:
        conservar.append((t, a))
    t = max(t, b)
conservar.append((t, fin_voz))

# ============================================================
# Paso 2.4: armar el audio editado, con fundidos de 15 ms en cada unión (evita chasquidos)
# ============================================================
fundido = int(0.015 * sr)
piezas = []
for a, b in conservar:
    p = mono[int(a * sr): int(b * sr)].copy()
    if len(p) > 2 * fundido:
        p[:fundido] *= np.linspace(0, 1, fundido)
        p[-fundido:] *= np.linspace(1, 0, fundido)
    piezas.append(p)
    if round(b, 2) in PAUSA_INSERTADA:
        piezas.append(np.zeros(int(PAUSA_INSERTADA[round(b, 2)] * sr), dtype="float32"))
editado = np.concatenate(piezas)
sf.write(VOZ / "_editado_1x.wav", editado, sr)
print(f"Duración sin pausas largas ni cortes: {len(editado) / sr:.1f} s")

# Paso 2.5: velocidad x1,10 (sin cambiar el tono) y volumen parejo; resultado en estéreo para el video
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", str(VOZ / "_editado_1x.wav"),
                "-af", f"atempo={TEMPO},loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "48000", "-ac", "2",
                str(VOZ / f"narracion_{VERSION}.wav")], check=True)
(VOZ / "_editado_1x.wav").unlink()
final, _ = sf.read(VOZ / f"narracion_{VERSION}.wav", dtype="float32")
print(f"Duración final de la voz: {len(final) / 48000:.1f} s")

# ============================================================
# Paso 2.6: tiempos de cada palabra en el audio final
#   Antes: tiempo original | Después: (tiempo acumulado de lo conservado) / 1,10. Palabras dentro de un corte se descartan
# ============================================================
def a_final(t):
    """Antes: segundo del audio original | Después: segundo del audio editado (un tiempo dentro de un corte va al borde)"""
    acumulado = 0.0
    for a, b in conservar:
        if t < a:
            return acumulado / TEMPO
        if t <= b:
            return (acumulado + t - a) / TEMPO
        acumulado += b - a + PAUSA_INSERTADA.get(round(b, 2), 0)
    return acumulado / TEMPO


def conservada(w):
    """Una palabra se conserva si NO cae dentro de un corte de contenido (las pausas recortadas son solo silencio;
    Whisper a veces marca el inicio de una palabra dentro de la pausa anterior)"""
    centro = (w["i"] + w["f"]) / 2
    return not any(a <= centro <= b for a, b, _ in CORTES)


salida = []
for w in palabras:
    if conservada(w):
        i, f = a_final(w["i"]), a_final(w["f"])
        salida.append({"p": w["p"], "i": round(i, 3), "f": round(max(f, i + 0.12), 3), "i_original": w["i"]})
(VOZ / f"palabras_{VERSION}.json").write_text(json.dumps({"duracion": round(len(final) / 48000, 2), "tempo": TEMPO,
                                                      "conservado": conservar, "palabras": salida}, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"Palabras conservadas: {len(salida)} de {len(palabras)}")
print(" ".join(w["p"] for w in salida))
