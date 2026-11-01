# ============================================================
# Designaciones de El Peruano — Script 06: preparar la base para el análisis
# ------------------------------------------------------------
# Agrega columnas NUEVAS a la tabla de movimientos; no cambia ni borra ninguna columna
# ni fila existente. Sigue los procesos 12 a 15 del mapa (docs/mapa_de_procesos.md):
#   12. Uniformar institución, completar sector y convertir fechas
#   13. Marcar el ámbito de cada movimiento (qué tipo de designación es)
#   14. Completar el sexo según el nombre de pila (columna aparte, marcada como inferida)
#   15. Identificar a cada persona (id_persona), clasificar el nivel del cargo y ubicarlo en la estructura
# Cada proceso imprime cuántos registros afecta.
#
# Insumo:    datos/procesados/movimientos.csv (script 03)
# Resultado: datos/procesados/movimientos_analisis.csv (mismas filas + columnas nuevas)
#
# Uso (desde la carpeta tarea_3):
#   python scripts/06_preparar_analisis.py
# ============================================================

# --- Paquetes ---
# re: reglas de texto (expresiones regulares) para clasificar cargos e instituciones
import re
# unicodedata: quitar tildes para comparar textos escritos de distinta forma
import unicodedata
# pathlib: manejar rutas de carpetas y archivos
from pathlib import Path
# pandas: trabajar la tabla de movimientos
import pandas as pd

CARPETA_PROCESADOS = Path(__file__).resolve().parent.parent / "datos" / "procesados"


def sin_tildes(texto):
    """Antes: "Ministerio Público " | Después: "MINISTERIO PUBLICO" (mayúsculas, sin tildes ni espacios sobrantes)"""
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", texto).upper().strip()


# ============================================================
# PROCESO 12: Uniformar institución, completar sector y convertir fechas
# Insumo:    movimientos.csv
# Resultado: columnas nuevas institucion_normalizada, sector_completado,
#            fecha_publicacion_dt, fecha_emision_corregida y nota_fecha
# ============================================================
# dtype=str: se lee todo como texto para no alterar códigos ni DNI (ej. "01234567" no pierde el 0)
movimientos = pd.read_csv(CARPETA_PROCESADOS / "movimientos.csv", encoding="utf-8-sig", dtype=str)
print("Movimientos leídos (filas, columnas):", movimientos.shape)

# --- 12.1 Institución: una sola escritura por institución ---
# Clave de comparación: sin tildes y sin el agregado "Publicación Digital" del listado
#   Antes: "MINISTERIO PÚBLICO" / "MINISTERIO PUBLICO" | Después: misma clave "MINISTERIO PUBLICO"
institucion_limpia = movimientos["institucion"].str.replace(r"\s+Publicaci[óo]n Digital$", "", regex=True)
clave_institucion = institucion_limpia.map(sin_tildes)
# Para cada clave se elige la escritura más frecuente (como "moda" en Excel)
escritura_mas_comun = institucion_limpia.groupby(clave_institucion).agg(lambda s: s.value_counts().index[0])
movimientos["institucion_normalizada"] = clave_institucion.map(escritura_mas_comun)
cambiadas = (movimientos["institucion_normalizada"] != movimientos["institucion"]).sum()
print(f"12.1 institucion_normalizada: {cambiadas} filas con una escritura distinta a la original "
      f"({movimientos['institucion'].nunique()} -> {movimientos['institucion_normalizada'].nunique()} instituciones)")

# --- 12.2 Sector: completar los vacíos por regla (aprobado el 30/10/2026) ---
def sector_por_regla(institucion):
    """Antes: "GOBIERNO REGIONAL DE AYACUCHO" (sin sector) | Después: "GOBIERNOS REGIONALES" """
    clave = sin_tildes(institucion)
    if "GOBIERNO REGIONAL" in clave:
        return "GOBIERNOS REGIONALES"
    if "MUNICIPALIDAD" in clave:
        return "GOBIERNOS LOCALES"
    if "AUTORIDAD NACIONAL DE CONTROL" in clave or "DEFENSORIA DEL PUEBLO" in clave:
        return "ORGANISMOS AUTÓNOMOS"
    return None


sin_sector = movimientos["sector_ep"].isna()
movimientos["sector_completado"] = movimientos["sector_ep"]
movimientos.loc[sin_sector, "sector_completado"] = movimientos.loc[sin_sector, "institucion"].map(sector_por_regla)
print(f"12.2 sector_completado: {sin_sector.sum()} filas sin sector; quedan vacías "
      f"{movimientos['sector_completado'].isna().sum()}")
print(movimientos.loc[sin_sector, ["institucion", "sector_completado"]].value_counts().to_string())
# Una sola escritura por sector: el índice de 2022-2023 escribe algunos sin tilde ("ORGANISMOS AUTONOMOS")
#   Antes: "ORGANISMOS AUTONOMOS" / "ORGANISMOS AUTÓNOMOS" | Después: la escritura más frecuente de las dos
clave_sector = movimientos["sector_completado"].map(lambda s: sin_tildes(s) if isinstance(s, str) else s)
escritura_sector = movimientos.groupby(clave_sector)["sector_completado"].agg(lambda s: s.mode().iloc[0])
sector_uniforme = clave_sector.map(escritura_sector)
print(f"     sector con otra escritura (sin tilde) unificado: {(sector_uniforme != movimientos['sector_completado']).sum()} filas")
movimientos["sector_completado"] = sector_uniforme

# --- 12.3 Fechas: de texto a fecha, con corrección de errores del original ---
# pd.to_datetime(): "05/11/2024" (texto) -> 2024-11-05 (fecha con la que se puede restar u ordenar)
movimientos["fecha_publicacion_dt"] = pd.to_datetime(movimientos["fecha_publicacion"], dayfirst=True)
movimientos["fecha_emision_corregida"] = pd.to_datetime(movimientos["fecha_emision"], errors="coerce")
# Errores de tipeo en el propio diario, verificados leyendo el PDF:
CORRECCIONES_FECHA = {
    "2542401-1": ("2026-08-11", "el original dice 2021 en una resolución numerada 2026"),
    "2398259-1": ("2025-05-09", "el original dice '20025'"),
    # Encontradas al ampliar a nov-2022 / oct-2024 (texto verificado en el PDF)
    "2137177-1": ("2022-12-22", "el original dice 2024 en una resolución numerada 2022"),
    "2172036-1": ("2023-04-24", "el original dice 2024 en una resolución numerada 2023"),
    "2151318-1": ("2023-02-13", "el original dice 2013 en una resolución numerada 2023"),
    "2253503-1": ("2024-01-17", "el original dice '20024'"),
}
movimientos["nota_fecha"] = ""
for codigo, (fecha, nota) in CORRECCIONES_FECHA.items():
    filas = movimientos["codigo_norma"] == codigo
    movimientos.loc[filas, "fecha_emision_corregida"] = pd.Timestamp(fecha)
    movimientos.loc[filas, "nota_fecha"] = nota
    print(f"12.3 fecha corregida en {codigo}: {filas.sum()} filas ({nota})")
print("     Publicación:", movimientos["fecha_publicacion_dt"].min().date(), "a",
      movimientos["fecha_publicacion_dt"].max().date())


# ============================================================
# PROCESO 13: Marcar el ámbito de cada movimiento
# Insumo:    institución, cargo, sumilla y texto del artículo
# Resultado: columna ambito y columna en_analisis_principal (Verdadero/Falso)
# ============================================================
# Las reglas se revisan en orden: la primera que se cumple decide el ámbito.
REGLAS_AMBITO = [
    ("notarios", r"\bnotari[oa]s?\b"),
    ("fedatarios, coactivos y responsables", r"fedatari|ejecutor(?:a|es)?\s+coactiv|auxiliar(?:es)?\s+coactiv|"
     r"funcionari[oa]s?\s+responsable|responsable\s+(?:del?|de\s+la)\s+(?:portal|acceso|entrega|elaboraci|"
     r"transparencia|libro|registro|remitir|brindar|atender)"),
    ("control institucional (OCI)", r"[óo]rgano\s+de\s+control\s+institucional|\bOCI\b"),
    ("subprefectos y prefectos", r"\b(?:sub)?prefect"),
    # "fiscal" seguido de su rango (no "Política Fiscal" del MEF)
    ("fiscales", r"\bfiscal(?:es)?\s+(?:adjunt|provincial|superior|suprem|de\s+la\s+naci|coordinador|titular|provisional)"),
    ("poder judicial y fuero militar", r"\bjuez|\bjueza|\bvocal(?:es)?\s+(?:supremo|superior|del?\s+(?:la\s+)?(?:sala|tribunal\s+supremo))|"
     r"magistrad|presidente\s+de\s+la\s+corte|juzgado|\bsala\s+(?:penal|civil|laboral|mixta|suprema|superior)"),
    ("fuerzas armadas y policía", r"\bempleo\b|agregad[oa]\s+(?:de\s+defensa|militar|naval|a[ée]re)|"
     r"comandante\s+general|jefe\s+del\s+comando\s+conjunto|inspector\s+general\s+del\s+(?:ej[ée]rcito|marina|fuerza)"),
    ("servicio diplomático", r"embajador|c[óo]nsul|consulado|representante\s+permanente|misi[óo]n\s+permanente|"
     r"servicio\s+diplom[áa]tico"),
    ("procuradores", r"procurador"),
    # Comisiones temporales; NO las que dirigen una entidad ("Comisión Nacional ... DEVIDA", "Comisión Organizadora")
    ("comités y comisiones", r"comit[ée]|grupo\s+de\s+trabajo|jurado\s+electoral|local\s+de\s+votaci|"
     r"coordinador(?:es)?\s+de\s+local|comisi[óo]n\s+(?:especial|t[ée]cnica|multisectorial|sectorial|"
     r"de\s+(?:selecci|evaluaci|concurso|procesos?|inventario|transferencia|cautela|[ée]tica))"),
    # "consejo de" sin "Ministros": la "Presidencia del Consejo de Ministros" es un ministerio, no un consejo
    # (corregido el 31/10/2026: 294 movimientos de la PCM estaban aquí)
    ("directorios y consejos", r"directorio|consejo\s+directivo|consejo\s+nacional|consejo\s+de\s+(?!ministros)|junta\s+directiva|"
     r"comisi[óo]n\s+organizadora|\bmiembro|representante|\btitular(?:es)?\b|\balterno|\bsuplente"),
]
# Grupos del análisis principal de rotación y redes (aprobado el 30/10/2026):
# designaciones políticas o de confianza. Los demás quedan para análisis aparte.
AMBITOS_PRINCIPALES = {"confianza y directivos", "subprefectos y prefectos", "directorios y consejos",
                       "servicio diplomático", "procuradores"}

# Representantes o miembros ante un órgano colegiado (aprobado el 30/10/2026). En estas normas el
# "cargo" suele ser la oficina de origen ("de la Dirección General de Contabilidad Pública"), así que
# la función se lee en la sumilla: "Designan representantes del MEF ante la Comisión Evaluadora..."
SUMILLA_REPRESENTANTES = (r"^(?:Designan|Formalizan\s+(?:la\s+)?designaci[óo]n\s+de)\s+(?:a\s+)?(?:los\s+|las\s+)?"
                          r"(?:dos\s+)?(?:representantes?|miembros?|integrantes)\b")
# Primer órgano que nombra la sumilla. "Consejo Directivo" va antes que "Consejo" para que gane el más largo
ORGANO_COLEGIADO = (r"directorio|consejo\s+directivo|comit[ée]\s+directivo|consejo|comit[ée]|comisi[óo]n|"
                    r"cuerpo\s+colegiado|grupo\s+de\s+trabajo|junta|mesa|autoridades")
# Órganos que gobiernan una entidad (aprueban presupuesto, eligen a la gerencia): puesto de poder
ORGANO_DE_GOBIERNO = r"directorio|consejo\s+directivo|comit[ée]\s+directivo"
# Casos revisados a mano en los que la regla no basta
AMBITO_POR_NORMA = {
    "2520807-1": ("comités y comisiones", "Comité Directivo Nacional de coordinación: no gobierna una entidad"),
}


def ambito_por_sumilla(fila):
    """Antes: sumilla "Designan representantes ... ante la Comisión Evaluadora ..."
    | Después: "comités y comisiones" (o "directorios y consejos", o None si no es de representantes)"""
    if fila["codigo_norma"] in AMBITO_POR_NORMA:
        return AMBITO_POR_NORMA[fila["codigo_norma"]][0]
    sumilla = str(fila["sumilla"])
    # Comisión organizadora de una universidad: gobierna la universidad (el cargo a veces solo dice "Presidente")
    if re.search(r"Comisi[óo]n\s+Organizadora", sumilla, re.I):
        return "directorios y consejos"
    if not re.search(SUMILLA_REPRESENTANTES, sumilla, re.I):
        return None
    if re.search(r"president[ae]\s+ejecutiv", sumilla, re.I):
        return None       # "representante del Estado ... quien desempeñará el cargo de Presidenta Ejecutiva"
    # "Presidencia del Consejo de Ministros" es una institución, no el órgano al que se designa
    organo = re.search(ORGANO_COLEGIADO, re.sub(r"Consejo\s+de\s+Ministros", "", sumilla, flags=re.I), re.I)
    if organo and re.fullmatch(ORGANO_DE_GOBIERNO, organo.group(0), re.I):
        return "directorios y consejos"
    return "comités y comisiones"   # comisiones, comités, consejos consultivos u honoríficos, cuerpos ad hoc


# Abreviaturas de las tablas militares de "asignación de empleos" (GRAL BRIG, CMDTE, CCFFAA...)
TABLA_MILITAR = r"\bGRAL\b|\bCMDTE\b|\bVALM\b|\bCALM\b|CCFFAA|COGAE|oficial(?:es)?\s+general|personal\s+militar|\bempleos?\b"


def ambito_de(fila):
    """Antes: una fila con institución, cargo y texto | Después: "fiscales", "confianza y directivos", etc."""
    cargo = fila["cargo"] if isinstance(fila["cargo"], str) else ""
    # Si no hay cargo, se usa el comienzo del artículo y la sumilla
    texto = cargo or f"{str(fila['texto_articulo'])[:300]} {fila['sumilla']}"
    # Texto amplio (cargo + artículo + sumilla): solo para ámbitos de una institución concreta,
    # porque en sus tablas el "cargo" a veces queda con el nombre de la entidad ("MUNICIPALIDAD PROVINCIAL")
    texto_amplio = f"{cargo} {str(fila['texto_articulo'])[:400]} {fila['sumilla']}"
    institucion = sin_tildes(fila["institucion"])
    for ambito, patron in REGLAS_AMBITO:
        if ambito == "control institucional (OCI)" and "CONTRALORIA" in institucion:
            if re.search(patron, texto_amplio, re.I):
                return ambito
        if ambito == "fiscales" and "MINISTERIO PUBLICO" in institucion:
            # "en la Fiscalía Provincial Penal de Paita", "con reserva de su plaza de origen": son fiscales
            if re.search(patron + r"|fiscal[ií]a\s+(?:provincial|superior|suprema|corporativa|especializada)|"
                         r"despacho|distrito\s+fiscal|reserva\s+de\s+su\s+plaza", texto_amplio, re.I):
                return ambito
        if ambito == "fuerzas armadas y policía":
            # Solo en Defensa/Interior, con grado militar o tabla de empleos
            if institucion not in ("DEFENSA", "INTERIOR"):
                continue
            grado = fila["grado_militar_policial"] if isinstance(fila["grado_militar_policial"], str) else ""
            en_actividad = grado and not re.search(r"\(r\)|retiro", grado, re.I)
            if not (en_actividad or re.search(patron + "|" + TABLA_MILITAR, texto_amplio, re.I)):
                continue
            if re.match(r"(?:vice)?ministr|secretari[oa]\s+general|jef[ea]\s+de\s+gabinete|asesor", cargo, re.I):
                continue          # un militar en un cargo político (viceministro, asesor) es confianza
            return ambito
        if re.search(patron, texto, re.I):
            return ambito
    # Solo para las filas que no cumplieron ninguna regla: representantes ante comisiones o directorios
    return ambito_por_sumilla(fila) or "confianza y directivos"


# .apply(..., axis=1): aplica la función fila por fila (como arrastrar una fórmula en Excel)
#   Antes: sin columna ambito | Después: cada fila con su ámbito
movimientos["ambito"] = movimientos.apply(ambito_de, axis=1)
movimientos["en_analisis_principal"] = movimientos["ambito"].isin(AMBITOS_PRINCIPALES)
print("\n13. Ámbito (movimientos y normas):")
resumen_ambito = movimientos.groupby("ambito").agg(movimientos=("id_movimiento", "size"),
                                                   normas=("codigo_norma", "nunique"))
print(resumen_ambito.sort_values("movimientos", ascending=False).to_string())
print("En el análisis principal:", movimientos["en_analisis_principal"].sum(), "movimientos")


# ============================================================
# PROCESO 14: Completar el sexo según el nombre de pila
# Insumo:    nombre_normalizado y sexo_segun_norma (cuando la norma dice "señor"/"señora")
# Resultado: columnas sexo_inferido, sexo_analisis y sexo_origen; sexo_segun_norma no se toca
# ============================================================
def primer_nombre(nombre):
    """Antes: "María del Carmen Pérez Ramos" | Después: "MARIA" (primera palabra, sin tildes)"""
    palabras = sin_tildes(nombre).split() if isinstance(nombre, str) else []
    return palabras[0] if palabras else ""


movimientos["primer_nombre"] = movimientos["nombre_normalizado"].map(primer_nombre)
# Diccionario aprendido de la misma base: solo filas cuyo sexo lo dice la norma
con_sexo = movimientos[movimientos["sexo_segun_norma"].isin(["M", "F"])]
conteo = pd.crosstab(con_sexo["primer_nombre"], con_sexo["sexo_segun_norma"])
conteo["total"] = conteo.sum(axis=1)
conteo["mayoria"] = conteo[["F", "M"]].idxmax(axis=1)
conteo["acuerdo"] = conteo[["F", "M"]].max(axis=1) / conteo["total"]
# Regla: el nombre se usa si aparece al menos 3 veces y el 95 % o más tiene el mismo sexo
# (descarta nombres ambiguos y apellidos que se colaron como primera palabra)
sexo_por_nombre = conteo.loc[(conteo["total"] >= 3) & (conteo["acuerdo"] >= 0.95), "mayoria"]
print(f"\n14. Nombres de pila con sexo confiable: {len(sexo_por_nombre)} de {len(conteo)} distintos")

sin_sexo = ~movimientos["sexo_segun_norma"].isin(["M", "F"]) & movimientos["nombre_normalizado"].notna()
movimientos["sexo_inferido"] = ""
movimientos.loc[sin_sexo, "sexo_inferido"] = movimientos.loc[sin_sexo, "primer_nombre"].map(sexo_por_nombre).fillna("")
movimientos["sexo_analisis"] = movimientos["sexo_segun_norma"].where(
    movimientos["sexo_segun_norma"].isin(["M", "F"]), movimientos["sexo_inferido"])
movimientos["sexo_origen"] = "sin dato"
movimientos.loc[movimientos["sexo_inferido"] != "", "sexo_origen"] = "inferido por nombre"
movimientos.loc[movimientos["sexo_segun_norma"].isin(["M", "F"]), "sexo_origen"] = "norma"
print(f"    Filas con nombre y sin sexo en la norma: {sin_sexo.sum()} | completadas: "
      f"{(movimientos['sexo_inferido'] != '').sum()}")
print(movimientos["sexo_origen"].value_counts().to_string())


# ============================================================
# PROCESO 15: Identificar a cada persona, clasificar el nivel del cargo y ubicarlo en la estructura
# Insumo:    nombre_normalizado, dni y cargo
# Resultado: columnas clave_persona, id_persona, nombre_dudoso, nivel_cargo, institucion_del_cargo,
#            nivel_organizacional, unidad_organica, unidad_superior y ubicacion
# ============================================================
# --- 15.1 Clave de persona: el nombre sin tildes, sin signos y en mayúsculas ---
#   Antes: "José Luis Peñaranda Sánchez" | Después: "JOSE LUIS PENARANDA SANCHEZ"
movimientos["clave_persona"] = (movimientos["nombre_normalizado"].fillna("").map(sin_tildes)
                                .str.replace(r"[^A-Z ]", "", regex=True).str.replace(r"\s+", " ", regex=True).str.strip())

# Homónimos: misma clave con DNI distintos. En ese caso se agrega el DNI a la clave.
dni_por_clave = movimientos[movimientos["dni"].notna()].groupby("clave_persona")["dni"].nunique()
claves_homonimas = set(dni_por_clave[dni_por_clave > 1].index)
es_homonimo = movimientos["clave_persona"].isin(claves_homonimas) & movimientos["dni"].notna()
movimientos.loc[es_homonimo, "clave_persona"] = movimientos.loc[es_homonimo, "clave_persona"] + " #" + movimientos.loc[es_homonimo, "dni"]
print(f"\n15.1 Nombres con más de un DNI (homónimos separados): {len(claves_homonimas)} nombres, {es_homonimo.sum()} filas")

# Nombres dudosos: empiezan con un cargo, tienen 7 o más palabras o una sola
EMPIEZA_CON_CARGO = r"^(?:SUB)?(?:GERENTE|JEFE|JEFA|DIRECTOR|DIRECTORA|ASESOR|COORDINADOR|SECRETARI|PRESIDENTE|MUNICIPALIDAD|DISTRITAL|PROVINCIAL)\b"
n_palabras = movimientos["clave_persona"].str.split().str.len()
movimientos["nombre_dudoso"] = (movimientos["clave_persona"] != "") & (
    movimientos["clave_persona"].str.match(EMPIEZA_CON_CARGO) | (n_palabras >= 7) | (n_palabras < 2))
print(f"     Nombres dudosos: {movimientos['nombre_dudoso'].sum()} filas "
      f"({(movimientos['nombre_dudoso'] & movimientos['en_analisis_principal']).sum()} en el análisis principal)")

# --- 15.2 id_persona: código estable desde el REGISTRO MAESTRO privado (scripts/registro_personas.py) ---
# Cambiado el 01/11/2026 (acordado con el autor): antes era un número por orden de aparición (P00001...), que se corría
# al ampliar el periodo. Ahora cada persona tiene un código aleatorio (P-XXXXX) que nunca cambia; la tabla
# código-nombre queda en datos/privado/registro_personas.csv (no se publica). El código no revela el nombre.
import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parent))
import registro_personas
con_clave = movimientos[movimientos["clave_persona"] != ""]
tabla_personas = (con_clave.sort_values(["fecha_publicacion_dt", "codigo_norma", "id_movimiento"])
                  .groupby("clave_persona", sort=False)
                  .agg(nombre_completo=("nombre_tal_cual", lambda s: s.dropna().mode().iloc[0] if s.notna().any() else ""),
                       dni=("dni", lambda s: s.dropna().iloc[0] if s.notna().any() else ""),
                       primera_aparicion=("fecha_publicacion_dt", "min"))
                  .reset_index())
codigo_de = registro_personas.asignar(tabla_personas, origen="designación (06)")
movimientos["id_persona"] = movimientos["clave_persona"].map(codigo_de)
print(f"15.2 Personas distintas: {len(codigo_de)} | movimientos sin persona: {movimientos['id_persona'].isna().sum()}")

# --- 15.3 Nivel del cargo: reglas sobre el comienzo del cargo ---
# Categorías del usuario: MIN, VMIN, SECGEN, JEFEGAB, ASES, DIRGEN, DIR, JEFE, GERGEN, PRES, SUPER, MIEMBRO
REGLAS_NIVEL = [
    ("JEFEGAB", r"jef[ea](?:/a)?\s+(?:de\s+|del\s+)?gabinete"),
    ("VMIN", r"vice\s*ministr"),
    ("MIN", r"ministr[oa]\s+(?:de|del)\s+(?!.*servicio\s+diplom)"),
    ("SECGEN", r"secretari[oa](?:/a)?\s+general"),
    ("SUPER", r"(?:vice\s*)?superintendent"),
    ("GERGEN", r"gerent[ea](?:/a)?\s+general"),
    ("DIRGEN", r"director[a]?(?:/a)?\s+(?:general|ejecutiv)|director[a]?(?:/a)?\s+de\s+la\s+direcci[óo]n\s+general"),
    ("PRES", r"(?:vice)?president[ea]"),
    ("ASES", r"asesor"),
    ("DIR", r"(?:sub\s*)?director"),
    ("JEFE", r"jef[ea]|(?:sub)?gerent[ea]|coordinador|ejecutiv[oa]|intendente|administrador|responsable|supervisor"),
    ("MIEMBRO", r"miembro|representante|integrante|consejer[oa]|vocal"),
]


def nivel_de(cargo):
    """Antes: "Directora General de la Oficina General de Administración" | Después: "DIRGEN"
    (se mira el comienzo del cargo; si ninguna regla aplica: "OTRO")"""
    if not isinstance(cargo, str) or not cargo.strip():
        return "SIN CARGO"
    comienzo = sin_tildes(cargo).lower()
    # Se quitan arranques que no son el cargo: "en el cargo de confianza de ...", "clasificado como (DSLDR) de ..."
    comienzo = re.sub(r"^(?:en\s+)?(?:e?l\s+)?(?:cargo|puesto)\s+(?:de\s+confianza\s+)?(?:de|como)?\s*|"
                      r"^clasificado\s+como\s+.*?\)\s+de\s+|^temporalmente,?\s+(?:a\s+partir\s+del?\s+[^,]+,\s+)?(?:como\s+)?",
                      "", comienzo)[:60]
    for nivel, patron in REGLAS_NIVEL:
        if re.match(patron, comienzo):
            return nivel
    return "OTRO"


movimientos["nivel_cargo"] = movimientos["cargo"].map(nivel_de)
print("\n15.3 Nivel del cargo (solo análisis principal):")
print(movimientos.loc[movimientos["en_analisis_principal"], "nivel_cargo"].value_counts().to_string())

# --- 15.4 Institución del cargo: a qué ministerio pertenece el puesto (aprobado el 30/10/2026, etapa 1) ---
# Los ministros se nombran por resolución suprema publicada bajo la PCM: "Ministra de Estado en el
# Despacho de Desarrollo e Inclusión Social". Para ubicarlos en su ministerio se lee el cargo.
MINISTERIOS = sorted(set(movimientos.loc[movimientos["sector_completado"] == "PODER EJECUTIVO", "institucion_normalizada"])
                     - {"PRESIDENCIA DEL CONSEJO DE MINISTROS", "DESPACHO PRESIDENCIAL"})
ALIAS_MINISTERIO = {"PRODUCCION": "PRODUCE"}


def ministerio_del_ministro(cargo):
    """Antes: "Ministro de Estado en el Despacho de Energía y Minas" | Después: "ENERGÍA Y MINAS" ("" si no se reconoce)"""
    # Primero "Despacho de X"; si no está, "Ministro de X" (sin "de Estado")
    m = (re.search(r"Despacho\s+(?:de\s+la|del|de)\s+([^,]+)", str(cargo), re.I)
         or re.search(r"Ministr[oa]\s+(?:de\s+la|del|de)\s+(?!Estado)([^,]+)", str(cargo), re.I))
    if not m:
        return ""
    nombre = sin_tildes(m.group(1)).strip()
    nombre = ALIAS_MINISTERIO.get(nombre.split()[0], nombre)
    for ministerio in MINISTERIOS:
        clave = sin_tildes(ministerio).split(",")[0]
        if nombre.startswith(clave) or clave.startswith(nombre):
            return ministerio
    return ""


movimientos["institucion_del_cargo"] = movimientos["institucion_normalizada"]
es_ministro = movimientos["nivel_cargo"] == "MIN"
ministerio_leido = movimientos.loc[es_ministro, "cargo"].map(ministerio_del_ministro)
movimientos.loc[es_ministro & (ministerio_leido != "").reindex(movimientos.index, fill_value=False),
                "institucion_del_cargo"] = ministerio_leido[ministerio_leido != ""]
print(f"\n15.4 institucion_del_cargo: {(movimientos['institucion_del_cargo'] != movimientos['institucion_normalizada']).sum()} "
      f"ministros ubicados en su ministerio | sin reconocer: {(ministerio_leido == '').sum()}")

# --- 15.5 Ubicar el cargo en la estructura: unidad orgánica, nivel N1-N4 y tipo de entidad ---
# Se lee la cadena de órganos que trae el propio cargo (la nomenclatura del Estado es común):
#   "Director de la Dirección X de la Dirección General Y del Viceministerio Z del Ministerio W"
#   -> título "Director", órganos [Dirección X, Dirección General Y, Viceministerio Z], entidad "Ministerio W"
# Nivel (dentro de su propia entidad: ministerio, programa u organismo):
#   N1 alta dirección (despachos, secretaría general, gabinete, presidencia o dirección ejecutiva, gerencia general)
#   N2 órganos que dependen de la alta dirección (direcciones u oficinas generales; en programas y organismos, sus unidades,
#      oficinas, gerencias o direcciones), N3 unidades orgánicas dentro de ellos, N4 subunidades o más abajo
ORGANO = (r"Despacho\s+(?:Vice\s*)?[Mm]inisterial|Viceministerio|Secretar[íi]a\s+General|Sub\s*secretar[íi]a|Secretar[íi]a|"
          r"Gabinete(?:\s+de\s+Asesores)?|Presidencia\s+Ejecutiva|Presidencia(?=\s+(?:del|de\s+la)\s+)(?!\s+del\s+Consejo\s+de\s+Ministros)|"
          r"Jefatura\s+(?:Zonal|Regional|Desconcentrada)|Jefatura(?:\s+(?:Institucional|Nacional))?|"
          r"Gerencia\s+(?:General|Municipal)|Superintendencia\s+(?:Nacional\s+)?Adjunta|Alta\s+Direcci[óo]n|"
          r"Direcci[óo]n\s+(?:Ejecutiva|General|Adjunta|Desconcentrada|Regional|Zonal|de\s+L[íi]nea)|Direcci[óo]n|"
          r"Sub\s*direcci[óo]n|Oficina\s+(?:General|Zonal|Desconcentrada|Regional|Departamental|de\s+Coordinaci[óo]n\s+Regional)|Oficina|"
          r"Sub\s*[Uu]nidad|Unidad\s+(?:Territorial|Zonal|Ejecutora|Funcional|Desconcentrada|de\s+L[íi]nea|Gerencial)|Unidad|"
          r"Sub\s*[Gg]erencia|Gerencia|Intendencia(?:\s+(?:Nacional|Regional))?|Divisi[óo]n|[ÁA]rea|Coordinaci[óo]n|Equipo|"
          r"Centro\s+Nacional|Escuela\s+Nacional|Tribunal|Procuradur[íi]a\s+P[úu]blica|"
          r"[ÓO]rgano\s+de\s+Control\s+Institucional|Programa(?!\s+Sectorial)|Proyecto\s+Especial|Proyecto")
# Entidades: donde termina la cadena (la institución misma, otro organismo, un programa, un hospital o una empresa)
ENTIDAD = (r"Ministerio|Despacho\s+Presidencial|Instituto|Superintendencia(?!\s+(?:Nacional\s+)?Adjunta)|Organismo|Autoridad|"
           r"Agencia|Servicio\s+Nacional|Seguro\s+(?:Integral|Social)|Archivo\s+General|Biblioteca\s+Nacional|"
           r"Procuradur[íi]a\s+General|Central\s+de\s+Compras|Comisi[óo]n\s+(?:de\s+Promoci[óo]n|Nacional)|Banco\s+(?:de\s+la\s+Naci[óo]n|Central|Agropecuario|de\s+Materiales)|Consejo\s+(?:Nacional|Superior)|"
           r"Registro\s+Nacional|Oficina\s+Nacional|Fondo|Presidencia\s+del\s+Consejo\s+de\s+Ministros|Gobierno\s+Regional|"
           r"Municipalidad|Universidad|Hospital|Entidad\s+Prestadora|Empresa|Sistema\s+Nacional|(?i:FONCODES)|"
           r"Centro\s+Nacional\s+de\s+(?:Estimaci[óo]n|Planeamiento\s+Estrat[ée]gico)|"   # CENEPRED y CEPLAN: organismos públicos
           r"Intendencia\s+Nacional\s+de\s+Bomberos")
ALTA_DIRECCION = re.compile(r"Despacho|Viceministerio|Secretar[íi]a\s+General|Gabinete|Presidencia|"
                            r"Jefatura(?!\s+(?:Zonal|Regional|Desconcentrada))|Gerencia\s+(?:General|Municipal)|"
                            r"Superintendencia|Alta\s+Direcci|Direcci[óo]n\s+Ejecutiva", re.I)
PROGRAMA = re.compile(r"^(?:Programa(?!\s+Sectorial)|Proyecto|Fondo|FONCODES)", re.I)
SUBUNIDAD = re.compile(r"^(?:Sub|Divisi|[ÁA]rea|Coordinaci|Equipo)", re.I)
ORGANO_GENERAL = re.compile(r"General|Centro\s+Nacional|Procuradur|[ÓO]rgano\s+de\s+Control|Intendencia\s+Nacional|Tribunal|"
                            r"Escuela\s+Nacional", re.I)
DESCONCENTRADO = re.compile(r"Territorial|Zonal|Desconcentrad|Regional|Departamental|\ben\s+la\s+ciudad\s+de\b|"
                            r"\bsede\s+(?:regional|desconcentrada)|Filial|Hospital|Redes\s+Integradas|Estaci[óo]n\s+Experimental", re.I)
# Corte de la cadena: "de la Dirección ...", "del Programa ...", "de Presidencia Ejecutiva ..."
CORTE = re.compile(rf"(?:,\s*|\s+)(?:de\s+la|del|de\s+los|de\s+las|de|en\s+la|en\s+el)\s+(?=(?:{ORGANO}|{ENTIDAD})\b)")
ALTA_POR_NIVEL = {"MIN": "Despacho Ministerial", "VMIN": "Despacho Viceministerial", "SECGEN": "Secretaría General",
                  "JEFEGAB": "Gabinete de Asesores"}
# Según el ROF (MIDIS art. 13, Interior art. 14): la Secretaría General y los viceministerios dependen del Despacho
# Ministerial, y el Gabinete de Asesores forma parte de él (Interior: "El Despacho Ministerial cuenta con un Gabinete de Asesores")
SUPERIOR_POR_NIVEL = {"VMIN": "Despacho Ministerial", "SECGEN": "Despacho Ministerial", "JEFEGAB": "Despacho Ministerial"}


def limpiar_cargo(cargo):
    """Antes: "Ejecutiva Adjunta I (CAP – P Nº 009), Nivel F-4, del Despacho Ministerial, a partir del 1 de julio"
    | Después: "Ejecutiva Adjunta I del Despacho Ministerial" (sin plaza, nivel remunerativo ni fechas)"""
    c = re.sub(r"\([^)]*\)", " ", cargo)
    c = re.sub(r",?\s*Nivel\s+F[\s\-–]?\d\s*,?", " ", c, flags=re.I)
    c = re.sub(r",?\s*con\s+C[óo]digo\s+AIRHSP\s+N[º°]?\s*\d+\s*,?", " ", c, flags=re.I)
    c = re.sub(r",?\s*(?:contenido|previsto|considerado)\s+en\s+el\s+(?:Cuadro|CAP|Presupuesto).*$", "", c, flags=re.I)
    c = re.sub(r",?\s*(?:a\s+partir\s+del?|con\s+eficacia|con\s+efectividad|desde\s+el|hasta\s+el|en\s+adici[óo]n|"
               r"con\s+relaci[óo]n|ejerciendo|siendo|formula\b|quien|por\s+consiguiente|d[áa]ndos?e|d[áa]ndole|"
               r"el\s+\d+\s+de\s+\w+).*$", "", c, flags=re.I)
    c = re.sub(r"^(?:en\s+)?(?:e?l\s+)?(?:cargo|puesto)\s+(?:estructural\s+)?(?:de\s+confianza\s+)?(?:de|como)?\s*", "", c, flags=re.I)
    c = re.sub(r"^temporalmente,?\s+(?:como\s+)?", "", c, flags=re.I)
    c = re.sub(r"^Director[a]?\s+de\s+(?:Sistema\s+Administrativo|Programa\s+Sectorial)\s+[IVX]+\s*,?\s*"
               r"(?=(?:Jef|Direct|Coordin|Ejecutiv|Gerent|Responsable))", "", c, flags=re.I)
    return re.sub(r"\s+", " ", c).strip(" ,.;-–")


def cadena_de(cargo):
    """Antes: "Director de la Dirección X de la Dirección General Y del Ministerio Z"
    | Después: ("Director", ["Dirección X", "Dirección General Y"], "Ministerio Z")"""
    partes = CORTE.split(cargo)
    titulo, organos, entidad = partes[0].strip(), [], ""
    for parte in partes[1:]:
        parte = parte.strip(" ,.;")
        if re.match(rf"(?:{ENTIDAD})\b", parte) and not re.match(rf"(?:{ORGANO})\b", parte):
            entidad = parte
            break
        # "Ejecutivo de la Unidad X de la Unidad X": el mismo órgano repetido se cuenta una vez
        if organos and sin_tildes(organos[-1]) == sin_tildes(parte):
            continue
        organos.append(parte)
    # Nombre genérico seguido del específico: "Jefatura Zonal" + "Jefatura Zonal de Ica",
    # "Órgano Desconcentrado" + "Dirección Desconcentrada de Cultura de Ucayali": se queda el específico
    # "Oficina I", "Unidad II": categoría de plaza seguida de la oficina real ("Jefa de Oficina I de la Oficina de Abastecimiento")
    organos = [o for k, o in enumerate(organos)
               if not (k + 1 < len(organos) and (sin_tildes(organos[k + 1]).startswith(sin_tildes(o)) or
                                                 (re.match(r"[ÓO]rgano\s+Desconcentrado$", o, re.I)
                                                  and re.search(r"Desconcentrad", organos[k + 1], re.I)) or
                                                 re.match(r"(?:Oficina|Unidad)\s+[IVX]+$", o, re.I)))]
    return titulo, organos, entidad


def area_del_titulo(titulo):
    """Antes: "Intendente Nacional de Recursos Humanos" | Después: "Recursos Humanos" ("" si el título no nombra un área)"""
    # Acepta "director/a", "jefe(a)", "administrador II": "administrador II del Centro Juvenil Lima" -> "Centro Juvenil Lima"
    m = re.match(r"^(?:Sub\s*)?(?:Director|Directora|Jef[ea]|Gerente|Intendente|Coordinador|Coordinadora|Ejecutiv[oa]|"
                 r"Responsable|Supervisor|Supervisora|Administrador|Administradora)(?:\s*/\s*a|\s*\(a\))?(?:\s+[IVX]+)?"
                 r"(?:\s+(?:Nacional|General|Central|Adjunt[oa]))?\s+"
                 r"(?:de\s+(?:la\s+|el\s+|los\s+|las\s+)?|del\s+)(.+)$", titulo, re.I)
    # Categorías de plaza o nombres genéricos que no son un área: "Director de Órgano Desconcentrado", "Jefe de Oficina I"
    if not m or re.search(r"Sistema\s+Administrativo|Programa\s+Sectorial|\bde\s+L[íi]nea\b", titulo, re.I) or \
            re.match(r"(?:[ÓO]rgano\s+Desconcentrado|(?:Oficina|Unidad|Equipo)\s+[IVX]+)$", m.group(1).strip(), re.I):
        return ""        # "Director de Sistema Administrativo III", "Director de Línea": categorías de plaza, no áreas
    return m.group(1).strip()


def tipo_de_entidad(fila, organos, entidad):
    """Antes: sector, ámbito y cadena de órganos | Después: "sede central del ministerio", "programa o proyecto", etc."""
    sector, ambito = fila["sector_completado"], fila["ambito"]
    cadena = " ".join(organos + [entidad])
    if sector == "GOBIERNOS REGIONALES":
        return "gobierno regional"
    if sector == "GOBIERNOS LOCALES":
        return "municipalidad"
    if sector in ("ORGANISMOS AUTÓNOMOS", "PODER JUDICIAL"):
        return "organismo autónomo u otro poder"
    if ambito == "subprefectos y prefectos":
        return "prefecturas (Interior)"
    if ambito == "servicio diplomático":
        return "servicio exterior"
    if re.match(r"Entidad\s+Prestadora|Empresa|Banco", entidad, re.I) or re.search(r"\bEPS\b|S\.A\.", cadena):
        return "empresa pública"
    # "Superintendente Nacional de Aduanas...": el título ya nombra la superintendencia (un organismo público)
    if fila["nivel_cargo"] == "SUPER" and not re.search(r"Adjunt", cadena + fila["cargo"], re.I) and sector == "PODER EJECUTIVO":
        return "organismo público"
    if any(PROGRAMA.match(o) for o in organos) or PROGRAMA.match(entidad):
        return "programa o proyecto"
    if sector == "PODER EJECUTIVO" and DESCONCENTRADO.search(cadena):
        return "órgano desconcentrado"
    if sector != "PODER EJECUTIVO" or (entidad and not re.match(r"Ministerio|Presidencia\s+del\s+Consejo|Despacho\s+Presidencial",
                                                                 entidad, re.I)):
        return "organismo público"
    return "sede central del ministerio"


def ubicar_cargo(fila):
    """Antes: una fila con cargo, ámbito, nivel_cargo y sector
    | Después: [nivel_organizacional, unidad_organica, unidad_superior, ubicacion, entidad_del_cargo]
    (vacíos fuera del análisis principal)"""
    if not fila["en_analisis_principal"]:
        return pd.Series(["", "", "", "", ""])
    ambito, nivel_c = fila["ambito"], fila["nivel_cargo"]
    cargo = fila["cargo"] if isinstance(fila["cargo"], str) else ""
    titulo, organos, entidad = cadena_de(limpiar_cargo(cargo))
    ubicacion = tipo_de_entidad(fila, organos, entidad)
    # Programa u organismo donde está el puesto ("Programa Nacional Cuna Más", "Superintendencia Nacional de Migraciones");
    # vacío si el puesto está en el propio ministerio. Sirve para no juntar puestos de entidades distintas.
    programa = next((o for o in organos if PROGRAMA.match(o)), "")
    otra_entidad = entidad if entidad and not re.match(r"Ministerio|Presidencia\s+del\s+Consejo|Despacho\s+Presidencial",
                                                       entidad, re.I) else ""
    # Un "órgano" que en realidad es un organismo del sector: "Secretario General del Centro Nacional de Estimación..."
    # (CENEPRED) o "del Centro de Altos Estudios Nacionales" (CAEN)
    organismo = next((o for o in organos if re.match(r"Centro\s+Nacional\s+de\s+(?:Estimaci|Planeamiento\s+Estrat)|"
                                                     r"Centro\s+de\s+Altos\s+Estudios", o, re.I)), "")
    otra_entidad = otra_entidad or organismo
    entidad_del_cargo = (programa or otra_entidad)[:120]
    en_ministerio = ubicacion in ("sede central del ministerio", "órgano desconcentrado")
    unidad = organos[0] if organos else ""
    superior = organos[1] if len(organos) > 1 else ""
    if ambito == "directorios y consejos":
        nivel = "órgano colegiado"
    elif ambito in ("subprefectos y prefectos", "servicio diplomático"):
        nivel = "territorial o exterior"
    elif ambito == "procuradores":
        nivel, unidad = "N2", unidad or "Procuraduría Pública"
    elif nivel_c in ("MIN", "VMIN", "SECGEN", "JEFEGAB") or (
            # Presidente, superintendente o gerente general: N1 si encabeza la entidad, no si preside un órgano
            # interno ("Presidente del Tribunal de Disciplina Policial" es N2)
            nivel_c in ("SUPER", "GERGEN", "PRES")
            and (not organos or ALTA_DIRECCION.match(organos[0]) or PROGRAMA.match(organos[0]))):
        nivel = "N1"
        if nivel_c in ALTA_POR_NIVEL and not (organos and ALTA_DIRECCION.match(organos[0]) and nivel_c != "JEFEGAB"):
            # "Secretario General del CENEPRED" -> Secretaría General; "Jefe de Gabinete" / "Gabinete de Asesoramiento"
            # -> Gabinete de Asesores (un solo nombre para el mismo órgano)
            unidad = ALTA_POR_NIVEL[nivel_c]
        unidad = unidad or ALTA_POR_NIVEL.get(nivel_c, "Alta Dirección")
    elif not organos:
        area = area_del_titulo(titulo)
        if area:
            # El título nombra el área ("Jefe de Recursos Humanos de SUCAMEC"): nivel típico de ese órgano
            nivel = "N2" if (ORGANO_GENERAL.search(titulo) or not en_ministerio) else "N3"
            unidad = area
        elif entidad:
            nivel, unidad = "N1", "Alta Dirección"   # "Director Ejecutivo del Programa X", "Asesor del Programa X"
        else:
            nivel = "sin dato"
    else:
        # Profundidad: cuántos órganos hay antes de llegar a la alta dirección o al programa
        profundidad = 0
        for organo in organos:
            if ALTA_DIRECCION.match(organo) or PROGRAMA.match(organo):
                break
            profundidad += 1
        if profundidad == 0:
            # En la alta dirección o cabeza del programa, salvo que el título nombre un área propia
            # ("directora del Centro Juvenil Santa Margarita del Programa Nacional de Centros Juveniles")
            area = area_del_titulo(titulo)
            nivel_n, unidad = (2, area) if area else (1, unidad)
            # Área dentro de otra área del título: "jefe/a de Seguridad del Centro Juvenil Lima" -> un nivel más abajo
            if area and re.search(r"\b(?:del|de\s+la)\s+(?:Centro|Unidad|Oficina|Direcci|Sub|Servicio)", area, re.I):
                nivel_n = 3
        else:
            nivel_n = 1 + profundidad
            area = area_del_titulo(titulo)
            if area and sin_tildes(area)[:20] not in sin_tildes(organos[0]):
                nivel_n, unidad, superior = nivel_n + 1, area, organos[0]
            # Cadena incompleta (un solo órgano y no "General"): se asume el nivel típico de ese órgano
            if profundidad == 1 and not ORGANO_GENERAL.search(organos[0]):
                if en_ministerio:
                    minimo = 4 if SUBUNIDAD.match(organos[0]) else 3
                else:
                    minimo = 3 if SUBUNIDAD.match(organos[0]) else 2
                nivel_n = max(nivel_n, minimo)
        nivel = f"N{min(nivel_n, 4)}"
    # Oficina desconcentrada sin nombre propio: se le agrega la ciudad ("... en la ciudad de Tumbes")
    ciudad = re.search(r"en\s+la\s+ciudad\s+de\s+([A-ZÁÉÍÓÚÑ][\wáéíóúñ ]+?)(?:,|\s+departamento|$)", cargo)
    if ciudad and re.match(r"(?:Oficina|Direcci[óo]n)\s+Desconcentrada$", unidad, re.I):
        unidad = f"{unidad} de {ciudad.group(1).strip()}"
    if nivel == "N1" and nivel_c in SUPERIOR_POR_NIVEL and not re.match(r"Despacho\s+Ministerial", superior, re.I):
        superior = SUPERIOR_POR_NIVEL[nivel_c] if ubicacion == "sede central del ministerio" else superior
    return pd.Series([nivel, unidad[:150], superior[:150], ubicacion, entidad_del_cargo])


# .apply(..., axis=1): aplica la función fila por fila
#   Antes: sin estas columnas | Después: 5 columnas nuevas (solo con valor en el análisis principal)
movimientos[["nivel_organizacional", "unidad_organica", "unidad_superior", "ubicacion", "entidad_del_cargo"]] = \
    movimientos.apply(ubicar_cargo, axis=1)
principal = movimientos[movimientos["en_analisis_principal"]]
print("\n15.5 Ubicación (análisis principal):")
print(principal["ubicacion"].value_counts().to_string())
print("\n     Nivel organizacional (análisis principal):")
print(principal["nivel_organizacional"].value_counts().to_string())
print(f"     Con unidad orgánica identificada: {(principal['unidad_organica'] != '').sum()} de {len(principal)}")

# --- 15.6 Jerarquía del puesto "sobre el papel" (30/10/2026) ---
# El nivel organizacional dice DÓNDE está el puesto; la jerarquía, CUÁNTO PESA formalmente. Un asesor del
# Despacho está en N1 pero pesa menos que un Director General (N2). Orden respaldado por el nivel remunerativo
# que traen algunas normas: Secretario General F-6 > Director General F-5 > asesor de despacho F-4/F-5 >
# director de unidad orgánica F-3/F-4 > subunidad F-2/F-3. Es referencial: en la práctica el peso depende de más cosas.
JERARQUIAS = ["J1 Ministro", "J2 Viceministro", "J3 Secretario general, jefe de gabinete o titular de entidad",
              "J4 Director general o jefe de órgano", "J5 Asesor o apoyo de alta dirección",
              "J6 Jefe de unidad orgánica", "J7 Subunidad o apoyo"]
# Títulos de apoyo (no encabezan el órgano): "Ejecutiva Adjunta I", "Asesor II", "Especialista", "Coordinador de ..."
TITULO_DE_APOYO = re.compile(r"Adjunt|Asesor|Asistent|Especialista|Analista|Secretari[oa](?!\s+General)|Profesional|"
                             r"Coordinador(?:a)?(?!\s+(?:General|Ejecutiv|T[ée]cnic))|T[ée]cnico|Auxiliar", re.I)
NIVEL_REMUNERATIVO = r"(?:Nivel|Categor[íi]a)\s*(?:Remunerativ[oa]\s*)?:?\s*F[\s\-–]?0?([1-8])\b|\bF[\-–]0?([1-8])\b"


def jerarquia_de(fila):
    """Antes: nivel_cargo, nivel_organizacional, ubicación y título del cargo
    | Después: "J1 Ministro" ... "J7 Subunidad o apoyo" ("" fuera del análisis principal o sin nivel N1-N4)"""
    nivel, nivel_c, ubicacion = fila["nivel_organizacional"], fila["nivel_cargo"], fila["ubicacion"]
    cargo = fila["cargo"] if isinstance(fila["cargo"], str) else ""
    if not fila["en_analisis_principal"]:
        return ""
    if nivel_c == "MIN" or re.search(r"President[ea]\s+del\s+Consejo\s+de\s+Ministros", cargo, re.I) and nivel_c == "PRES":
        return JERARQUIAS[0]
    if nivel_c == "VMIN":
        return JERARQUIAS[1]
    if fila["ambito"] == "procuradores":
        return JERARQUIAS[3]
    if nivel not in ("N1", "N2", "N3", "N4"):
        return ""
    titulo = cadena_de(limpiar_cargo(cargo))[0]
    apoyo = bool(TITULO_DE_APOYO.search(titulo)) and nivel_c not in ("SECGEN", "JEFEGAB")
    en_ministerio = ubicacion in ("sede central del ministerio", "órgano desconcentrado")
    if nivel == "N1":
        if nivel_c in ("SECGEN", "JEFEGAB") and en_ministerio:
            return JERARQUIAS[2]
        # Titular de un organismo o programa: "Superintendente Nacional de Migraciones", "Director Ejecutivo de JUNTOS"
        es_titular = (nivel_c in ("PRES", "SUPER") or fila["unidad_organica"] == "Alta Dirección"
                      or bool(PROGRAMA.match(fila["unidad_organica"]))) and not apoyo
        if not en_ministerio and es_titular:
            return JERARQUIAS[2]
        # Secretario general o gerente general de un organismo o programa: conduce, pero no es el titular
        if not en_ministerio and (nivel_c in ("SECGEN", "GERGEN") or (nivel_c == "SUPER" and apoyo)):
            return JERARQUIAS[3]
        return JERARQUIAS[4]
    if nivel == "N2":
        return JERARQUIAS[5] if apoyo else JERARQUIAS[3]
    if nivel == "N3":
        return JERARQUIAS[6] if apoyo else JERARQUIAS[5]
    return JERARQUIAS[6]


movimientos["jerarquia_puesto"] = movimientos.apply(jerarquia_de, axis=1)
# Nivel remunerativo tal como lo dice la norma (solo cuando lo menciona): "Nivel F-4" -> "F-4"
texto_cargo = movimientos["cargo"].fillna("") + " " + movimientos["texto_articulo"].fillna("")
nivel_f = texto_cargo.str.extract(NIVEL_REMUNERATIVO)
movimientos["nivel_remunerativo"] = ("F-" + nivel_f[0].fillna(nivel_f[1])).fillna("")
principal = movimientos[movimientos["en_analisis_principal"]]
print("\n15.6 Jerarquía del puesto (análisis principal):")
print(principal["jerarquia_puesto"].replace("", "(no aplica: directorio, territorial o sin dato)").value_counts().sort_index().to_string())
# Verificación: el nivel remunerativo promedio debería bajar de J3 a J7
con_f = principal[principal["nivel_remunerativo"] != ""]
print(f"     Nivel remunerativo promedio por jerarquía ({len(con_f)} movimientos que lo mencionan):")
print(con_f.assign(F=con_f["nivel_remunerativo"].str[2:].astype(int)).groupby("jerarquia_puesto")["F"]
      .agg(["count", "mean"]).round(1).to_string())


# ============================================================
# Guardar y verificar
# ============================================================
columnas_nuevas = ["institucion_normalizada", "sector_completado", "fecha_publicacion_dt", "fecha_emision_corregida",
                   "nota_fecha", "ambito", "en_analisis_principal", "primer_nombre", "sexo_inferido", "sexo_analisis",
                   "sexo_origen", "clave_persona", "nombre_dudoso", "id_persona", "nivel_cargo", "institucion_del_cargo",
                   "nivel_organizacional", "unidad_organica", "unidad_superior", "ubicacion", "entidad_del_cargo",
                   "jerarquia_puesto",
                   "nivel_remunerativo"]
print("\nTabla final (filas, columnas):", movimientos.shape, "| columnas nuevas:", len(columnas_nuevas))
movimientos.to_csv(CARPETA_PROCESADOS / "movimientos_analisis.csv", index=False, encoding="utf-8-sig")
