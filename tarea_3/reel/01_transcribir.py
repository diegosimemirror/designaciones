# ============================================================
# Reel · Paso 1: transcribir la narración (voz propia del autor) con marcas de tiempo por palabra
# Insumo:    reel/voz/relato.wav (grabación del autor; no se sube a GitHub)
# Resultado: reel/voz/transcripcion.json (segmentos y palabras con inicio y fin en segundos)
# Uso (entorno del reel, ver reel/README del paso a paso):
#   <venv_reel>/Scripts/python reel/01_transcribir.py
# ============================================================

# --- Paquetes ---
# json: guardar la transcripción
import json
# subprocess y tempfile: convertir el audio con ffmpeg a 16 kHz mono (lo que usa Whisper)
import subprocess
import tempfile
# soundfile: leer el audio convertido como números
import soundfile as sf
# imageio_ffmpeg: trae el programa ffmpeg (no hay que instalarlo aparte)
import imageio_ffmpeg
# pathlib: rutas
from pathlib import Path
# faster_whisper: reconocimiento de voz (Whisper large-v3-turbo, licencia MIT), corre en CPU
from faster_whisper import WhisperModel

CARPETA = Path(__file__).resolve().parent
AUDIO = CARPETA / "voz" / "relato.wav"
SALIDA = CARPETA / "voz" / "transcripcion.json"

# Paso 1.1: cargar el modelo (la primera vez lo descarga, ~1,6 GB)
#   int8 = números de 8 bits: más rápido en CPU con casi la misma precisión
modelo = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")

# Paso 1.2: transcribir en español con marcas de tiempo por palabra
#   Antes: audio | Después: lista de segmentos (frases) y palabras con su segundo de inicio y fin
#   (el audio se convierte antes con ffmpeg: la versión de PyAV instalada no es compatible con faster-whisper 1.2)
with tempfile.TemporaryDirectory() as tmp:
    wav16 = Path(tmp) / "voz_16k.wav"
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", str(AUDIO), "-ac", "1", "-ar", "16000", str(wav16)], check=True)
    audio, _ = sf.read(wav16, dtype="float32")
segmentos, info = modelo.transcribe(audio, language="es", word_timestamps=True, vad_filter=False, beam_size=5)
datos = []
for s in segmentos:
    datos.append({"inicio": round(s.start, 2), "fin": round(s.end, 2), "texto": s.text.strip(),
                  "palabras": [{"p": w.word.strip(), "i": round(w.start, 2), "f": round(w.end, 2)} for w in s.words]})
    print(f"[{s.start:6.2f} - {s.end:6.2f}] {s.text.strip()}")
SALIDA.write_text(json.dumps({"duracion": round(info.duration, 2), "segmentos": datos}, ensure_ascii=False, indent=1), encoding="utf-8")
print("Guardado:", SALIDA)
