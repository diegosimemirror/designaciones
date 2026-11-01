# ============================================================
# Designaciones de El Peruano — Script 05: exploración de la base
# ------------------------------------------------------------
# Recorre la lista de revisión de la fase 3 (tamaño, tipos, duplicados, faltantes,
# estadísticos, frecuencias, valores únicos, fechas y atípicos) sobre las dos tablas
# que arma el script 03. NO modifica ningún dato: solo cuenta y describe.
# No escribe nombres de personas (el resultado se puede publicar en el repositorio).
#
# Insumo:    datos/procesados/normas.csv y movimientos.csv
# Resultado: docs/exploracion_resultados.md
#
# Uso (desde la carpeta tarea_3):
#   python scripts/05_explorar_base.py
# ============================================================

# --- Paquetes ---
# re: buscar patrones de texto (por ejemplo, caracteres mal codificados)
import re
# unicodedata: quitar tildes para detectar categorías escritas de dos formas
import unicodedata
# pathlib: manejar rutas de carpetas y archivos
from pathlib import Path
# pandas: leer y describir las tablas
import pandas as pd

CARPETA_TAREA = Path(__file__).resolve().parent.parent
CARPETA_PROCESADOS = CARPETA_TAREA / "datos" / "procesados"
salida = []          # líneas del informe (Markdown)


def escribir(texto=""):
    """Antes: una línea de texto | Después: la misma línea agregada al informe y mostrada en pantalla"""
    salida.append(texto)
    print(texto)


def tabla_md(serie_o_tabla, titulo_valor="n"):
    """Antes: una Serie o tabla de pandas | Después: texto en formato de tabla Markdown"""
    tabla = serie_o_tabla.to_frame(titulo_valor) if isinstance(serie_o_tabla, pd.Series) else serie_o_tabla
    return tabla.to_markdown()


def vacio(columna):
    """Antes: una columna | Después: Verdadero donde no hay dato (nulo o texto vacío)"""
    return columna.isna() | (columna.astype(str).str.strip() == "")


def sin_tildes(texto):
    """Antes: "PÚBLICO" | Después: "PUBLICO" """
    texto = unicodedata.normalize("NFKD", str(texto))
    return "".join(c for c in texto if not unicodedata.combining(c)).upper().strip()


# ============================================================
# PROCESO 1: Cargar las dos tablas
# Insumo:    normas.csv y movimientos.csv
# Resultado: tablas normas y movimientos en memoria
# ============================================================
# low_memory=False: lee cada columna completa antes de decidir su tipo (evita tipos mezclados)
normas = pd.read_csv(CARPETA_PROCESADOS / "normas.csv", encoding="utf-8-sig", low_memory=False)
movimientos = pd.read_csv(CARPETA_PROCESADOS / "movimientos.csv", encoding="utf-8-sig", low_memory=False)

escribir("# Resultados de la exploración (generado por scripts/05_explorar_base.py)")
escribir()
escribir("## 1. Tamaño")
escribir(f"- normas.csv: {normas.shape[0]:,} filas × {normas.shape[1]} columnas (una fila por norma)")
escribir(f"- movimientos.csv: {movimientos.shape[0]:,} filas × {movimientos.shape[1]} columnas (una fila por persona y movimiento)")
escribir()
escribir("Estado de la extracción por norma:")
escribir(tabla_md(normas["estado_extraccion"].value_counts()))
escribir()

# ============================================================
# PROCESO 2: Tipos de columna y una muestra sin nombres
# Insumo:    las dos tablas
# Resultado: lista de columnas con su tipo; muestra de filas al azar
# ============================================================
escribir("## 2-3. Muestra y tipos de columna")
columnas_muestra = ["codigo_norma", "fecha_publicacion", "institucion", "tipo_movimiento", "metodo_nombre", "cargo"]
# sample(): toma filas al azar (random_state fija el azar para que salga siempre la misma muestra)
escribir(tabla_md(movimientos[columnas_muestra].sample(8, random_state=1).assign(cargo=lambda t: t["cargo"].str[:70])))
escribir()
tipos = movimientos.dtypes.astype(str).value_counts()
escribir("Tipos en movimientos.csv: " + ", ".join(f"{k}: {v}" for k, v in tipos.items()))
escribir("Las fechas se leen como texto: fecha_publicacion viene como dd/mm/aaaa y fecha_emision como aaaa-mm-dd; "
         "hay que convertirlas a fecha antes de analizarlas.")
escribir()

# ============================================================
# PROCESO 3: Duplicados
# Insumo:    las dos tablas
# Resultado: conteo de filas repetidas con distintas definiciones
# ============================================================
escribir("## 4. Duplicados")
escribir(f"- Códigos de norma repetidos en normas.csv: {normas['codigo_norma'].duplicated().sum()}")
escribir(f"- id_movimiento repetidos: {movimientos['id_movimiento'].duplicated().sum()}")
escribir(f"- Filas idénticas en todo menos el id: {movimientos.drop(columns='id_movimiento').duplicated().sum()}")
clave = ["codigo_norma", "nombre_normalizado", "tipo_movimiento"]
con_nombre = movimientos[~vacio(movimientos["nombre_normalizado"])]
repetidos = con_nombre[con_nombre.duplicated(subset=clave, keep=False)]
escribir(f"- Misma norma + misma persona + mismo tipo de movimiento: {con_nombre.duplicated(subset=clave).sum()} "
         f"(en {repetidos['codigo_norma'].nunique()} normas)")
misma_persona = con_nombre[con_nombre.duplicated(subset=["codigo_norma", "nombre_normalizado"], keep=False)]
escribir(f"- Misma persona con dos movimientos distintos en la misma norma (p. ej. concluye y se designa en otro cargo): "
         f"{misma_persona['codigo_norma'].nunique()} normas")
# Misma persona, mismo tipo y mismo cargo en DOS normas distintas: puede ser una norma repetida (o corregida)
# o un hecho real (por ejemplo, se le encarga el mismo puesto dos veces)
otra_norma = con_nombre[con_nombre.duplicated(subset=["nombre_normalizado", "tipo_movimiento", "cargo"], keep=False)
                        & ~vacio(con_nombre["cargo"])]
escribir(f"- Misma persona + mismo tipo + mismo cargo en normas distintas: {len(otra_norma)} filas "
         f"({otra_norma.groupby(['nombre_normalizado', 'tipo_movimiento', 'cargo']).ngroups} casos); se revisan a mano, "
         f"no se borran: pueden ser hechos reales repetidos (dos encargos del mismo puesto)")
escribir()

# ============================================================
# PROCESO 4: Faltantes por columna
# Insumo:    movimientos (y normas)
# Resultado: % de filas sin dato por columna, incluidos los textos vacíos
# ============================================================
escribir("## 5. Faltantes (% de filas sin dato)")
faltantes = pd.DataFrame({
    "% vacío": (vacio(movimientos[c]).mean() * 100 for c in movimientos.columns),
}, index=movimientos.columns).round(1).sort_values("% vacío", ascending=False)
escribir(tabla_md(faltantes[faltantes["% vacío"] > 0]))
escribir()
# Faltantes disfrazados: guiones, "S/N", "ND", "-" o solo signos
disfrazados = {c: movimientos[c].astype(str).str.fullmatch(r"\s*(?:-+|S/N|N/?D|s/d|\.+|—)\s*").sum()
               for c in ["nombre_tal_cual", "cargo", "dni", "ubicacion_tabla", "firmante1_nombre", "firmante1_cargo"]}
escribir("Faltantes disfrazados (\"-\", \"S/N\", \"ND\"...): " + ", ".join(f"{k}: {v}" for k, v in disfrazados.items()))
escribir()

# ============================================================
# PROCESO 5: Estadísticos de las columnas numéricas o medibles
# Insumo:    normas y movimientos
# Resultado: mínimo, máximo, mediana de movimientos por norma, días de demora y largo de textos
# ============================================================
escribir("## 6. Estadísticos")
# pd.to_datetime(): convierte texto en fecha. Antes: "21/10/2026" (texto) | Después: 2026-10-21 (fecha)
normas["f_pub"] = pd.to_datetime(normas["fecha_publicacion"], format="%d/%m/%Y", errors="coerce")
normas["f_emi"] = pd.to_datetime(normas["fecha_emision"], errors="coerce")
normas["dias_emision_a_publicacion"] = (normas["f_pub"] - normas["f_emi"]).dt.days
movimientos["palabras_nombre"] = movimientos["nombre_tal_cual"].fillna("").str.split().str.len()
movimientos["largo_cargo"] = movimientos["cargo"].fillna("").str.len()
estadisticos = pd.DataFrame({
    "movimientos por norma": normas["n_movimientos"].describe(),
    "días de emisión a publicación": normas["dias_emision_a_publicacion"].describe(),
    "palabras del nombre": movimientos.loc[movimientos["palabras_nombre"] > 0, "palabras_nombre"].describe(),
    "caracteres del cargo": movimientos.loc[movimientos["largo_cargo"] > 0, "largo_cargo"].describe(),
}).round(1)
escribir(tabla_md(estadisticos))
escribir()

# ============================================================
# PROCESO 6: Frecuencias de las categorías
# Insumo:    movimientos y normas
# Resultado: conteos por tipo de movimiento, sector, método del nombre, sexo, edición y fuente
# ============================================================
escribir("## 7. Frecuencias")
for columna in ["tipo_movimiento", "sector_ep", "metodo_nombre", "sexo_segun_norma", "temporal", "objeto_conclusion"]:
    escribir(f"**{columna}**")
    escribir(tabla_md(movimientos[columna].fillna("(vacío)").value_counts()))
    escribir()
for columna in ["fuente", "edicion"]:
    escribir(f"**{columna}** (normas)")
    escribir(tabla_md(normas[columna].fillna("(vacío)").value_counts()))
    escribir()
normas["tipo_dispositivo"] = normas["dispositivo"].fillna("").map(sin_tildes).str.extract(r"^(.+?)\s+N")[0]
escribir("**Tipo de dispositivo** (normas; sin tildes para no contar dos veces la misma categoría)")
escribir(tabla_md(normas["tipo_dispositivo"].value_counts().head(15)))
escribir()

# ============================================================
# PROCESO 7: Valores únicos y categorías escritas de varias formas
# Insumo:    columnas de texto
# Resultado: grupos de valores que solo se diferencian por tildes o mayúsculas
# ============================================================
escribir("## 8. Valores únicos y variantes de escritura")
for columna in ["institucion", "tratamiento", "firmante1_cargo"]:
    serie = movimientos[columna].dropna()
    grupos = serie.groupby(serie.map(sin_tildes)).unique()
    variantes = grupos[grupos.str.len() > 1]
    escribir(f"- {columna}: {serie.nunique()} valores distintos; {len(variantes)} grupos que solo cambian en tildes o mayúsculas")
    for valores in variantes.head(5):
        escribir(f"  - {' | '.join(valores)}")
mal_codificados = movimientos.astype(str).apply(lambda c: c.str.contains("Ã|�", regex=True).sum()).sum()
escribir(f"- Celdas con caracteres mal codificados (Ã o �): {mal_codificados}")
escribir()

# ============================================================
# PROCESO 8: Fechas
# Insumo:    fechas de publicación y emisión
# Resultado: rango, normas por mes, días sin normas y fechas incoherentes
# ============================================================
escribir("## 9. Fechas")
escribir(f"- Publicación: del {normas['f_pub'].min():%d/%m/%Y} al {normas['f_pub'].max():%d/%m/%Y}")
escribir(f"- Emisión: del {normas['f_emi'].min():%d/%m/%Y} al {normas['f_emi'].max():%d/%m/%Y}; "
         f"sin fecha de emisión: {normas['f_emi'].isna().sum()} normas")
escribir(f"- Emitidas después de publicarse (imposible): {(normas['dias_emision_a_publicacion'] < 0).sum()}")
escribir(f"- Publicadas más de 60 días después de emitirse: {(normas['dias_emision_a_publicacion'] > 60).sum()}")
# dt.to_period("M"): convierte cada fecha en su mes. Antes: 2026-10-21 | Después: 2026-10
por_mes = normas.groupby(normas["f_pub"].dt.to_period("M")).size()
escribir("Normas por mes de publicación:")
escribir(tabla_md(por_mes))
todos_los_dias = pd.date_range(normas["f_pub"].min(), normas["f_pub"].max())
dias_sin_normas = todos_los_dias.difference(normas["f_pub"].dropna().unique())
escribir(f"- Días del periodo sin ninguna norma de personal: {len(dias_sin_normas)}")
escribir()

# ============================================================
# PROCESO 9: Valores atípicos
# Insumo:    movimientos y normas
# Resultado: casos extremos para revisar a mano
# ============================================================
escribir("## 10. Atípicos")
escribir("Normas con más movimientos:")
escribir(tabla_md(normas.nlargest(8, "n_movimientos")[["codigo_norma", "institucion", "n_movimientos"]].set_index("codigo_norma")))
escribir(f"- Nombres de 2 palabras (posible nombre incompleto): {(movimientos['palabras_nombre'] == 2).sum()}")
escribir(f"- Nombres de 7 o más palabras (posibles dos personas unidas o apellidos compuestos): "
         f"{(movimientos['palabras_nombre'] >= 7).sum()}")
escribir(f"- Cargos de más de 250 caracteres (el cargo arrastró texto de más): {(movimientos['largo_cargo'] > 250).sum()}")
escribir(f"- Movimientos sin nombre: {vacio(movimientos['nombre_tal_cual']).sum()}; sin cargo (con nombre): "
         f"{(~vacio(movimientos['nombre_tal_cual']) & vacio(movimientos['cargo'])).sum()}")

(CARPETA_TAREA / "docs" / "exploracion_resultados.md").write_text("\n".join(salida), encoding="utf-8")
