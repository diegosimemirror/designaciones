# ============================================================
# Designaciones de El Peruano — Script 07: indicadores (proceso 16 del mapa)
# ------------------------------------------------------------
# Calcula los indicadores de las preguntas acordadas (docs/preguntas_y_metodologia.md) con las reglas de
# docs/metodologia_indicadores.md. No modifica la base: escribe tablas nuevas en datos/procesados/indicadores/.
#   16.1 Gobiernos y llegadas de ministros (fechas cero)
#   16.2 Rotación ministerial
#   16.3 Continuidad del elenco entre gobiernos            (hallazgo 1)
#   16.4 Armado del equipo tras la llegada de un ministro   (hallazgo 2)
#   16.5 Puestos, titulares y duración (regla de sucesión) y supervivencia
#   16.6 Género por jerarquía y duración
#   16.7 Olas de designaciones
#   16.8 Subprefectos por departamento (mapa)
#   16.9 Red: equipos, co-movimiento, comunidades, puentes y arrastre   (hallazgo 3)
#
# Insumos:   datos/procesados/movimientos_analisis.csv (script 06) y normas.csv (script 03)
# Resultado: datos/procesados/indicadores/*.csv (con nombres; NO se suben al repositorio)
#
# Uso (desde la carpeta tarea_3):
#   python scripts/07_indicadores.py
# ============================================================

# --- Paquetes ---
# re y unicodedata: normalizar textos (nombres de instituciones y unidades) para comparar
import re
import unicodedata
# pathlib: rutas de archivos
from pathlib import Path
# numpy: cálculos numéricos (percentiles, sorteos al azar para la comparación de la red)
import numpy as np
# pandas: tablas
import pandas as pd
# networkx: redes (grafos): comunidades, modularidad e intermediación. Viene con Anaconda (versión 3.6)
import networkx as nx

CARPETA_TAREA = Path(__file__).resolve().parent.parent
CARPETA_PROCESADOS = CARPETA_TAREA / "datos" / "procesados"
CARPETA_SALIDA = CARPETA_PROCESADOS / "indicadores"
CARPETA_SALIDA.mkdir(exist_ok=True)
FIN_VENTANA = pd.Timestamp("2026-10-29")       # última fecha de publicación de la base
ENTRADA = {"designación", "nombramiento", "encargatura"}
SALIDA = {"conclusión", "renuncia", "dejar sin efecto"}
# Cargos de apoyo: varios ocupantes a la vez, no "titulares" (excepción 2 de la regla de sucesión)
APOYO = r"Asesor|Adjunt|Asistent|Especialista|Analista|Profesional|T[ée]cnico|Auxiliar|Consejer|Miembro|Representante|Vocal"
# Unidades con nombre genérico: no identifican un puesto único ("Jefe de Equipo II" hay muchos)
UNIDAD_GENERICA = (r"^(?:Equipo(?:\s+[IVX]+)?|(?:Unidad|Oficina)(?:\s+[IVX]+)?|Direcci[óo]n|[ÁA]rea|Coordinaci[óo]n|"
                   r"Procuradur[íi]a P[úu]blica|(?:Oficina|Direcci[óo]n|[ÓO]rgano)\s+Desconcentrad[ao]|Alta Direcci[óo]n)$")


def sin_tildes(texto):
    """Antes: "Programa de Desarrollo Productivo Agrario Rural – AGRO RURAL" | Después: "PROGRAMA DE DESARROLLO ... AGRO RURAL" """
    texto = "".join(c for c in unicodedata.normalize("NFD", str(texto)) if unicodedata.category(c) != "Mn").upper()
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]", " ", texto)).strip()


def guardar(tabla, nombre):
    """Antes: tabla en memoria | Después: archivo datos/procesados/indicadores/<nombre>.csv"""
    tabla.to_csv(CARPETA_SALIDA / f"{nombre}.csv", index=False, encoding="utf-8-sig")
    print(f"     -> {nombre}.csv ({len(tabla)} filas)")


# ============================================================
# PROCESO 16.1: Gobiernos y llegadas de ministros
# Insumo:    normas.csv (firmante de las resoluciones supremas) y movimientos_analisis.csv
# Resultado: gobiernos (presidente e inicio) y llegadas de ministros por cartera
# ============================================================
movimientos = pd.read_csv(CARPETA_PROCESADOS / "movimientos_analisis.csv", encoding="utf-8-sig", dtype=str)
# Fecha de referencia (regla R4): efectividad si la norma la dice (y es razonable), si no la firma, si no la publicación
firma = pd.to_datetime(movimientos["fecha_emision_corregida"], errors="coerce")
publicacion = pd.to_datetime(movimientos["fecha_publicacion"], dayfirst=True)
efectividad = pd.to_datetime(movimientos["fecha_efectividad"], errors="coerce")
efectividad = efectividad.where((efectividad - firma.fillna(publicacion)).abs() <= pd.Timedelta(days=365))
movimientos["fecha_ref"] = efectividad.fillna(firma).fillna(publicacion)
movimientos["temporal"] = movimientos["temporal"] == "True"
principal = movimientos[movimientos["en_analisis_principal"] == "True"].copy()
# Personas confiables: con nombre y sin nombre dudoso
personas = principal[principal["clave_persona"].notna() & (principal["nombre_dudoso"] != "True")].copy()
print("16.1 Movimientos del análisis principal:", len(principal), "| con persona confiable:", len(personas))

# El Presidente firma las resoluciones supremas: el cambio de firmante marca el cambio de gobierno
normas = pd.read_csv(CARPETA_PROCESADOS / "normas.csv", encoding="utf-8-sig", dtype=str,
                     usecols=["dispositivo", "fecha_emision", "fecha_publicacion", "firmante1_nombre", "firmante1_cargo"])
normas["fecha"] = pd.to_datetime(normas["fecha_emision"], errors="coerce").fillna(
    pd.to_datetime(normas["fecha_publicacion"], dayfirst=True))
supremas = normas[normas["dispositivo"].fillna("").str.contains(r"RESOLUCI[OÓ]N SUPREMA", case=False)
                  & normas["firmante1_cargo"].fillna("").str.contains("President", case=False)]
supremas = supremas.assign(presidente=supremas["firmante1_nombre"].map(sin_tildes))
por_presidente = supremas.groupby("presidente")["fecha"].agg(["min", "max", "count"])
# Solo quienes firman 50 o más (descarta encargos breves del despacho presidencial)
gobiernos = por_presidente[por_presidente["count"] >= 50].sort_values("min").reset_index()
gobiernos.columns = ["presidente", "inicio", "ultima_firma", "resoluciones_supremas"]
print(gobiernos.to_string(index=False))
guardar(gobiernos, "gobiernos")
INICIOS = list(gobiernos["inicio"])


def gobierno_de(fecha):
    """Antes: una fecha | Después: el presidente que gobernaba ese día (según la primera firma de cada uno)"""
    anteriores = gobiernos[gobiernos["inicio"] <= fecha]
    return anteriores["presidente"].iloc[-1] if len(anteriores) else gobiernos["presidente"].iloc[0]


# Llegadas de ministros: designaciones de ministros (y del Presidente del Consejo de Ministros)
es_ministro = (principal["nivel_cargo"] == "MIN") | principal["cargo"].fillna("").str.contains(
    r"President[ea] del Consejo de Ministros", case=False)
ministros = principal[es_ministro & principal["tipo_movimiento"].isin(ENTRADA) & principal["clave_persona"].notna()]
ministros = (ministros.sort_values("fecha_ref")
             .drop_duplicates(["institucion_del_cargo", "clave_persona", "fecha_ref"])[
                 ["institucion_del_cargo", "clave_persona", "id_persona", "fecha_ref"]])
# Si la misma persona aparece dos veces seguidas en la misma cartera (dos normas), cuenta una sola llegada
ministros = ministros[ministros["clave_persona"] != ministros.groupby("institucion_del_cargo")["clave_persona"].shift()]
ministros["siguiente_llegada"] = ministros.groupby("institucion_del_cargo")["fecha_ref"].shift(-1)
print(f"     Llegadas de ministros: {len(ministros)} en {ministros['institucion_del_cargo'].nunique()} carteras")


# ============================================================
# PROCESO 16.2: Rotación ministerial
# Insumo:    llegadas de ministros
# Resultado: ministros distintos y duración mediana por cartera
# ============================================================
ministros["dias"] = (ministros["siguiente_llegada"].fillna(FIN_VENTANA) - ministros["fecha_ref"]).dt.days
ministros["censurado"] = ministros["siguiente_llegada"].isna()   # el último ministro sigue al cierre de la base
rotacion = ministros.groupby("institucion_del_cargo").agg(
    ministros_distintos=("clave_persona", "nunique"), llegadas=("clave_persona", "size"),
    dias_mediana=("dias", lambda d: d[~ministros.loc[d.index, "censurado"]].median()))
rotacion = rotacion.sort_values("ministros_distintos", ascending=False).reset_index()
print("\n16.2 Rotación ministerial (4 años):")
print(rotacion.to_string(index=False))
guardar(rotacion, "rotacion_ministerial")
guardar(ministros, "llegadas_ministros")


# ============================================================
# PROCESO 16.3: Continuidad del elenco entre gobiernos (hallazgo 1)
# Insumo:    movimientos de personas confiables y fechas de inicio de cada gobierno
# Resultado: % de designados por cada gobierno nuevo que ya tenían cargos antes
# ============================================================
filas = []
for k in range(1, len(gobiernos)):
    inicio = gobiernos["inicio"].iloc[k]
    inicio_anterior = gobiernos["inicio"].iloc[k - 1]
    # Hasta 180 días o hasta que empieza el gobierno siguiente; el último gobierno incluye el último día de la base
    # (corregido el 01/11/2026: antes el 29/10/2026 quedaba fuera y no cuadraba con el indicador del dashboard)
    fin = min(inicio + pd.Timedelta(days=180),
              gobiernos["inicio"].iloc[k + 1] if k + 1 < len(gobiernos) else FIN_VENTANA + pd.Timedelta(days=1))
    nuevos = personas[(personas["fecha_ref"] >= inicio) & (personas["fecha_ref"] < fin)
                      & personas["tipo_movimiento"].isin(ENTRADA)]
    for grupo, filtro in [("todos", nuevos.index), ("J1-J4 (alta dirección y jefes de órgano)",
                                                    nuevos[nuevos["jerarquia_puesto"].fillna("").str.match("J[1-4]")].index)]:
        designados = set(nuevos.loc[filtro, "clave_persona"])
        antes = personas[personas["fecha_ref"] < inicio]
        con_cargo_previo = designados & set(antes["clave_persona"])
        con_cargo_gobierno_anterior = designados & set(antes[antes["fecha_ref"] >= inicio_anterior]["clave_persona"])
        filas.append({"gobierno_que_entra": gobiernos["presidente"].iloc[k], "inicio": inicio.date(),
                      "ventana_hacia_atras_dias": (inicio - personas["fecha_ref"].min()).days, "grupo": grupo,
                      "personas_designadas_180_dias": len(designados),
                      "con_cargo_previo_en_la_base": len(con_cargo_previo),
                      "pct_con_cargo_previo": round(100 * len(con_cargo_previo) / max(len(designados), 1), 1),
                      "con_cargo_en_gobierno_anterior": len(con_cargo_gobierno_anterior),
                      "pct_con_cargo_en_gobierno_anterior": round(100 * len(con_cargo_gobierno_anterior) / max(len(designados), 1), 1)})
continuidad = pd.DataFrame(filas)
print("\n16.3 Continuidad del elenco entre gobiernos:")
print(continuidad.to_string(index=False))
guardar(continuidad, "continuidad_gobiernos")


# ============================================================
# PROCESO 16.4: Armado del equipo tras la llegada de un ministro (hallazgo 2)
# Insumo:    llegadas de ministros + designaciones del núcleo directivo en la sede central de su ministerio
# Resultado: días hasta la primera designación de cada familia de cargos, por llegada de ministro
# ============================================================
FAMILIAS = [("Secretaría General", r"Secretar[íi]a General"), ("Gabinete de asesores", r"Gabinete"),
            ("Viceministerio", r"Viceminister|Despacho Viceministerial"),
            ("Administración", r"Administraci|Abastecimiento|Log[íi]stica|Contabilidad|Tesorer|Finanzas|Patrimonio"),
            ("Asesoría jurídica", r"Jur[íi]dic|Legal"),
            ("Planeamiento y presupuesto", r"Planeamiento|Presupuesto|Modernizaci|Inversiones|Cooperaci"),
            ("Recursos humanos", r"Recursos Humanos|Talento|Personal"),
            ("Tecnologías de la información", r"Tecnolog|Inform[áa]tica|Gobierno Digital"),
            ("Comunicaciones", r"Comunicaci|Imagen|Prensa"),
            ("Órganos de línea", r"Direcci[óo]n General|Direcci[óo]n de|Oficina General")]


def familia_de(fila):
    """Antes: unidad_organica y nivel_cargo | Después: familia funcional ("Recursos humanos", "Órganos de línea"...)"""
    if fila["nivel_cargo"] == "VMIN":
        return "Viceministerio"
    unidad = str(fila["unidad_organica"])
    return next((nombre for nombre, patron in FAMILIAS if re.search(patron, unidad, re.I)), "Otros")


nucleo = principal[(principal["ubicacion"] == "sede central del ministerio") & principal["tipo_movimiento"].isin(ENTRADA)
                   & ~principal["temporal"] & principal["jerarquia_puesto"].fillna("").str.match("J[2-4]")].copy()
nucleo["familia"] = nucleo.apply(familia_de, axis=1)
filas = []
for _, llegada in ministros.iterrows():
    t0 = llegada["fecha_ref"]
    fin = min(t0 + pd.Timedelta(days=180), llegada["siguiente_llegada"] if pd.notna(llegada["siguiente_llegada"]) else FIN_VENTANA)
    equipo = nucleo[(nucleo["institucion_del_cargo"] == llegada["institucion_del_cargo"])
                    & (nucleo["fecha_ref"] >= t0) & (nucleo["fecha_ref"] < fin)]
    fila = {"ministerio": llegada["institucion_del_cargo"], "fecha_llegada": t0.date(), "dias_observados": (fin - t0).days,
            "gobierno": gobierno_de(t0), "designaciones_nucleo_30_dias": int((equipo["fecha_ref"] < t0 + pd.Timedelta(days=30)).sum()),
            "designaciones_nucleo_90_dias": int((equipo["fecha_ref"] < t0 + pd.Timedelta(days=90)).sum())}
    for nombre, _ in FAMILIAS:
        primera = equipo.loc[equipo["familia"] == nombre, "fecha_ref"].min()
        fila[f"dias_{nombre}"] = (primera - t0).days if pd.notna(primera) else np.nan
    filas.append(fila)
armado = pd.DataFrame(filas)
# Resumen: en cuántas llegadas se renovó cada familia y en cuántos días (mediana)
resumen_armado = pd.DataFrame([{"familia": nombre, "llegadas_con_renovacion": armado[f"dias_{nombre}"].notna().sum(),
                                "pct_llegadas": round(100 * armado[f"dias_{nombre}"].notna().mean(), 1),
                                "dias_mediana": armado[f"dias_{nombre}"].median()} for nombre, _ in FAMILIAS])
print("\n16.4 Armado del equipo: en cuántas de las", len(armado), "llegadas de ministros se renovó cada familia y en cuántos días")
print(resumen_armado.sort_values("dias_mediana").to_string(index=False))
guardar(armado, "armado_equipo_por_llegada")
guardar(resumen_armado, "armado_equipo_resumen")
# Caso vitrina: llegada del nuevo gobierno (todas las carteras a la vez)
ultimo_inicio = gobiernos["inicio"].iloc[-1]
vitrina = armado[pd.to_datetime(armado["fecha_llegada"]).between(ultimo_inicio - pd.Timedelta(days=3), ultimo_inicio + pd.Timedelta(days=3))]
print(f"     Vitrina ({ultimo_inicio.date()}): mediana de días a Secretaría General",
      vitrina["dias_Secretaría General"].median(), "| a viceministerios", vitrina["dias_Viceministerio"].median())
guardar(vitrina, "armado_equipo_vitrina")
secuencia = nucleo[(nucleo["fecha_ref"] >= ultimo_inicio) & (nucleo["fecha_ref"] < ultimo_inicio + pd.Timedelta(days=60))].copy()
secuencia["dia"] = (secuencia["fecha_ref"] - ultimo_inicio).dt.days
guardar(secuencia[["institucion_del_cargo", "dia", "familia", "jerarquia_puesto", "unidad_organica", "id_persona",
                   "clave_persona", "cargo"]].sort_values(["institucion_del_cargo", "dia"]), "secuencia_vitrina")


# ============================================================
# PROCESO 16.5: Puestos, titulares y duración (regla de sucesión R1) y supervivencia
# Insumo:    entradas y salidas de puestos de titular
# Resultado: periodos (inicio, fin, duración) por titular; titulares por puesto; curvas de supervivencia
# ============================================================
def clave_puesto(fila):
    """Antes: institución, programa u organismo, unidad (o ubicación del subprefecto)
    | Después: "DESARROLLO E INCLUSION SOCIAL | PROGRAMA NACIONAL CUNA MAS | UNIDAD DE ADMINISTRACION" ("" si no es puesto único)"""
    if fila["ambito"] == "subprefectos y prefectos":
        lugar = sin_tildes(fila["ubicacion_tabla"]) if isinstance(fila["ubicacion_tabla"], str) else ""
        tipo = re.search(r"Distrital|Provincial|Regional", str(fila["cargo"]), re.I)
        return f"SUBPREFECTURA {tipo.group(0).upper() if tipo else ''} | {lugar}" if lugar else ""
    unidad = str(fila["unidad_organica"]) if isinstance(fila["unidad_organica"], str) else ""
    entidad = sin_tildes(fila["entidad_del_cargo"]) if isinstance(fila["entidad_del_cargo"], str) else ""
    # "Alta Dirección" sí identifica el puesto cuando se sabe de qué programa u organismo es (su titular)
    generica = re.match(UNIDAD_GENERICA, unidad, re.I) and not (re.match(r"Alta Direcci[óo]n$", unidad, re.I) and entidad)
    if (not unidad or generica or re.search(APOYO, str(fila["cargo"]), re.I)
            or not re.match(r"J[2-4]|J6|J7", str(fila["jerarquia_puesto"]))
            or (fila["nivel_cargo"] == "VMIN" and sin_tildes(unidad) == "DESPACHO VICEMINISTERIAL")):
        return ""
    # El coordinador o el administrador de una unidad son puestos distintos del titular (jefe, director, gerente, ejecutivo).
    # Criterio conservador: puede partir un mismo puesto en dos, pero no mezcla puestos distintos (que inventaría rotación)
    inicio_cargo = re.sub(r"^\s*(?:en\s+)?(?:e?l\s+)?(?:cargo|puesto)\s+(?:de\s+confianza\s+)?(?:de|como)?\s*", "",
                          str(fila["cargo"]), flags=re.I)
    rol = ("COORDINADOR | " if re.match(r"coordinador", inicio_cargo, re.I) else
           "ADMINISTRADOR | " if re.match(r"administrador", inicio_cargo, re.I) else "")
    return f"{sin_tildes(fila['institucion_del_cargo'])} | {entidad} | {rol}{sin_tildes(unidad)}"


personas["puesto"] = personas.apply(clave_puesto, axis=1)
entradas = personas[(personas["puesto"] != "") & personas["tipo_movimiento"].isin(ENTRADA) & ~personas["temporal"]]
entradas = entradas.sort_values(["puesto", "fecha_ref"])
# Varias normas seguidas para la misma persona en el mismo puesto = un solo periodo
entradas = entradas[entradas["clave_persona"] != entradas.groupby("puesto")["clave_persona"].shift()]
salidas = personas[personas["tipo_movimiento"].isin(SALIDA)][["clave_persona", "institucion_del_cargo", "fecha_ref"]]
entradas["siguiente_titular"] = entradas.groupby("puesto")["fecha_ref"].shift(-1)
# Salida explícita propia: la primera conclusión, renuncia o "dejar sin efecto" de esa persona en esa institución
cruce = entradas[["id_movimiento", "clave_persona", "institucion_del_cargo", "fecha_ref"]].merge(
    salidas, on=["clave_persona", "institucion_del_cargo"], suffixes=("", "_salida"))
cruce = cruce[cruce["fecha_ref_salida"] > cruce["fecha_ref"]].groupby("id_movimiento")["fecha_ref_salida"].min()
entradas["salida_propia"] = entradas["id_movimiento"].map(cruce)
# (corregido el 31/10/2026) El periodo también termina cuando la misma persona es designada en OTRO cargo (confianza,
# subprefecto o diplomático; no directorios ni comisiones, que pueden ser simultáneos). Antes, quien se iba a otra
# institución sin que se publicara su salida quedaba "abierto" y su duración se alargaba. El mismo día = simultáneo (no cuenta)
otros_cargos = personas[personas["tipo_movimiento"].isin(ENTRADA) & ~personas["temporal"]
                        & personas["ambito"].isin(["confianza y directivos", "subprefectos y prefectos", "servicio diplomático"])][
    ["clave_persona", "fecha_ref", "puesto"]]
cruce_otro = entradas[["id_movimiento", "clave_persona", "puesto", "fecha_ref"]].merge(
    otros_cargos, on="clave_persona", suffixes=("", "_otro"))
cruce_otro = cruce_otro[(cruce_otro["fecha_ref_otro"] > cruce_otro["fecha_ref"]) & (cruce_otro["puesto_otro"] != cruce_otro["puesto"])]
entradas["otro_cargo"] = entradas["id_movimiento"].map(cruce_otro.groupby("id_movimiento")["fecha_ref_otro"].min())
entradas["fin"] = entradas[["siguiente_titular", "salida_propia", "otro_cargo"]].min(axis=1)
entradas["censurado"] = entradas["fin"].isna()
entradas["fin"] = entradas["fin"].fillna(FIN_VENTANA)
entradas["dias"] = (entradas["fin"] - entradas["fecha_ref"]).dt.days.clip(lower=0)
periodos = entradas[["puesto", "clave_persona", "id_persona", "institucion_del_cargo", "entidad_del_cargo", "unidad_organica",
                     "ubicacion_tabla", "ambito", "jerarquia_puesto", "ubicacion", "sexo_analisis", "codigo_norma", "enlace_web",
                     "enlace_pdf", "fecha_ref", "fin", "dias",
                     "censurado"]].rename(columns={"fecha_ref": "inicio"})
print("\n16.5 Periodos de titulares:", len(periodos), "| en", periodos["puesto"].nunique(), "puestos | terminados:",
      int((~periodos["censurado"]).sum()), "| abiertos al cierre:", int(periodos["censurado"].sum()))
guardar(periodos, "periodos_titulares")

anios_observados = ((periodos.groupby("puesto")["fin"].max() - periodos.groupby("puesto")["inicio"].min()).dt.days / 365.25).clip(lower=1)
puestos = periodos.groupby("puesto").agg(titulares=("clave_persona", "nunique"), institucion=("institucion_del_cargo", "first"),
                                         ambito=("ambito", "first"), jerarquia=("jerarquia_puesto", "first"),
                                         dias_mediana=("dias", "median"))
puestos["titulares_por_anio"] = (puestos["titulares"] / anios_observados).round(2)
puestos = puestos.sort_values("titulares", ascending=False).reset_index()
print("     Puestos con más titulares (sin subprefecturas):")
print(puestos[puestos["ambito"] != "subprefectos y prefectos"].head(12).to_string(index=False))
guardar(puestos, "puestos_titulares")


def kaplan_meier(dias, terminado):
    """Antes: duraciones y si el periodo terminó (True) o sigue abierto (False)
    | Después: tabla dia -> % que sigue en el cargo (estimador de Kaplan-Meier)"""
    tabla = pd.DataFrame({"dias": dias, "evento": terminado}).sort_values("dias")
    en_riesgo, sigue, filas_km = len(tabla), 1.0, [(0, 100.0)]
    for dia, grupo in tabla.groupby("dias"):
        eventos = grupo["evento"].sum()
        if eventos:
            sigue *= 1 - eventos / en_riesgo
            filas_km.append((dia, round(100 * sigue, 2)))
        en_riesgo -= len(grupo)
    return pd.DataFrame(filas_km, columns=["dia", "pct_sigue"])


curvas = []
grupos_km = [("jerarquia", g) for g in ["J2 Viceministro", "J3 Secretario general, jefe de gabinete o titular de entidad",
                                         "J4 Director general o jefe de órgano", "J6 Jefe de unidad orgánica", "J7 Subunidad o apoyo"]]
for tipo, valor in grupos_km + [("sexo", "F"), ("sexo", "M"), ("ambito", "subprefectos y prefectos")]:
    columna = {"jerarquia": "jerarquia_puesto", "sexo": "sexo_analisis", "ambito": "ambito"}[tipo]
    datos = periodos[periodos[columna] == valor]
    if len(datos) < 30:
        continue
    km = kaplan_meier(datos["dias"], ~datos["censurado"])
    mediana = km.loc[km["pct_sigue"] <= 50, "dia"].min()
    curvas.append(km.assign(grupo=f"{tipo}: {valor}", periodos=len(datos), mediana_dias=mediana))
    print(f"     Supervivencia {tipo}: {valor[:40]:40s} periodos {len(datos):5d} | mediana {mediana} días")
supervivencia = pd.concat(curvas, ignore_index=True)
guardar(supervivencia, "supervivencia_curvas")


# ============================================================
# PROCESO 16.6: Género por jerarquía y por gobierno
# Insumo:    designaciones de personas con sexo (de la norma o inferido)
# Resultado: % de mujeres por jerarquía y por gobierno
# ============================================================
designaciones = personas[personas["tipo_movimiento"].isin(ENTRADA) & personas["sexo_analisis"].isin(["F", "M"])].copy()
designaciones["gobierno"] = designaciones["fecha_ref"].map(gobierno_de)
genero = (designaciones.groupby(["jerarquia_puesto", "gobierno"])["sexo_analisis"]
          .agg(designaciones="size", pct_mujeres=lambda s: round(100 * (s == "F").mean(), 1)).reset_index())
genero_total = designaciones.groupby("jerarquia_puesto")["sexo_analisis"].agg(
    designaciones="size", pct_mujeres=lambda s: round(100 * (s == "F").mean(), 1)).reset_index()
print("\n16.6 Mujeres por jerarquía (4 años):")
print(genero_total.to_string(index=False))
guardar(genero, "genero_jerarquia_gobierno")
guardar(genero_total, "genero_jerarquia")


# ============================================================
# PROCESO 16.7: Olas de designaciones
# Insumo:    designaciones del análisis principal
# Resultado: serie semanal por sector y semanas "ola" (por encima del percentil 95)
# ============================================================
entradas_todas = principal[principal["tipo_movimiento"].isin(ENTRADA)].copy()
entradas_todas["semana"] = entradas_todas["fecha_ref"].dt.to_period("W").dt.start_time
semanal = entradas_todas.groupby(["semana", "sector_completado"]).size().rename("designaciones").reset_index()
total_semana = entradas_todas.groupby("semana").size()
umbral = total_semana.quantile(0.95)
olas = total_semana[total_semana > umbral].rename("designaciones").reset_index()
olas["gobierno"] = olas["semana"].map(gobierno_de)
print(f"\n16.7 Semanas 'ola' (más de {umbral:.0f} designaciones, percentil 95):")
print(olas.to_string(index=False))
guardar(semanal, "olas_semanal_sector")
guardar(olas, "olas_semanas")


# ============================================================
# PROCESO 16.8: Subprefectos y prefectos por departamento (mapa)
# Insumo:    movimientos del ámbito subprefectos y prefectos
# Resultado: movimientos por departamento y mes
# ============================================================
DEPARTAMENTOS = ["AMAZONAS", "ANCASH", "APURIMAC", "AREQUIPA", "AYACUCHO", "CAJAMARCA", "CALLAO", "CUSCO", "HUANCAVELICA",
                 "HUANUCO", "ICA", "JUNIN", "LA LIBERTAD", "LAMBAYEQUE", "LIMA", "LORETO", "MADRE DE DIOS", "MOQUEGUA",
                 "PASCO", "PIURA", "PUNO", "SAN MARTIN", "TACNA", "TUMBES", "UCAYALI"]


def departamento_de(fila):
    """Antes: ubicación "SAN JUAN DE LOPECANCHA LUYA AMAZONAS" o cargo "Prefecto Regional de Lambayeque"
    | Después: "AMAZONAS" / "LAMBAYEQUE" (el departamento que aparece al final; Lima Provincias y Lima Metropolitana = LIMA)"""
    texto = sin_tildes(f"{fila['ubicacion_tabla'] if isinstance(fila['ubicacion_tabla'], str) else ''} "
                       f"{fila['cargo'] if isinstance(fila['cargo'], str) else ''}").replace("CUZCO", "CUSCO")
    encontrados = [(m.start(), d) for d in DEPARTAMENTOS for m in re.finditer(rf"\b{d}\b", texto)]
    return max(encontrados)[1] if encontrados else ""


subprefectos = principal[principal["ambito"] == "subprefectos y prefectos"].copy()
subprefectos["departamento"] = subprefectos.apply(departamento_de, axis=1)
subprefectos["mes"] = subprefectos["fecha_ref"].dt.to_period("M").astype(str)
subprefectos["gobierno"] = subprefectos["fecha_ref"].map(gobierno_de)
mapa = subprefectos.groupby(["departamento", "gobierno", "mes", "tipo_movimiento"]).size().rename("movimientos").reset_index()
print(f"\n16.8 Subprefectos: {len(subprefectos)} movimientos | sin departamento: {(subprefectos['departamento'] == '').sum()}")
print(subprefectos[subprefectos["mes"] == "2022-12"].groupby("departamento").size().sort_values(ascending=False).head(8).to_string())
guardar(mapa, "subprefectos_departamento_mes")


# ============================================================
# PROCESO 16.9: Red — equipos, co-movimiento, comunidades, puentes y arrastre (hallazgo 3)
# Insumo:    designaciones de personas confiables; llegadas de jefes (ministros y titulares de entidad)
# Resultado: red de co-movimiento (comunidades y modularidad), intermediación, tipología y tasa de arrastre
# ============================================================
red = personas[personas["tipo_movimiento"].isin(ENTRADA) & ~personas["temporal"]].copy()
# Entidad = institución + programa u organismo (los programas del MIDIS son entidades distintas).
# Clave única por entidad (corregido el 31/10/2026): "SUSALUD | SUSALUD" y "SUSALUD | " son la misma entidad, y un organismo
# escrito dentro de su ministerio ("SALUD | INSTITUTO NACIONAL DE SALUD") va a su propia clave ("INSTITUTO NACIONAL DE SALUD")
INSTITUCIONES_PROPIAS = set(principal["institucion_del_cargo"].dropna().map(sin_tildes))


def clave_entidad(institucion, entidad):
    """Antes: ("SALUD", "Instituto Nacional de Salud") | Después: "INSTITUTO NACIONAL DE SALUD" (programas: "MIDIS | PROGRAMA X")"""
    i, e = sin_tildes(institucion), sin_tildes(entidad) if isinstance(entidad, str) else ""
    if e in ("", i):
        return i
    return e if e in INSTITUCIONES_PROPIAS else f"{i} | {e}"


red["entidad"] = [clave_entidad(i, e) for i, e in zip(red["institucion_del_cargo"], red["entidad_del_cargo"])]
# Llegadas de jefes que abren una "gestión": ministros (en su ministerio) y titulares de cada programa u organismo
jefes = red[(red["jerarquia_puesto"].fillna("").str.startswith("J1")) |
            ((red["jerarquia_puesto"].fillna("").str.startswith("J3")) & (red["entidad_del_cargo"].fillna("") != "")
             & (red["nivel_cargo"] != "SECGEN"))][["entidad", "fecha_ref", "clave_persona"]]
# Una gestión nueva empieza solo cuando cambia la PERSONA al mando: si el mismo ministro es redesignado
# (recomposición del gabinete), sigue siendo el mismo equipo (corregido el 31/10/2026)
jefes = jefes.sort_values(["entidad", "fecha_ref"])
jefes = jefes[jefes["clave_persona"] != jefes.groupby("entidad")["clave_persona"].shift()]
llegadas_jefe = jefes.groupby("entidad")["fecha_ref"].apply(lambda s: sorted(set(s))).to_dict()


def equipo_de(fila):
    """Antes: entidad y fecha | Después: "ENTIDAD #3" (la gestión del tercer jefe observado) o "ENTIDAD #año" si no hay jefes"""
    fechas = llegadas_jefe.get(fila["entidad"])
    if not fechas:
        return f"{fila['entidad']} #{fila['fecha_ref'].year}"
    return f"{fila['entidad']} #{int(np.searchsorted(fechas, fila['fecha_ref'], side='right'))}"


red["equipo"] = red.apply(equipo_de, axis=1)
red = red.sort_values(["clave_persona", "fecha_ref"])
print(f"\n16.9 Red: {red['clave_persona'].nunique()} personas en {red['equipo'].nunique()} equipos de {red['entidad'].nunique()} entidades")

# --- 16.9.1 Traslados: la persona pasa de un equipo a otro de OTRA entidad ---
red["equipo_anterior"] = red.groupby("clave_persona")["equipo"].shift()
red["entidad_anterior"] = red.groupby("clave_persona")["entidad"].shift()
traslados = red[red["entidad_anterior"].notna() & (red["entidad_anterior"] != red["entidad"])][
    ["clave_persona", "id_persona", "equipo_anterior", "entidad", "equipo", "fecha_ref"]]
print(f"     Traslados entre entidades: {len(traslados)} de {traslados['clave_persona'].nunique()} personas")


def pares_que_se_mueven_juntos(tabla, dias=180):
    """Antes: traslados (persona, equipo de origen, entidad de destino, fecha)
    | Después: pares de personas que salen del mismo equipo y llegan a la misma entidad con menos de 180 días de diferencia"""
    pares = {}
    for (_, _), grupo in tabla.groupby(["equipo_anterior", "entidad"]):
        if len(grupo) < 2:
            continue
        filas_grupo = grupo.sort_values("fecha_ref")[["clave_persona", "fecha_ref"]].values
        for i in range(len(filas_grupo)):
            for j in range(i + 1, len(filas_grupo)):
                if (filas_grupo[j][1] - filas_grupo[i][1]).days > dias:
                    break
                a, b = sorted((filas_grupo[i][0], filas_grupo[j][0]))
                if a != b:
                    pares[(a, b)] = pares.get((a, b), 0) + 1
    return pares


pares = pares_que_se_mueven_juntos(traslados)
co = nx.Graph()
co.add_weighted_edges_from((a, b, w) for (a, b), w in pares.items())
recurrentes = sum(1 for w in pares.values() if w >= 2)
# Comparación con el azar: se sortea el equipo de origen entre los traslados que llegan a la misma entidad
rng = np.random.default_rng(1)
recurrentes_azar = []
for _ in range(20):
    sorteo = traslados.copy()
    sorteo["equipo_anterior"] = sorteo.groupby("entidad")["equipo_anterior"].transform(lambda s: rng.permutation(s.values))
    recurrentes_azar.append(sum(1 for w in pares_que_se_mueven_juntos(sorteo).values() if w >= 2))
print(f"     Pares que se trasladan juntos: {len(pares)} | dos o más veces: {recurrentes} "
      f"(al azar se esperarían {np.mean(recurrentes_azar):.1f})")

# --- 16.9.2 Comunidades (Louvain) y modularidad de la red de co-movimiento ---
comunidades = nx.community.louvain_communities(co, weight="weight", seed=1)
modularidad = nx.community.modularity(co, comunidades, weight="weight")
filas = []
for n, comunidad in enumerate(sorted(comunidades, key=len, reverse=True), start=1):
    sub = co.subgraph(comunidad)
    miembros = red[red["clave_persona"].isin(comunidad)]
    filas.append({"comunidad": n, "personas": len(comunidad),
                  "traslados_conjuntos": int(sum(d["weight"] for _, _, d in sub.edges(data=True))),
                  "pares_recurrentes": sum(1 for _, _, d in sub.edges(data=True) if d["weight"] >= 2),
                  "entidades_recorridas": miembros["entidad"].nunique(),
                  "gobiernos": miembros["fecha_ref"].map(gobierno_de).nunique(),
                  "miembros_id": " ".join(sorted(red.loc[red["clave_persona"].isin(comunidad), "id_persona"].unique())),
                  "miembros": " | ".join(sorted(comunidad))})
tabla_comunidades = pd.DataFrame(filas)
print(f"     Comunidades: {len(comunidades)} | modularidad {modularidad:.2f} | con 5+ personas: {(tabla_comunidades['personas'] >= 5).sum()}")
print(tabla_comunidades.drop(columns=["miembros", "miembros_id"]).sort_values("pares_recurrentes", ascending=False).head(10).to_string(index=False))
guardar(tabla_comunidades, "red_comunidades")
guardar(pd.DataFrame([{"persona_a": a, "persona_b": b, "traslados_juntos": w} for (a, b), w in pares.items()]), "red_pares")

# --- 16.9.3 Puentes: intermediación en la red persona–equipo ---
bipartita = nx.Graph()
bipartita.add_edges_from(("P:" + p, "E:" + e) for p, e in red[["clave_persona", "equipo"]].drop_duplicates().values)
# Intermediación exacta (todos los nodos, sin muestra): el orden entre personas vecinas en el ranking es confiable
intermediacion = nx.betweenness_centrality(bipartita)
perfil = red.groupby("clave_persona").agg(id_persona=("id_persona", "first"), equipos=("equipo", "nunique"),
                                         entidades=("entidad", "nunique"),
                                         gobiernos=("fecha_ref", lambda f: f.map(gobierno_de).nunique()),
                                         designaciones=("equipo", "size"),
                                         jerarquia_max=("jerarquia_puesto", lambda j: j.dropna().min() if j.notna().any() else ""))
perfil["intermediacion"] = [intermediacion.get("P:" + p, 0) for p in perfil.index]
# Permanencia: a cuántos jefes "sobrevivió" en un mismo puesto (llegadas de jefe dentro de su periodo)
periodos["entidad"] = periodos["institucion_del_cargo"].map(sin_tildes)


def jefes_sobrevividos(fila):
    """Antes: un periodo (inicio, fin) en un puesto | Después: cuántos ministros llegaron a su ministerio mientras seguía"""
    fechas = ministros.loc[ministros["institucion_del_cargo"] == fila["institucion_del_cargo"], "fecha_ref"]
    return int(((fechas > fila["inicio"]) & (fechas < fila["fin"])).sum())


periodos["jefes_sobrevividos"] = periodos.apply(jefes_sobrevividos, axis=1)
perfil["jefes_sobrevividos_max"] = periodos.groupby("clave_persona")["jefes_sobrevividos"].max().reindex(perfil.index).fillna(0)
movil = perfil[perfil["equipos"] >= 2]
corte_puente = movil["intermediacion"].quantile(0.95)
perfil["alta_intermediacion"] = perfil["intermediacion"] >= corte_puente
perfil["alta_permanencia"] = perfil["jefes_sobrevividos_max"] >= 2
perfil["tipo"] = np.select(
    [perfil["alta_permanencia"] & perfil["alta_intermediacion"], perfil["alta_permanencia"],
     perfil["alta_intermediacion"]],
    ["articulador estable", "memoria institucional", "operador puente"], "paso fugaz u ocasional")
print("     Tipología (permanencia x intermediación):", perfil["tipo"].value_counts().to_dict())
print(perfil.sort_values("intermediacion", ascending=False).head(15)[
    ["id_persona", "equipos", "entidades", "gobiernos", "jerarquia_max", "jefes_sobrevividos_max", "tipo"]].to_string())
guardar(perfil.reset_index().sort_values("intermediacion", ascending=False), "red_perfil_personas")

# --- 16.9.4 Tasa de arrastre: cuando un jefe cambia de entidad, ¿quiénes de su equipo llegan con él? ---
lideres = red[red["jerarquia_puesto"].fillna("").str.match("J[1-3]")]
filas = []
for persona, trayectoria in lideres.groupby("clave_persona"):
    trayectoria = trayectoria.drop_duplicates("entidad").sort_values("fecha_ref")
    for (_, origen), (_, destino) in zip(trayectoria.iterrows(), trayectoria.iloc[1:].iterrows()):
        equipo_origen = set(red.loc[red["equipo"] == origen["equipo"], "clave_persona"]) - {persona}
        if len(equipo_origen) < 3:
            continue
        t = destino["fecha_ref"]
        ventana = red[(red["fecha_ref"] >= t - pd.Timedelta(days=30)) & (red["fecha_ref"] <= t + pd.Timedelta(days=180))]
        se_mueven = ventana[ventana["clave_persona"].isin(equipo_origen) & (ventana["entidad"] != origen["entidad"])]
        siguen = se_mueven[se_mueven["entidad"] == destino["entidad"]]["clave_persona"].nunique()
        movidos = se_mueven["clave_persona"].nunique()
        esperado = (ventana["entidad"] == destino["entidad"]).mean()   # peso del destino entre todas las llegadas
        filas.append({"lider": persona, "id_lider": origen["id_persona"], "de": origen["entidad"], "a": destino["entidad"],
                      "fecha": t.date(), "equipo_origen": len(equipo_origen), "se_movieron": movidos, "llegan_con_el_lider": siguen,
                      "pct_de_los_que_se_movieron": round(100 * siguen / movidos, 1) if movidos else np.nan,
                      "pct_esperado_por_azar": round(100 * esperado, 1)})
arrastre = pd.DataFrame(filas)
con_movidos = arrastre[arrastre["se_movieron"] > 0]
# Total (no mediana): la mayoría de los traslados tiene 0 seguidores, y la mediana lo esconde
print(f"     Arrastre: {len(arrastre)} traslados de líderes | con al menos un seguidor: {(arrastre['llegan_con_el_lider'] > 0).sum()}"
      f" | de {con_movidos['se_movieron'].sum()} integrantes del equipo que cambiaron de entidad, "
      f"{con_movidos['llegan_con_el_lider'].sum()} fueron al destino del líder "
      f"({100 * con_movidos['llegan_con_el_lider'].sum() / con_movidos['se_movieron'].sum():.1f} %)"
      f" vs {con_movidos['pct_esperado_por_azar'].mean():.1f} % esperado por azar")
guardar(arrastre.sort_values("llegan_con_el_lider", ascending=False), "red_arrastre")
# Resumen de la red (para el dashboard y el informe)
guardar(pd.DataFrame([{
    "personas_en_la_red": red["clave_persona"].nunique(), "equipos": red["equipo"].nunique(), "entidades": red["entidad"].nunique(),
    "traslados_entre_entidades": len(traslados), "pares_que_se_trasladan_juntos": len(pares),
    "pares_dos_o_mas_veces": recurrentes, "pares_dos_o_mas_veces_azar": round(float(np.mean(recurrentes_azar)), 2),
    "comunidades": len(comunidades), "comunidades_5_o_mas": int((tabla_comunidades["personas"] >= 5).sum()),
    "modularidad": round(modularidad, 3),
    "arrastre_movidos": int(con_movidos["se_movieron"].sum()), "arrastre_al_destino_del_lider": int(con_movidos["llegan_con_el_lider"].sum()),
    "arrastre_pct": round(100 * con_movidos["llegan_con_el_lider"].sum() / con_movidos["se_movieron"].sum(), 1),
    "arrastre_pct_azar": round(con_movidos["pct_esperado_por_azar"].mean(), 1),
    **{f"tipo_{k}": int(v) for k, v in perfil["tipo"].value_counts().items()}}]), "red_resumen")

# ============================================================
# PROCESO 16.10: Red de seguimiento — quién llega detrás de quién (hallazgo 3, idea del usuario, aprobada el 31/10/2026)
# Insumo:    designaciones de la red (16.9) con su firmante; llegadas de jefes
# Resultado: parejas jefe -> acompañante que se repiten en 2 o más entidades, comparadas con el azar
# Regla: un jefe "llega" a una entidad cuando asume un cargo de decisión (J1-J4) o cuando firma allí su primera
#   designación (así se ven jefes cuya propia designación es anterior a la base o no se publicó en ella).
#   Acompañante: persona NUEVA en esa entidad que llega entre 0 y 180 días después del jefe.
#   Solo cuenta si se repite con el mismo jefe en 2 o más entidades distintas (una sola vez puede ser personal "impuesto").
# ============================================================
VENTANA_SEGUIMIENTO = 180
claves_conocidas = set(personas["clave_persona"])
indice_nombres = {}
for c in claves_conocidas:
    w = c.split()
    if len(w) >= 3:
        indice_nombres.setdefault((w[0], w[-2], w[-1]), []).append(c)


def es_subsecuencia(corta, larga):
    """Antes: dos listas de palabras | Después: True si todas las palabras de la corta aparecen, en orden, en la larga"""
    resto = iter(larga)
    return all(p in resto for p in corta)


def clave_de_firmante(nombre):
    """Antes: "JUAN PÉREZ LÓPEZ" (como firma) | Después: "JUAN CARLOS PEREZ LOPEZ" (como fue designado)
    Se une solo si hay UN candidato con el mismo primer nombre y los mismos dos apellidos (corregido el 31/10/2026)"""
    k = sin_tildes(nombre)
    if not k or k in claves_conocidas:
        return k
    w = k.split()
    if len(w) < 3:
        return k
    candidatos = [c for c in indice_nombres.get((w[0], w[-2], w[-1]), [])
                  if es_subsecuencia(w, c.split()) or es_subsecuencia(c.split(), w)]
    return candidatos[0] if len(candidatos) == 1 else k


# Quién designa: el firmante; en resoluciones supremas firma el Presidente, así que cuenta el ministro que refrenda
es_suprema = (red["firmante1_cargo"].fillna("").str.contains("President", case=False)
              & red["firmante1_cargo"].fillna("").str.contains(r"Rep[úu]blica", case=False))
red["designa"] = red["firmante2_nombre"].where(es_suprema, red["firmante1_nombre"]).map(
    lambda v: clave_de_firmante(v) if isinstance(v, str) else "")
print(f"\n16.10 Red de seguimiento | firmantes unidos a la persona designada: "
      f"{(red['designa'] != red['firmante2_nombre'].where(es_suprema, red['firmante1_nombre']).map(lambda v: sin_tildes(v) if isinstance(v, str) else '')).sum()} filas")

# Llegada del jefe a cada entidad: primera designación en un cargo de decisión, o primera firma (sin resoluciones supremas)
llegada_por_cargo = red[red["jerarquia_puesto"].fillna("").str[:2].isin(["J1", "J2", "J3", "J4"])].groupby(
    ["clave_persona", "entidad"], as_index=False)["fecha_ref"].min()
llegada_por_firma = red[~es_suprema & (red["designa"] != "")].groupby(["designa", "entidad"], as_index=False)["fecha_ref"].min()
llegadas_jefes = (pd.concat([llegada_por_cargo, llegada_por_firma.rename(columns={"designa": "clave_persona"})])
                  .groupby(["clave_persona", "entidad"], as_index=False)["fecha_ref"].min())
print(f"     Llegadas de jefes a una entidad: {len(llegadas_jefes)} de {llegadas_jefes['clave_persona'].nunique()} personas")
# Primera llegada de cada persona a cada entidad (es "nueva" en esa entidad)
primeras = red.groupby(["clave_persona", "entidad"], as_index=False)["fecha_ref"].min()


def acompanamientos(primeras_llegadas):
    """Antes: primeras llegadas a cada entidad | Después: (jefe, acompañante, entidad) cuando el acompañante llega 0-180 días después"""
    por_entidad = {e: (g["fecha_ref"].values, g["clave_persona"].values)
                   for e, g in primeras_llegadas.sort_values("fecha_ref").groupby("entidad")}
    filas = []
    for jefe, entidad, t in llegadas_jefes[["clave_persona", "entidad", "fecha_ref"]].itertuples(index=False):
        if entidad not in por_entidad:
            continue
        fechas, quienes = por_entidad[entidad]
        i0 = np.searchsorted(fechas, np.datetime64(t), "left")
        i1 = np.searchsorted(fechas, np.datetime64(t + pd.Timedelta(days=VENTANA_SEGUIMIENTO)), "right")
        filas += [(jefe, q, entidad) for q in quienes[i0:i1] if q != jefe]
    return pd.DataFrame(filas, columns=["jefe", "acompanante", "entidad"]).drop_duplicates()


eventos = acompanamientos(primeras)
conteo = eventos.groupby(["jefe", "acompanante"])["entidad"].agg(instituciones="nunique", entidades=lambda e: " ; ".join(sorted(set(e))))
seguimiento = conteo[conteo["instituciones"] >= 2].reset_index()
# Evidencia adicional: el jefe firmó la designación del acompañante al menos una vez
firmadas = set(zip(red["designa"], red["clave_persona"]))
seguimiento["firmo"] = [(j, a) in firmadas for j, a in zip(seguimiento["jefe"], seguimiento["acompanante"])]
# Comparación con el azar: dentro de cada entidad se sortea QUIÉN llega (mismas fechas y cantidades); los jefes no cambian
azar_2, azar_3 = [], []
for _ in range(10):
    sorteo = primeras.copy()
    sorteo["clave_persona"] = sorteo.groupby("entidad")["clave_persona"].transform(lambda s: rng.permutation(s.values))
    n = acompanamientos(sorteo).groupby(["jefe", "acompanante"])["entidad"].nunique()
    azar_2.append(int((n >= 2).sum())); azar_3.append(int((n >= 3).sum()))
# Códigos anónimos: los de la base; los jefes que solo aparecen como firmantes reciben un código F0001, F0002...
codigos = personas.drop_duplicates("clave_persona").set_index("clave_persona")["id_persona"].to_dict()
solo_firmantes = sorted(set(seguimiento["jefe"]) - set(codigos))
if solo_firmantes:     # los jefes que solo aparecen firmando también reciben su código del registro maestro (antes: F0001...)
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import registro_personas
    primera_firma = red[red["designa"].isin(solo_firmantes)].groupby("designa")["fecha_ref"].min()
    tabla_firmantes = pd.DataFrame({"clave_persona": solo_firmantes, "nombre_completo": [s.title() for s in solo_firmantes],
                                    "dni": "", "primera_aparicion": [primera_firma.get(s) for s in solo_firmantes]})
    asignados = registro_personas.asignar(tabla_firmantes, origen="firmante (07)")
    codigos.update({s: asignados[s] for s in solo_firmantes})
seguimiento["id_jefe"] = seguimiento["jefe"].map(codigos)
seguimiento["id_acompanante"] = seguimiento["acompanante"].map(codigos)
jefes_seg = seguimiento.groupby("jefe").agg(id_jefe=("id_jefe", "first"), acompanantes=("acompanante", "nunique"),
                                            en_3_o_mas=("instituciones", lambda s: int((s >= 3).sum())),
                                            firmados=("firmo", "sum")).sort_values("acompanantes", ascending=False).reset_index()
print(f"     Parejas jefe -> acompañante en 2+ entidades: {len(seguimiento)} (azar {np.mean(azar_2):.0f}) | "
      f"en 3+: {(seguimiento['instituciones'] >= 3).sum()} (azar {np.mean(azar_3):.1f}) | el jefe firmó: {seguimiento['firmo'].sum()}")
print(f"     Jefes con 3+ acompañantes: {(jefes_seg['acompanantes'] >= 3).sum()} | con 5+: {(jefes_seg['acompanantes'] >= 5).sum()}")
print(jefes_seg.head(10).to_string(index=False))
guardar(seguimiento.sort_values(["jefe", "instituciones"], ascending=[True, False]), "seguimiento_parejas")
guardar(jefes_seg, "seguimiento_jefes")
guardar(pd.DataFrame([{
    "llegadas_de_jefes": len(llegadas_jefes), "jefes_distintos": llegadas_jefes["clave_persona"].nunique(),
    "parejas_2_o_mas": len(seguimiento), "parejas_2_o_mas_azar": round(float(np.mean(azar_2)), 1),
    "parejas_3_o_mas": int((seguimiento["instituciones"] >= 3).sum()), "parejas_3_o_mas_azar": round(float(np.mean(azar_3)), 1),
    "parejas_firmadas_por_el_jefe": int(seguimiento["firmo"].sum()),
    "jefes_con_3_o_mas": int((jefes_seg["acompanantes"] >= 3).sum()), "jefes_con_5_o_mas": int((jefes_seg["acompanantes"] >= 5).sum()),
    "sorteos": 10, "ventana_dias": VENTANA_SEGUIMIENTO}]), "seguimiento_resumen")
print("\nListo: tablas en", CARPETA_SALIDA)
