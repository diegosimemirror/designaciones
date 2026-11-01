# ============================================================
# Designaciones de El Peruano — Script 04: diccionario de datos
# ------------------------------------------------------------
# Genera docs/diccionario_de_datos.md: qué significa cada columna de la base,
# de dónde sale y en qué % de filas tiene dato (calculado con los datos reales).
# Los ejemplos están escritos a mano para no publicar nombres de personas.
#
# Uso (desde la carpeta tarea_3):
#   python scripts/04_diccionario_datos.py
# ============================================================

# --- Paquetes ---
# pathlib: rutas de archivos
from pathlib import Path
# pandas: leer las tablas y medir cuántas celdas tienen dato
import pandas as pd

CARPETA_TAREA = Path(__file__).resolve().parent.parent
CARPETA_PROCESADOS = CARPETA_TAREA / "datos" / "procesados"
ARCHIVO_SALIDA = CARPETA_TAREA / "docs" / "diccionario_de_datos.md"

# Fuentes: ÍNDICE = servicio de designaciones de El Peruano | LISTADO = listado general de normas
#          PDF = texto oficial de la norma | DERIVADO = calculado por nosotros a partir de lo anterior
MOVIMIENTOS = [
    ("id_movimiento", "Código único del movimiento: código de la norma + # + orden dentro de la norma", "DERIVADO", "2538840-2#1"),
    ("codigo_norma", "Código de El Peruano que figura al pie de la norma; une esta tabla con normas.csv", "ÍNDICE / LISTADO", "2538840-2"),
    ("fecha_publicacion", "Fecha en que la norma salió en el diario", "ÍNDICE / LISTADO", "30/07/2026"),
    ("fecha_emision", "Fecha en que la entidad emitió la resolución", "PDF", "2026-07-30"),
    ("sector_ep", "Agrupación que usa El Peruano (Poder Ejecutivo, organismos autónomos...)", "ÍNDICE; si falta, según la institución", "PODER EJECUTIVO"),
    ("institucion", "Institución que publica la norma", "ÍNDICE / LISTADO", "DEFENSA"),
    ("dispositivo", "Tipo y número de la norma", "ÍNDICE / LISTADO", "RESOLUCIÓN MINISTERIAL N° 00909-2026-DE"),
    ("sumilla", "Título breve con que se publica la norma", "LISTADO", "Designan Jefa de Gabinete del Despacho Ministerial"),
    ("articulo", "Artículo de la norma del que sale el movimiento", "PDF", "1"),
    ("tipo_movimiento", "designación, encargatura, renuncia, conclusión, dejar sin efecto, nombramiento, asignación de funciones, ratificación, rotación o reasignación, prórroga (según el primer verbo del artículo)", "PDF", "renuncia"),
    ("temporal", "La norma dice 'temporal' o 'temporalmente'", "PDF", "True"),
    ("objeto_conclusion", "En conclusiones: qué se da por concluido (designación, encargo, nombramiento, funciones)", "PDF", "designación"),
    ("nombre_tal_cual", "Nombre de la persona tal como aparece en la norma (algunas tablas lo escriben APELLIDOS, NOMBRES)", "PDF", "NOMBRE APELLIDO APELLIDO"),
    ("nombre_normalizado", "El mismo nombre en mayúsculas, sin tildes ni signos y siempre en orden NOMBRES APELLIDOS, para comparar entre normas", "DERIVADO", "NOMBRE APELLIDO APELLIDO"),
    ("metodo_nombre", "Cómo se encontró el nombre. 'tratamiento' (después de señor/señora...) es lo más confiable; tablas y listas, menos", "DERIVADO", "tratamiento"),
    ("tratamiento", "Palabras que preceden al nombre", "PDF", "señora / abogado / servidor"),
    ("sexo_segun_norma", "F o M según el tratamiento y el artículo (la/el). No es autoidentificación; vacío si no se puede saber", "DERIVADO", "F"),
    ("profesion_mencionada", "Profesión que la norma antepone al nombre", "PDF", "abogada"),
    ("grado_militar_policial", "Grado militar, policial o rango diplomático", "PDF", "Teniente General FAP"),
    ("dni", "DNI, solo cuando la norma lo publica (sobre todo tablas de subprefectos)", "PDF", "(8 dígitos)"),
    ("ubicacion_tabla", "En tablas con DNI: distrito, provincia y departamento que siguen al DNI (subprefectos) o entidad que precede al nombre (Contraloría)", "PDF", "HUANCAYO JUNIN"),
    ("cargo", "Cargo tal como lo escribe la norma (en tablas, la columna de cargo; en fiscales, 'cargo — despacho')", "PDF", "Jefa de Gabinete del Despacho Ministerial del Ministerio de Defensa"),
    ("cargo_actual_mencionado", "Cargo que la persona ya ocupaba, si la norma lo menciona junto al nombre", "PDF", "Viceministro de Pesca y Acuicultura"),
    ("en_adicion_a_funciones", "Asume el cargo sin dejar el que ya tenía", "PDF", "True"),
    ("funciones_que_mantiene", "Funciones que conserva cuando es 'en adición'", "PDF", "ejecutiva de recursos humanos"),
    ("fecha_efectividad", "Desde cuándo rige el movimiento, si la norma lo dice; vacío = rige desde su publicación", "PDF", "2025-11-05"),
    ("fecha_fin", "Fin del encargo (del X al Y) o último día de labores, si la norma lo dice", "PDF", "2026-01-08"),
    ("inicio_texto", "Frase original sobre el inicio", "PDF", "a partir de la fecha de publicación"),
    ("condicion_texto", "Condiciones del movimiento", "PDF", "en tanto se designe al titular"),
    ("agradecimiento", "La norma agradece los servicios prestados", "PDF", "True"),
    ("norma_antecedente", "Norma con la que se había designado a la persona (o la que se deja sin efecto)", "PDF", "Resolución Suprema N° 118-2026-PCM"),
    ("en_tabla_con_dni", "El nombre salió de una tabla con DNI", "DERIVADO", "False"),
    ("texto_articulo", "Texto del artículo (hasta 1.500 caracteres), para verificar a mano", "PDF", "Designar a la señora ..."),
    ("firmante1_nombre", "Primer firmante de la norma (2 y 3 si hay más, p. ej. el ministro que refrenda)", "PDF", "NOMBRE APELLIDO APELLIDO"),
    ("firmante1_cargo", "Cargo del primer firmante", "PDF", "Presidenta de la República"),
    ("enlace_pdf", "Enlace al PDF oficial", "ÍNDICE / LISTADO", "https://epdoc2.elperuano.pe/..."),
    ("enlace_web", "Enlace a la ficha web de la norma", "ÍNDICE / LISTADO", "https://busquedas.elperuano.pe/..."),
]
NORMAS = [
    ("codigo_norma", "Código de El Peruano al pie de la norma (llave)", "ÍNDICE / LISTADO", "2538840-2"),
    ("fuente", "De dónde vino la norma: 'índice' de designaciones o 'listado general' (normas que el índice no tenía)", "DERIVADO", "listado general"),
    ("edicion", "Edición ordinaria, extraordinaria o publicación digital", "LISTADO", "extraordinaria"),
    ("cargo_indice", "Cargo según el índice de El Peruano", "ÍNDICE", "Jefa de Gabinete..."),
    ("tipo_indice", "Tipo según el índice: designación o renuncia/conclusión", "ÍNDICE", "designación"),
    ("lugar_emision", "Ciudad o distrito donde se emitió", "PDF", "Lima"),
    ("vistos_texto", "Texto de la sección VISTOS", "PDF", "El Oficio N° ... de la Secretaría General..."),
    ("documentos_sustento", "Documentos citados como sustento, con la oficina que los emitió", "PDF", "Informe N° ... de la Oficina de Recursos Humanos"),
    ("n_documentos_sustento", "Cuántos documentos de sustento cita", "DERIVADO", "3"),
    ("visado_texto", "Frase de visado (oficinas que revisaron la norma)", "PDF", "de la Secretaría General, de RR.HH. y de Asesoría Jurídica"),
    ("oficinas_visado", "Lista de oficinas que visaron, separadas por |", "DERIVADO", "Secretaría General | Oficina de Asesoría Jurídica"),
    ("n_oficinas_visado", "Cuántas oficinas visaron", "DERIVADO", "3"),
    ("propuesta_texto", "Quién propuso o solicitó la designación, si la norma lo dice", "PDF", "Estando a lo propuesto por el Ministro de Defensa"),
    ("motivo_vacante", "Los considerandos dicen que el cargo está vacante", "PDF", "True"),
    ("motivo_conveniente", "Los considerandos dicen 'por conveniente' (decisión discrecional)", "PDF", "True"),
    ("menciona_renuncia", "Los considerandos mencionan una renuncia", "PDF", "True"),
    ("motivo_texto", "Frase del motivo", "PDF", "se encuentra vacante el cargo de..."),
    ("cita_ley_31419_idoneidad", "Cita la Ley 31419 (idoneidad de funcionarios de libre designación)", "PDF", "True"),
    ("verificacion_perfil_texto", "Frase sobre el cumplimiento del perfil o requisitos", "PDF", "cumple con los requisitos..."),
    ("tipo_cargo_mencionado", "Tipo de cargo que menciona: de confianza, libre designación y remoción, directivo superior, funcionario público", "PDF", "cargo de confianza"),
    ("nivel_remunerativo", "Nivel remunerativo (escala de sueldo), si lo menciona", "PDF", "F-5"),
    ("menciona_cap", "Menciona el CAP (Cuadro para Asignación de Personal: lista oficial de plazas)", "PDF", "True"),
    ("numero_plaza", "Número de plaza o de orden en el CAP", "PDF", "931"),
    ("regimen_laboral_mencionado", "Régimen laboral citado (CAS 1057, 276, 728, Servicio Civil 30057)", "PDF", "CAS (D. Leg. 1057)"),
    ("base_legal_texto", "Frase 'De conformidad con...' / 'En uso de...'", "PDF", "De conformidad con la Ley N° 27594..."),
    ("leyes_citadas", "Leyes y decretos legislativos citados, separados por |", "PDF", "Ley N° 27594 | Ley N° 31419"),
    ("facultad_delegada", "Menciona facultades delegadas", "PDF", "False"),
    ("refrendo", "Quién refrenda (en resoluciones supremas)", "PDF", "Presidente del Consejo de Ministros"),
    ("personas_en_considerandos", "Personas nombradas en los considerandos (p. ej. quien ocupaba antes el cargo)", "PDF", "NOMBRE APELLIDO"),
    ("firmante1_encargado", "El firmante firma como encargado (e) o interino (i)", "PDF", "True"),
    ("n_movimientos", "Cuántos movimientos se extrajeron de la norma", "DERIVADO", "2"),
    ("n_sin_nombre", "Cuántos de esos movimientos no tienen nombre", "DERIVADO", "0"),
    ("estado_extraccion", "ok / revisar: movimiento sin nombre / sin movimientos detectados / sin texto descargado", "DERIVADO", "ok"),
    ("fuente_reparada", "True si el PDF tenía la fuente antigua que lee algunas mayúsculas como minúsculas "
     "(\"deSIGnaR\") y el texto se reparó antes de extraer", "DERIVADO", "False"),
    ("texto_norma", "Texto completo de la norma", "PDF", "..."),
]


# ============================================================
# PROCESO 1: Medir el % de filas con dato en cada columna
# Insumo:    movimientos.csv y normas.csv
# Resultado: diccionario {columna: % con dato}
# ============================================================
def porcentaje_lleno(tabla):
    """Antes: tabla | Después: {columna: % de filas con un valor no vacío}"""
    lleno = tabla.notna() & (tabla.astype(str).apply(lambda c: c.str.strip()) != "")
    return (100 * lleno.mean()).round(1).to_dict()


# ============================================================
# PROCESO 2: Escribir el diccionario en Markdown
# Insumo:    descripciones de arriba + porcentajes
# Resultado: docs/diccionario_de_datos.md
# ============================================================
def tabla_markdown(campos, porcentajes, n_filas):
    filas = ["| Columna | Qué significa | Fuente | % con dato | Ejemplo |", "|---|---|---|---|---|"]
    for columna, descripcion, fuente, ejemplo in campos:
        pct = porcentajes.get(columna)
        filas.append(f"| `{columna}` | {descripcion} | {fuente} | {'' if pct is None else f'{pct} %'} | {ejemplo} |")
    return f"Filas: {n_filas:,}\n\n" + "\n".join(filas)


def main():
    movimientos = pd.read_csv(CARPETA_PROCESADOS / "movimientos.csv", encoding="utf-8-sig", low_memory=False)
    normas = pd.read_csv(CARPETA_PROCESADOS / "normas.csv", encoding="utf-8-sig", low_memory=False)
    normas_con_texto = normas[normas["estado_extraccion"] != "sin texto descargado"]
    ARCHIVO_SALIDA.parent.mkdir(exist_ok=True)
    texto = ("# Diccionario de datos — Designaciones de El Peruano\n\n"
             "Fuentes: **ÍNDICE** = servicio de designaciones de El Peruano; **LISTADO** = listado general de normas "
             "(trae las que el índice omite, como ministros y embajadores); **PDF** = texto oficial de la norma; "
             "**DERIVADO** = calculado a partir de lo anterior.\n\n"
             "Una celda vacía significa que la norma no trae ese dato o que la regla de extracción no lo encontró.\n\n"
             "## movimientos.csv — una fila por persona y movimiento\n\n"
             + tabla_markdown(MOVIMIENTOS, porcentaje_lleno(movimientos), len(movimientos)) +
             "\n\n## normas.csv — una fila por norma\n\n"
             "(Las columnas de fecha, institución, dispositivo, sumilla, firmantes y enlaces son las mismas de movimientos.csv; "
             "el % se calcula sobre las normas con texto descargado.)\n\n"
             + tabla_markdown(NORMAS, porcentaje_lleno(normas_con_texto), len(normas)) + "\n")
    ARCHIVO_SALIDA.write_text(texto, encoding="utf-8")
    print("Diccionario escrito en", ARCHIVO_SALIDA, "| columnas sin describir:",
          sorted(set(movimientos.columns) - {c for c, *_ in MOVIMIENTOS} - {"firmante2_nombre", "firmante2_cargo",
                                                                          "firmante3_nombre", "firmante3_cargo"}))


if __name__ == "__main__":
    main()
