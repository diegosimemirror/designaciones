# ============================================================
# Designaciones de El Peruano — Script 07c: trayectorias personales y rankings de rotación y permanencia
# (proceso 16.11; pedido del usuario el 31/10/2026)
# ------------------------------------------------------------
# Ranking 1 (rotación): quiénes pasaron por MÁS cargos en MENOS tiempo, dónde y cuánto duraron en cada uno.
# Ranking 2 (permanencia): quiénes permanecieron MÁS tiempo en un mismo puesto de titular, y dónde.
#
# Reglas (ver docs/metodologia_indicadores.md, R8):
#   - Solo cargos de confianza y directivos (sin directorios, comisiones, subprefectos ni diplomáticos) y sin encargos temporales.
#   - Un "cargo" es cada designación en un puesto distinto; si la misma persona es designada otra vez en el mismo cargo
#     (misma institución y mismo texto de cargo), es el mismo periodo.
#   - Fin de cada cargo: lo que ocurra primero entre (a) su siguiente designación en otro cargo, (b) su conclusión, renuncia
#     o "dejar sin efecto" en esa institución, (c) la designación de un sucesor en ese puesto (regla de sucesión R1).
#     Si no ocurre nada, el cargo sigue "abierto" al 29/10/2026 (cierre de la base).
#   - Rotación: se ordena por el máximo de cargos distintos iniciados en 12 meses; luego por total de cargos y por la
#     mediana de días en cada cargo (menos días = más rotación).
#   - Dos designaciones de la misma persona el mismo día son cargos SIMULTÁNEOS, no un cambio: el de 0 días no se cuenta.
#   - Permanencia: periodos de titular (regla de sucesión R1, proceso 16.5) de 3 años o más, ordenados por días en el puesto;
#     a igualdad, por cuántos ministros llegaron mientras seguía. Ese dato solo se calcula en ministerios: en los organismos,
#     contar sus cambios de jefe no es confiable con estos datos (firman designaciones adjuntos, encargados e intendentes).
#   - Claves que no son personas (textos de la norma leídos como nombre) se excluyen; prefijos pegados al nombre
#     ("SEÑOR", "INGENIERO", "Y FINANZAS") se quitan. Solo aquí: la base no se cambia (los códigos anónimos se mantendrían).
#
# Insumos:   datos/procesados/movimientos_analisis.csv (06), indicadores/periodos_titulares.csv y llegadas_ministros.csv (07)
# Resultado: indicadores/trayectorias.csv, ranking_rotacion.csv, ranking_permanencia.csv (con nombres; no se publican)
#            datos/privado/rankings_rotacion_permanencia.xlsx (versión de trabajo con nombres)
# Uso (desde la carpeta tarea_3): python scripts/07c_trayectorias_rankings.py
# ============================================================

# --- Paquetes ---
# re y unicodedata: normalizar textos de institución y cargo para compararlos
import re
import unicodedata
# pathlib: rutas de archivos
from pathlib import Path
# numpy: contar cargos en ventanas de 12 meses
import numpy as np
# pandas: tablas; el Excel se escribe con openpyxl (viene con Anaconda)
import pandas as pd

CARPETA_TAREA = Path(__file__).resolve().parent.parent
PROCESADOS = CARPETA_TAREA / "datos" / "procesados"
INDICADORES = PROCESADOS / "indicadores"
PRIVADO = CARPETA_TAREA / "datos" / "privado"
PRIVADO.mkdir(parents=True, exist_ok=True)
FIN_VENTANA = pd.Timestamp("2026-10-29")
ENTRADA = {"designación", "nombramiento", "encargatura"}
SALIDA = {"conclusión", "renuncia", "dejar sin efecto"}


def sin_tildes(texto):
    """Antes: "Asesor II (CAP-P N° 003) del Despacho" | Después: "ASESOR II CAP P N 003 DEL DESPACHO" """
    texto = "".join(c for c in unicodedata.normalize("NFD", str(texto)) if unicodedata.category(c) != "Mn").upper()
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]", " ", texto)).strip()


def duracion(dias):
    """Antes: 95 | Después: "3,1 meses" (menos de 60 días: "45 días")"""
    return f"{int(dias)} días" if dias < 60 else f"{dias / 30.44:.1f} meses".replace(".", ",")


# ============================================================
# PROCESO 16.11.1: Cargos de cada persona (trayectoria) con su duración
# Insumo:    designaciones y salidas del análisis principal; periodos de titulares (16.5)
# Resultado: una fila por persona y cargo, con inicio, fin, días y si sigue abierto
# ============================================================
mov = pd.read_csv(PROCESADOS / "movimientos_analisis.csv", encoding="utf-8-sig", dtype=str)
# Fecha de referencia (regla R4): efectividad si la norma la dice (y es razonable), si no la firma, si no la publicación
firma = pd.to_datetime(mov["fecha_emision_corregida"], errors="coerce")
publicacion = pd.to_datetime(mov["fecha_publicacion"], dayfirst=True)
efectividad = pd.to_datetime(mov["fecha_efectividad"], errors="coerce")
efectividad = efectividad.where((efectividad - firma.fillna(publicacion)).abs() <= pd.Timedelta(days=365))
mov["fecha_ref"] = efectividad.fillna(firma).fillna(publicacion)
personas = mov[(mov["en_analisis_principal"] == "True") & mov["clave_persona"].notna() & (mov["nombre_dudoso"] != "True")].copy()

# --- Limpieza de claves de persona (solo para estos rankings) ---
# Ojo: "PORTAL" y "PORTALES" son apellidos reales; solo se excluyen frases como "PORTAL DE TRANSPARENCIA"
NO_ES_PERSONA = r"PORTAL (?:DE|WEB)|TRANSPARENCIA|LABORES|^LEY D|^PROCEDIMIENTO|^SENOR GENERAL|^LICENCIADO CC$"
PREFIJO = r"^(?:SENORA?|INGENIER[OA]|LICENCIAD[OA]|DOCTOR[A]?|ABOGAD[OA]|Y (?:FINANZAS|COMUNICACIONES|MANTENIMIENTO))\s+"


def limpiar_clave(clave):
    """Antes: "SENORA ANA TORRES DIAZ" | Después: "ANA TORRES DIAZ"; "LEY DE TRANSPARENCIA" -> "" (no es persona)"""
    if re.search(NO_ES_PERSONA, clave):
        return ""
    return re.sub(PREFIJO, "", clave)


personas["clave_original"] = personas["clave_persona"]
personas["clave_persona"] = personas["clave_persona"].map(limpiar_clave)
cambiadas = personas[personas["clave_persona"] != personas["clave_original"]]
print(f"16.11 Claves corregidas solo para los rankings: {cambiadas['clave_original'].nunique()} "
      f"({(cambiadas['clave_persona'] == '').sum()} filas de textos que no son personas se excluyen)")
personas = personas[personas["clave_persona"] != ""]
# El código anónimo de la persona es el de su clave limpia si ya existía; si no, el que tenía
codigo_limpio = personas[personas["clave_persona"] == personas["clave_original"]].groupby("clave_persona")["id_persona"].first()
personas["id_persona"] = personas["clave_persona"].map(codigo_limpio).fillna(personas["id_persona"])

cargos = personas[(personas["ambito"] == "confianza y directivos") & personas["tipo_movimiento"].isin(ENTRADA)
                  & (personas["temporal"] != "True")].copy()
# Clave del cargo: institución + texto del cargo sin números ni paréntesis (el "CAP-P N° 003" o el "Nivel F-5" cambian de una norma a otra)
cargos["cargo_clave"] = cargos["institucion_del_cargo"].map(sin_tildes) + " | " + cargos["cargo"].fillna("").map(
    lambda c: re.sub(r"\s+", " ", re.sub(r"\(.*?\)|NIVEL F ?\d+|\d+", " ", sin_tildes(c))).strip())
cargos = cargos.sort_values(["clave_persona", "fecha_ref"])
antes = len(cargos)
# Antes: varias normas para la misma persona en el mismo cargo | Después: un solo periodo (se queda la primera)
cargos = cargos[cargos["cargo_clave"] != cargos.groupby("clave_persona")["cargo_clave"].shift()]
print(f"16.11 Cargos de confianza (sin encargos temporales): {antes} designaciones -> {len(cargos)} cargos "
      f"de {cargos['clave_persona'].nunique()} personas")

# (a) siguiente designación propia en otro cargo
cargos["siguiente_cargo"] = cargos.groupby("clave_persona")["fecha_ref"].shift(-1)
# (b) salida propia: primera conclusión, renuncia o "dejar sin efecto" de esa persona en esa institución, después del inicio
salidas = personas[personas["tipo_movimiento"].isin(SALIDA)][["clave_persona", "institucion_del_cargo", "fecha_ref"]]
cruce = cargos[["id_movimiento", "clave_persona", "institucion_del_cargo", "fecha_ref"]].merge(
    salidas, on=["clave_persona", "institucion_del_cargo"], suffixes=("", "_salida"))
cruce = cruce[cruce["fecha_ref_salida"] > cruce["fecha_ref"]].groupby("id_movimiento")["fecha_ref_salida"].min()
cargos["salida_propia"] = cargos["id_movimiento"].map(cruce)
# (c) sucesor en el mismo puesto de titular (regla de sucesión, del proceso 16.5)
periodos = pd.read_csv(INDICADORES / "periodos_titulares.csv", encoding="utf-8-sig", parse_dates=["inicio", "fin"])
periodos["clave_persona"] = periodos["clave_persona"].map(limpiar_clave)
periodos = periodos[periodos["clave_persona"] != ""]
periodos["id_persona"] = periodos["clave_persona"].map(codigo_limpio).fillna(periodos["id_persona"])
con_sucesor = periodos[~periodos["censurado"]].groupby(["clave_persona", "institucion_del_cargo", "inicio"])["fin"].min()
cargos["fin_titular"] = [con_sucesor.get((p, i, f)) for p, i, f in
                         zip(cargos["clave_persona"], cargos["institucion_del_cargo"], cargos["fecha_ref"])]
cargos["fin"] = cargos[["siguiente_cargo", "salida_propia", "fin_titular"]].min(axis=1)
cargos["abierto"] = cargos["fin"].isna()
cargos["fin"] = cargos["fin"].fillna(FIN_VENTANA)
cargos["dias"] = (cargos["fin"] - cargos["fecha_ref"]).dt.days.clip(lower=0)
# Cargos simultáneos: si el siguiente cargo empieza el MISMO día, no hubo cambio (dos designaciones a la vez)
simultaneos = (cargos["dias"] == 0) & ~cargos["abierto"] & (cargos["fin"] == cargos["siguiente_cargo"])
print(f"     Designaciones simultáneas (mismo día que otra): {simultaneos.sum()} -> no cuentan como cambio de cargo")
cargos = cargos[~simultaneos]
print(f"     Terminados: {(~cargos['abierto']).sum()} | abiertos al cierre: {cargos['abierto'].sum()} | "
      f"mediana de días (terminados): {cargos.loc[~cargos['abierto'], 'dias'].median():.0f}")
trayectorias = cargos[["clave_persona", "id_persona", "institucion_del_cargo", "entidad_del_cargo", "cargo", "jerarquia_puesto",
                       "fecha_ref", "fin", "dias", "abierto", "codigo_norma", "enlace_web", "enlace_pdf"]].rename(columns={"fecha_ref": "inicio"})
trayectorias.to_csv(INDICADORES / "trayectorias.csv", index=False, encoding="utf-8-sig")


# ============================================================
# PROCESO 16.11.2: Ranking de rotación (más cargos en menos tiempo)
# Insumo:    trayectorias
# Resultado: una fila por persona con el máximo de cargos en 12 meses, total de cargos y mediana de días por cargo
# ============================================================
def maximo_en_12_meses(inicios):
    """Antes: fechas de inicio de los cargos de una persona | Después: el mayor número de cargos iniciados en 365 días seguidos"""
    f = np.sort(inicios.values.astype("datetime64[D]"))
    hasta = np.searchsorted(f, f + np.timedelta64(365, "D"), side="left")
    return int((hasta - np.arange(len(f))).max())


def recorrido(grupo):
    """Antes: cargos de una persona | Después: "Institución · cargo (duración) → ..." en orden"""
    return " → ".join(f"{str(r.institucion_del_cargo).title()} · {str(r.cargo)[:70]} ({duracion(r.dias)}{', sigue' if r.abierto else ''})"
                      for r in grupo.sort_values("inicio").itertuples())


por_persona = trayectorias.groupby("clave_persona")
rotacion = por_persona.agg(id_persona=("id_persona", "first"), cargos=("inicio", "size"),
                           instituciones=("institucion_del_cargo", "nunique"),
                           primer_cargo=("inicio", "min"), ultimo_cargo=("inicio", "max"),
                           mediana_dias=("dias", "median"))
rotacion["cargos_en_12_meses"] = por_persona["inicio"].apply(maximo_en_12_meses)
rotacion["recorrido"] = por_persona.apply(recorrido)
rotacion = rotacion.sort_values(["cargos_en_12_meses", "cargos", "mediana_dias"], ascending=[False, False, True]).reset_index()
rotacion.insert(0, "puesto_ranking", rotacion.index + 1)
rotacion.to_csv(INDICADORES / "ranking_rotacion.csv", index=False, encoding="utf-8-sig")
print(f"     Rotación: personas con 4+ cargos en 12 meses: {(rotacion['cargos_en_12_meses'] >= 4).sum()} | "
      f"con 6+: {(rotacion['cargos_en_12_meses'] >= 6).sum()}")

# ============================================================
# PROCESO 16.11.3: Ranking de permanencia (más tiempo en un mismo puesto de titular)
# Insumo:    periodos de titulares (16.5) y llegadas de ministros (16.1)
# Resultado: una fila por persona con su periodo más largo, dónde, y cuántos ministros "sobrevivió"
# ============================================================
llegadas = pd.read_csv(INDICADORES / "llegadas_ministros.csv", encoding="utf-8-sig", parse_dates=["fecha_ref"])
llegadas["i"] = llegadas["institucion_del_cargo"].map(sin_tildes)
MINISTERIOS = set(llegadas["i"])
# Jefes de cada organismo: quien FIRMA sus designaciones es su titular. Cada firmante nuevo (con 2 o más firmas, para no
# contar nombres mal escritos) es un cambio de jefe. No se usan las designaciones J3 del organismo: OTASS, por ejemplo,
# designa a los gerentes de muchas empresas de agua, y eso no son cambios de jefe de OTASS (corregido el 31/10/2026)
es_suprema = (mov["firmante1_cargo"].fillna("").str.contains("President", case=False)
              & mov["firmante1_cargo"].fillna("").str.contains(r"Rep[úu]blica", case=False))
firmas = mov[(mov["en_analisis_principal"] == "True") & mov["tipo_movimiento"].isin(ENTRADA) & ~es_suprema
             & mov["firmante1_nombre"].notna()].copy()
firmas["i"] = firmas["institucion_del_cargo"].map(sin_tildes)
firmas["firmante"] = firmas["firmante1_nombre"].map(sin_tildes)
primeras_firmas = firmas.groupby(["i", "firmante"])["fecha_ref"].agg(["min", "size"]).reset_index()
primeras_firmas = primeras_firmas[(primeras_firmas["size"] >= 2) & ~primeras_firmas["i"].isin(MINISTERIOS)]
llegadas_jefe = pd.concat([llegadas[["i", "fecha_ref"]].assign(firmante=""),
                           primeras_firmas.rename(columns={"min": "fecha_ref"})[["i", "fecha_ref", "firmante"]]])
jefes_por_institucion = {i: (g["fecha_ref"].values, g["firmante"].values) for i, g in llegadas_jefe.groupby("i")}

titulares = periodos[periodos["ambito"] == "confianza y directivos"].copy()
titulares["tipo_de_jefe"] = np.where(titulares["institucion_del_cargo"].map(sin_tildes).isin(MINISTERIOS), "ministros", "titulares de la entidad")


def jefes_que_llegaron(institucion, inicio, fin, persona):
    """Antes: institución, periodo y persona | Después: cuántos jefes nuevos (ministros, o firmantes nuevos en un organismo)
    llegaron mientras la persona seguía en el puesto (sin contarse a sí misma si ella firmaba)"""
    if sin_tildes(institucion) not in MINISTERIOS:
        return -1          # organismo o programa: no se calcula (ver nota del encabezado)
    if sin_tildes(institucion) not in jefes_por_institucion:
        return 0
    fechas, firmantes = jefes_por_institucion[sin_tildes(institucion)]
    return int(((fechas > np.datetime64(inicio)) & (fechas < np.datetime64(fin)) & (firmantes != persona)).sum())


titulares["jefes_que_llegaron"] = [jefes_que_llegaron(i, a, b, c) for i, a, b, c in
                                   zip(titulares["institucion_del_cargo"], titulares["inicio"], titulares["fin"], titulares["clave_persona"])]
titulares["sigue"] = titulares["censurado"]
# 3 años o más en el mismo puesto; entre ellos, más ministros vistos pasar primero (y luego más días)
permanencia = (titulares[titulares["dias"] >= 3 * 365].sort_values(["dias", "jefes_que_llegaron"], ascending=False)
               .drop_duplicates("clave_persona").reset_index(drop=True))
permanencia.insert(0, "puesto_ranking", permanencia.index + 1)
permanencia = permanencia[["puesto_ranking", "clave_persona", "id_persona", "institucion_del_cargo", "entidad_del_cargo",
                           "unidad_organica", "jerarquia_puesto", "inicio", "fin", "dias", "sigue", "tipo_de_jefe",
                           "jefes_que_llegaron", "puesto", "codigo_norma", "enlace_web", "enlace_pdf"]]
permanencia.to_csv(INDICADORES / "ranking_permanencia.csv", index=False, encoding="utf-8-sig")
print(f"     Permanencia: personas con 3+ años en el mismo puesto de titular: {len(permanencia)} | "
      f"siguen desde fines de 2022: {(permanencia['sigue'] & (permanencia['inicio'] < '2023-01-01')).sum()}")

# ============================================================
# PROCESO 16.11.4: Excel de trabajo con nombres (privado, no se publica)
# Insumo:    los dos rankings y las trayectorias
# Resultado: datos/privado/rankings_rotacion_permanencia.xlsx
# ============================================================
top_rotacion = rotacion.head(50)
detalle = (trayectorias[trayectorias["clave_persona"].isin(top_rotacion["clave_persona"])]
           .merge(top_rotacion[["clave_persona", "puesto_ranking"]], on="clave_persona")
           .sort_values(["puesto_ranking", "inicio"]))
detalle["duracion"] = detalle["dias"].map(duracion)
with pd.ExcelWriter(PRIVADO / "rankings_rotacion_permanencia.xlsx") as excel:
    top_rotacion.assign(nombre=top_rotacion["clave_persona"].str.title())[
        ["puesto_ranking", "nombre", "id_persona", "cargos_en_12_meses", "cargos", "instituciones", "mediana_dias",
         "primer_cargo", "ultimo_cargo", "recorrido"]].to_excel(excel, sheet_name="rotación (50)", index=False)
    detalle.assign(nombre=detalle["clave_persona"].str.title())[
        ["puesto_ranking", "nombre", "institucion_del_cargo", "cargo", "jerarquia_puesto", "inicio", "fin", "dias", "duracion",
         "abierto", "codigo_norma", "enlace_web"]].to_excel(excel, sheet_name="rotación - cargos", index=False)
    permanencia.head(50).assign(nombre=permanencia.head(50)["clave_persona"].str.title())[
        ["puesto_ranking", "nombre", "id_persona", "institucion_del_cargo", "entidad_del_cargo", "unidad_organica",
         "jerarquia_puesto", "inicio", "fin", "dias", "sigue", "tipo_de_jefe", "jefes_que_llegaron", "codigo_norma", "enlace_web"]].to_excel(excel, sheet_name="permanencia (50)", index=False)
    por_ministros = permanencia[permanencia["jefes_que_llegaron"] >= 0].sort_values(["jefes_que_llegaron", "dias"], ascending=False).head(50)
    por_ministros.assign(nombre=por_ministros["clave_persona"].str.title())[
        ["nombre", "id_persona", "institucion_del_cargo", "unidad_organica", "jerarquia_puesto", "inicio", "fin", "dias", "sigue",
         "jefes_que_llegaron"]].to_excel(excel, sheet_name="permanencia por ministros", index=False)
print("     Excel privado:", PRIVADO / "rankings_rotacion_permanencia.xlsx")
