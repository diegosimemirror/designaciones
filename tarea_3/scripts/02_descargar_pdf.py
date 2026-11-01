# ============================================================
# Designaciones de El Peruano — Script 02: descargar los PDF
# ------------------------------------------------------------
# Qué hace: por cada norma de la lista (script 01c: índice + listado general), baja el PDF oficial,
# es decir, la página o páginas del diario donde salió publicada, y
# guarda su texto. Si se interrumpe, al volver a correrlo salta lo que
# ya bajó.
#
# Uso (desde la carpeta tarea_3):
#   python scripts/02_descargar_pdf.py          -> todas las normas pendientes
#   python scripts/02_descargar_pdf.py 3        -> solo 3 (para probar)
# ============================================================

# --- Paquetes ---
# sys: leer el límite opcional que se escribe al ejecutar el script
import sys
# time: pausa entre descargas y medición de cuánto tarda cada una
import time
# pathlib: manejar rutas de carpetas y archivos
from pathlib import Path
# requests: descargar cada PDF por internet
import requests
# pymupdf: leer el texto de un PDF. Se instaló una sola vez en esta computadora
#   (pip install pymupdf, el 30/10/2026); aquí solo se carga
import pymupdf
# pandas: leer el índice (CSV) y llevar el registro de descargas
import pandas as pd

# --- Configuración ---
CABECERAS = {"User-Agent": "DesignacionesElPeruano/0.1 (proyecto academico)"}
PAUSA_SEGUNDOS = 1
CARPETA_TAREA = Path(__file__).resolve().parent.parent
# Lista de normas: la unión de índice + listado general (script 01c); si aún no existe, el índice
ARCHIVO_LISTA = CARPETA_TAREA / "datos" / "procesados" / "normas_personal.csv"
ARCHIVO_INDICE = CARPETA_TAREA / "datos" / "procesados" / "indice_normas.csv"
CARPETA_TEXTOS = CARPETA_TAREA / "datos" / "crudos" / "textos"
ARCHIVO_REGISTRO = CARPETA_TAREA / "datos" / "crudos" / "registro_descargas.csv"
# Los PDF pesan ~1 MB cada uno: van fuera de la carpeta de Google Drive
# para no llenar la nube. El texto (lo que usamos) sí queda en el proyecto.
CARPETA_PDF = Path.home() / "designaciones_cache" / "pdf"


# ============================================================
# PROCESO 1: Elegir las normas pendientes
# Insumo:    normas_personal.csv (script 01c; desde nov-2022)
# Resultado: lista de normas cuyo texto todavía no está en disco
# ============================================================
def normas_pendientes(limite=None):
    """Antes: todas las normas de la lista | Después: solo las que faltan bajar"""
    if ARCHIVO_LISTA.exists():
        indice = pd.read_csv(ARCHIVO_LISTA, encoding="utf-8-sig")
    else:
        indice = pd.read_csv(ARCHIVO_INDICE, encoding="utf-8-sig").rename(columns={"vchLinkPDF": "enlace_pdf"})
    ya_bajadas = {p.stem for p in CARPETA_TEXTOS.glob("*.txt")}
    pendientes = indice[~indice["codigo_norma"].isin(ya_bajadas)]
    print(f"Índice: {len(indice)} normas | ya bajadas: {len(ya_bajadas)} "
          f"| pendientes: {len(pendientes)}")
    return pendientes.head(limite) if limite else pendientes


# ============================================================
# PROCESO 2: Descargar el PDF de una norma
# Insumo:    enlace oficial (vchLinkPDF)
# Resultado: archivo <codigo>.pdf en la carpeta local de PDF
# ============================================================
def descargar_pdf(enlace, ruta_pdf):
    """Antes: enlace web | Después: PDF en disco (o error si no llega un PDF)"""
    for intento in (1, 2, 3):
        try:
            respuesta = requests.get(enlace, headers=CABECERAS, timeout=90)
            # Todo PDF empieza con los caracteres "%PDF"; si no, llegó una página de error
            if respuesta.ok and respuesta.content[:4] == b"%PDF":
                ruta_pdf.write_bytes(respuesta.content)
                return len(respuesta.content)
            motivo = f"respuesta no es PDF ({len(respuesta.content)} bytes)"
        except requests.RequestException as error:
            motivo = f"error de conexión: {error}"
        time.sleep(PAUSA_SEGUNDOS * 10 * intento)
    raise RuntimeError(motivo)


# ============================================================
# PROCESO 3: Extraer el texto del PDF
# Insumo:    <codigo>.pdf (una o más páginas del diario, con varias normas)
# Resultado: <codigo>.txt con el texto de todas las páginas
# ============================================================
def extraer_texto(ruta_pdf, ruta_txt):
    """Antes: PDF | Después: texto plano; cada página se separa con el carácter \\f"""
    documento = pymupdf.open(ruta_pdf)
    paginas = [pagina.get_text() for pagina in documento]
    ruta_txt.write_text("\f".join(paginas), encoding="utf-8")
    return len(paginas)


# ============================================================
# PROCESO 4: Recorrer las normas y llevar un registro
# Insumo:    normas pendientes
# Resultado: textos en datos/crudos/textos/ y registro_descargas.csv
#            (una fila por intento: código, estado, páginas, peso, segundos)
# ============================================================
def main():
    limite = int(sys.argv[1]) if len(sys.argv) > 1 else None
    CARPETA_PDF.mkdir(parents=True, exist_ok=True)
    CARPETA_TEXTOS.mkdir(parents=True, exist_ok=True)

    pendientes = normas_pendientes(limite)
    inicio_total = time.time()
    for n, (codigo, enlace) in enumerate(
            zip(pendientes["codigo_norma"], pendientes["enlace_pdf"]), start=1):
        inicio = time.time()
        fila = {"codigo_norma": codigo, "estado": "ok", "paginas": None,
                "bytes": None, "segundos": None, "mensaje": ""}
        try:
            ruta_pdf = CARPETA_PDF / f"{codigo}.pdf"
            fila["bytes"] = descargar_pdf(enlace, ruta_pdf)
            fila["paginas"] = extraer_texto(ruta_pdf, CARPETA_TEXTOS / f"{codigo}.txt")
        except Exception as error:
            fila["estado"], fila["mensaje"] = "error", str(error)
        fila["segundos"] = round(time.time() - inicio, 1)

        # Se agrega una fila al registro en cada vuelta, para no perder nada si se corta
        pd.DataFrame([fila]).to_csv(ARCHIVO_REGISTRO, mode="a", index=False,
                                    header=not ARCHIVO_REGISTRO.exists(),
                                    encoding="utf-8")
        if n % 100 == 0 or n == len(pendientes) or fila["estado"] == "error":
            minutos = (time.time() - inicio_total) / 60
            print(f"{n}/{len(pendientes)} | {minutos:.0f} min | "
                  f"último: {codigo} {fila['estado']} {fila['mensaje']}", flush=True)
        time.sleep(PAUSA_SEGUNDOS)

    # Verificación final: cuántas salieron bien y cuántas con error
    registro = pd.read_csv(ARCHIVO_REGISTRO)
    print("\nResumen del registro:", registro["estado"].value_counts().to_dict())


if __name__ == "__main__":
    main()
