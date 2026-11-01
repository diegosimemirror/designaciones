# ============================================================
# Designaciones de El Peruano — Script 01c: lista final de normas de personal
# ------------------------------------------------------------
# Une las dos fuentes:
#   - el índice de designaciones (script 01): trae sector y cargo, pero está incompleto
#   - el listado general (script 01b): trae TODAS las normas; aquí se eligen las de
#     personal por las palabras con que empieza su sumilla
# Resultado: datos/procesados/normas_personal.csv (una fila por norma, sin repetir)
#
# Uso (desde la carpeta tarea_3):
#   python scripts/01c_unir_normas_personal.py
# ============================================================

# --- Paquetes ---
# re: buscar patrones de texto (expresiones regulares), por ejemplo "empieza con Designan"
import re
# unicodedata: quitar tildes para comparar nombres de instituciones escritos distinto
import unicodedata
# pathlib: manejar rutas de carpetas y archivos
from pathlib import Path
# pandas: trabajar las tablas
import pandas as pd

CARPETA_PROCESADOS = Path(__file__).resolve().parent.parent / "datos" / "procesados"

# Sumillas de movimientos de personal: se eligen por cómo empieza la sumilla.
# Calibrada el 30/10/2026: marca 6.359 de las 6.360 normas del índice (y se corrigió la que faltaba,
# "Acepta renuncia") y se revisaron muestras de lo que marca fuera del índice para excluir falsos
# positivos como "Ratifican el Acta...", "Conforman la Red contra la Trata..." o "Aceptan donación...".
SUMILLA_PERSONAL = re.compile(
    r"^\s*(Designan|Desígnan|Designa\b|Encargan|Encárgan|Encarga\b|"
    r"Aceptan?\s+(?:la\s+|las\s+)?renuncia|"
    r"(?:Dan|Da)\s+por\s+(?:conclu|terminad)|Dan\s+t[ée]rmino|"
    r"Declaran\s+(?:la\s+)?conclu\w*\s+(?:de\s+)?(?:la\s+|el\s+)?(?:designaci|encarg|nombramiento|funciones)|"
    r"Concluyen\s+(?:la\s+|el\s+)?(?:designaci|encarg|nombramiento)|"
    r"Nombran|Nombra\b|Formalizan\s+(?:la\s+)?designaci|"
    r"Dejan\s+sin\s+efecto\s+.{0,80}?(?:designaci|encarg|nombr)|"
    r"Ratifican\s+(?:la\s+)?designaci|Cesan|Remueven|Rotan|Reasignan|Reincorporan|Asignan\s+funciones|"
    r"Prorrogan\s+(?:la\s+)?(?:designaci|encarg)|(?:Re)?[Cc]onforman\s+(?:la\s+)?Comisi[oó]n\s+Organizadora)",
    re.IGNORECASE)


def sin_tildes(texto):
    """Antes: "PROMOCIÓN" | Después: "PROMOCION" (para comparar textos escritos distinto)"""
    texto = unicodedata.normalize("NFKD", str(texto))
    return "".join(c for c in texto if not unicodedata.combining(c)).upper().strip()


# ============================================================
# PROCESO 1: Cargar las dos fuentes
# Insumo:    indice_normas.csv y listado_general.csv
# Resultado: dos tablas en memoria
# ============================================================
indice = pd.read_csv(CARPETA_PROCESADOS / "indice_normas.csv", encoding="utf-8-sig")
listado = pd.read_csv(CARPETA_PROCESADOS / "listado_general.csv", encoding="utf-8-sig")
print("Índice:", indice.shape, "| Listado general:", listado.shape)

# ============================================================
# PROCESO 2: Marcar en el listado las normas de personal
# Insumo:    listado general (todas las normas)
# Resultado: columna nueva "es_personal" (Verdadero/Falso); no se borra ninguna fila
# ============================================================
listado["es_personal"] = listado["sumilla"].fillna("").str.match(SUMILLA_PERSONAL)
listado["en_indice"] = listado["codigo_norma"].isin(indice["codigo_norma"])
print("\nNormas del índice que el listado NO marcaría como personal (para revisar el filtro):",
      (listado["en_indice"] & ~listado["es_personal"]).sum())
print("Normas de personal del listado que NO están en el índice:",
      (listado["es_personal"] & ~listado["en_indice"]).sum())

# ============================================================
# PROCESO 3: Unir: todas las del índice + las de personal que solo están en el listado
# Insumo:    índice y listado marcado
# Resultado: normas_personal (una fila por código de norma)
# ============================================================
# Columnas del índice, con nombres en español
del_indice = pd.DataFrame({
    "codigo_norma": indice["codigo_norma"],
    "fecha_publicacion": indice["dtmFechaPublicacion"],
    "sector_ep": indice["vchSector"],
    "institucion": indice["vchInstitucionWeb"],
    "dispositivo": indice["vchNomTipoDispositivo"] + " " + indice["vchNomDispositivo"],
    "cargo_indice": indice["vchCargo"],
    "tipo_indice": indice["intTipo"].map({1: "designación", 2: "renuncia/conclusión"}),
    "enlace_pdf": indice["vchLinkPDF"],
    "enlace_web": indice["vchLinkHtml"],
})
# merge(): pega a cada norma del índice la sumilla y la edición del listado (por código)
#   Antes: filas del índice sin sumilla | Después: mismas filas con sumilla y edición
del_indice = del_indice.merge(
    listado[["codigo_norma", "sumilla", "edicion"]], on="codigo_norma", how="left")
del_indice["fuente"] = "índice"

solo_listado = listado[listado["es_personal"] & ~listado["en_indice"]]
del_listado = solo_listado[["codigo_norma", "fecha_publicacion", "institucion", "dispositivo",
                            "sumilla", "edicion", "enlace_pdf", "enlace_web"]].copy()
del_listado["fuente"] = "listado general"

# ============================================================
# PROCESO 4: Completar el sector de El Peruano para las normas que no están en el índice
# Insumo:    institución de cada norma
# Resultado: sector_ep completado según el sector que esa institución tiene en el índice
# ============================================================
sector_de = (indice.assign(clave=indice["vchInstitucionWeb"].map(sin_tildes))
             .groupby("clave")["vchSector"].agg(lambda s: s.mode().iloc[0]))
del_listado["sector_ep"] = del_listado["institucion"].map(sin_tildes).map(sector_de)

# pd.concat(): pone una tabla debajo de la otra (como pegar filas al final en Excel)
normas_personal = pd.concat([del_indice, del_listado], ignore_index=True)
print("\nNormas de personal (filas, columnas):", normas_personal.shape)
print("Por fuente:", normas_personal["fuente"].value_counts().to_dict())
print("Códigos repetidos:", normas_personal["codigo_norma"].duplicated().sum())
print("Sin sector (institución que no aparece en el índice):", normas_personal["sector_ep"].isna().sum())
normas_personal.to_csv(CARPETA_PROCESADOS / "normas_personal.csv", index=False, encoding="utf-8-sig")
