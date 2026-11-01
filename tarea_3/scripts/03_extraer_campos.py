# ============================================================
# Designaciones de El Peruano — Script 03: extraer la información de cada norma
# ------------------------------------------------------------
# Lee el texto de cada norma (script 02) y llena la base de datos con todo lo
# que dice el PDF. Usa reglas de texto (expresiones regulares): no usa IA.
# Un campo vacío significa "la norma no lo dice" (o la regla no lo encontró:
# por eso cada fila guarda el texto del artículo, para poder verificar).
#
# Insumo:    datos/procesados/normas_personal.csv  (o el índice, si aún no existe)
#            datos/crudos/textos/<codigo_norma>.txt
# Resultado: datos/procesados/normas.csv        -> 1 fila por norma (con su texto completo)
#            datos/procesados/movimientos.csv   -> 1 fila por persona y movimiento
#
# Uso (desde la carpeta tarea_3):
#   python scripts/03_extraer_campos.py
# ============================================================

# --- Paquetes (todos vienen con Python o Anaconda) ---
# re: buscar patrones de texto ("Designar a la señora ...") y recortar partes
import re
# unicodedata: quitar tildes para normalizar nombres
import unicodedata
# datetime.date: convertir "5 de noviembre de 2025" en una fecha de verdad
from datetime import date
# itertools.combinations: probar las formas de unir celdas de una tabla partidas en dos líneas
from itertools import combinations
# pathlib: manejar rutas de carpetas y archivos
from pathlib import Path
# pandas: armar y guardar las tablas
import pandas as pd

CARPETA_TAREA = Path(__file__).resolve().parent.parent
CARPETA_TEXTOS = CARPETA_TAREA / "datos" / "crudos" / "textos"
CARPETA_PROCESADOS = CARPETA_TAREA / "datos" / "procesados"

MESES = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7,
         "agosto": 8, "setiembre": 9, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12}


# ============================================================
# PROCESO 1: Cargar la lista de normas
# Insumo:    normas_personal.csv (script 01c) o, si no existe, indice_normas.csv
# Resultado: tabla con una fila por norma y sus datos de origen
# ============================================================
def cargar_lista():
    """Antes: archivo CSV | Después: tabla con codigo_norma, fecha, institución, etc."""
    archivo = CARPETA_PROCESADOS / "normas_personal.csv"
    if archivo.exists():
        return pd.read_csv(archivo, encoding="utf-8-sig")
    indice = pd.read_csv(CARPETA_PROCESADOS / "indice_normas.csv", encoding="utf-8-sig")
    return pd.DataFrame({
        "codigo_norma": indice["codigo_norma"], "fecha_publicacion": indice["dtmFechaPublicacion"],
        "sector_ep": indice["vchSector"], "institucion": indice["vchInstitucionWeb"],
        "dispositivo": indice["vchNomTipoDispositivo"] + " " + indice["vchNomDispositivo"],
        "cargo_indice": indice["vchCargo"], "enlace_pdf": indice["vchLinkPDF"],
        "enlace_web": indice["vchLinkHtml"], "fuente": "índice"})


# ============================================================
# PROCESO 2: Recortar la norma dentro de la página
# Insumo:    texto de la página o páginas del diario (varias normas)
# Resultado: líneas que pertenecen solo a nuestra norma
# ============================================================
# Líneas que no son parte de ninguna norma: número de página, cabecera y firma digital del diario
RUIDO = re.compile(r"^(\d{1,4}|NORMAS LEGALES|/|El Peruano\s*/?|/?\s*El Peruano|Firmado por:.*|"
                   r"Fecha: \d.*|(Lunes|Martes|Miércoles|Jueves|Viernes|Sábado|Domingo) \d.*)\s*$")
# Cada norma termina con una línea que solo tiene su código (ej. "2538840-2")
LINEA_CODIGO = re.compile(r"^\s*(\d{6,8}-\d{1,3})\s*$")


def recortar_norma(texto_paginas, codigo):
    """Antes: página completa | Después: líneas entre el código anterior y el de la norma"""
    actual = []
    for linea in texto_paginas.replace("\f", "\n").split("\n"):
        if RUIDO.match(linea.strip()):
            continue
        m = LINEA_CODIGO.match(linea)
        if m:
            if m.group(1) == codigo:
                return actual
            actual = []
        else:
            actual.append(linea.strip())
    return recortar_publicacion_digital(texto_paginas, codigo)


# Publicaciones digitales (sobre todo municipalidades de Lima, 2024-2025): el PDF trae UNA sola norma
# y su código no va al final, sino en la cabecera de cada página ("OP N° 2339400-1")
LINEA_OP = re.compile(r"^\s*OP\s*N\s*[°º]\s*(\d{6,8}-\d{1,3})\s*$")
RUIDO_DIGITAL = re.compile(r"^(Esta es una representaci[óo]n impresa|localizada en la https://elperuano|"
                           r"la Directiva N\s*[º°] 00[23]-2021-PCM/SGTD|C[óo]digo de validaci[óo]n|OP\s*N\s*[°º]|"
                           r"Gerente de Publicaciones Oficiales|Ricardo Montero Reyes|FUNDADO EL 22 DE OCTUBRE DE 1825|"
                           r"DIARIO OFICIAL DEL BICENTENARIO|[“\"]A[ÑN]O DE)")


def recortar_publicacion_digital(texto_paginas, codigo):
    """Antes: PDF de una sola norma, con la cabecera del diario repetida en cada página
    | Después: líneas de la norma (desde el título) sin las cabeceras; None si no es este formato"""
    lineas = [l.strip() for l in texto_paginas.replace("\f", "\n").split("\n")]
    if not any(LINEA_OP.match(l) and LINEA_OP.match(l).group(1) == codigo for l in lineas):
        return None
    # La norma empieza después de la primera línea "FUNDADO EL 22 DE OCTUBRE DE 1825 ..."
    inicio = next((i for i, l in enumerate(lineas) if l.startswith("FUNDADO EL 22 DE OCTUBRE")), None)
    if inicio is None:
        # Formato de 2024: sin esa cabecera; el PDF empieza con la numeración de líneas ("1. 1", "2. 2", "10.")
        # y cada página cierra con la fecha ("Lima, viernes 26 de enero de 2024")
        return [l for l in lineas if not RUIDO.match(l) and not RUIDO_DIGITAL.match(l)
                and not re.match(r"^\d{1,3}\.?(?:\s+\d{1,3})?$|^Lima,\s+\w+\s+\d{1,2}\s+de\s+\w+\s+de\s+\d{4}$", l)]
    return [l for l in lineas[inicio + 1:] if not RUIDO.match(l) and not RUIDO_DIGITAL.match(l)]


# --- Fuente antigua (PDF de 2022-2023): algunas mayúsculas se leen como minúsculas ---
# En esa fuente, las mayúsculas A, D, E, N, O y U salen como minúsculas al extraer el texto:
#   "deSIGnaR" (DESIGNAR), "Se ReSueLVe", "RoSa eLena" (ROSA ELENA), "a la profesional andrea Matos"
LETRA = "A-Za-zÁÉÍÓÚÀÈÌÒÙÑÜáéíóúàèìòùñü"
PALABRA = re.compile(rf"[{LETRA}]+")
LETRAS_DANADAS = set("adenouáéíóú")
# Palabras comunes que empiezan con esas letras y no son nombres: no se les pone mayúscula inicial
NO_CAPITALIZAR = {"al", "ante", "de", "del", "desde", "durante", "el", "en", "entre", "un", "una", "uno", "unos", "unas",
                  "otro", "otra", "otros", "otras", "este", "esta", "estos", "estas", "ese", "esa", "dicho", "dicha",
                  "donde", "dentro", "ello", "ella", "ellos", "ellas", "aquel", "aquella", "aun", "antes", "despues",
                  "después", "ademas", "además", "asimismo", "and"}


def palabra_danada(palabra):
    """Antes: "deSIGnaR" -> True | "Matos" -> False | "PerúCompras" -> False
    (tiene mayúsculas en medio y todas sus minúsculas son letras de las que se dañan)"""
    minusculas = [c for c in palabra if c.islower()]
    return (len(palabra) >= 2 and any(c.isupper() for c in palabra[1:]) and bool(minusculas)
            and all(c in LETRAS_DANADAS for c in minusculas))


def reparar_fuente_antigua(texto):
    """Antes: "Artículo 2.- deSIGnaR ... a la profesional andrea Matos Vega ... RoSa eLena QuISPe"
    | Después: "Artículo 2.- DESIGNAR ... a la profesional Andrea Matos Vega ... ROSA ELENA QUISPE"
    (si el texto no tiene la fuente dañada —menos de 5 palabras DISTINTAS con el patrón—, se devuelve sin cambios;
    así una sigla legítima repetida, como "PPoR" o "CTeI", o una tilde en minúscula, "RESOLUCIóN", no la activan)"""
    distintas = {p for p in PALABRA.findall(texto) if palabra_danada(p) and any(c in "adenou" for c in p)}
    if len(distintas) < 5:
        return texto
    lineas = []
    for linea in texto.split("\n"):
        # 1) Palabra con mayúsculas en medio y minúsculas dañadas: toda en mayúsculas ("ReSueLVe" -> "RESUELVE")
        linea = PALABRA.sub(lambda m: m.group(0).upper() if palabra_danada(m.group(0)) else m.group(0), linea)
        # 2) Línea casi toda en mayúsculas (firmas, títulos): entera en mayúsculas ("CARLOS ALBERTO Rojas")
        palabras = [p for p in PALABRA.findall(linea) if len(p) >= 2]
        en_mayusculas = [p for p in palabras if p.isupper()]
        if len(en_mayusculas) >= 2 and len(en_mayusculas) >= 0.6 * len(palabras):
            linea = linea.upper()
        lineas.append(linea)
    # 3) Nombre que empieza con letra dañada, junto a otra palabra con mayúscula: "andrea Matos" -> "Andrea Matos"
    #    (se recorre dos veces para cadenas como "andrea elena Torres")
    partes = PALABRA.split("\n".join(lineas))
    palabras = PALABRA.findall("\n".join(lineas))
    for _ in range(2):
        for i, p in enumerate(palabras):
            if len(p) >= 3 and p.islower() and p[0] in LETRAS_DANADAS and p not in NO_CAPITALIZAR:
                antes = i > 0 and partes[i].isspace() and palabras[i - 1][:1].isupper()
                despues = i + 1 < len(palabras) and partes[i + 1].isspace() and palabras[i + 1][:1].isupper()
                if antes or despues:
                    palabras[i] = p[0].upper() + p[1:]
    return "".join(s + (palabras[i] if i < len(palabras) else "") for i, s in enumerate(partes))


# --- Tablas con una celda por línea (subprefectos 2022-2023) ---
# El PDF trae cada celda en su línea: "N°", "Región", "Provincia", "Distrito", "Nombre", "Apellido", "Paterno", ..., "DNI",
# y luego cada fila: "1", "AMAZONAS", "BAGUA", "EL PARCO", "LUIS ALBERTO", "QUISPE", "RAMOS", "87654321".
# Al unir las líneas, la ubicación queda pegada al nombre; por eso se reordena cada fila antes de unir.
CELDA_ENCABEZADO = re.compile(r"^(N\s*[°º]|N\.?\s*[°º]?|Nro\.?|Item|Región|Region|Departamento|Provincia|Distrito|Nombres?|"
                              r"Apellidos?|Paterno|Materno|y|Apellidos?\s*y\s*Nombres?|Nombres?\s*y\s*Apellidos?|"
                              r"Apellido\s+(?:Paterno|Materno)|DNI|D\.N\.I\.?)$", re.I)
COLUMNA_UBICACION = re.compile(r"^(Región|Region|Departamento|Provincia|Distrito)$", re.I)
# Pie de página que corta la tabla entre páginas ("Peru")
PIE_TABLA = re.compile(r"^Per[uú]$")


def tablas_por_celda(lineas):
    """Antes: ["N°", "Región", ..., "DNI", "1", "AMAZONAS", "BAGUA", "ARAMANGO", "MARCO", "TORRES", "VEGA", "12345678", ...]
    | Después: ["N° NOMBRES Y APELLIDOS DNI UBICACIÓN", "1. MARCO TORRES VEGA 12345678 ARAMANGO BAGUA AMAZONAS", ...]
    (solo si todas las filas tienen tantas celdas como columnas; si no, las líneas quedan como estaban)"""
    salida, i = [], 0
    while i < len(lineas):
        if lineas[i].strip().upper() not in ("DNI", "D.N.I.", "D.N.I"):
            salida.append(lineas[i])
            i += 1
            continue
        # Encabezado: líneas cortas de nombres de columna justo antes de "DNI"
        j = len(salida)
        while j > 0 and CELDA_ENCABEZADO.match(salida[j - 1].strip()):
            j -= 1
        columnas = []
        for celda in (l.strip() for l in salida[j:]):
            ultima = columnas[-1] if columnas else ""
            # "Apellido" + "Paterno" -> "Apellido Paterno"; "Apellidos" + "y" + "Nombres" -> "Apellidos y Nombres"
            if (re.match(r"^(Paterno|Materno)$", celda, re.I) and re.match(r"^Apellidos?$", ultima, re.I)) or \
                    (celda.lower() == "y" and re.match(r"^(Apellidos?|Nombres?)$", ultima, re.I)) or \
                    (re.match(r"^(Apellidos?|Nombres?)$", celda, re.I) and ultima.lower().endswith(" y")):
                columnas[-1] += " " + celda
            else:
                columnas.append(celda)
        # Sin la columna de número de fila (el limpiador de la página ya quitó esos números)
        columnas = [c for c in columnas if not re.match(r"^(N\s*[°º]|N\.?\s*[°º]?|Nro\.?|Item)$", c, re.I)]
        ubicacion = [n for n, c in enumerate(columnas) if COLUMNA_UBICACION.match(c)]
        # Antes del encabezado debe ir la frase que presenta la tabla ("... de los siguientes ciudadanos:"); si va
        # una palabra corta, es otra columna que no se reconoce ("Cargo", "Entidad") y la tabla no se toca
        # (o el DNI de la última fila de la página anterior, cuando la tabla continúa: "... 11223344", "Peru", "")
        previas = [l.strip() for l in salida[:j] if l.strip() and not PIE_TABLA.match(l.strip())]
        presentacion = previas[-1] if previas else ""
        if not ubicacion or len(columnas) < 3 or (previas and not presentacion.endswith(":") and len(presentacion) <= 30
                                                  and not re.match(r"^\d{8}$", presentacion)):
            salida.append(lineas[i])
            i += 1
            continue
        # Filas: una celda en mayúsculas por columna y luego el DNI de 8 dígitos.
        # El encabezado se repite en cada página y se salta; la tabla termina en la primera línea que no es celda.
        filas_celdas, k = [], i + 1
        while k < len(lineas):
            if CELDA_ENCABEZADO.match(lineas[k].strip()) or not lineas[k].strip() or PIE_TABLA.match(lineas[k].strip()):
                k += 1
                continue
            if not re.match(rf"^(?:\d{{1,4}}\s+)?[{MAY}'’\-\.,()\s]{{2,45}}$", lineas[k].strip()):
                break                                           # fin de la tabla ("Artículo 2.- ...")
            celdas, inicio_fila = [], k
            while k < len(lineas) and not re.match(r"^\d{8}$", lineas[k].strip()) and len(celdas) <= len(columnas) + 3:
                # Se saltan las líneas vacías, el encabezado repetido, el pie "Peru" y las celdas que son solo un signo
                linea = lineas[k].strip()
                if re.search(r"\w", linea) and not CELDA_ENCABEZADO.match(linea) and not PIE_TABLA.match(linea):
                    # El número de fila a veces va pegado a la primera celda: "1 AMAZONAS" -> "AMAZONAS"
                    celdas.append(re.sub(r"^\d{1,4}\s+", "", linea) if not celdas else linea)
                k += 1
            if k >= len(lineas) or not re.match(r"^\d{8}$", lineas[k].strip()):
                k = inicio_fila
                break
            filas_celdas.append((celdas, lineas[k].strip()))
            k += 1
        if not filas_celdas:
            salida.append(lineas[i])
            i += 1
            continue
        # Ubicaciones ya vistas en las filas completas: ayudan a decidir qué celda se partió en dos líneas
        conocidas = {n: {c[n] for c, _ in filas_celdas if len(c) == len(columnas)} for n in ubicacion}
        es_region = [n for n in ubicacion if re.match(r"^(Región|Region|Departamento)$", columnas[n], re.I)]
        filas = []
        for celdas, dni in filas_celdas:
            celdas = unir_celdas_partidas(celdas, len(columnas), conocidas, ubicacion, es_region)
            nombre = " ".join(c for n, c in enumerate(celdas) if n not in ubicacion)
            lugar = " ".join(celdas[n] for n in reversed(ubicacion) if n < len(celdas))   # distrito, provincia, región
            filas.append(f"{len(filas) + 1}. {nombre} {dni} {lugar}")
        salida = salida[:j] + ["N° NOMBRES Y APELLIDOS DNI UBICACIÓN"] + filas
        i = k
    return salida


def unir_celdas_partidas(celdas, n_columnas, conocidas, ubicacion, es_region=()):
    """Antes: ["AMAZONAS", "LUYA", "SAN JUAN DE", "LOPECANCHA", "JUAN CARLOS", "RIOS", "PAREDES"] (7 celdas, 6 columnas)
    | Después: ["AMAZONAS", "LUYA", "SAN JUAN DE LOPECANCHA", "JUAN CARLOS", "RIOS", "PAREDES"]
    Se prueban todas las formas de unir celdas vecinas y gana la que más ubicaciones reconoce
    (+1 si la celda unida terminaba en "DE", "DEL", "SAN"...; ante empate, se unen celdas del nombre)"""
    sobran = len(celdas) - n_columnas
    if sobran <= 0 or sobran > 3:
        return celdas
    mejor, mejor_puntaje = celdas, None
    for cortes in combinations(range(1, len(celdas)), n_columnas - 1):
        limites = list(zip((0,) + cortes, cortes + (len(celdas),)))
        partes = [" ".join(celdas[a:b]) for a, b in limites]
        puntaje = sum(2 for n in ubicacion if partes[n] in conocidas[n])
        # La región se compara también con la lista cerrada de departamentos ("LIMA" + "PROVINCIAS" -> "LIMA PROVINCIAS")
        puntaje += sum(2 for n in es_region if partes[n] not in conocidas[n] and re.fullmatch(DEPARTAMENTO, partes[n]))
        puntaje += sum(1 for a, b in limites if b - a > 1 and re.search(r"\b(DE|DEL|LA|LAS|LOS|SAN|SANTA|Y)$", celdas[b - 2]))
        puntaje -= 0.1 * sum(1 for n, (a, b) in enumerate(limites) if b - a > 1 and n in ubicacion)
        # Un nombre de más de 4 palabras suele ser una ubicación pegada ("CALLERIA ROSA ELENA SOTO VEGA")
        palabras_nombre = sum(len(p.split()) for n, p in enumerate(partes) if n not in ubicacion)
        puntaje -= 0.5 * max(0, palabras_nombre - 4)
        if mejor_puntaje is None or puntaje > mejor_puntaje:
            mejor, mejor_puntaje = partes, puntaje
    return mejor


def unir_lineas(lineas):
    """Antes: ["...Nº 00684-2026-MINDEF/VRD-", "DGRRHH de la..."] | Después: un solo texto corrido
    (si una línea termina en guion o barra pegada, se une sin espacio)"""
    texto = ""
    for linea in lineas:
        if not linea:
            continue
        if re.search(r"\S[-/]$", texto):
            texto += linea
        else:
            texto += (" " if texto else "") + linea
    return re.sub(r"\s+", " ", texto).strip()


# ============================================================
# PROCESO 3: Separar las partes de la norma
# Insumo:    texto corrido de la norma
# Resultado: encabezado, VISTOS, CONSIDERANDOS, parte resolutiva y líneas de firmas
# ============================================================
CIERRE = re.compile(r"(Reg[íi]strese|Comun[íi]quese|Publ[íi]quese|Cúmplase|Archívese)", re.I)


def separar_partes(lineas):
    """Antes: líneas de la norma | Después: diccionario con cada parte en texto"""
    texto = unir_lineas(lineas)
    m_vistos = re.search(r"\bVISTOS?\b", texto)
    m_consid = re.search(r"\bCONSIDERANDO\b", texto)
    m_resuelve = re.search(r"\b(SE RESUELVE|RESUELVE|SE DECRETA|DECRETA|RESUELVEN|SE ACUERDA|ACUERDA)\b\s*:?", texto)
    if not m_resuelve:
        # Acuerdos de consejo (OTASS): "El Consejo Directivo ... acordó designar en el cargo ..."
        m_resuelve = re.search(r"\bacord[óo]\b\s*:?", texto)
    inicio_cuerpo = min([m.start() for m in (m_vistos, m_consid, m_resuelve) if m] or [len(texto)])

    # Las firmas van después de la última línea con "Regístrese / Comuníquese / Publíquese"
    posiciones_cierre = [i for i, l in enumerate(lineas) if CIERRE.search(l)]
    if not posiciones_cierre:
        # Sin "Regístrese": las firmas van después de la última línea "Lima, 20 de noviembre de 2025"
        # si está en la segunda mitad de la norma
        lugar_fecha = [i for i, l in enumerate(lineas)
                       if re.match(r"^[A-ZÁÉÍÓÚ][\w .]{2,40},\s*\d{1,2}\s+de\s+\w+\s+del?\s+\d{4}\s*\.?$", l)]
        if lugar_fecha and lugar_fecha[-1] > len(lineas) / 2:
            posiciones_cierre = [lugar_fecha[-1]]
    lineas_firmas = lineas[posiciones_cierre[-1] + 1:] if posiciones_cierre else []
    fin_resolutiva = len(texto)
    if posiciones_cierre:
        m_cierre = list(CIERRE.finditer(texto))
        if not m_cierre and lineas_firmas:
            # Sin "Regístrese": la parte resolutiva termina donde empieza la línea de lugar y fecha
            m_cierre = list(re.finditer(re.escape(lineas[posiciones_cierre[-1]].strip()), texto))
        fin_resolutiva = m_cierre[-1].start() if m_cierre else len(texto)

    partes = {"texto": texto, "encabezado": texto[:inicio_cuerpo], "vistos": "",
              "considerandos": "", "resolutiva": "", "lineas_firmas": lineas_firmas}
    if m_vistos and (not m_consid or m_vistos.start() < m_consid.start()):
        partes["vistos"] = texto[m_vistos.end():(m_consid or m_resuelve or m_vistos).start()] if (m_consid or m_resuelve) else ""
    if m_resuelve:
        desde = (m_consid or m_vistos).end() if (m_consid or m_vistos) else inicio_cuerpo
        partes["considerandos"] = texto[desde:m_resuelve.start()]
        partes["resolutiva"] = texto[m_resuelve.end():fin_resolutiva if fin_resolutiva > m_resuelve.end() else len(texto)]
    else:
        partes["considerandos"] = texto[inicio_cuerpo:]
    return partes


# ============================================================
# PROCESO 4: Datos de la norma (una fila por norma)
# Insumo:    partes de la norma
# Resultado: fecha y lugar de emisión, VISTOS, visados, propuesta, motivo, base legal,
#            características del cargo, refrendo y firmantes
# ============================================================
def a_fecha(dia, mes, anio):
    """Antes: ("5", "noviembre", "2025") | Después: date(2025, 11, 5) o None si no se puede"""
    try:
        return date(int(anio), MESES[mes.lower()], int(dia))
    except (KeyError, ValueError):
        return None


def fragmentos(patron, texto, maximo=3):
    """Antes: texto largo | Después: los fragmentos que cumplen el patrón, unidos con " | " """
    encontrados = [m.group(0).strip(" ,;") for m in re.finditer(patron, texto, re.I)]
    return " | ".join(dict.fromkeys(encontrados[:maximo]))


DOCUMENTO = (r"(?:Informe(?: Legal| Técnico| Múltiple| de Evaluación)?|Oficio(?: Múltiple)?|Memorando(?: Múltiple)?|"
             r"Memorándum|Nota(?: de Elevación| Informativa)?|Hoja de Elevación|Proveído|Carta|Expediente|"
             r"Hoja de Trámite|Solicitud|Informe Técnico Legal)\s+N[°º.o]*\s*[\w\-/\.]+")
OFICINA_DE = r"(?:\s*,?\s*(?:de|del|emitid[oa] por|elaborad[oa] por)\s+(?:la|el)\s+([A-ZÁÉÍÓÚ][^,;]+?))?(?=[,;]|\s+y\s+(?:el|la|los)\s|\s*$)"


def separar_firmantes(lineas_firmas):
    """Antes: ["KEIKO ... HIGUCHI", "Presidenta de la República", "LUIS ...", ...]
    Después: [("KEIKO ... HIGUCHI", "Presidenta de la República"), ("LUIS ...", "Presidente del Consejo...")]
    Un nombre es una línea casi toda en mayúsculas, con 3 palabras o más y sin palabras de entidad."""
    entidad = {"NACIONAL", "MINISTERIO", "PROGRAMA", "SERVICIO", "SUPERINTENDENCIA", "GOBIERNO",
               "MUNICIPALIDAD", "DIRECCIÓN", "DIRECCION", "OFICINA", "PROYECTO", "ORGANISMO", "INSTITUTO",
               "SECRETARÍA", "SECRETARIA", "CONSEJO", "REPÚBLICA", "REPUBLICA", "GENERAL", "FISCAL",
               "EJECUTIVO", "EJECUTIVA", "REGIONAL", "AUTORIDAD", "ANEXO", "PRESIDENTE", "PRESIDENTA"}
    firmantes = []
    for linea in lineas_firmas:
        if re.match(r"^\s*ANEXO", linea, re.I):   # lo que sigue es un anexo, no firmas
            break
        if firmantes and re.search(r"\b(?:se|que|conforme|actualmente|dispuesto|mediante|denomina)\b", linea, re.I):
            break                                  # nota al pie después de las firmas
        letras = [c for c in linea if c.isalpha()]
        palabras = re.findall(r"[A-ZÁÉÍÓÚÑÜ][A-ZÁÉÍÓÚÑÜ'’\-]*\.?", linea)
        es_nombre = (len(letras) >= 6 and sum(c.isupper() for c in letras) / len(letras) > 0.85
                     and len(palabras) >= 3 and not entidad & {p.strip(".") for p in palabras})
        if es_nombre:
            firmantes.append([linea.strip(" ,"), ""])
        elif firmantes and len(firmantes[-1][1]) < 120 and len(linea) <= 80 and not linea.endswith("."):
            # Las líneas largas o que terminan en punto son notas al pie, no parte del cargo
            firmantes[-1][1] = (firmantes[-1][1] + " " + linea).strip()
    return [(n, c) for n, c in firmantes][:4]


def datos_de_norma(partes):
    """Antes: partes de la norma | Después: diccionario con los campos de la norma"""
    texto, consid = partes["texto"], partes["considerandos"]
    datos = {}

    # Lugar y fecha de emisión: "Lima, 30 de julio de 2026" (la última del encabezado)
    emision = list(re.finditer(r"((?:[A-ZÁÉÍÓÚ][a-záéíóúñ]+\s){0,2}[A-ZÁÉÍÓÚ][a-záéíóúñ]+),\s*(\d{1,2})[°º]?\s+de\s+"
                               r"([a-záéíóú]+)\s+del?\s+(\d{4})", partes["encabezado"] or texto[:400]))
    if emision:
        m = emision[-1]
        datos["lugar_emision"], datos["fecha_emision"] = m.group(1), a_fecha(m.group(2), m.group(3), m.group(4))

    # VISTOS: documentos que sustentan la decisión y la oficina que los emitió
    fuente_docs = partes["vistos"] or consid
    documentos = [m.group(0).strip(" ,;") for m in re.finditer(DOCUMENTO + OFICINA_DE, fuente_docs)]
    datos["vistos_texto"] = partes["vistos"].strip(" :;,")
    datos["documentos_sustento"] = " | ".join(dict.fromkeys(documentos))
    datos["n_documentos_sustento"] = len(set(documentos))

    # Visado: oficinas que revisaron la norma ("Con el visado de la Secretaría General, ...")
    visado = re.search(r"(?:Con|Contando con)\s+(?:el|los|la|las)\s+(?:visado|visados|visto|vistos|visación|"
                       r"visaciones|visto bueno)\s+(?:de|del)\s+([^;]+)", texto)
    datos["visado_texto"] = visado.group(1).strip(" ,.") if visado else ""
    if visado:
        oficinas = re.split(r",\s*|\s+y\s+(?=(?:de\s+)?(?:la|el|los|las|del)\s)", visado.group(1))
        oficinas = [re.sub(r"^(?:de\s+)?(?:la|el|los|las|del)\s+|^de\s+", "", o).strip(" ,.") for o in oficinas
                    if not re.match(r"\s*(?:en lo que|seg[úu]n|en el [áa]mbito|en sus)", o)]
        datos["oficinas_visado"] = " | ".join(o for o in oficinas if len(o) > 3)
        datos["n_oficinas_visado"] = len([o for o in oficinas if len(o) > 3])

    # Quién propone a la persona
    datos["propuesta_texto"] = fragmentos(
        r"(?:Estando a lo propuesto por|a propuesta (?:de|del)|la propuesta (?:presentada|formulada|efectuada|realizada) por|"
        r"propone(?:n)? (?:designar|la designación|encargar)|solicita[^;.]{0,80}(?:evaluar el perfil|designaci))[^;.]*", texto)

    # Motivo que menciona la norma
    datos["motivo_vacante"] = bool(re.search(r"vacante", consid, re.I))
    datos["motivo_conveniente"] = bool(re.search(r"(?:por |resulta |es )conveniente", consid, re.I))
    datos["menciona_renuncia"] = bool(re.search(r"renuncia", consid, re.I))
    datos["motivo_texto"] = fragmentos(r"[^;.]*(?:vacante|por conveniente|ha formulado renuncia|presentó renuncia|"
                                       r"resulta necesario designar|dar por concluid)[^;.]*", consid, 2)

    # Verificación del perfil o idoneidad (Ley 31419)
    datos["cita_ley_31419_idoneidad"] = "31419" in texto
    datos["verificacion_perfil_texto"] = fragmentos(r"[^;.]*(?:cumple con (?:los|el) (?:requisitos|perfil)|"
                                                   r"perfil (?:del puesto|de puesto|requerido)|idoneidad)[^;.]*", consid, 2)

    # Características del cargo
    tipos = [t for t, p in [("cargo de confianza", r"(?:cargo|puesto|empleado|empleada) de confianza|confianza"),
                            ("libre designación y remoción", r"libre designaci[oó]n y remoci[oó]n"),
                            ("directivo superior", r"directiv[oa]s? superior"),
                            ("funcionario público", r"funcionari[oa] públic[oa]")] if re.search(p, texto, re.I)]
    datos["tipo_cargo_mencionado"] = " | ".join(tipos)
    nivel = re.search(r"\b[Nn]ivel\s+(?:[Rr]emunerativo\s+)?([FDE]\s?-\s?\d+)|\b(F-\d)\b", texto)
    datos["nivel_remunerativo"] = (nivel.group(1) or nivel.group(2)).replace(" ", "") if nivel else ""
    datos["menciona_cap"] = bool(re.search(r"\bCAP\b|Cuadro (?:para|de) Asignaci[oó]n de Personal", texto))
    plaza = re.search(r"N[°º]\s*(?:de\s+)?(?:orden|plaza|CAP)\s*:?\s*(\d{1,5})|plaza\s+N[°º]\s*(\d{1,5})", texto, re.I)
    datos["numero_plaza"] = (plaza.group(1) or plaza.group(2)) if plaza else ""
    regimen = [r for r, p in [("CAS (D. Leg. 1057)", r"1057"), ("D. Leg. 276", r"Legislativo\s+N[°º]\s*276\b"),
                              ("D. Leg. 728", r"N[°º]\s*728\b"), ("Servicio Civil (Ley 30057)", r"30057")]
               if re.search(p, texto)]
    datos["regimen_laboral_mencionado"] = " | ".join(regimen)

    # Base legal y facultades
    datos["base_legal_texto"] = fragmentos(r"(?:De conformidad con|En uso de|En ejercicio de|Con arreglo a)[^;]*(?:;[^;]*){0,6}",
                                           consid, 1)
    leyes = re.findall(r"(?:Ley|Decreto Legislativo|Decreto de Urgencia)\s+N[°º]\s*\d+", texto)
    datos["leyes_citadas"] = " | ".join(dict.fromkeys(re.sub(r"\s+", " ", l).replace("º", "°") for l in leyes))
    datos["facultad_delegada"] = bool(re.search(r"delegad[oa]s?|delegaci[oó]n de facultades", consid, re.I))
    refrendo = re.search(r"refrendad[ao] por (?:el|la|los|las)\s+([^.]+)", partes["resolutiva"] + " " + texto[-600:])
    datos["refrendo"] = refrendo.group(1).strip() if refrendo else ""

    # Personas mencionadas en los considerandos (por ejemplo, quien ocupaba antes el puesto)
    datos["personas_en_considerandos"] = " | ".join(dict.fromkeys(
        p["nombre"] for p in buscar_personas(consid) if p["nombre"]))

    # Firmantes: nombre, cargo y si firma como encargado "(e)" o interino "(i)"
    for n, (nombre, cargo) in enumerate(separar_firmantes(partes["lineas_firmas"]), start=1):
        datos[f"firmante{n}_nombre"] = nombre
        datos[f"firmante{n}_cargo"] = cargo
        datos[f"firmante{n}_encargado"] = bool(re.search(r"\((?:e|i|E|I)\)", nombre + " " + cargo))
    return datos


# ============================================================
# PROCESO 5: Personas y movimientos (una fila por persona y movimiento)
# Insumo:    parte resolutiva ("SE RESUELVE: Artículo 1.- Designar a la señora ...")
# Resultado: lista de movimientos con tipo, persona, cargo, fechas y condiciones
# ============================================================
TRATAMIENTO = (r"Srta\.|Sra\.|Sr\.|Dra\.|Dr\.|Ing\.|Abog\.|Abg\.|Lic\.|Econ\.|Mg\.|Mag\.|Mtr\.|Mtra\.|Arq\.|M[ée]d\.|"
               r"M\.C\.|Q\.F\.|C\.D\.|Obst\.|Blgo\.|Bach\.|CPC\.|"
               r"señor(?:es)?|señora(?:s)?|señorita(?:s)?|servidor(?:a|es|as)?|funcionari[oa]s?|profesional(?:es)?|"
               r"abogad[oa]s?|ingenier[oa]s?|economistas?|contador(?:a)?|CPC|C\.P\.C\.|m[ée]dic[oa]s?|licenciad[oa]s?|"
               r"doctor(?:a)?|arquitect[oa]s?|mag[íi]ster|ciudadan[oa]s?|bachiller|t[ée]cnic[oa]s?|psic[oó]log[oa]|"
               r"soci[oó]log[oa]|antrop[oó]log[oa]|comunicador(?:a)?|administrador(?:a)?|odont[oó]log[oa]|obstetra|"
               r"enfermer[oa]|qu[íi]mic[oa]|bi[oó]log[oa]|periodista|polit[oó]log[oa]|cirujano dentista|"
               # Agregados al revisar el año nov-2023/oct-2024: "al médico cirujano X", "de la colaboradora X",
               # "a la magistrada X", "señor consejero doctor X"
               r"cirujan[oa]s?|colaborador(?:a|es|as)?|magistrad[oa]s?|consejer[oa]s?|veterinari[oa]s?|"
               r"tecn[oó]log[oa]s?|nutricionistas?|"
               r"Fiscal(?:es)? Superior(?:es)?|Fiscal(?:es)? Provincial(?:es)?|Fiscal(?:es)? Adjunt[oa]s?")
PROFESIONES = re.compile(r"abogad|ingenier|economista|contador|CPC|C\.P\.C|m[ée]dic|licenciad|doctor|arquitect|mag[íi]ster|"
                         r"bachiller|psic|soci[oó]log|antrop|comunicador|administrador|odont|obstetra|enfermer|qu[íi]mic|"
                         r"bi[oó]log|periodista|polit[oó]log|cirujan|veterinari|tecn[oó]log|nutricion|"
                         r"Ing\.|Abog\.|Abg\.|Lic\.|Econ\.|Mg\.|Mag\.|Mtr|"
                         r"Arq\.|M[ée]d\.|M\.C\.|Q\.F\.|C\.D\.|Obst\.|Blgo\.|Bach\.", re.I)
FEMENINO = re.compile(r"(?:Srta\.|Sra\.|Dra\.|señora|señorita|servidora|funcionaria|abogada|ingeniera|contadora|m[ée]dica|licenciada|"
                      r"doctora|arquitecta|ciudadana|t[ée]cnica|psic[oó]loga|soci[oó]loga|antrop[oó]loga|comunicadora|"
                      r"administradora|odont[oó]loga|enfermera|qu[íi]mica|bi[oó]loga|polit[oó]loga|adjunta|"
                      r"colaboradora|magistrada|cirujana|consejera|veterinaria|tecn[oó]loga)s?\b", re.I)
GRADO = (r"(?:(?:Teniente|General|Coronel|Comandante|Capit[áa]n|Mayor|Almirante|Vicealmirante|Contralmirante|"
         r"Brigadier|de|Navío|Fragata|Corbeta|División|Brigada|Ejército|FAP|EP|MGP|PNP|CJ|SN|IM|AP|Polic[íi]a|"
         r"en\s+situaci[oó]n\s+de\s+retiro|Inspector|Suboficial|Superior|Primera|Segunda|Tercera|Clase|\([rR]\)|\(Ret\.?\))\s+)*")
# Letras que pueden ir en un nombre (incluye tildes graves, que aparecen por error: "HERNÀN")
MAY = "A-ZÁÉÍÓÚÀÈÌÒÙÑÜ"
MIN = "a-záéíóúàèìòùñü"
NOMBRE_MAYUS = rf"(?:[{MAY}][{MAY}'’\-]*\.?\s+){{1,7}}[{MAY}][{MAY}'’\-]+"
# Nombre con mayúscula inicial; acepta apellidos en mayúsculas: "Carlos Alberto PÉREZ RAMOS".
# \b al final de cada palabra: sin él, "del" se leía como "de" y "Margarita del Rosario" quedaba en "Margarita".
# "Sal y Rosas" es el único apellido con "y" que se acepta (la "y" suele separar dos personas).
_PALABRA_NOMBRE = rf"[{MAY}](?:[{MIN}'’\-]+|[{MAY}'’\-]+)"
NOMBRE_TITULO = (rf"[{MAY}][{MIN}'’\-]+(?:\s+(?:" + _PALABRA_NOMBRE +
                 r"|de|del|la|las|los|De|Del|La|DE|DEL|LA|LOS|y(?=\s+Rosas))\b){1,7}")
# (?i:...) = sin distinguir mayúsculas solo en el tratamiento ("Señora" o "señora")
PERSONA = re.compile(r"\b((?i:al|a la|a el|a|del|de la|por el|por la|el|la|los|las|a los|a las))\s+((?:(?i:" + TRATAMIENTO +
                     r")\s+)+)(" + GRADO + r")(" + NOMBRE_MAYUS + r"|" + NOMBRE_TITULO + r")")
DIPLOMATICO = re.compile(r"((?:Embajador(?:a)?|Ministr[oa](?:\s+Consejer[oa])?|Consejer[oa]|Primer(?:a)?\s+Secretari[oa]|"
                         r"Segund[oa]\s+Secretari[oa]|Tercer(?:a)?\s+Secretari[oa])\s+en\s+el\s+Servicio\s+Diplom[áa]tico\s+de\s+la\s+"
                         r"Rep[úu]blica)(?:\s*,\s*en\s+situaci[oó]n\s+de\s+retiro\s*,)?\s*,?\s+(" + NOMBRE_MAYUS + r"|" + NOMBRE_TITULO + r")")
PALABRAS_CARGO = re.compile(r"^(Ministr|Viceministr|Director|Directora|Jef|Presidente|Presidenta|Secretari|Gerente|Fiscal|"
                            r"Superintendente|Procurador|Alcalde|Gobernador|Prefect|Subprefect|Coordinador|Asesor|Titular|"
                            r"Responsable|Supervisor|Especialista|Analista|Ejecutiv|Representante|Miembro|Integrante|"
                            r"Administrador|Auxiliar|Ejecutor|Vocal|Juez|Defensor|Contralor|Comisionad|Embajador)", re.I)
# Palabras en mayúsculas que NO son parte de un nombre (encabezados de tabla, verbos, entidades)
NO_NOMBRE = re.compile(r"\b(NACIONAL|MINISTERIO|PROGRAMA|SERVICIO|OFICINA|DIRECCI[ÓO]N|GERENCIA|UNIDAD|GOBIERNO|MUNICIPAL\w*|"
                       r"PER[ÚU]|FISCAL\w*|DISTRITO|PROVINCIA|DEPARTAMENTO|APELLIDO|NOMBRES|CARGO|REGIONAL|SUPERINTENDENCIA|"
                       r"DEJAR|EFECTO|DESIGNAR|CONCLUIDA|ACEPTAR|ENCARGAR|NOMBRAR|ART[ÍI]CULO|RESOLUCI[ÓO]N|DNI|PATERNO|"
                       r"MATERNO|REGI[ÓO]N|SEDE|ANEXO|PUESTO|ENTIDAD|CONSEJO|DIRECTORIO|EMPRESA|SOCIEDAD|COMIT[ÉE]|"
                       r"COMISI[ÓO]N|ELECTORAL|AM[ÉE]RICA|INTENDENCIA|JEFATURA|SUBDIRECCI[ÓO]N|SECRETAR[ÍI]A|ADJUNT[OA]|"
                       r"GESTI[ÓO]N|SOCIOAMBIENTAL|PROYECTO|INSTITUTO|UNIVERSIDAD|DESPACHO|PENAL|CORPORATIVA|PROVINCIAL|"
                       r"TRANSITORI[OA]|TRIBUTARI[OA]|NOROESTE|NORESTE|SUROESTE|SURESTE|SECCI[ÓO]N|JUZGADO|"
                       # ordinales de despachos ("CUARTO DESPACHO"); no "SEGUNDO", que también es nombre de pila
                       r"(?:PRIMER|TERCER|CUART|QUINT|SEXT|S[ÉE]PTIM|OCTAV|NOVEN|D[ÉE]CIM)[OA]?S?)\b")
# Palabras de rol que a veces quedan pegadas delante del nombre en listas ("TITULAR LUIS ...")
ROLES = {"TITULAR", "TITULARES", "ALTERNO", "ALTERNA", "ALTERNOS", "ALTERNAS", "SUPLENTE", "SUPLENTES", "CARGOS",
         "CARGO", "MIEMBRO", "MIEMBROS", "PRESIDENTE", "PRESIDENTA", "REPRESENTANTE", "REPRESENTANTES", "NOMBRE",
         "NOMBRES", "APELLIDOS"}
RANGOS = {"TENIENTE", "GENERAL", "CORONEL", "COMANDANTE", "CAPITÁN", "CAPITAN", "MAYOR", "ALMIRANTE", "VICEALMIRANTE",
          "CONTRALMIRANTE", "BRIGADIER", "NAVÍO", "NAVIO", "FRAGATA", "CORBETA", "DIVISIÓN", "DIVISION", "BRIGADA", "EP",
          "FAP", "MGP", "PNP", "CJ", "SN", "(R)", "TÉCNICO", "TECNICO", "INSPECTOR", "SUBOFICIAL", "SUPERIOR", "DE",
          "PRIMERA", "SEGUNDA", "TERCERA", "CLASE", "EMBAJADOR", "EMBAJADORA", "CONSEJERO", "CONSEJERA", "MINISTRO",
          "MINISTRA"}
CABECERA_TABLA = {"N°", "Nº", "NO", "N", "NOMBRES", "NOMBRE", "APELLIDO", "APELLIDOS", "PATERNO", "MATERNO", "Y", "DNI",
                  "DISTRITO", "PROVINCIA", "DEPARTAMENTO", "REGIÓN", "REGION", "CARGO", "ENTIDAD", "(*)"}
# Palabras de cargo o de área que en una tabla van delante del nombre ("GERENTE DE ADMINISTRACIÓN Y FINANZAS JUAN ...")
CARGO_EN_TABLA = re.compile(r"^(?:SUB)?(?:GERENTE|JEF[EA]|DIRECTOR[A]?|ASESOR[A]?|COORDINADOR[A]?|SUPERVISOR[A]?|ESPECIALISTA|"
                            r"ANALISTA|ADMINISTRADOR[A]?|SECRETARI[OA]|PRESIDENT[EA]|VOCAL|EJECUTIV[OA]|RESPONSABLE|AUXILIAR|"
                            r"PROCURADOR[A]?|INTENDENTE|PREFECT[OA]|COMERCIAL|OPERACIONES|ADMINISTRACI[ÓO]N|FINANZAS|HUMANOS|"
                            r"RECURSOS|PLANEAMIENTO|PRESUPUESTO|INGENIER[ÍI]A|PROYECTOS|OBRAS|LEGAL|ASESOR[ÍI]A|JUR[ÍI]DICA|"
                            r"CONTROL|CALIDAD|LOG[ÍI]STICA|TECNOLOG[ÍI]AS?|INFORMACI[ÓO]N|EPS|S\.A\.?)$")
PARTICULAS = {"DE", "DEL", "LA", "LAS", "LOS", "Y", "VDA.", "VDA"}
# Los 24 departamentos del Perú, más Callao y "Lima Provincias"/"Lima Metropolitana" (última columna de ubicación)
DEPARTAMENTO = (r"(?:AMAZONAS|[ÁA]NCASH|APUR[ÍI]MAC|AREQUIPA|AYACUCHO|CAJAMARCA|CALLAO|CUSCO|CUZCO|HUANCAVELICA|"
                r"HU[ÁA]NUCO|ICA|JUN[ÍI]N|LA\s+LIBERTAD|LAMBAYEQUE|LIMA(?:\s+PROVINCIAS|\s+METROPOLITANA)?|LORETO|"
                r"MADRE\s+DE\s+DIOS|MOQUEGUA|PASCO|PIURA|PUNO|SAN\s+MART[ÍI]N|TACNA|TUMBES|UCAYALI)")


def ultimos_apellidos(palabras, cuantos=2):
    """Antes: ["MUNICIPALIDAD", "DE", "CHEPEN", "MATIENZO", "CASTILLO"] | Después: ["MATIENZO", "CASTILLO"]
    (toma los dos últimos apellidos con sus partículas: "SANCHEZ DE LA CRUZ" cuenta como dos)"""
    tomadas, i = [], len(palabras) - 1
    for _ in range(cuantos):
        if i < 0:
            break
        unidad = [palabras[i]]
        i -= 1
        while i >= 0 and palabras[i].upper() in PARTICULAS:
            unidad.insert(0, palabras[i])
            i -= 1
        tomadas = unidad + tomadas
    return tomadas


def normalizar_nombre(nombre):
    """Antes: "María  Elena Quispe Rodríguez" | Después: "MARIA ELENA QUISPE RODRIGUEZ"
    Antes: "MAMANI QUISPE, ROSA ELVIRA" (apellidos, nombres) | Después: "ROSA ELVIRA MAMANI QUISPE" """
    if nombre.count(",") == 1:
        apellidos, nombres = nombre.split(",")
        nombre = f"{nombres} {apellidos}"
    nombre = unicodedata.normalize("NFKD", nombre)
    nombre = "".join(c for c in nombre if not unicodedata.combining(c)).upper()
    return re.sub(r"\s+", " ", re.sub(r"[^A-ZÑ' \-]", " ", nombre)).strip()


def limpiar_nombre(nombre):
    """Antes: "Luis Torres Huamán Director de la Estación" | Después: "Luis Torres Huamán"
    (corta donde empieza un cargo, un DNI o una partícula suelta al final)"""
    nombre = re.sub(r"\s+(?:DNI|D\.N\.I)\b.*$", "", nombre)
    palabras = nombre.split()
    while palabras and palabras[0].upper().strip(".:") in ROLES:     # "TITULAR LUIS ..." -> "LUIS ..."
        palabras = palabras[1:]
    for i, palabra in enumerate(palabras):
        if i >= 2 and (PALABRAS_CARGO.match(palabra) or NO_NOMBRE.search(palabra.upper())):
            palabras = palabras[:i]
            break
    nombre = " ".join(palabras)
    return re.sub(r"(?:\s+(?:de|del|la|las|los|y|De|Del|La))+$", "", nombre).strip()


def nueva_persona(nombre, tratamiento="", articulo_gramatical="", grado="", inicio=0, fin=0, metodo="tratamiento"):
    """Antes: datos sueltos de una persona | Después: diccionario con sexo y profesión deducidos del tratamiento"""
    if FEMENINO.search(tratamiento) or (tratamiento and articulo_gramatical.lower() in ("a la", "de la", "por la", "la", "las", "a las")
                                        and not re.search(r"señor(?:es)?\b|servidor(?:es)?\b|funcionarios?\b", tratamiento, re.I)):
        sexo = "F"
    elif tratamiento:
        sexo = "M"
    else:
        sexo = ""
    return {"nombre": nombre, "tratamiento": tratamiento, "sexo_segun_norma": sexo,
            "profesion_mencionada": " ".join(t for t in tratamiento.split() if PROFESIONES.match(t)),
            "grado_militar_policial": grado, "inicio": inicio, "fin": fin, "metodo_nombre": metodo}


def buscar_personas(texto):
    """Antes: "Designar a la señora ANA SOFÍA GARCÍA LÓPEZ en el cargo de ..."
    Después: [{"nombre": "ANA SOFÍA GARCÍA LÓPEZ", "tratamiento": "señora", "sexo_segun_norma": "F", ...}]"""
    personas = []
    # Servicio Diplomático: "del Embajador en el Servicio Diplomático de la República Jorge Luis Medina Vargas como ..."
    for m in DIPLOMATICO.finditer(texto):
        nombre = limpiar_nombre(m.group(2))
        if len(nombre.split()) >= 2:
            personas.append(nueva_persona(nombre, grado=m.group(1), inicio=m.start(), fin=m.start(2) + len(nombre),
                                          metodo="rango diplomático"))
    for m in PERSONA.finditer(texto):
        articulo_gramatical, tratamiento, grado, nombre = (m.group(1), m.group(2).strip(), m.group(3).strip(), m.group(4).strip())
        if PALABRAS_CARGO.match(nombre):          # "al señor Ministro de Defensa" no es un nombre
            continue
        # Grado que quedó dentro del nombre: "Contralmirante CJ (R) Carlos ..." -> grado aparte
        palabras = nombre.split()
        while len(palabras) > 2 and palabras[0].upper() in RANGOS:
            grado = f"{grado} {palabras.pop(0)}".strip()
        nombre = limpiar_nombre(" ".join(palabras))
        if len(nombre.split()) < 2:
            continue
        fin = m.start(4) + max(m.group(4).find(nombre), 0) + len(nombre)
        # "a la señora MAMANI QUISPE, ROSA ELVIRA, con ..." -> apellidos y nombres separados por coma
        nombres_pila = re.match(rf"\s*,\s*([{MAY}][{MAY}'’\-]+(?:\s+[{MAY}][{MAY}'’\-]+){{0,3}})(?=\s*[,;.]|\s+(?:con|en|a|al|como|identificad)\b)",
                                texto[fin:])
        if (nombres_pila and nombre.isupper() and len(nombre.split()) <= 3
                and not NO_NOMBRE.search(nombres_pila.group(1)) and not PALABRAS_CARGO.match(nombres_pila.group(1))
                and not re.search(r"\bDNI\b", nombres_pila.group(1))):
            nombre = f"{nombre}, {nombres_pila.group(1)}"
            fin += nombres_pila.end(1)
        personas.append(nueva_persona(nombre, tratamiento, articulo_gramatical, grado, m.start(), fin))
        # Plural: "de los señores Rosa María Flores Díaz y Pedro Pablo Rojas Silva"
        if re.search(r"(?:es|as|os)$", tratamiento.split()[0]):
            pos = personas[-1]["fin"]
            while True:
                siguiente = re.match(r"\s*(?:,|y)\s+(" + NOMBRE_MAYUS + r"|" + NOMBRE_TITULO + r")", texto[pos:])
                if not siguiente or PALABRAS_CARGO.match(siguiente.group(1)):
                    break
                otro = limpiar_nombre(siguiente.group(1))
                if len(otro.split()) < 2:
                    break
                personas.append(nueva_persona(otro, tratamiento, articulo_gramatical, grado,
                                              pos + siguiente.start(1), pos + siguiente.start(1) + len(otro)))
                pos = personas[-1]["fin"]
    return personas


def personas_sin_tratamiento(trozo):
    """Para artículos sin "señor/señora": tablas con DNI, listas numeradas o nombres en mayúsculas.
    Antes: "... DNI PROVINCIA DEPARTAMENTO JUAN JOSE RAMOS CRUZ 12345678 HUANCAYO JUNIN"
    Después: [{"nombre": "JUAN JOSE RAMOS CRUZ", "dni": "12345678", "ubicacion_tabla": "HUANCAYO JUNIN"}]"""
    personas = []
    if re.search(r"\bDNI\b", trozo):
        cuerpo = trozo[re.search(r"\bDNI\b", trozo).end():]
        # Tablas de subprefectos con la ubicación DESPUÉS del DNI ("DNI DISTRITO PROVINCIA DEPARTAMENTO"):
        # si se pierde la numeración de filas, entre dos DNI queda "ubicación anterior + nombre siguiente".
        # La ubicación termina en el departamento (lista cerrada), así que se corta ahí.
        columnas_ubicacion = re.match(r"\s*((?:(?:DISTRITO|PROVINCIA|DEPARTAMENTO|REGI[ÓO]N)\s+)+)", cuerpo + " ")
        fin_ubicacion = None
        if columnas_ubicacion:
            previas = len(columnas_ubicacion.group(1).split()) - 1
            fin_ubicacion = re.compile(rf"^\s*((?:\S+\s+){{{previas},8}}?{DEPARTAMENTO}(?:\s+{DEPARTAMENTO})*)(?=\s|$)")
        for fila in re.split(r"\s\d{1,3}[\.\)]\s", " " + cuerpo):
            dnis = list(re.finditer(r"(?<!\d)(\d{8})(?!\d)", fila))
            for k, m in enumerate(dnis):
                # Las palabras en mayúsculas justo antes de cada DNI son el nombre (y quizá entidad o cargo)
                antes = fila[dnis[k - 1].end() if k else 0:m.start()]
                corrida = re.search(rf"((?:[{MAY}'’\-\.]+,?\s+){{1,12}})$", antes)
                if not corrida:
                    continue
                palabras = [w for w in corrida.group(1).split() if w.strip(".") not in CABECERA_TABLA - {"Y"}]
                if k and fin_ubicacion:
                    # "CHAVIN DE HUANTAR HUARI ANCASH PEDRO ANTONIO SILVA CHAVEZ" -> se quita "... ANCASH"
                    m_ubic = fin_ubicacion.match(" ".join(palabras))
                    if m_ubic and len(palabras) - len(m_ubic.group(1).split()) >= 2:
                        palabras = palabras[len(m_ubic.group(1).split()):]
                previo, cargo_tabla = [], ""
                coma = [i for i, w in enumerate(palabras) if w.endswith(",")]
                if coma:
                    # "MUNICIPALIDAD PROVINCIAL DE CHEPEN RAMOS CASTILLO, JOSE ANTONIO"
                    #  -> entidad "MUNICIPALIDAD PROVINCIAL DE CHEPEN" | nombre "RAMOS CASTILLO, JOSE ANTONIO"
                    antes_coma, nombres_pila = palabras[:coma[-1] + 1], palabras[coma[-1] + 1:]
                    apellidos = ultimos_apellidos([w.rstrip(",") for w in antes_coma])
                    previo = antes_coma[:len(antes_coma) - len(apellidos)]
                    palabras = apellidos[:-1] + [apellidos[-1] + ","] + nombres_pila
                else:
                    # "GERENTE GENERAL ROSA ELENA TORRES PEREZ" -> cargo "GERENTE GENERAL" | nombre el resto
                    no_nombre = [i for i, w in enumerate(palabras) if CARGO_EN_TABLA.match(w) or NO_NOMBRE.search(w)
                                 or w.strip(".") in (RANGOS | ROLES) - {"DE"}]
                    if no_nombre and len(palabras) - no_nombre[-1] - 1 >= 2:
                        cargo_tabla = " ".join(palabras[:no_nombre[-1] + 1])
                        palabras = palabras[no_nombre[-1] + 1:]
                if len(palabras) >= 2:
                    nombre = " ".join(palabras)
                    p = nueva_persona(nombre, inicio=trozo.find(palabras[0]), fin=trozo.find(palabras[0]),
                                      metodo="tabla con DNI")
                    despues = re.match(rf"\s*((?:[{MAY}'’\-\.]+\s*){{0,8}})", fila[m.end():dnis[k + 1].start() if k + 1 < len(dnis) else None])
                    p["dni"] = m.group(1)
                    p["ubicacion_tabla"] = " ".join(previo) if coma else (despues.group(1).strip() if despues else "")
                    if fin_ubicacion and fin_ubicacion.match(p["ubicacion_tabla"]):
                        p["ubicacion_tabla"] = fin_ubicacion.match(p["ubicacion_tabla"]).group(1).strip()
                    p["cargo_tabla"] = cargo_tabla
                    personas.append(p)
        if personas:
            return personas
    # Lista numerada: "1. Luis Torres Huamán Director de la Estación ..."
    for m in re.finditer(r"(?:^|\s)\d{1,3}[\.\)]\s+(" + NOMBRE_MAYUS + r"|" + NOMBRE_TITULO + r")", trozo):
        nombre = limpiar_nombre(m.group(1))
        if len(nombre.split()) >= 2 and not NO_NOMBRE.search(nombre.upper()):
            personas.append(nueva_persona(nombre, inicio=m.start(1), fin=m.start(1) + len(nombre), metodo="lista numerada"))
    if personas:
        return personas
    # Lista con viñetas: "• Carlos Eduardo Rojas Vega • Luis Alberto Soto Ruiz" o "- Ángel Mario Castro León, en ..."
    for m in re.finditer(r"(?:^|\s)[•▪●\-–]\s+(" + NOMBRE_MAYUS + r"|" + NOMBRE_TITULO + r")", trozo):
        nombre = limpiar_nombre(m.group(1))
        if (3 <= len(nombre.split()) <= 6 and not PALABRAS_CARGO.match(nombre) and not NO_NOMBRE.search(nombre.upper())
                and not re.search(r"Direcci|Oficina|Unidad|Gerencia|Programa|Fiscal|Distrito|Sala|Junta|Tribunal", nombre)):
            personas.append(nueva_persona(nombre, inicio=m.start(1), fin=m.start(1) + len(nombre), metodo="lista con viñetas"))
    if personas:
        return personas
    # Nombre justo después del verbo, sin tratamiento: "Designar a Rosa Esther Vargas Sanchez en el cargo de ..."
    m = re.search(r"\b(?:a|al)\s+(" + NOMBRE_MAYUS + r"|" + NOMBRE_TITULO + r")(?=\s*,|\s+en\s+(?:el|los)\s|\s+como\s|\s+para\s)",
                  trozo[:300])
    if m and not PALABRAS_CARGO.match(m.group(1)) and not NO_NOMBRE.search(m.group(1).upper()):
        palabras = m.group(1).split()
        grado = []
        while palabras and palabras[0].upper().strip(".") in RANGOS:     # "Coronel EP Luis ..." -> grado + nombre
            grado.append(palabras.pop(0))
        nombre = limpiar_nombre(" ".join(palabras))
        if len(nombre.split()) >= 2:
            return [nueva_persona(nombre, grado=" ".join(grado), inicio=m.start(1), fin=m.end(1), metodo="después del verbo")]
    # Tabla "Nombres y apellidos | Puesto": nombres con mayúscula inicial de 3 a 6 palabras
    if re.search(r"Nombres?\s+y\s+Apellidos|NOMBRES?\s+Y\s+APELLIDOS", trozo):
        cuerpo = trozo[re.search(r"Nombres?\s+y\s+Apellidos|NOMBRES?\s+Y\s+APELLIDOS", trozo).end():]
        desfase = len(trozo) - len(cuerpo)
        for m in re.finditer(NOMBRE_MAYUS + r"|" + NOMBRE_TITULO, cuerpo):
            nombre = limpiar_nombre(m.group(0))
            if 3 <= len(nombre.split()) <= 6 and not PALABRAS_CARGO.match(nombre) and not NO_NOMBRE.search(nombre.upper()) \
                    and not re.search(r"C[oó]digo|Puesto|Efectiv|Gerencia|Oficina|Unidad|Direcci|Programa", nombre):
                personas.append(nueva_persona(nombre, inicio=desfase + m.start(), fin=desfase + m.start() + len(nombre),
                                              metodo="tabla nombres y apellidos"))
        if personas:
            return personas
    # Nombres en mayúsculas sin tratamiento (3 a 7 palabras, sin palabras de entidad ni verbos)
    for m in re.finditer(rf"(?:^|[\s:\-–•,])((?:[{MAY}'’]{{2,}}\s+){{2,8}}[{MAY}'’]{{2,}})(?=[\s,;.]|$)", trozo):
        # Se conservan las palabras antes de la primera palabra de entidad:
        # "MARCO ANTONIO RIOS VEGA INTENDENCIA NACIONAL ..." -> "MARCO ANTONIO RIOS VEGA"
        palabras = m.group(1).split()
        corte = next((i for i, w in enumerate(palabras) if NO_NOMBRE.search(w)), len(palabras))
        palabras = palabras[:corte]
        while palabras and palabras[-1] in PARTICULAS:
            palabras.pop()
        if len(palabras) < 3 or palabras[0] in PARTICULAS:
            continue
        # Ocho palabras seguidas suelen ser dos personas de una lista: "LUIS MIGUEL CRUZ PALMA JUAN CARLOS SOTO LEON"
        grupos = [palabras[:4], palabras[4:]] if len(palabras) == 8 else [palabras]
        for grupo in grupos:
            nombre = " ".join(grupo)
            inicio = m.start(1) + m.group(1).find(nombre)
            personas.append(nueva_persona(nombre, inicio=inicio, fin=inicio + len(nombre), metodo="mayúsculas sin tratamiento"))
    return personas


# Primer verbo en infinitivo del artículo. Los de movimiento definen el tipo; los administrativos
# (notificar, disponer, publicar...) indican que el artículo no es un movimiento.
# Se busca en los primeros 200 caracteres porque algunos artículos llevan un título antes del verbo:
# "Artículo 1.- Designación Designar al señor ..."
VERBO = re.compile(r"\b(dejar\s+sin\s+efecto|dar(?:se)?(?:\s*,[^,]{0,80},)?\s+por\s+conclu\w*|declarar\s+(?:la\s+)?conclu\w*|"
                   r"dar(?:se)?(?:\s*,[^,]{0,80},)?\s+por\s+terminad\w*|dar\s+t[ée]rmino|se\s+da\s+t[ée]rmino|"
                   r"se\s+da(?:n)?\s+por\s+terminad\w*|"
                   r"se\s+deja\s+sin\s+efecto|se\s+da(?:n)?(?:\s*,[^,]{0,80},)?\s+por\s+conclu\w*|se\s+acepta|se\s+encarga|"
                   r"se\s+designa|se\s+nombra|"
                   r"concluir|cesar|remover|aceptar|encargar|designar|des[íi]gnese|nombrar|ratificar|asignar|rotar|reasignar|"
                   r"prorrogar|(?:se\s+)?formaliza(?:r)?\s+la\s+designaci[oó]n|"
                   r"disponer\s+la\s+(?:incorporaci[oó]n\s+y\s+)?designaci[oó]n|notificar|disponer|remitir|publicar|transcribir|"
                   r"comunicar|precisar|establecer|autorizar|aprobar|modificar|derogar|expresar|dar\s+las\s+gracias|"
                   r"agradecer)\b", re.I)
ARTICULO = re.compile(r"Art[íi]culo\s*\.?\s*(\d+[°º]?|[ÚU]nico|Primero|Segundo|Tercero|Cuarto|Quinto|Sexto|S[ée]p?timo|"
                      r"Octavo|Noveno|D[ée]cimo)\s*[\.\-–:]+\s*", re.I)
FECHA_INICIO = re.compile(r"(?:a partir del?|con efectividad al?|con eficacia anticipada al?|desde el|con efectos? al?)\s+"
                          r"(?:d[íi]a\s+)?(\d{1,2})[°º]?\s+de\s+([a-záéíóú]+)\s+(?:de|del)\s+(\d{4})", re.I)
PERIODO = re.compile(r"del?\s+(\d{1,2})[°º]?\s+(?:de\s+([a-záéíóú]+)\s+(?:de\s+(\d{4})\s+)?)?al\s+(\d{1,2})[°º]?\s+de\s+"
                     r"([a-záéíóú]+)\s+(?:de|del)\s+(\d{4})", re.I)


def tipo_de(texto_articulo):
    """Antes: "Designación Designar TEMPORALMENTE, a partir del ..." | Después: "designación"
    (None si el primer verbo es administrativo, como "Notificar la presente resolución")"""
    m = VERBO.search(texto_articulo[:200])
    if not m:
        return None
    verbo = re.sub(r"^se\s+", "", re.sub(r"\s+", " ", m.group(1).lower()))   # "se designa" -> "designa"
    if verbo.startswith(("dejar", "deja ")):
        return "dejar sin efecto"
    if "conclu" in verbo or "termin" in verbo or "término" in verbo or verbo in ("cesar", "remover"):
        return "conclusión"
    if verbo in ("aceptar", "acepta"):
        return "renuncia" if re.search(r"renuncia", texto_articulo[m.start():m.start() + 200], re.I) else None
    if verbo in ("encargar", "encarga"):
        return "encargatura"
    if verbo.startswith("des") or "formaliza" in verbo or "designaci" in verbo:
        return "designación"
    if verbo == "nombra":
        return "nombramiento"
    return {"nombrar": "nombramiento", "ratificar": "ratificación", "asignar": "asignación de funciones",
            "rotar": "rotación o reasignación", "reasignar": "rotación o reasignación", "prorrogar": "prórroga"}.get(verbo)


FIN_CARGO = (r"(?=,\s*(?:cargo|puesto) considerado|,?\s*con efectividad|,?\s*con eficacia|,\s*a partir|,\s*en adici[oó]n|"
             r",\s*d[aá]ndos|,\s*agradeci|,\s*en tanto|,\s*mientras|,\s*por el periodo|,\s*del?\s+\d|,\s*materia de|,?\s*efectuad|"
             r",\s*por motivo|,\s*bajo|,\s*siendo|,\s*designad[oa]\s+(?:mediante|por|con)|,\s*dispuest[oa]|,\s*con sede|,\s*quien|"
             r",\s*conforme|,\s*de acuerdo|,\s*en reemplazo|,\s*perteneciente|,?\s*con\s+c[óo]digo|;|\.\s|\.$|$)")
# Frases que pueden ir entre el nombre y el cargo y que se saltan para llegar al cargo
# (consume cada inciso pero deja la coma que le sigue, para que los patrones de abajo funcionen igual)
INCISOS = (r"^(?:\s*,?\s*(?:identificad[oa] con[^,]*|a partir[^,]*|con efectividad[^,]*|con eficacia[^,]*|"
           r"en adici[oó]n (?:a|de) sus funciones(?: que viene desempeñando)?)(?=\s*,))*")


def cargo_de(texto, persona, tipo):
    """Antes: texto del artículo y la persona | Después: (cargo, cargo que ya ocupaba mencionado junto al nombre)"""
    if persona.get("cargo_tabla"):
        # Tabla con el cargo en su propia columna: "GERENTE GENERAL | ROSA ELENA TORRES PEREZ | DNI"
        return persona["cargo_tabla"], ""
    if persona.get("metodo_nombre") == "mayúsculas sin tratamiento":
        # Lista "- Intendente Nacional de Asesoría Legal Interna MARCO ANTONIO RIOS VEGA": el cargo va antes
        previo_lista = re.search(r"[-–•]\s*([A-ZÁÉÍÓÚ][^-–•]{3,200}?)\s*$", texto[:persona["inicio"]])
        if previo_lista and not previo_lista.group(1).isupper():
            # quita el nombre de la persona anterior si quedó pegado al final ("Supervisor 1 LUIS MIGUEL ...")
            return re.sub(rf"(?:\s+[{MAY}'’]{{2,}})+$", "", previo_lista.group(1)), ""
    despues = re.sub(INCISOS, "", texto[persona["fin"]:], count=1)
    # Fiscales y jueces: "..., fiscal adjunta provincial titular de Huaraz, Distrito Fiscal de Áncash, en la Quinta Fiscalía ..."
    fiscal = re.match(r"^\s*,?\s*((?:fiscal|juez|jueza)\b[^;]+?),\s*(?:actualmente[^,]*,\s*)?(?:en|para)\s+(?:la|el)\s+(.+?)" + FIN_CARGO,
                      despues, re.I)
    if fiscal:
        return f"{fiscal.group(1).strip()} — {fiscal.group(2).strip(' ,;.')}", fiscal.group(1).strip()
    actual = re.match(r"^\s*,\s*([A-ZÁÉÍÓÚ][^,]{3,150}?),\s*(?=como|en el cargo|en el puesto|en adici|en el despacho|al cargo|y|para)",
                      despues)
    if actual:
        despues = re.sub(INCISOS, "", despues[actual.end():], count=1)
    m = re.match(r"^\s*,?\s*(?:en\s+(?:el\s+|los\s+)?(?:cargo|puesto|cargos|puestos)(?:\s+estructural)?(?:\s+(?:p[úu]blico\s+)?de\s+confianza)?(?:\s+de)?|como|"
                 r"(?:al|el)\s+(?:cargo|puesto)(?:\s+de\s+confianza)?\s+de|para\s+(?:el\s+desempeño\s+de\s+)?(?:las\s+funciones|el\s+cargo|el\s+puesto)\s+de|"
                 r"en\s+las\s+funciones\s+de|las\s+funciones\s+de|en\s+el\s+[Dd]espacho\s+de|que\s+venía\s+desempeñando\s+como|"
                 r"(?:la|el)\s+(?=(?:Jefatura|Direcci[oó]n|Gerencia|Presidencia|Secretar[íi]a|Coordinaci[oó]n|Subdirecci[oó]n|"
                 r"Subgerencia|Oficina|Unidad|Despacho|Intendencia|Superintendencia)\b))\s*(.+?)" + FIN_CARGO,
                 despues)
    cargo = m.group(1) if m else ""
    if not cargo and not actual:
        # Cargo como aposición: "... al señor X, Viceministro de Pesca y Acuicultura, dándosele las gracias"
        aposicion = re.match(r"^\s*,\s*([A-ZÁÉÍÓÚ][^,]{3,150}?)" + FIN_CARGO, despues)
        if aposicion:
            return aposicion.group(1).strip(" ,;."), aposicion.group(1).strip()
    if not cargo and not persona["tratamiento"]:
        # Lista sin tratamiento: el cargo sigue al nombre hasta el siguiente número o el siguiente nombre en mayúsculas
        lista = re.match(r"^\s*,?\s*(?:como\s+)?([A-ZÁÉÍÓÚa-záéíóú].+?)(?=\s\d{1,3}[\.\)]\s|\s(?:[A-ZÁÉÍÓÚÑ]{2,}\s+){2,}|;|\.\s|\.$|$)",
                         despues)
        cargo = lista.group(1) if lista and not persona.get("dni") else ""
        if persona.get("dni"):
            cabecera = re.search(r"(?:en\s+el\s+cargo|en\s+los\s+cargos|como)\s+(?:de\s+)?(.+?)\s+(?:a|al|a\s+los(?:/as)?|a\s+las|"
                                 r"de\s+los(?:/las)?|de\s+las)\s+(?:siguientes?|ciudadan|profesional|servidor|persona|funcionari)",
                                 texto, re.I)
            cargo = cabecera.group(1) if cabecera else ""
    if not cargo:
        antes = texto[:persona["inicio"]]
        # El cargo va justo después del verbo: "Nombrar Ministro de Estado en el Despacho del Ambiente, al señor X"
        tras_verbo = re.search(r"^\s*(?:[A-ZÁÉÍÓÚa-záéíóú]+\s+){0,4}?(?:nombrar|designar|encargar)\s+(?:como\s+)?"
                               r"([A-ZÁÉÍÓÚ][^;]+?)\s*,?\s*$", antes, re.I)
        if tras_verbo and not re.match(r"(?:a|al|la|el)\s", tras_verbo.group(1), re.I):
            return tras_verbo.group(1).strip(" ,;."), ""
    if not cargo:
        # El cargo va antes del nombre: "Encargar el puesto de Viceministro ... al señor X"
        previo = list(re.finditer(r"(?:cargo|puesto|funciones|designaci[oó]n|Presidencia|Jefatura|Direcci[oó]n)(?:\s+de\s+confianza)?"
                                  r"\s+(?:de|del|de la)\s+(.+?)\s*,?\s*$|como\s+(.+?)\s*,?\s*$", antes))
        if previo:
            cargo = previo[-1].group(1) or previo[-1].group(2) or ""
        if not cargo and actual:
            cargo = actual.group(1)
    return cargo.strip(" ,;."), (actual.group(1).strip() if actual else "")


def recortar_cargo(cargo):
    """Antes: "Jefe/a del Órgano de Control Institucional de los/las profesionales que se detallan a continuación: N° ..."
    Después: "Jefe/a del Órgano de Control Institucional"
    (corta donde empieza la tabla, el cierre "Regístrese..." o el artículo siguiente; vacío si queda una sola sílaba)"""
    cargo = re.split(r"(?:^|\s+)Reg[íi]strese|\s+Art[íi]culo\s|\s+(?:de|a)\s+(?:los|las)(?:/(?:as|las|os))?\s+(?:siguientes|profesional|"
                     r"servidor|persona|ciudadan|funcionari)|\s+que\s+se\s+(?:detallan|indican|señalan)|\s*:", cargo, maxsplit=1)[0]
    # "al 01 de abril de 2025, en el cargo de Auxiliar Coactivo ..." -> desde lo que sigue a "en el cargo de"
    #   (no se aplica si antes aparece otra persona: "Presidente, y del señor X, en el cargo de Vicepresidente")
    trozos = re.split(r"\ben\s+el\s+(?:cargo|puesto)\s+(?:de\s+confianza\s+(?:de\s+)?|(?:de|como)\s+)", cargo, maxsplit=1, flags=re.I)
    if (len(trozos) == 2 and not re.match(r"(?:en\s+)?el\s+(?:cargo|puesto)", cargo, re.I)
            and not re.search(r"(?:\by|as[íi]\s+como)\s+(?:del?|al?|la)\s+(?:la\s+)?se[ñn]or", trozos[0], re.I)):
        cargo = trozos[1]
    cargo = cargo.strip(" ,;.-–")
    return cargo if len(cargo) >= 4 else ""


def movimientos_de_norma(partes, datos_norma):
    """Antes: parte resolutiva | Después: lista de movimientos (diccionarios)"""
    resolutiva = partes["resolutiva"]
    cortes = list(ARTICULO.finditer(resolutiva))
    articulos = ([(m.group(1), resolutiva[m.end():(cortes[i + 1].start() if i + 1 < len(cortes) else len(resolutiva))])
                  for i, m in enumerate(cortes)] or [("", resolutiva)])
    agradece_aparte = any(re.match(r"^\s*(?:dar|darle|darles|expresar)\s+(?:las\s+)?gracias|^\s*agradecer", t, re.I)
                          for _, t in articulos)
    movimientos, vistos_personas = [], set()
    for numero, texto_art in articulos:
        # Un artículo puede tener dos acciones: "Dar por concluida ... y designar ..."
        trozos = re.split(r"[;,]?\s+y\s+(?=(?:designar|encargar|aceptar|dar por|nombrar)\b)", texto_art, flags=re.I)
        for trozo in trozos:
            tipo = tipo_de(trozo)
            if tipo is None:
                continue
            if tipo == "encargatura" and re.search(
                    r"encarga(?:r)?\s*,?\s+(?:a|al)\s+(?:la|el|las|los)?\s*(?:Oficina|Unidad|Sub|Gerencia|Secretar|Direcci|[ÓO]rgano|"
                    r"Coordinaci|[ÁA]rea|Equipo|Procuradur|Despacho|Jefatura|Mesa|Concejo|Comit)|"
                    r"encarga(?:r)?\s+(?:la|el)\s+(?:notificaci|publicaci|cumplimiento|ejecuci)",
                    trozo[:200], re.I):
                continue   # "ENCARGAR, a la Oficina de RR.HH. la notificación...": es administrativo
            personas = buscar_personas(trozo)
            if not personas:
                personas = personas_sin_tratamiento(trozo)
            if not personas and tipo == "dejar sin efecto" and not re.search(r"N[°º]|designaci|encarg", trozo, re.I):
                continue   # "Dejar sin efecto toda resolución que se oponga...": cláusula general, no es un movimiento
            if not personas and tipo == "encargatura" and re.search(r"publicaci|notifica|Portal de Transparencia", trozo, re.I):
                continue   # "Encargar al responsable del Portal ... la publicación": administrativo, sin persona
            fecha_ini = FECHA_INICIO.search(trozo)
            periodo = PERIODO.search(trozo)
            ultimo_dia = re.search(r"[úu]ltimo d[íi]a de labores (?:el )?(\d{1,2})[°º]?\s+de\s+([a-záéíóú]+)\s+(?:de|del)\s+(\d{4})", trozo, re.I)
            adicion = re.search(r"en adici[oó]n (?:a|de) (?:sus|las) funciones(?: que viene desempeñando)?(?:\s+(?:de|como)\s+([^,;.]+))?",
                                trozo, re.I)
            antecedente = re.search(r"(?:efectuad[oa]|dispuest[oa]|realizad[oa]|formalizad[oa]|conferid[oa]|otorgad[oa]|"
                                    r"encargad[oa]|materia de|aprobad[oa])\s+(?:con|mediante|por|a través de|de)?\s*(?:el|la)?\s*"
                                    r"((?:Resoluci[oó]n|Decreto)[^,;.]*?N[°º]\s*[\w\-/]+)", trozo, re.I)
            if not personas:
                personas = [{"nombre": "", "tratamiento": "", "sexo_segun_norma": "", "profesion_mencionada": "",
                             "grado_militar_policial": "", "inicio": 0, "fin": 0}]
            for p in personas:
                clave = (normalizar_nombre(p["nombre"]), tipo)
                if p["nombre"] and clave in vistos_personas:
                    continue
                vistos_personas.add(clave)
                cargo, cargo_actual = cargo_de(trozo, p, tipo) if p["nombre"] else ("", "")
                cargo = recortar_cargo(cargo)
                norma_previa = antecedente.group(1) if antecedente else ""
                if not norma_previa and p["nombre"] and tipo in ("renuncia", "conclusión", "dejar sin efecto"):
                    # Buscar en los considerandos la frase que dice con qué norma se designó a esta persona
                    apellido = normalizar_nombre(p["nombre"]).split()[-2] if len(p["nombre"].split()) > 2 else ""
                    for frase in re.split(r";", partes["considerandos"]):
                        if apellido and apellido in normalizar_nombre(frase) and re.search(r"design|encarg", frase, re.I):
                            r = re.search(r"((?:Resoluci[oó]n|Decreto)[^,;]*?N[°º]\s*[\w\-/]+)", frase)
                            if r:
                                norma_previa = r.group(1)
                                break
                if tipo == "dejar sin efecto" and not norma_previa:
                    r = re.search(r"((?:Resoluci[oó]n|Decreto)[^,;]*?N[°º]\s*[\w\-/]+)", trozo)
                    norma_previa = r.group(1) if r else ""
                movimientos.append({
                    "articulo": numero,
                    "tipo_movimiento": tipo,
                    "temporal": bool(re.search(r"temporal", trozo[:300], re.I)),
                    # en minúsculas y con tilde, para que "DESIGNACION" y "designación" cuenten como lo mismo
                    "objeto_conclusion": ((re.search(r"conclu\w+\s+(?:la|el|las|los)\s+(designaci[oó]n|encargo|encargatura|"
                                                     r"nombramiento|funciones|asignaci[oó]n)", trozo, re.I) or [None, ""])[1]
                                          .lower().replace("cion", "ción").replace("funciónes", "funciones")
                                          if tipo == "conclusión" else ""),
                    "nombre_tal_cual": p["nombre"],
                    "nombre_normalizado": normalizar_nombre(p["nombre"]),
                    "metodo_nombre": p.get("metodo_nombre", "") if p["nombre"] else "",
                    "tratamiento": p["tratamiento"].lower(),
                    "sexo_segun_norma": p["sexo_segun_norma"],
                    "profesion_mencionada": p["profesion_mencionada"],
                    "grado_militar_policial": p["grado_militar_policial"],
                    "dni": p.get("dni") or ((re.search(re.escape(p["nombre"]) + r"\D{0,40}?(\d{8})", trozo) or [None, ""])[1]
                                            if p["nombre"] else ""),
                    "ubicacion_tabla": p.get("ubicacion_tabla", ""),
                    "cargo": cargo,
                    "cargo_actual_mencionado": cargo_actual,
                    "en_adicion_a_funciones": bool(adicion),
                    "funciones_que_mantiene": (adicion.group(1) or "").strip() if adicion else "",
                    # fecha_efectividad: desde cuándo rige el movimiento si la norma lo dice (si no, rige desde la publicación)
                    "fecha_efectividad": (a_fecha(*fecha_ini.groups()) if fecha_ini else
                                          a_fecha(periodo.group(1), periodo.group(2) or periodo.group(5), periodo.group(3) or periodo.group(6))
                                          if periodo else None),
                    "fecha_fin": (a_fecha(periodo.group(4), periodo.group(5), periodo.group(6)) if periodo else
                                  a_fecha(*ultimo_dia.groups()) if ultimo_dia else None),
                    "inicio_texto": fragmentos(r"(?:a partir|con efectividad|con eficacia anticipada|con efectos?)[^,;.]*", trozo, 1),
                    "condicion_texto": fragmentos(r"(?:en tanto se design[ae]|mientras dure|por (?:motivo de )?(?:vacaciones|licencia|"
                                                  r"descanso|comisi[oó]n de servicio)|con retenci[oó]n de (?:su )?cargo)[^,;.]*", trozo, 2),
                    "agradecimiento": bool(re.search(r"d[aá]ndos[e]?le[s]? las gracias|agradec", trozo, re.I))
                                      or (agradece_aparte and tipo in ("renuncia", "conclusión")),
                    "norma_antecedente": norma_previa,
                    "en_tabla_con_dni": bool(p.get("dni")),
                    "texto_articulo": trozo.strip()[:1500],
                })
    return movimientos


# ============================================================
# PROCESO 6: Recorrer todas las normas, armar las dos tablas y verificarlas
# Insumo:    lista de normas + textos
# Resultado: normas.csv y movimientos.csv
# ============================================================
def main():
    lista = cargar_lista()
    filas_normas, filas_mov = [], []
    for norma in lista.to_dict("records"):
        archivo = CARPETA_TEXTOS / f"{norma['codigo_norma']}.txt"
        fila = dict(norma)
        if not archivo.exists():
            fila["estado_extraccion"] = "sin texto descargado"
            filas_normas.append(fila)
            continue
        texto_paginas = archivo.read_text(encoding="utf-8")
        texto_reparado = reparar_fuente_antigua(texto_paginas)   # solo cambia los PDF con la fuente dañada
        fila["fuente_reparada"] = texto_reparado != texto_paginas
        lineas = recortar_norma(texto_reparado, norma["codigo_norma"])
        if lineas is None:
            fila["estado_extraccion"] = "código no encontrado en el PDF"
            filas_normas.append(fila)
            continue
        lineas = tablas_por_celda(lineas)   # tablas con una celda por línea: nombre separado de la ubicación
        partes = separar_partes(lineas)
        fila.update(datos_de_norma(partes))
        movimientos = movimientos_de_norma(partes, fila)
        fila["n_movimientos"] = len(movimientos)
        fila["n_sin_nombre"] = sum(1 for m in movimientos if not m["nombre_tal_cual"])
        fila["estado_extraccion"] = ("sin movimientos detectados" if not movimientos else
                                     "revisar: movimiento sin nombre" if fila["n_sin_nombre"] else "ok")
        fila["texto_norma"] = partes["texto"]
        filas_normas.append(fila)
        # Cada movimiento lleva los datos clave de la norma (como en una hoja de Excel "plana")
        for orden, mov in enumerate(movimientos, start=1):
            filas_mov.append({
                "id_movimiento": f"{norma['codigo_norma']}#{orden}",
                "codigo_norma": norma["codigo_norma"],
                "fecha_publicacion": norma.get("fecha_publicacion"),
                "fecha_emision": fila.get("fecha_emision"),
                "sector_ep": norma.get("sector_ep"),
                "institucion": norma.get("institucion"),
                "dispositivo": norma.get("dispositivo"),
                "sumilla": norma.get("sumilla"),
                **mov,
                **{k: fila.get(k, "") for k in ["firmante1_nombre", "firmante1_cargo", "firmante2_nombre",
                                                "firmante2_cargo", "firmante3_nombre", "firmante3_cargo"]},
                "enlace_pdf": norma.get("enlace_pdf"),
                "enlace_web": norma.get("enlace_web"),
            })

    normas = pd.DataFrame(filas_normas)
    movimientos = pd.DataFrame(filas_mov)

    # Verificación: tamaños, estado de la extracción y campos vacíos
    print("Normas:", normas.shape, "| Movimientos:", movimientos.shape)
    print("\nEstado de la extracción:\n", normas["estado_extraccion"].value_counts().to_string())
    if len(movimientos):
        print("\nTipos de movimiento:\n", movimientos["tipo_movimiento"].value_counts().to_string())
        print("\n% de movimientos con dato, por campo:")
        for col in ["nombre_tal_cual", "cargo", "sexo_segun_norma", "fecha_emision", "fecha_efectividad",
                    "norma_antecedente", "firmante1_nombre", "firmante2_nombre"]:
            lleno = movimientos[col].notna() & (movimientos[col].astype(str).str.strip() != "")
            print(f"  {col:25s} {100 * lleno.mean():5.1f} %")

    normas.to_csv(CARPETA_PROCESADOS / "normas.csv", index=False, encoding="utf-8-sig")
    movimientos.to_csv(CARPETA_PROCESADOS / "movimientos.csv", index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
