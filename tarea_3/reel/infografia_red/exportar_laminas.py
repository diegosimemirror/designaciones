# ============================================================
# Exportar la infografía de la red como 3 imágenes PNG para el reel (1080 x 1920 cada una)
# Insumo:    reel/infografia_red/infografia_red.html
# Resultado: reel/infografia_red/lamina_1.png, lamina_2.png, lamina_3.png
# Uso (desde la carpeta tarea_3): python reel/infografia_red/exportar_laminas.py [otra_infografia.html]
#   (sin argumento exporta esta infografía; con argumento, las láminas quedan junto a ese HTML)
# ============================================================

# --- Paquetes ---
# subprocess: ejecutar Chrome sin ventana (modo "headless") para tomar la captura de la página
import subprocess
# sys: leer la ruta opcional de otra infografía
import sys
# pathlib: rutas de archivos
from pathlib import Path
# PIL (Pillow, viene con Anaconda): recortar la captura larga en 3 láminas
from PIL import Image

HTML = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent / "infografia_red.html"
CARPETA = HTML.parent
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
ANCHO, ALTO, LAMINAS = 1080, 1920, 3

# Paso 1: captura de la página completa (las 3 láminas una debajo de otra)
#   Antes: página HTML | Después: una imagen de 1080 x 5760
captura = CARPETA / "_captura_completa.png"
subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                f"--window-size={ANCHO},{ALTO * LAMINAS}", f"--screenshot={captura}",
                HTML.as_uri()], check=True, capture_output=True)

# Paso 2: recortar cada lámina
#   Antes: una imagen larga | Después: 3 imágenes de 1080 x 1920
imagen = Image.open(captura)
for i in range(LAMINAS):
    imagen.crop((0, i * ALTO, ANCHO, (i + 1) * ALTO)).save(CARPETA / f"lamina_{i + 1}.png")
    print("Guardada", CARPETA / f"lamina_{i + 1}.png")
captura.unlink()
