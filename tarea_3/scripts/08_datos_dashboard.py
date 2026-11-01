# ============================================================
# Designaciones de El Peruano — Script 08: datos para el dashboard (proceso 17 del mapa)
# ------------------------------------------------------------
# Prepara los datos que usa la página web (web/index.html): solo cifras agregadas y códigos anónimos
# (id_persona). NINGÚN nombre de persona sale de este script: es lo único que se publica.
#
# Insumos:   datos/procesados/movimientos_analisis.csv (script 06) y datos/procesados/indicadores/*.csv (script 07)
# Resultado: web/data/dashboard.json
#
# Uso (desde la carpeta tarea_3):
#   python scripts/08_datos_dashboard.py
# ============================================================

# --- Paquetes ---
# json: escribir el archivo de datos que lee la página web
import json
# Counter y combinations: contar instituciones por punto y revisar pares de jefes (puentes)
from collections import Counter
from itertools import combinations
# re y unicodedata: normalizar nombres de instituciones
import re
import unicodedata
# pathlib: rutas de archivos
from pathlib import Path
# numpy y pandas: tablas y cálculos
import numpy as np
import pandas as pd
# networkx: calcular la posición de cada persona en el dibujo de la red
import networkx as nx

CARPETA_TAREA = Path(__file__).resolve().parent.parent
PROCESADOS = CARPETA_TAREA / "datos" / "procesados"
INDICADORES = PROCESADOS / "indicadores"
SALIDA = CARPETA_TAREA / "web" / "data" / "dashboard.json"
SALIDA.parent.mkdir(parents=True, exist_ok=True)
FIN_VENTANA = pd.Timestamp("2026-10-29")
ENTRADA = {"designación", "nombramiento", "encargatura"}


def sin_tildes(texto):
    """Antes: "Desarrollo e Inclusión Social" | Después: "DESARROLLO E INCLUSION SOCIAL" """
    texto = "".join(c for c in unicodedata.normalize("NFD", str(texto)) if unicodedata.category(c) != "Mn").upper()
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]", " ", texto)).strip()


# ============================================================
# PROCESO 17.1: Catálogos (gobiernos, ministerios, niveles)
# Insumo:    gobiernos.csv y movimientos_analisis.csv
# Resultado: listas con nombre legible e índice, que la página usa en sus filtros
# ============================================================
gobiernos = pd.read_csv(INDICADORES / "gobiernos.csv", parse_dates=["inicio"])
APELLIDO = {"JERI": "Jerí", "BALCAZAR": "Balcázar"}
gobiernos["corto"] = gobiernos["presidente"].map(lambda p: APELLIDO.get(p.split()[-2], p.split()[-2].title()))
gobiernos["fin"] = gobiernos["inicio"].shift(-1).fillna(FIN_VENTANA)
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "set", "oct", "nov", "dic"]


def mes_anio(fecha):
    """Antes: Timestamp(2025-10-13) | Después: "oct-2025" """
    return f"{MESES[fecha.month - 1]}-{fecha.year}"


catalogo_gobiernos = [{"id": i, "corto": g["corto"], "inicio": g["inicio"].date().isoformat(),
                       "fin": g["fin"].date().isoformat(),
                       "etiqueta": f"{g['corto']} ({'hasta ' + mes_anio(g['fin']) if i == 0 else mes_anio(g['inicio']) + ' – ' + (mes_anio(g['fin']) if i < len(gobiernos) - 1 else 'oct-2026')})"}
                      for i, g in gobiernos.iterrows()]


def gobierno_idx(fecha):
    """Antes: una fecha | Después: índice del gobierno de ese día (0 = el primero de la ventana)"""
    return int(max(0, np.searchsorted(gobiernos["inicio"].values, np.datetime64(fecha), side="right") - 1))


MINISTERIOS = {  # nombre en la base (sin tildes) -> nombre legible
    "PRESIDENCIA DEL CONSEJO DE MINISTROS": "Presidencia del Consejo de Ministros (PCM)", "AMBIENTE": "Ambiente (MINAM)",
    "COMERCIO EXTERIOR Y TURISMO": "Comercio Exterior y Turismo (MINCETUR)", "CULTURA": "Cultura", "DEFENSA": "Defensa (MINDEF)",
    "DESARROLLO AGRARIO Y RIEGO": "Desarrollo Agrario y Riego (MIDAGRI)",
    "DESARROLLO E INCLUSION SOCIAL": "Desarrollo e Inclusión Social (MIDIS)", "ECONOMIA Y FINANZAS": "Economía y Finanzas (MEF)",
    "EDUCACION": "Educación (MINEDU)", "ENERGIA Y MINAS": "Energía y Minas (MINEM)", "INTERIOR": "Interior (MININTER)",
    "JUSTICIA Y DERECHOS HUMANOS": "Justicia y Derechos Humanos (MINJUSDH)",
    "MUJER Y POBLACIONES VULNERABLES": "Mujer y Poblaciones Vulnerables (MIMP)", "PRODUCE": "Producción (PRODUCE)",
    "RELACIONES EXTERIORES": "Relaciones Exteriores (RREE)", "SALUD": "Salud (MINSA)",
    "TRABAJO Y PROMOCION DEL EMPLEO": "Trabajo y Promoción del Empleo (MTPE)",
    "TRANSPORTES Y COMUNICACIONES": "Transportes y Comunicaciones (MTC)",
    "VIVIENDA CONSTRUCCION Y SANEAMIENTO": "Vivienda, Construcción y Saneamiento (MVCS)"}
CLAVES_MINISTERIO = list(MINISTERIOS)
catalogo_ministerios = [MINISTERIOS[k] for k in CLAVES_MINISTERIO] + ["Otras entidades (organismos, autónomos, regiones)"]
OTRAS = len(CLAVES_MINISTERIO)


def ministerio_idx(institucion):
    """Antes: "DESARROLLO E INCLUSIÓN SOCIAL" | Después: índice en catalogo_ministerios (OTRAS si no es ministerio)"""
    clave = sin_tildes(institucion)
    return CLAVES_MINISTERIO.index(clave) if clave in MINISTERIOS else OTRAS


NIVELES = ["J1 Ministro", "J2 Viceministro", "J3 Secretario general, jefe de gabinete o titular de entidad",
           "J4 Director general o jefe de órgano", "J5 Asesor o apoyo de alta dirección", "J6 Jefe de unidad orgánica",
           "J7 Subunidad o apoyo", "Sin nivel (directorios, subprefectos, diplomáticos)"]


def nivel_idx(jerarquia):
    """Antes: "J4 Director general o jefe de órgano" | Después: 3 (7 si no tiene nivel)"""
    return NIVELES.index(jerarquia) if jerarquia in NIVELES else 7


SEXOS = ["F", "M"]

# ============================================================
# PROCESO 17.2: Movimientos del análisis principal, agregados (sin nombres)
# Insumo:    movimientos_analisis.csv
# Resultado: "cubo" de designaciones por mes, gobierno, ministerio, nivel y sexo; indicadores por cada combinación de filtros
# ============================================================
mov = pd.read_csv(PROCESADOS / "movimientos_analisis.csv", encoding="utf-8-sig", dtype=str)
mov = mov[mov["en_analisis_principal"] == "True"].copy()
firma = pd.to_datetime(mov["fecha_emision_corregida"], errors="coerce")
publicacion = pd.to_datetime(mov["fecha_publicacion"], dayfirst=True)
efectividad = pd.to_datetime(mov["fecha_efectividad"], errors="coerce")
efectividad = efectividad.where((efectividad - firma.fillna(publicacion)).abs() <= pd.Timedelta(days=365))
mov["fecha"] = efectividad.fillna(firma).fillna(publicacion)
# Totales del análisis principal (los mismos del informe), antes de quitar las fechas fuera de la ventana
# Personas se cuentan por clave normalizada, igual que en el análisis (07); el código del registro puede unir variantes
# del mismo nombre que comparten DNI (alias), y eso todavía no se aplica a la identidad del análisis
TOTAL_PRINCIPAL, PERSONAS_PRINCIPAL = len(mov), mov["clave_persona"].nunique()
# Para los gráficos por mes y por gobierno: solo fechas dentro de la ventana (algunas normas tienen efectividad anterior)
mov = mov[(mov["fecha"] >= "2022-11-01") & (mov["fecha"] <= FIN_VENTANA)]
mov["g"] = mov["fecha"].map(gobierno_idx)
mov["m"] = mov["institucion_del_cargo"].map(ministerio_idx)
mov["j"] = mov["jerarquia_puesto"].map(nivel_idx)
mov["s"] = mov["sexo_analisis"].map(lambda s: SEXOS.index(s) if s in SEXOS else -1)
mov["mes"] = mov["fecha"].dt.strftime("%Y-%m")
entradas = mov[mov["tipo_movimiento"].isin(ENTRADA)]
meses = sorted(mov["mes"].unique())
cubo = (entradas.assign(mi=entradas["mes"].map(meses.index)).groupby(["mi", "g", "m", "j", "s"]).size()
        .reset_index().values.tolist())
print("17.2 Designaciones del análisis principal:", len(entradas), "| filas del cubo:", len(cubo))

# Primera aparición de cada persona en la base (cualquier movimiento) y en cuántos gobiernos tuvo movimientos:
# con un gobierno elegido, "ya tenía cargo" = apareció antes de que empezara ese gobierno;
# sin gobierno elegido, se cuenta a quienes tuvieron cargos en dos o más gobiernos
primera_vez = mov.dropna(subset=["clave_persona"]).groupby("clave_persona")["fecha"].min()
gobiernos_por_persona = mov.dropna(subset=["clave_persona"]).groupby("clave_persona")["g"].nunique()

# ============================================================
# PROCESO 17.3: Duración en el cargo (periodos de titulares, regla de sucesión), sin nombres
# Insumo:    periodos_titulares.csv (script 07)
# Resultado: lista de periodos con ministerio, gobierno de inicio, nivel, sexo, días y si sigue abierto
# ============================================================
periodos = pd.read_csv(INDICADORES / "periodos_titulares.csv", parse_dates=["inicio", "fin"], dtype={"censurado": bool})


# Vocabulario de lugares del UBIGEO (palabras de departamentos, provincias y distritos) y nombres de departamento:
# sirven para limpiar la ubicación de las subprefecturas (corregido el 01/11/2026, control de privacidad antes del push)
_ubigeo_lugares = pd.read_csv(CARPETA_TAREA / "datos" / "crudos" / "ubigeo" / "ubigeo_distrito.csv", dtype=str,
                              usecols=["departamento", "provincia", "distrito"])
VOCABULARIO_LUGARES = {w for col in _ubigeo_lugares.columns for v in _ubigeo_lugares[col].dropna() for w in sin_tildes(v).split()}
VOCABULARIO_LUGARES |= {"PROVINCIAS", "PROV", "CONST", "CONSTITUCIONAL", "CERCADO"}
DEPARTAMENTOS = {tuple(sin_tildes(d).split()) for d in _ubigeo_lugares["departamento"].dropna()} | {("CALLAO",)}


def ubicacion_sin_nombres(texto):
    """Antes: "ANTA ACOBAMBA HUANCAVELIC A <nombre de la persona>" (la tabla de la norma pegó el nombre a la ubicación)
    | Después: "ANTA ACOBAMBA HUANCAVELICA". Paso 1: une palabras partidas por el PDF si juntas forman un lugar del UBIGEO.
    Paso 2: corta todo lo que viene después del último nombre de departamento (más "PROVINCIAS" en "LIMA PROVINCIAS").
    Si no encuentra ningún departamento, deja el texto como está."""
    originales = str(texto).split()
    palabras = []                                   # pares (texto original, texto normalizado)
    i = 0
    while i < len(originales):
        actual, normal = originales[i], sin_tildes(originales[i])
        if i + 1 < len(originales) and normal and normal not in VOCABULARIO_LUGARES:   # un guion suelto no se une
            unida = normal + sin_tildes(originales[i + 1])
            if unida in VOCABULARIO_LUGARES:
                actual, normal, i = originales[i] + originales[i + 1], unida, i + 1
        palabras.append((actual, normal))
        i += 1
    normales = [n for _, n in palabras]
    fin = None
    for inicio in range(len(normales)):
        for depto in DEPARTAMENTOS:
            if tuple(normales[inicio:inicio + len(depto)]) == depto:
                fin = inicio + len(depto)
    if fin is None:
        return " ".join(a for a, _ in palabras)
    if fin < len(normales) and normales[fin] == "PROVINCIAS":
        fin += 1
    return " ".join(a for a, _ in palabras[:fin])


def nombre_puesto(fila):
    """Antes: unidad, entidad, institución y ubicación | Después: "Unidad de Administración — Programa Nacional Cuna Más" """
    if fila["ambito"] == "subprefectos y prefectos":
        return f"Subprefectura — {ubicacion_sin_nombres(fila['ubicacion_tabla']).title()}"
    donde = fila["entidad_del_cargo"] if isinstance(fila["entidad_del_cargo"], str) else \
        MINISTERIOS.get(sin_tildes(fila["institucion_del_cargo"]), str(fila["institucion_del_cargo"]).title())
    return f"{fila['unidad_organica']} — {donde}"


# Nombres de personas confiables (extraídos con un método seguro y sin marca de dudoso): sirven para
# quitar cualquier nombre que se haya colado dentro del nombre de una oficina antes de publicar
todas = pd.read_csv(PROCESADOS / "movimientos_analisis.csv", encoding="utf-8-sig", dtype=str,
                    usecols=["clave_persona", "nombre_dudoso", "metodo_nombre"])
INSTITUCIONAL = r"\b(?:DIRECCION|OFICINA|UNIDAD|GERENCIA|PROGRAMA|MINISTERIO|MUNICIPALIDAD|SERVICIO|NACIONAL|GENERAL|REGIONAL)\b"
PERSONAS_REALES = {c for c in todas.loc[(todas["nombre_dudoso"] != "True") & (todas["metodo_nombre"] != "mayúsculas sin tratamiento"),
                                        "clave_persona"].dropna()
                   if 3 <= len(c.split()) <= 7 and not re.search(INSTITUCIONAL, c)}


def primer_nombre_en(texto):
    """Antes: "Oficina de Planeamiento ... Juan Pérez Soto Director II" | Después: posición (en palabras) donde empieza un
    nombre de persona conocido, o None si el texto no contiene ninguno"""
    palabras = [sin_tildes(p) for p in str(texto).split()]
    for i in range(len(palabras)):
        for n in range(3, 8):
            if " ".join(w for w in palabras[i:i + n] if w) in PERSONAS_REALES:
                return i
    return None


def sin_nombres(texto):
    """Antes: "Dirección X Laura Pérez Soto Directora" | Después: "Dirección X" (se corta donde empieza el nombre).
    También quita números de 8 dígitos (DNI) que algunas tablas dejan pegados al nombre de la unidad (corregido el 01/11/2026)"""
    texto = re.sub(r"\s*\b\d{8}\b", "", str(texto))
    corte = primer_nombre_en(texto)
    return texto if corte is None else " ".join(str(texto).split()[:corte]).rstrip(" ,;-—")


nombres_puesto = periodos.groupby("puesto").apply(lambda g: sin_nombres(nombre_puesto(g.iloc[0])))
claves_puesto = list(nombres_puesto.index)
periodos["p"] = periodos["puesto"].map(claves_puesto.index)
periodos["g"] = periodos["inicio"].map(gobierno_idx)
periodos["m"] = periodos["institucion_del_cargo"].map(ministerio_idx)
periodos["j"] = periodos["jerarquia_puesto"].map(nivel_idx)
periodos["s"] = periodos["sexo_analisis"].map(lambda s: SEXOS.index(s) if s in SEXOS else -1)
lista_periodos = periodos[["m", "g", "j", "s", "dias", "censurado", "p"]].assign(censurado=lambda t: t["censurado"].astype(int)).values.tolist()
print("17.3 Periodos de titulares:", len(lista_periodos), "en", len(claves_puesto), "puestos")


def mediana_km(dias, abierto):
    """Antes: duraciones y si siguen abiertas | Después: día en que la mitad ya dejó el cargo (Kaplan-Meier); None si no llega"""
    tabla = pd.DataFrame({"d": dias, "e": ~abierto}).sort_values("d")
    en_riesgo, sigue = len(tabla), 1.0
    for dia, grupo in tabla.groupby("d"):
        if grupo["e"].sum():
            sigue *= 1 - grupo["e"].sum() / en_riesgo
            if sigue <= 0.5:
                return int(dia)
        en_riesgo -= len(grupo)
    return None


# ============================================================
# PROCESO 17.4: Indicadores (KPI) para cada combinación de filtros
# Insumo:    entradas, periodos y llegadas de ministros
# Resultado: designaciones, personas, % con cargo previo, % de mujeres, ministros y duración mediana
# ============================================================
llegadas = pd.read_csv(INDICADORES / "llegadas_ministros.csv", parse_dates=["fecha_ref", "siguiente_llegada"])
llegadas["g"] = llegadas["fecha_ref"].map(gobierno_idx)
llegadas["m"] = llegadas["institucion_del_cargo"].map(ministerio_idx)
GRUPOS_NIVEL = {"todos": list(range(8)), "alta": [0, 1, 2], "j4": [3], "j5": [4], "j67": [5, 6], "sn": [7]}


def mascara(tabla, g, m):
    """Antes: tabla con columnas g y m | Después: filas del gobierno g y el ministerio m (-1 = todos)"""
    filtro = pd.Series(True, index=tabla.index)
    if g >= 0:
        filtro &= tabla["g"] == g
    if m >= 0:
        filtro &= tabla["m"] == m
    return filtro


kpis = {}
for g in [-1] + list(range(len(gobiernos))):
    for m in [-1] + list(range(len(catalogo_ministerios))):
        for grupo, niveles in GRUPOS_NIVEL.items():
            sub = entradas[mascara(entradas, g, m) & entradas["j"].isin(niveles)]
            # Personas: solo las de nombre confiable (sin "nombre dudoso"), igual que en el resto del análisis (07);
            # las designaciones se cuentan todas (corregido el 01/11/2026 para que cuadre con el titular)
            con_persona = sub[sub["nombre_dudoso"] != "True"].dropna(subset=["clave_persona"])
            ids = con_persona["clave_persona"].unique()
            if not len(ids):
                previo = None
            elif g >= 0:
                previo = (primera_vez.reindex(ids) < pd.Timestamp(catalogo_gobiernos[g]["inicio"])).mean()
            else:
                previo = (gobiernos_por_persona.reindex(ids) >= 2).mean()
            con_sexo = sub[sub["s"] >= 0]
            per = periodos[mascara(periodos, g, m) & periodos["j"].isin(niveles)]
            lleg = llegadas[mascara(llegadas, g, m)]
            kpis[f"{g}|{m}|{grupo}"] = [
                int(len(sub)), int(con_persona["clave_persona"].nunique()),
                None if previo is None or np.isnan(previo) else round(100 * float(previo), 1),
                round(100 * float((con_sexo["s"] == 0).mean()), 1) if len(con_sexo) else None,
                int(len(lleg)), mediana_km(per["dias"], per["censurado"]) if len(per) >= 20 else None]
print("17.4 Combinaciones de filtros con indicadores:", len(kpis))

# ============================================================
# PROCESO 17.5: Armado del equipo, rotación, continuidad, subprefectos y red (sin nombres)
# Insumo:    tablas del script 07
# Resultado: listas compactas para los gráficos
# ============================================================
armado = pd.read_csv(INDICADORES / "armado_equipo_por_llegada.csv", parse_dates=["fecha_llegada"])
familias = [c.replace("dias_", "") for c in armado.columns if c.startswith("dias_") and c != "dias_observados"]
lista_armado = [[ministerio_idx(f["ministerio"]), gobierno_idx(f["fecha_llegada"])] +
                [None if pd.isna(f[f"dias_{x}"]) else int(f[f"dias_{x}"]) for x in familias] for _, f in armado.iterrows()]
lista_llegadas = llegadas[["m", "g", "dias"]].assign(abierto=llegadas["censurado"].astype(int)).values.tolist()

continuidad = pd.read_csv(INDICADORES / "continuidad_gobiernos.csv")
continuidad["g"] = continuidad["inicio"].map(lambda f: gobierno_idx(pd.Timestamp(f)))
lista_continuidad = continuidad[["g", "grupo", "personas_designadas_180_dias", "pct_con_cargo_previo",
                                 "pct_con_cargo_en_gobierno_anterior"]].values.tolist()

sub = pd.read_csv(INDICADORES / "subprefectos_departamento_mes.csv")
sub = sub[sub["tipo_movimiento"].isin(ENTRADA) & (sub["departamento"].fillna("") != "")]
sub["g"] = sub["gobierno"].map(lambda p: int(gobiernos.index[gobiernos["presidente"] == p][0]))
lista_subprefectos = sub.groupby(["departamento", "g"])["movimientos"].sum().reset_index().values.tolist()
serie_subprefectos = sub.groupby("mes")["movimientos"].sum().reindex(meses, fill_value=0).astype(int).tolist()
# Puestos de subprefecto por departamento (para comparar departamentos de distinto tamaño): un puesto por distrito
# (subprefectura distrital o, en el distrito capital de provincia, provincial) más la prefectura regional. Aproximado.
# Fuente: UBIGEO INEI-RENIEC compilado en github.com/jmcastagnetto/ubigeo-peru-aumentado (licencia MIT; actualizado en 2021)
ubigeo = pd.read_csv(CARPETA_TAREA / "datos" / "crudos" / "ubigeo" / "ubigeo_distrito.csv", dtype=str)
ubigeo["dep"] = ubigeo["departamento"].map(sin_tildes)
puestos_sub = ubigeo.groupby("dep").agg(distritos=("inei", "size"), provincias=("provincia", "nunique"))
puestos_sub["puestos"] = puestos_sub["distritos"] + 1
lista_puestos_sub = [[d, int(r.distritos), int(r.provincias), int(r.puestos)] for d, r in puestos_sub.iterrows()]
sin_puestos = sorted(set(sub["departamento"].dropna()) - set(puestos_sub.index) - {""})
print(f"     Subprefecturas (aprox.): {int(puestos_sub['puestos'].sum())} en {len(puestos_sub)} departamentos "
      f"({int(puestos_sub['distritos'].sum())} distritos) | departamentos de la base sin cruce: {sin_puestos}")

# Red: comunidades de 5 o más personas; posiciones calculadas aquí (algoritmo de fuerzas, semilla fija)
perfil = pd.read_csv(INDICADORES / "red_perfil_personas.csv")
id_de = perfil.set_index("clave_persona")["id_persona"]
comunidades = pd.read_csv(INDICADORES / "red_comunidades.csv")
grandes = comunidades[comunidades["personas"] >= 5]
comunidad_de = {}
for _, c in grandes.iterrows():
    for persona in c["miembros"].split(" | "):
        comunidad_de[persona] = int(c["comunidad"])
pares = pd.read_csv(INDICADORES / "red_pares.csv")
pares = pares[pares["persona_a"].isin(comunidad_de) & pares["persona_b"].isin(comunidad_de)]
grafo = nx.Graph()
grafo.add_weighted_edges_from(pares[["persona_a", "persona_b", "traslados_juntos"]].values)
# Cada grupo se dibuja por separado (algoritmo de fuerzas) y los grupos se acomodan en filas, de mayor a menor:
# así se ve la forma de cada grupo y quiénes lo conectan, en vez de manchas superpuestas
ANCHO_LIENZO = 3.2
posicion, x_cursor, y_cursor, alto_fila = {}, 0.0, 0.0, 0.0
for comunidad in sorted(set(comunidad_de.values()), key=lambda c: -sum(1 for v in comunidad_de.values() if v == c)):
    miembros = [p for p, c in comunidad_de.items() if c == comunidad and p in grafo]
    sub_grafo = grafo.subgraph(miembros)
    local = nx.spring_layout(sub_grafo, weight="weight", seed=7, k=1.6 / np.sqrt(len(miembros)), iterations=300)
    radio = 0.045 * np.sqrt(len(miembros))
    if x_cursor + 2 * radio > ANCHO_LIENZO:
        x_cursor, y_cursor, alto_fila = 0.0, y_cursor + alto_fila + 0.04, 0.0
    lx = np.array([v[0] for v in local.values()]); ly = np.array([v[1] for v in local.values()])
    escala = radio / max(1e-9, max(np.abs(lx).max(), np.abs(ly).max()))
    for persona, (px, py) in local.items():
        posicion[persona] = (x_cursor + radio + px * escala, y_cursor + radio + py * escala)
    x_cursor += 2 * radio + 0.04
    alto_fila = max(alto_fila, 2 * radio)
xs, ys = np.array([p[0] for p in posicion.values()]), np.array([p[1] for p in posicion.values()])
aspecto = float((ys.max() - ys.min()) / (xs.max() - xs.min()))
ministerios_de = mov.dropna(subset=["clave_persona"]).groupby("clave_persona")["m"].agg(lambda s: sorted(set(int(v) for v in s)))
perfil = perfil.set_index("clave_persona")
rango = perfil["intermediacion"].rank(pct=True)
nodos = []
for persona, (x, y) in posicion.items():
    p = perfil.loc[persona]
    # x en [0, 1]; y en [0, aspecto]: la misma escala en los dos ejes (no deforma los grupos)
    nodos.append([str(p["id_persona"]), round(float((x - xs.min()) / (xs.max() - xs.min())), 4),
                  round(float((y - ys.min()) / (xs.max() - xs.min())), 4), comunidad_de[persona], int(p["equipos"]),
                  int(p["entidades"]), int(p["gobiernos"]), str(p["tipo"]), round(100 * float(rango[persona]), 1),
                  ministerios_de.get(persona, [])])
aristas = [[str(id_de[a]), str(id_de[b]), int(w)] for a, b, w in pares[["persona_a", "persona_b", "traslados_juntos"]].values]
resumen_red = pd.read_csv(INDICADORES / "red_resumen.csv").iloc[0].to_dict()
print("17.5 Red de co-traslado (ya no se dibuja; quedan sus cifras):", len(nodos), "personas,", len(aristas), "conexiones")

# Red de seguimiento (proceso 16.10, gráfico principal del hallazgo 3): flecha jefe -> persona que llegó detrás de él en
# 2 o más instituciones. Grupos = comunidades (Louvain) de esa red; cada grupo se dibuja por separado y se acomoda en filas
MIN_GRUPO = 4   # grupos de 4 o más personas (los de 3 alargan el dibujo sin agregar formas nuevas)
seguimiento = pd.read_csv(INDICADORES / "seguimiento_parejas.csv")
dirigido = nx.DiGraph()
for f in seguimiento.itertuples(index=False):
    dirigido.add_edge(f.jefe, f.acompanante, instituciones=int(f.instituciones), firmo=bool(f.firmo), entidades=f.entidades)
codigo_de = dict(zip(seguimiento["jefe"], seguimiento["id_jefe"])) | dict(zip(seguimiento["acompanante"], seguimiento["id_acompanante"]))
grupos_seg = [g for g in nx.community.louvain_communities(dirigido.to_undirected(), seed=1) if len(g) >= MIN_GRUPO]
grupos_seg = sorted(grupos_seg, key=lambda g: (-len(g), sorted(g)[0]))
grupo_de = {p: n for n, g in enumerate(grupos_seg, start=1) for p in g}
posicion, x_cursor, y_cursor, alto_fila = {}, 0.0, 0.0, 0.0
for g in grupos_seg:
    # Grafo del grupo con sus personas en orden alfabético: así el dibujo sale igual en cada corrida (corregido el
    # 01/11/2026). Antes: el orden venía de un conjunto (set), que Python baraja en cada corrida, y la semilla no bastaba
    sub_grafo = nx.Graph()
    sub_grafo.add_nodes_from(sorted(g))
    sub_grafo.add_edges_from((a, b) for a, b in dirigido.edges() if a in g and b in g)
    local = nx.spring_layout(sub_grafo, seed=7, k=1.8 / np.sqrt(len(g)), iterations=300)
    radio = 0.05 * np.sqrt(len(g))
    if x_cursor + 2 * radio > ANCHO_LIENZO:
        x_cursor, y_cursor, alto_fila = 0.0, y_cursor + alto_fila + 0.05, 0.0
    lx = np.array([v[0] for v in local.values()]); ly = np.array([v[1] for v in local.values()])
    escala = radio / max(1e-9, max(np.abs(lx).max(), np.abs(ly).max()))
    for persona, (px, py) in local.items():
        posicion[persona] = (x_cursor + radio + px * escala, y_cursor + radio + py * escala)
    x_cursor += 2 * radio + 0.05
    alto_fila = max(alto_fila, 2 * radio)
xs, ys = np.array([p[0] for p in posicion.values()]), np.array([p[1] for p in posicion.values()])
aspecto = float((ys.max() - ys.min()) / (xs.max() - xs.min()))
# Nombre corto de cada institución para el dashboard (siglas conocidas; si no, el nombre con mayúsculas iniciales)
SIGLAS_RED = {
    "PRESIDENCIA DEL CONSEJO DE MINISTROS": "PCM", "DESARROLLO E INCLUSION SOCIAL": "MIDIS", "DESARROLLO AGRARIO Y RIEGO": "MIDAGRI",
    "TRABAJO Y PROMOCION DEL EMPLEO": "MTPE", "TRANSPORTES Y COMUNICACIONES": "MTC", "MUJER Y POBLACIONES VULNERABLES": "MIMP",
    "ECONOMIA Y FINANZAS": "MEF", "ENERGIA Y MINAS": "MINEM", "JUSTICIA Y DERECHOS HUMANOS": "MINJUSDH", "RELACIONES EXTERIORES": "RREE",
    "COMERCIO EXTERIOR Y TURISMO": "MINCETUR", "VIVIENDA CONSTRUCCION Y SANEAMIENTO": "Vivienda", "INTERIOR": "Interior",
    "EDUCACION": "MINEDU", "SALUD": "MINSA", "DEFENSA": "Defensa", "AMBIENTE": "MINAM", "CULTURA": "Cultura", "PRODUCE": "PRODUCE",
    "SEGURO INTEGRAL DE SALUD": "SIS", "INSTITUTO NACIONAL DE SALUD": "INS", "SUPERINTENDENCIA NACIONAL DE SALUD": "SUSALUD",
    "DESPACHO PRESIDENCIAL": "Despacho Presidencial", "AUTORIDAD DE TRANSPORTE URBANO PARA LIMA Y CALLAO": "ATU",
    "ORGANISMO DE FORMALIZACION DE LA PROPIEDAD INFORMAL": "COFOPRI", "INSTITUTO PERUANO DEL DEPORTE": "IPD",
    "BIBLIOTECA NACIONAL DEL PERU": "Biblioteca Nacional", "ARCHIVO GENERAL DE LA NACION": "Archivo General de la Nación",
    "CENTRAL DE COMPRAS PUBLICAS": "Perú Compras", "PROCURADURIA GENERAL DEL ESTADO": "Procuraduría General",
    "SUPERINTENDENCIA NACIONAL DE MIGRACIONES": "Migraciones", "SUPERINTENDENCIA NACIONAL DE FISCALIZACION LABORAL": "SUNAFIL",
    "INSTITUTO NACIONAL DE DEFENSA CIVIL": "INDECI", "AUTORIDAD NACIONAL DEL AGUA": "ANA", "SUPERINTENDENCIA NACIONAL DE LOS REGISTROS PUBLICOS": "SUNARP",
    "SERVICIO NACIONAL FORESTAL Y DE FAUNA SILVESTRE": "SERFOR", "INSTITUTO NACIONAL DE RADIO Y TELEVISION DEL PERU": "IRTP",
    "COMISION DE PROMOCION DEL PERU PARA LA EXPORTACION Y EL TURISMO": "PROMPERÚ", "AGENCIA DE PROMOCION DE LA INVERSION PRIVADA": "PROINVERSIÓN",
    "INSTITUTO TECNOLOGICO DE LA PRODUCCION": "ITP", "SERVICIO NACIONAL DE AREAS NATURALES PROTEGIDAS POR EL ESTADO": "SERNANP",
    "ORGANISMO DE EVALUACION Y FISCALIZACION AMBIENTAL": "OEFA", "CENTRO NACIONAL DE PLANEAMIENTO ESTRATEGICO": "CEPLAN",
    "ORGANISMO TECNICO DE LA ADMINISTRACION DE LOS SERVICIOS DE SANEAMIENTO": "OTASS",
    "ORGANISMO SUPERVISOR DE LAS CONTRATACIONES DEL ESTADO": "OSCE", "INSTITUTO NACIONAL DE ESTADISTICA E INFORMATICA": "INEI",
}
PROGRAMAS_RED = [(r"PROMPERU|PROMOCION DEL PERU", "PROMPERÚ"), (r"COMPRAS A MYPERU", "Compras a MYPerú"), (r"BIENES INCAUTADOS", "PRONABI"),
                 (r"BIENESTAR FAMILIAR|INABIF", "INABIF"), (r"ENTREGA DE LA PENSION NO CONTRIBUTIVA", "Programa CONTIGO"), (r"ASISTENCIA SOLIDARIA", "Pensión 65"),
                 (r"APOYO DIRECTO A LOS MAS POBRES", "JUNTOS"), (r"CUNA MAS", "Cuna Más"), (r"ALIMENTACION ESCOLAR", "Alimentación Escolar"),
                 (r"COOPERACION PARA EL DESARROLLO SOCIAL|\bFONCODES\b", "FONCODES"), (r"\bPAIS\b", "Programa PAIS")]
MINUSCULAS = {"DE", "DEL", "LA", "LAS", "LOS", "Y", "E", "PARA", "EN", "EL", "A", "AL", "CON", "POR"}


def nombre_corto(entidad):
    """Antes: "DESARROLLO E INCLUSION SOCIAL | PROGRAMA NACIONAL DE ..." | Después: "Pensión 65" (o el nombre abreviado)"""
    k = entidad.split(" | ")[-1]
    if k in SIGLAS_RED:
        return SIGLAS_RED[k]
    for patron, nombre in PROGRAMAS_RED:
        if re.search(patron, k):
            return nombre
    texto = " ".join(w.lower() if (i and w in MINUSCULAS) else w.capitalize() for i, w in enumerate(k.split()))
    return texto if len(texto) <= 45 else texto[:44].rstrip() + "…"


# Instituciones de cada persona en esta red: donde siguió a un jefe o donde la siguieron
instituciones_de = {}
for a, b, d in dirigido.edges(data=True):
    for e in d["entidades"].split(" ; "):
        for persona in (a, b):
            instituciones_de.setdefault(persona, Counter())[nombre_corto(e)] += 1
catalogo_instituciones = sorted({i for c in instituciones_de.values() for i in c})
indice_institucion = {n: i for i, n in enumerate(catalogo_instituciones)}


def es_puente(persona):
    """Puente (corregido el 31/10/2026): siguió a dos jefes que NO están unidos entre sí (ninguno siguió al otro).
    Si siguió al ministro y a su secretaria general, que llegan juntos, es parte del mismo equipo, no un puente"""
    jefes = list(dirigido.predecessors(persona))
    return any(not (dirigido.has_edge(a, b) or dirigido.has_edge(b, a)) for a, b in combinations(jefes, 2))


nodos = []
for persona, (x, y) in posicion.items():
    lleva, sigue = dirigido.out_degree(persona), dirigido.in_degree(persona)
    rol = "jefe" if lleva > 0 else ("puente" if es_puente(persona) else "acompañante")
    nodos.append([str(codigo_de[persona]), round(float((x - xs.min()) / (xs.max() - xs.min())), 4),
                  round(float((y - ys.min()) / (xs.max() - xs.min())), 4), grupo_de[persona], rol, int(lleva), int(sigue),
                  ministerios_de.get(persona, []),
                  [indice_institucion[n] for n, _ in sorted(instituciones_de[persona].items(), key=lambda t: (-t[1], t[0]))[:6]]])
# Instituciones principales de cada grupo (por número de flechas dentro del grupo)
instituciones_grupo = []
for n, g in enumerate(grupos_seg, start=1):
    cuenta = Counter(nombre_corto(e) for a, b, d in dirigido.subgraph(g).edges(data=True) for e in d["entidades"].split(" ; "))
    # Orden: más flechas primero; los empates, en orden alfabético (así el resultado no cambia entre corridas)
    instituciones_grupo.append([n, [indice_institucion[i] for i, _ in sorted(cuenta.items(), key=lambda t: (-t[1], t[0]))[:4]]])
print(f"     Roles: {Counter(n[4] for n in nodos)} | instituciones en el catálogo: {len(catalogo_instituciones)}")
aristas = [[str(codigo_de[a]), str(codigo_de[b]), d["instituciones"], int(d["firmo"])]
           for a, b, d in dirigido.edges(data=True) if a in grupo_de and b in grupo_de]
resumen_seg = pd.read_csv(INDICADORES / "seguimiento_resumen.csv").iloc[0].to_dict()
print(f"     Red de seguimiento para el dashboard: {len(nodos)} personas, {len(aristas)} flechas, {len(grupos_seg)} grupos "
      f"de {MIN_GRUPO}+ personas (tamaños: {[len(g) for g in grupos_seg[:8]]}...)")

# ============================================================
# PROCESO 17.7: Rankings de rotación y permanencia (script 07c), sin nombres: los 20 primeros, en total y por ministerio
# Insumo:    trayectorias.csv, ranking_rotacion.csv y ranking_permanencia.csv
# Resultado: por cada filtro de ministerio, 20 filas con código anónimo, cifras y cargos (institución, nivel, inicio, días)
# ============================================================
INICIO_BASE = pd.Timestamp("2022-11-01")
tray = pd.read_csv(INDICADORES / "trayectorias.csv", encoding="utf-8-sig", parse_dates=["inicio", "fin"])
rot = pd.read_csv(INDICADORES / "ranking_rotacion.csv", encoding="utf-8-sig")
perm = pd.read_csv(INDICADORES / "ranking_permanencia.csv", encoding="utf-8-sig", parse_dates=["inicio", "fin"])
instituciones_rank = []


def idx_institucion(institucion):
    """Antes: "DESARROLLO E INCLUSIÓN SOCIAL" | Después: índice de "MIDIS" en el catálogo de instituciones de los rankings"""
    nombre = nombre_corto(sin_tildes(institucion))
    if nombre not in instituciones_rank:
        instituciones_rank.append(nombre)
    return instituciones_rank.index(nombre)


tray["m"] = tray["institucion_del_cargo"].map(ministerio_idx)
cargos_de = {p: g.sort_values("inicio") for p, g in tray.groupby("clave_persona")}


def referencia_pdf(enlace):
    """Antes: "https://epdoc2.elperuano.pe/EpPo/DescargaIN.asp?Referencias=MjEz..." | Después: "MjEz..." (la página arma el enlace)"""
    return str(enlace).split("Referencias=")[-1] if isinstance(enlace, str) and "Referencias=" in enlace else ""


def fila_rotacion(r):
    """Antes: una persona del ranking | Después: [código, cargos en 12 meses, cargos, instituciones, mediana de días,
    [[institución, nivel, día de inicio desde nov-2022, días, sigue], ...]]"""
    return [str(r.id_persona), int(r.cargos_en_12_meses), int(r.cargos), int(r.instituciones), int(round(r.mediana_dias)),
            [[idx_institucion(x.institucion_del_cargo), nivel_idx(x.jerarquia_puesto), int((x.inicio - INICIO_BASE).days),
              int(x.dias), int(bool(x.abierto)), str(x.codigo_norma), referencia_pdf(x.enlace_pdf)]
             for x in cargos_de[r.clave_persona].itertuples()]]


perm["m"] = perm["institucion_del_cargo"].map(ministerio_idx)
rankings_rotacion, rankings_permanencia = {}, {}
for m in [-1] + list(range(len(catalogo_ministerios))):
    candidatos = rot if m == -1 else rot[rot["clave_persona"].isin(set(tray.loc[tray["m"] == m, "clave_persona"]))]
    rankings_rotacion[str(m)] = [fila_rotacion(r) for r in candidatos.head(20).itertuples()]
    candidatos = perm if m == -1 else perm[perm["m"] == m]
    rankings_permanencia[str(m)] = [[str(r.id_persona), idx_institucion(r.institucion_del_cargo), nivel_idx(r.jerarquia_puesto),
                                     int((r.inicio - INICIO_BASE).days), int(r.dias), int(bool(r.sigue)), int(r.jefes_que_llegaron),
                                     "m" if r.tipo_de_jefe == "ministros" else "t", str(r.codigo_norma), referencia_pdf(r.enlace_pdf)]
                                    for r in candidatos.head(20).itertuples()]
print(f"17.7 Rankings: rotación {len(rankings_rotacion['-1'])} y permanencia {len(rankings_permanencia['-1'])} personas "
      f"(más 20 por ministerio) | instituciones en el catálogo: {len(instituciones_rank)}")

# ============================================================
# PROCESO 17.6: Escribir el archivo para la página (y verificar que no salga ningún nombre)
# Insumo:    todo lo anterior
# Resultado: web/data/dashboard.json
# ============================================================
normas = pd.read_csv(PROCESADOS / "normas.csv", encoding="utf-8-sig", usecols=["codigo_norma"])
todos = pd.read_csv(PROCESADOS / "movimientos_analisis.csv", encoding="utf-8-sig", usecols=["id_movimiento"])
datos = {
    "meta": {"normas": len(normas), "movimientos": len(todos), "principal": int(TOTAL_PRINCIPAL),
             "personas_principal": int(PERSONAS_PRINCIPAL), "desde": "2022-11-01", "hasta": FIN_VENTANA.date().isoformat(),
             "generado": pd.Timestamp.now().strftime("%Y-%m-%d")},
    "gobiernos": catalogo_gobiernos, "ministerios": catalogo_ministerios, "niveles": NIVELES, "meses": meses,
    "familias": familias, "cubo": cubo, "kpis": kpis, "periodos": lista_periodos, "puestos": list(nombres_puesto.values),
    "armado": lista_armado, "llegadas": lista_llegadas, "continuidad": lista_continuidad,
    "subprefectos": lista_subprefectos, "serie_subprefectos": serie_subprefectos, "puestos_subprefecto": lista_puestos_sub,
    "rankings": {"inicio": INICIO_BASE.date().isoformat(), "fin": FIN_VENTANA.date().isoformat(),
                 "instituciones": instituciones_rank, "rotacion": rankings_rotacion, "permanencia": rankings_permanencia},
    "red": {"nodos": nodos, "aristas": aristas, "aspecto": round(aspecto, 4),
            "resumen": {k: (v.item() if hasattr(v, "item") else v) for k, v in resumen_red.items()},
            "seg": {k: (v.item() if hasattr(v, "item") else v) for k, v in resumen_seg.items()},
            "instituciones": catalogo_instituciones, "grupos": instituciones_grupo},
}
texto = json.dumps(datos, ensure_ascii=False, separators=(",", ":"))
# Verificación de privacidad: ningún nombre de persona de la base puede aparecer en el archivo público
# (se revisan todas las secuencias de 3 a 7 palabras del archivo contra los nombres de personas)
palabras = sin_tildes(texto).split()
secuencias = {" ".join(palabras[i:i + n]) for n in range(3, 8) for i in range(len(palabras) - n + 1)}
filtrados = sorted(secuencias & PERSONAS_REALES)
assert not filtrados, f"El archivo público contiene nombres: {filtrados[:3]}"
# ...ni números con forma de DNI (8 dígitos)
dni = re.findall(r"\b\d{8}\b", texto)
assert not dni, f"El archivo público contiene números con forma de DNI: {dni[:3]}"
SALIDA.write_text(texto, encoding="utf-8")
print(f"17.6 Escrito {SALIDA} ({len(texto) / 1e6:.2f} MB) | nombres de personas en el archivo: 0 | números con forma de DNI: 0")
