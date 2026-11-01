# ============================================================
# Designaciones de El Peruano — Script 06b: validar la ubicación de los cargos con el ROF
# ------------------------------------------------------------
# Compara lo que el script 06 dedujo del texto del cargo (unidad_organica y nivel_organizacional)
# con la estructura oficial del ROF (Reglamento de Organización y Funciones) de dos ministerios.
# No modifica la base: solo mide cuánto coincide.
#
# Insumos:   datos/procesados/movimientos_analisis.csv (script 06)
#            datos/crudos/rof/*.pdf (texto integrado del ROF, descargado de gob.pe el 30/10/2026)
# Resultado: docs/validacion_rof.md (tablas de coincidencia)
#
# En el ROF cada órgano tiene un código que indica su nivel:
#   01.x = alta dirección (N1) | 05.2 = órgano (N2) | 05.2.1 = unidad orgánica (N3)
#
# Uso (desde la carpeta tarea_3):
#   python scripts/06b_validar_con_rof.py
# ============================================================

# --- Paquetes ---
# re: leer los códigos y nombres de la estructura orgánica
import re
# unicodedata: comparar nombres sin tildes
import unicodedata
# pathlib: rutas de archivos
from pathlib import Path
# pymupdf: leer el texto del PDF del ROF (ya instalado para el script 02)
import pymupdf
# pandas: tablas de comparación
import pandas as pd

CARPETA_TAREA = Path(__file__).resolve().parent.parent
CARPETA_ROF = CARPETA_TAREA / "datos" / "crudos" / "rof"
ARCHIVO_SALIDA = CARPETA_TAREA / "docs" / "validacion_rof.md"
# Ministerio (como figura en institucion_del_cargo) -> PDF del ROF y secciones que son órganos del ministerio
# (se excluyen programas, organismos adscritos, PNP y órganos desconcentrados, que tienen su propia ubicación)
ROF = {
    "DESARROLLO E INCLUSIÓN SOCIAL": ("midis_rof_texto_integrado_rm026-2025.pdf", range(1, 8)),
    "INTERIOR": ("mininter_rof_texto_integrado_vigente.pdf", range(1, 8)),
}


def sin_tildes(texto):
    """Antes: "Oficina General de Administración" | Después: "OFICINA GENERAL DE ADMINISTRACION" (sin signos)"""
    texto = "".join(c for c in unicodedata.normalize("NFD", str(texto)) if unicodedata.category(c) != "Mn").upper()
    texto = re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]", " ", texto)).strip()
    # "Dirección de los Canales" y "Dirección de Canales" son el mismo órgano: se quitan los artículos
    return re.sub(r"\b(?:DE LOS|DE LAS|DE LA|DEL)\b", "DE", texto)


# ============================================================
# PROCESO 1: Leer la estructura orgánica de cada ROF
# Insumo:    PDF del texto integrado del ROF
# Resultado: tabla con código, nombre y nivel de cada órgano
# ============================================================
def estructura_del_rof(archivo, secciones):
    """Antes: PDF del ROF | Después: tabla codigo, nombre, nivel (solo el artículo "Estructura Orgánica")"""
    texto = "\n".join(pagina.get_text() for pagina in pymupdf.open(CARPETA_ROF / archivo))
    inicio = re.search(r"Art[íi]culo\s+\d+\.?-?\s*Estructura\s+Org[áa]nica", texto, re.I).start()
    fin = re.search(r"CAP[ÍI]TULO\s+I\b", texto[inicio:]).start() + inicio
    lineas = [l.strip() for l in texto[inicio:fin].split("\n") if l.strip()]
    filas, i = [], 0
    while i < len(lineas):
        m = re.match(r"^(\d{2}(?:\.\d+)+)\.?\s*(.*)$", lineas[i])
        if m:
            codigo, nombre = m.group(1), m.group(2)
            if not nombre and i + 1 < len(lineas):      # el nombre viene en la línea siguiente
                i += 1
                nombre = lineas[i]
            partes = codigo.split(".")
            if int(partes[0]) in secciones:
                # 01.x (alta dirección) = nivel 1; el resto, según la cantidad de partes del código
                nivel = 1 if partes[0] == "01" and len(partes) == 2 else len(partes)
                filas.append({"codigo": codigo, "nombre": nombre.rstrip(". "), "nivel_rof": f"N{nivel}"})
        i += 1
    return pd.DataFrame(filas)


# ============================================================
# PROCESO 2: Buscar cada unidad orgánica de la base en el ROF
# Insumo:    movimientos de la sede central del ministerio con unidad_organica
# Resultado: cada movimiento con el órgano del ROF que le corresponde (o sin coincidencia)
# ============================================================
def buscar_en_rof(unidad, estructura):
    """Antes: "Oficina de Abastecimiento" | Después: fila del ROF con ese nombre (None si no está)"""
    clave = sin_tildes(unidad)
    if len(clave) < 8:
        return None
    for _, organo in estructura.iterrows():
        nombre = sin_tildes(organo["nombre"])
        # Igual, o uno empieza con el otro (el ROF a veces corta el nombre en dos líneas)
        if clave == nombre or (len(nombre) >= 15 and clave.startswith(nombre)) or (len(clave) >= 15 and nombre.startswith(clave)):
            return organo
    # Despachos viceministeriales sin el nombre del despacho, y el Gabinete de Asesores, que el ROF
    # no lista como órgano porque forma parte del Despacho Ministerial
    if clave in ("DESPACHO VICEMINISTERIAL", "GABINETE DE ASESORES"):
        return pd.Series({"codigo": "01.x", "nombre": unidad, "nivel_rof": "N1"})
    return None


movimientos = pd.read_csv(CARPETA_TAREA / "datos" / "procesados" / "movimientos_analisis.csv", encoding="utf-8-sig", dtype=str)
informe = ["# Validación de la ubicación de los cargos con el ROF", "",
           "Generado por `scripts/06b_validar_con_rof.py`. Compara la unidad orgánica y el nivel que el script 06 deduce del "
           "texto del cargo con la estructura orgánica del texto integrado del ROF vigente (descargado de gob.pe el 30/10/2026).",
           "Solo se comparan movimientos de la **sede central** del ministerio (sin programas, organismos adscritos ni "
           "órganos desconcentrados). Nivel del ROF: 01.x = N1 (alta dirección), 05.2 = N2 (órgano), 05.2.1 = N3 (unidad orgánica).", ""]
resumen = []
for ministerio, (archivo, secciones) in ROF.items():
    estructura = estructura_del_rof(archivo, secciones)
    print(f"\n{ministerio}: {len(estructura)} órganos en el ROF |", estructura["nivel_rof"].value_counts().sort_index().to_dict())
    base = movimientos[(movimientos["institucion_del_cargo"] == ministerio)
                       & (movimientos["ubicacion"] == "sede central del ministerio")
                       & movimientos["nivel_organizacional"].isin(["N1", "N2", "N3", "N4"])].copy()
    encontrados = base["unidad_organica"].fillna("").map(lambda u: buscar_en_rof(u, estructura))
    base["nivel_rof"] = encontrados.map(lambda o: o["nivel_rof"] if o is not None else "")
    base["organo_rof"] = encontrados.map(lambda o: f"{o['codigo']} {o['nombre']}" if o is not None else "")
    con_rof = base[base["nivel_rof"] != ""]
    coincide = (con_rof["nivel_rof"] == con_rof["nivel_organizacional"]).sum()
    resumen.append({"Ministerio": ministerio, "Movimientos (sede central)": len(base),
                    "Unidad encontrada en el ROF": f"{len(con_rof)} ({len(con_rof) / len(base):.0%})",
                    "Nivel igual al del ROF": f"{coincide} de {len(con_rof)} ({coincide / len(con_rof):.0%})"})
    print(resumen[-1])

    # ============================================================
    # PROCESO 3: Describir las diferencias
    # Insumo:    movimientos comparados
    # Resultado: tablas para el informe (cruce de niveles, unidades no encontradas, desacuerdos)
    # ============================================================
    cruce = pd.crosstab(con_rof["nivel_organizacional"], con_rof["nivel_rof"], margins=True, margins_name="Total")
    no_encontradas = base.loc[base["nivel_rof"] == "", "unidad_organica"].value_counts().head(15)
    desacuerdos = (con_rof[con_rof["nivel_rof"] != con_rof["nivel_organizacional"]]
                   .groupby(["organo_rof", "nivel_rof", "nivel_organizacional"]).size().sort_values(ascending=False).head(10))
    informe += [f"## {ministerio}", "",
                f"ROF: `{archivo}` — {len(estructura)} órganos y unidades orgánicas en las secciones 01 a 07.", "",
                "**Nivel de la base (filas) frente al nivel del ROF (columnas)**", "", cruce.to_markdown(), "",
                "**Unidades de la base que no se encontraron en el ROF (las 15 más frecuentes)**", "",
                no_encontradas.rename("movimientos").to_markdown(), "",
                "**Desacuerdos de nivel más frecuentes**", "",
                desacuerdos.rename("movimientos").reset_index().to_markdown(index=False), ""]

# El resumen va antes del detalle por ministerio (después del párrafo de introducción)
informe[5:5] = ["## Resumen", "", pd.DataFrame(resumen).to_markdown(index=False), ""]
ARCHIVO_SALIDA.write_text("\n".join(informe), encoding="utf-8")
print("\nInforme guardado en", ARCHIVO_SALIDA)
