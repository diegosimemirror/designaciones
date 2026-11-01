# ============================================================
# Designaciones de El Peruano — Script 01: descargar el índice
# ------------------------------------------------------------
# Qué hace: pide a El Peruano, mes por mes, la lista de normas de
# designación, renuncia y conclusión (la "tabla de contenidos").
# Esta lista NO trae el nombre de la persona: eso se saca del PDF
# en el script 02.
#
# Uso (desde la carpeta tarea_3):
#   python scripts/01_descargar_indice.py 2022-11 2026-10
# Si el mes ya se bajó antes (archivo indice_AAAA-MM.json), se usa esa copia y no se
# vuelve a pedir: así el periodo ya descargado no cambia al ampliar hacia atrás.
# ============================================================

# --- Paquetes ---
# Todos vienen con Python o con Anaconda: no hay que instalar nada.
# sys: leer los meses que se escriben al ejecutar el script
import sys
# time: hacer una pausa entre consultas para no saturar el servidor
import time
# json: convertir la respuesta del servidor (texto JSON) en una lista de registros
import json
# base64: decodificar el enlace del PDF, que esconde el código de la norma
import base64
# pathlib: manejar rutas de carpetas y archivos sin preocuparse por "/" o "\"
from pathlib import Path
# calendar: saber cuántos días tiene cada mes (28, 29, 30 o 31)
import calendar
# requests: hacer la consulta por internet (como abrir una página, pero desde código)
import requests
# pandas: juntar todos los meses en una sola tabla, como una hoja de Excel
import pandas as pd

# --- Configuración ---
URL_INDICE = "https://diariooficial.elperuano.pe/Normas/LoadRenunciasFiltro"
# Nos identificamos con un nombre propio, sin hacernos pasar por un navegador
CABECERAS = {"User-Agent": "DesignacionesElPeruano/0.1 (proyecto academico)"}
PAUSA_SEGUNDOS = 2
CARPETA_TAREA = Path(__file__).resolve().parent.parent
CARPETA_CRUDOS = CARPETA_TAREA / "datos" / "crudos" / "indice"
CARPETA_PROCESADOS = CARPETA_TAREA / "datos" / "procesados"


# ============================================================
# PROCESO 1: Armar la lista de meses a consultar
# Insumo:    mes inicial y mes final ("2025-11", "2026-10")
# Resultado: lista de (año, mes), una por consulta
# ============================================================
def lista_de_meses(inicio, fin):
    """Antes: "2025-11", "2026-10" | Después: [(2025, 11), (2025, 12), ..., (2026, 10)]"""
    anio, mes = map(int, inicio.split("-"))
    anio_fin, mes_fin = map(int, fin.split("-"))
    meses = []
    while (anio, mes) <= (anio_fin, mes_fin):
        meses.append((anio, mes))
        mes += 1
        if mes == 13:
            anio, mes = anio + 1, 1
    return meses


# ============================================================
# PROCESO 2: Descargar el índice de un mes
# Insumo:    (año, mes)
# Resultado: archivo crudo indice_AAAA-MM.json, sin ningún cambio
# ============================================================
def descargar_mes(anio, mes):
    """Antes: (2026, 3) | Después: lista de registros del mes y su copia en disco"""
    archivo = CARPETA_CRUDOS / f"indice_{anio}-{mes:02d}.json"
    # Si la copia ya existe, se lee del disco (json.loads: texto JSON -> lista de registros)
    if archivo.exists():
        return json.loads(archivo.read_text(encoding="utf-8"))
    ultimo_dia = calendar.monthrange(anio, mes)[1]
    parametros = {"cddesde": f"01/{mes:02d}/{anio}",
                  "cdhasta": f"{ultimo_dia:02d}/{mes:02d}/{anio}"}
    for intento in (1, 2):
        respuesta = requests.get(URL_INDICE, params=parametros,
                                 headers=CABECERAS, timeout=60)
        # Si el servidor falla, devuelve una página HTML de error en vez de JSON
        if respuesta.ok and respuesta.text.lstrip().startswith("["):
            registros = respuesta.json()
            archivo.write_text(respuesta.text, encoding="utf-8")
            return registros
        print(f"   intento {intento} falló ({len(respuesta.text)} bytes); reintento...")
        time.sleep(PAUSA_SEGUNDOS * 5)
    raise RuntimeError(f"No se pudo descargar {anio}-{mes:02d}")


# ============================================================
# PROCESO 3: Sacar el código de la norma del enlace PDF
# Insumo:    enlace ...DescargaIN.asp?Referencias=MjUzODg0MF8yMjAyNjA3MzA=
# Resultado: código "2538840-2", el mismo que aparece al pie de la norma en el PDF
# ============================================================
def codigo_desde_enlace(enlace_pdf):
    """Antes: enlace con texto en base64 | Después: "2538840-2" (id_norma-orden)"""
    referencia = enlace_pdf.split("Referencias=")[1]
    texto = base64.b64decode(referencia).decode()  # "2538840_220260730"
    id_norma, resto = texto.split("_")
    orden = resto[:-8]                             # los últimos 8 caracteres son la fecha
    return f"{id_norma}-{orden}"


# ============================================================
# PROCESO 4: Juntar todos los meses en una sola tabla
# Insumo:    registros de cada mes
# Resultado: datos/procesados/indice_normas.csv (una fila por registro del índice)
# ============================================================
def main():
    inicio, fin = sys.argv[1], sys.argv[2]
    CARPETA_CRUDOS.mkdir(parents=True, exist_ok=True)
    CARPETA_PROCESADOS.mkdir(parents=True, exist_ok=True)

    todos = []
    for anio, mes in lista_de_meses(inicio, fin):
        registros = descargar_mes(anio, mes)
        print(f"{anio}-{mes:02d}: {len(registros)} registros")
        for r in registros:
            r["mes_consulta"] = f"{anio}-{mes:02d}"
        todos.extend(registros)
        time.sleep(PAUSA_SEGUNDOS)

    # pd.DataFrame(): convierte la lista de registros en tabla
    #   Antes: lista de diccionarios | Después: tabla con una columna por campo
    indice = pd.DataFrame(todos)
    # Columna nueva (no se modifica ninguna existente): código de la norma
    indice["codigo_norma"] = indice["vchLinkPDF"].map(codigo_desde_enlace)

    # Verificación: tamaño y duplicados exactos (solo se informan, no se borran)
    print("\nTabla final (filas, columnas):", indice.shape)
    print("Filas repetidas exactas:", indice.duplicated().sum())
    print("Códigos de norma repetidos:", indice["codigo_norma"].duplicated().sum())

    # utf-8-sig: para que Excel muestre bien las tildes al abrir el CSV
    indice.to_csv(CARPETA_PROCESADOS / "indice_normas.csv",
                  index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
