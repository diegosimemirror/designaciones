# ============================================================
# Designaciones de El Peruano — Registro maestro de seudónimos (acordado con el autor el 01/11/2026)
# ------------------------------------------------------------
# Cada persona recibe UN código estable (por ejemplo, P-7K3QF). La tabla que une código y nombre es PRIVADA
# (datos/privado/, excluida de GitHub) y es la única forma de volver del código al nombre.
#
# Reglas:
#   1) Un código se asigna una sola vez y nunca cambia ni se reutiliza: el registro solo crece. Así los códigos publicados
#      siguen valiendo cuando se amplía el periodo de la base (por ejemplo, 2018-2022).
#   2) Los códigos son aleatorios (no revelan orden ni fecha), con letras y números que no se confunden (sin 0/O ni 1/I).
#   3) Misma persona = misma clave normalizada (nombre sin tildes ni signos) o un alias registrado. El DNI solo se usa
#      cuando la propia norma lo trae: un DNI distinto separa homónimos (ya viene en la clave como "#DNI") y un mismo DNI
#      con otra escritura del nombre se registra como alias.
#   4) Si después se descubre que dos códigos eran la misma persona, NO se renumera: se anota estado = "fusionado" y
#      fusionado_en = código que queda. Si un código mezclaba a dos homónimos, el segundo recibe un código nuevo.
#   5) Solo este módulo crea códigos; las tablas de análisis solo los consultan. Correrlo dos veces no cambia nada.
#   6) Los casos dudosos (tratamiento pegado al nombre, textos que no parecen personas, homónimos) van a una lista de
#      revisión: no se unen ni se separan sin que el autor lo decida.
#
# Archivos (privados):
#   datos/privado/registro_personas.csv  codigo, nombre_completo, clave_normalizada, dni, primera_aparicion, origen,
#                                        alta, estado, fusionado_en, nota
#   datos/privado/alias_personas.csv     alias (otra clave de la misma persona), codigo, motivo, alta
#   datos/privado/revision_personas.csv  casos para revisar a mano (se reescribe en cada corrida)
# Respaldo: guardar una copia del registro en un lugar privado (por ejemplo, Drive con acceso restringido); si se pierde,
# los códigos nuevos no coincidirían con los ya publicados.
# ============================================================

# --- Paquetes ---
# re: reconocer tratamientos pegados al nombre y textos que no son personas
import re
# secrets: generar códigos aleatorios no predecibles
import secrets
# datetime.date: fecha de alta de cada código
from datetime import date
# pathlib: rutas
from pathlib import Path
# pandas: leer y escribir el registro como tabla
import pandas as pd

CARPETA = Path(__file__).resolve().parent.parent / "datos" / "privado"
CARPETA.mkdir(parents=True, exist_ok=True)
REGISTRO = CARPETA / "registro_personas.csv"
ALIAS = CARPETA / "alias_personas.csv"
REVISION = CARPETA / "revision_personas.csv"
ALFABETO = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
COLUMNAS = ["codigo", "nombre_completo", "clave_normalizada", "dni", "primera_aparicion", "origen", "alta", "estado",
            "fusionado_en", "nota"]
TRATAMIENTO = r"^(?:SENORA?|INGENIER[OA]|LICENCIAD[OA]|DOCTOR[A]?|ABOGAD[OA]|Y (?:FINANZAS|COMUNICACIONES|MANTENIMIENTO))\s+"
NO_ES_PERSONA = r"PORTAL (?:DE|WEB)|TRANSPARENCIA|LABORES|^LEY D|^PROCEDIMIENTO|^SENOR GENERAL|^LICENCIADO CC$"


def _leer(ruta, columnas):
    if ruta.exists():
        return pd.read_csv(ruta, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    return pd.DataFrame(columns=columnas)


def _codigo_nuevo(usados):
    """Antes: códigos ya usados | Después: un código aleatorio P-XXXXX que no se haya usado nunca"""
    while True:
        codigo = "P-" + "".join(secrets.choice(ALFABETO) for _ in range(5))
        if codigo not in usados:
            usados.add(codigo)
            return codigo


def asignar(personas, origen):
    """Antes: tabla con clave_persona, nombre_completo, dni y primera_aparicion (una fila por persona)
    | Después: diccionario clave -> código. Las claves nuevas se agregan al registro; los códigos existentes no cambian."""
    registro = _leer(REGISTRO, COLUMNAS)
    alias = _leer(ALIAS, ["alias", "codigo", "motivo", "alta"])
    # Código vigente: si un código fue fusionado en otro, se usa el que queda
    vigente = {c: (f or c) for c, f in zip(registro["codigo"], registro["fusionado_en"])}
    codigo_de = dict(zip(registro["clave_normalizada"], registro["codigo"]))
    codigo_de.update(dict(zip(alias["alias"], alias["codigo"])))
    dni_a_codigo = {d: c for c, ds in zip(registro["codigo"], registro["dni"]) for d in str(ds).split(";") if d}
    usados = set(registro["codigo"])
    hoy = date.today().isoformat()
    nuevos, alias_nuevos = [], []
    for p in personas.sort_values("primera_aparicion").itertuples(index=False):
        clave = p.clave_persona
        if not clave or clave in codigo_de:
            continue
        dni = str(p.dni or "")
        if dni and dni in dni_a_codigo:                    # mismo DNI, otra escritura del nombre: misma persona
            codigo_de[clave] = dni_a_codigo[dni]
            alias_nuevos.append({"alias": clave, "codigo": dni_a_codigo[dni], "motivo": "mismo DNI en la norma", "alta": hoy})
            continue
        codigo = _codigo_nuevo(usados)
        codigo_de[clave] = codigo
        if dni:
            dni_a_codigo[dni] = codigo
        nuevos.append({"codigo": codigo, "nombre_completo": p.nombre_completo, "clave_normalizada": clave, "dni": dni,
                       "primera_aparicion": str(p.primera_aparicion)[:10], "origen": origen, "alta": hoy,
                       "estado": "activo", "fusionado_en": "", "nota": ""})
    if nuevos:
        registro = pd.concat([registro, pd.DataFrame(nuevos)], ignore_index=True)
        registro.to_csv(REGISTRO, index=False, encoding="utf-8-sig")
    if alias_nuevos:
        alias = pd.concat([alias, pd.DataFrame(alias_nuevos)], ignore_index=True)
        alias.to_csv(ALIAS, index=False, encoding="utf-8-sig")
    _lista_de_revision(registro)
    print(f"     Registro de personas: {len(registro)} códigos ({len(nuevos)} nuevos en esta corrida, origen: {origen}) | "
          f"alias nuevos: {len(alias_nuevos)}")
    return {clave: vigente.get(codigo, codigo) for clave, codigo in codigo_de.items()}


def _lista_de_revision(registro):
    """Antes: registro completo | Después: revision_personas.csv con los casos dudosos (no cambia ningún código)"""
    claves = set(registro["clave_normalizada"])
    filas = []
    for codigo, clave in zip(registro["codigo"], registro["clave_normalizada"]):
        if re.search(NO_ES_PERSONA, clave):
            filas.append((codigo, clave, "no parece una persona (texto de la norma leído como nombre)", ""))
        sin = re.sub(TRATAMIENTO, "", clave)
        if sin != clave:
            filas.append((codigo, clave, "tratamiento pegado al nombre", f"¿misma persona que '{sin}'?" if sin in claves else sin))
        if "#" in clave:
            filas.append((codigo, clave, "homónimo separado por DNI", clave.split("#")[0].strip()))
    pd.DataFrame(filas, columns=["codigo", "clave", "motivo", "sugerencia"]).to_csv(REVISION, index=False, encoding="utf-8-sig")
