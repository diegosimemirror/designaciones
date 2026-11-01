# ============================================================
# Designaciones de El Peruano — Script 01b: listado general de normas
# ------------------------------------------------------------
# Por qué existe: el índice de designaciones (script 01) está incompleto.
# En noviembre de 2025 le faltaban Resoluciones Supremas de alto nivel
# (viceministros, jefes de organismos, Fuerzas Armadas, embajadores).
# El listado general de "Normas Legales" trae TODAS las normas de cada día
# con su sumilla; aquí se descarga día por día. El script 01c elige
# después las que son movimientos de personal.
#
# Uso (desde la carpeta tarea_3):
#   python scripts/01b_descargar_listado_general.py 2022-11-01 2026-10-30
# ============================================================

# --- Paquetes ---
# sys: leer las fechas que se escriben al ejecutar el script
import sys
# time: pausa entre consultas para no saturar el servidor
import time
# base64: armar el enlace oficial del PDF a partir del código y la fecha
import base64
# re: encontrar el código de la norma al final de los enlaces del formato anterior (hasta 2023)
import re
# datetime: recorrer el calendario día por día
from datetime import date, timedelta
# pathlib: manejar rutas de carpetas y archivos
from pathlib import Path
# requests: hacer la consulta por internet
import requests
# bs4 (BeautifulSoup): leer una página web (HTML) y encontrar sus partes por etiqueta,
#   como buscar celdas por su encabezado. Viene con Anaconda: no hay que instalarlo
from bs4 import BeautifulSoup
# pandas: juntar todos los días en una tabla
import pandas as pd

# --- Configuración ---
URL_LISTADO = "https://diariooficial.elperuano.pe/Normas/Filtro"
CABECERAS = {"User-Agent": "DesignacionesElPeruano/0.1 (proyecto academico)"}
PAUSA_SEGUNDOS = 2
CARPETA_TAREA = Path(__file__).resolve().parent.parent
CARPETA_CRUDOS = CARPETA_TAREA / "datos" / "crudos" / "listado_general"
ARCHIVO_SALIDA = CARPETA_TAREA / "datos" / "procesados" / "listado_general.csv"


# ============================================================
# PROCESO 1: Descargar el listado de un día
# Insumo:    una fecha (date)
# Resultado: archivo crudo AAAA-MM-DD.html, sin cambios
#            (si ya existe, no se vuelve a pedir: el script se puede reanudar)
# ============================================================
def descargar_dia(dia):
    """Antes: date(2025, 11, 5) | Después: texto HTML del listado de ese día"""
    archivo = CARPETA_CRUDOS / f"{dia.isoformat()}.html"
    if archivo.exists():
        return archivo.read_text(encoding="utf-8")
    fecha = dia.strftime("%d/%m/%Y")
    parametro = dia.strftime("%m%%2F%d%%2F%Y%%2000%%3A00%%3A00")  # formato que usa la página
    for intento in (1, 2, 3):
        try:
            respuesta = requests.post(f"{URL_LISTADO}?dateparam={parametro}",
                                      data={"cddesde": fecha, "cdhasta": fecha},
                                      headers=CABECERAS, timeout=90)
            if respuesta.ok:
                archivo.write_text(respuesta.text, encoding="utf-8")
                time.sleep(PAUSA_SEGUNDOS)
                return respuesta.text
        except requests.RequestException as error:
            print(f"   {fecha}: intento {intento} falló ({error})")
        time.sleep(PAUSA_SEGUNDOS * 10 * intento)
    raise RuntimeError(f"No se pudo descargar el listado del {fecha}")


# ============================================================
# PROCESO 2: Convertir el listado de un día en filas
# Insumo:    HTML del día (cada norma es un bloque <article>)
# Resultado: lista de normas con código, edición, institución, número y sumilla
# ============================================================
def enlace_pdf(codigo, fecha_publicacion):
    """Antes: "2455762-2", "05/11/2025" | Después: enlace oficial epdoc2 del PDF
    (la referencia es "2455762_2" + "20251105" escrito en base64; probado el 30/10/2026)"""
    id_norma, orden = codigo.split("-")
    d, m, a = fecha_publicacion.split("/")
    referencia = base64.b64encode(f"{id_norma}_{orden}{a}{m}{d}".encode()).decode()
    return f"https://epdoc2.elperuano.pe/EpPo/DescargaIN.asp?Referencias={referencia}"


def leer_normas(texto_html, dia):
    """Antes: HTML con bloques <article> | Después: una fila (diccionario) por norma"""
    pagina = BeautifulSoup(texto_html, "html.parser")
    filas = []
    for articulo in pagina.find_all("article"):
        enlace = articulo.find("h5").find("a")["href"]
        if "Referencias=" in enlace:
            # Formato de las publicaciones digitales: ...VistaDE.asp?Referencias=<base64 de "2455140-120251104">
            texto = base64.b64decode(enlace.split("Referencias=")[1]).decode()
            edicion, codigo = "DIG", texto[:-8]   # los últimos 8 caracteres son la fecha
        elif "/dispositivo/" in enlace:
            # Formato normal: .../dispositivo/NL/2538545-1  (NL = ordinaria, EX = extraordinaria)
            _, edicion, codigo = enlace.rsplit("/", 2)
        else:
            # Formatos hasta 2023, con el código al final del enlace:
            #   .../normaslegales/designan-asesora-...-2120784-1/   .../download/url/reglamento-...-2122118-1
            #   https://elperuano.pe/NormasElperuano/2023/05/15/2177792-1/2177792-1.htm
            # La edición sale del enlace "Todo el cuadernillo": .../cuadernillo/NL/20221101 (NL u EX)
            al_final = re.search(r"(\d{5,8}-\d{1,3})(?:\.htm)?/?$", enlace)
            codigo = al_final.group(1) if al_final else ""
            cuadernillo = re.search(r"/cuadernillo/([A-Z]{2})/", str(articulo))
            edicion = cuadernillo.group(1) if cuadernillo else "NL"
        parrafos = [p.get_text(" ", strip=True) for p in articulo.find_all("p")]
        fecha = parrafos[0].split("Fecha:")[1].split()[0] if parrafos else ""
        if not re.fullmatch(r"\d{5,8}-\d{1,3}", codigo):
            # Formato de enlace desconocido: se avisa y la norma queda sin enlace al PDF (no se detiene la descarga)
            print(f"   {dia}: enlace con formato desconocido, sin código: {enlace[:120]}", flush=True)
            fecha = ""
        filas.append({
            "fecha_publicacion": fecha,
            "codigo_norma": codigo,
            "edicion": {"EX": "extraordinaria", "NL": "ordinaria"}.get(edicion, "digital"),
            "publicacion_digital": "articulos_dig" in " ".join(articulo.get("class", [])),
            "institucion": articulo.find("h4").get_text(" ", strip=True),
            "dispositivo": articulo.find("h5").get_text(" ", strip=True),
            "sumilla": parrafos[1] if len(parrafos) > 1 else "",
            "enlace_web": enlace,
            "enlace_pdf": enlace_pdf(codigo, fecha) if fecha else "",
            "dia_consultado": dia.isoformat(),
        })
    return filas


# ============================================================
# PROCESO 3: Recorrer todos los días y juntar la tabla
# Insumo:    fecha inicial y final
# Resultado: datos/procesados/listado_general.csv (una fila por norma publicada)
# ============================================================
def main():
    inicio = date.fromisoformat(sys.argv[1])
    fin = date.fromisoformat(sys.argv[2])
    CARPETA_CRUDOS.mkdir(parents=True, exist_ok=True)

    todas, dia = [], inicio
    while dia <= fin:
        normas_dia = leer_normas(descargar_dia(dia), dia)
        todas.extend(normas_dia)
        if dia.day == 1 or dia == fin:
            print(f"{dia}: {len(normas_dia)} normas | acumulado {len(todas)}", flush=True)
        dia += timedelta(days=1)

    # pd.DataFrame(): lista de diccionarios -> tabla
    listado = pd.DataFrame(todas)
    # Verificación: tamaño y repetidos (solo se informan; no se borra nada)
    print("\nTabla (filas, columnas):", listado.shape)
    print("Códigos repetidos:", listado["codigo_norma"].duplicated().sum())
    print("Por edición:", listado["edicion"].value_counts().to_dict())
    listado.to_csv(ARCHIVO_SALIDA, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
