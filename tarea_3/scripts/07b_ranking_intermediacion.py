# ============================================================
# Designaciones de El Peruano — Script 07b: ranking de intermediación (versión privada, con nombres)
# ------------------------------------------------------------
# Arma el ranking de quiénes más conectan equipos distintos (intermediación en la red persona–equipo, script 07),
# con el recorrido de cada persona. Es la versión DE TRABAJO, con nombres: se guarda en datos/privado/ y no se publica.
# La versión pública (anonimizada) la prepara el script 08.
#
# Insumos:   datos/procesados/indicadores/red_perfil_personas.csv (script 07) y movimientos_analisis.csv (script 06)
# Resultado: datos/privado/ranking_intermediacion.xlsx (una fila por persona, ordenadas por intermediación)
#
# Uso (desde la carpeta tarea_3):
#   python scripts/07b_ranking_intermediacion.py [ranking_anterior.csv]   (opcional: para comparar puestos)
# ============================================================

# --- Paquetes ---
# sys: leer el archivo opcional con el ranking anterior
import sys
# pathlib: rutas de archivos
from pathlib import Path
# pandas: tablas; escribe el Excel con openpyxl (viene con Anaconda)
import pandas as pd

CARPETA_TAREA = Path(__file__).resolve().parent.parent
INDICADORES = CARPETA_TAREA / "datos" / "procesados" / "indicadores"
SALIDA = CARPETA_TAREA / "datos" / "privado" / "ranking_intermediacion.xlsx"
SALIDA.parent.mkdir(parents=True, exist_ok=True)
ENTRADA = {"designación", "nombramiento", "encargatura"}

# ============================================================
# PROCESO 1: Ranking y recorrido de cada persona
# Insumo:    perfil de la red (intermediación, equipos, entidades, gobiernos, tipo) y designaciones
# Resultado: tabla ordenada con el recorrido por institución y el cargo más alto
# ============================================================
perfil = pd.read_csv(INDICADORES / "red_perfil_personas.csv").sort_values("intermediacion", ascending=False).reset_index(drop=True)
perfil.insert(0, "puesto", perfil.index + 1)
mov = pd.read_csv(CARPETA_TAREA / "datos" / "procesados" / "movimientos_analisis.csv", encoding="utf-8-sig", dtype=str)
mov["fecha"] = pd.to_datetime(mov["fecha_emision_corregida"], errors="coerce").fillna(
    pd.to_datetime(mov["fecha_publicacion"], dayfirst=True))
designaciones = mov[(mov["en_analisis_principal"] == "True") & mov["tipo_movimiento"].isin(ENTRADA)
                    & mov["clave_persona"].isin(perfil["clave_persona"])].sort_values("fecha")


def recorrido(grupo):
    """Antes: designaciones de una persona | Después: "SALUD (2023) → PRODUCE (2023) → ..." (cambios de institución)"""
    pasos = []
    for institucion, fecha in zip(grupo["institucion_normalizada"], grupo["fecha"]):
        if not pasos or pasos[-1][0] != institucion:
            pasos.append((institucion, fecha.year))
    return " → ".join(f"{i.title()} ({a})" for i, a in pasos)


def cargo_mas_alto(grupo):
    """Antes: designaciones de una persona | Después: el cargo con la jerarquía más alta (J1 es la más alta) y su fecha"""
    con_nivel = grupo[grupo["jerarquia_puesto"].notna()].sort_values(["jerarquia_puesto", "fecha"])
    fila = con_nivel.iloc[0] if len(con_nivel) else grupo.iloc[-1]
    return f"{str(fila['cargo'])[:160]} ({fila['fecha'].date()})"


por_persona = designaciones.groupby("clave_persona")
perfil["recorrido"] = perfil["clave_persona"].map(por_persona.apply(recorrido))
perfil["cargo_mas_alto"] = perfil["clave_persona"].map(por_persona.apply(cargo_mas_alto))
perfil["primera_designacion"] = perfil["clave_persona"].map(por_persona["fecha"].min().dt.date)
perfil["ultima_designacion"] = perfil["clave_persona"].map(por_persona["fecha"].max().dt.date)
perfil["nombre"] = perfil["clave_persona"].str.title()
if len(sys.argv) > 1:
    anterior = pd.read_csv(sys.argv[1]).sort_values("intermediacion", ascending=False).reset_index(drop=True)
    perfil["puesto_version_anterior"] = perfil["clave_persona"].map(pd.Series(anterior.index + 1, index=anterior["clave_persona"]))

# ============================================================
# PROCESO 2: Guardar el Excel (hoja 1: los 200 primeros; hoja 2: todos)
# Insumo:    ranking
# Resultado: datos/privado/ranking_intermediacion.xlsx
# ============================================================
columnas = ["puesto", "nombre", "id_persona", "equipos", "entidades", "gobiernos", "jefes_sobrevividos_max", "jerarquia_max",
            "tipo", "intermediacion", "cargo_mas_alto", "primera_designacion", "ultima_designacion", "recorrido"] + \
           (["puesto_version_anterior"] if "puesto_version_anterior" in perfil else [])
nombres = {"puesto": "Puesto", "nombre": "Nombre", "id_persona": "Código", "equipos": "Equipos", "entidades": "Instituciones",
           "gobiernos": "Gobiernos", "jefes_sobrevividos_max": "Ministros que llegaron mientras seguía", "jerarquia_max": "Nivel más alto",
           "tipo": "Tipo", "intermediacion": "Intermediación", "cargo_mas_alto": "Cargo más alto (fecha)",
           "primera_designacion": "Primera designación", "ultima_designacion": "Última designación", "recorrido": "Recorrido",
           "puesto_version_anterior": "Puesto en la versión anterior"}
with pd.ExcelWriter(SALIDA) as excel:
    perfil[columnas].head(200).rename(columns=nombres).to_excel(excel, sheet_name="200 primeros", index=False)
    perfil[columnas].rename(columns=nombres).to_excel(excel, sheet_name="todos", index=False)
print(f"Ranking guardado en {SALIDA} ({len(perfil)} personas)")
print(perfil[columnas].head(10).to_string(index=False))
