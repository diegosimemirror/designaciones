# Diccionario de datos — Designaciones de El Peruano

Fuentes: **ÍNDICE** = servicio de designaciones de El Peruano; **LISTADO** = listado general de normas (trae las que el índice omite, como ministros y embajadores); **PDF** = texto oficial de la norma; **DERIVADO** = calculado a partir de lo anterior.

Una celda vacía significa que la norma no trae ese dato o que la regla de extracción no lo encontró.

## movimientos.csv — una fila por persona y movimiento

Filas: 46,892

| Columna | Qué significa | Fuente | % con dato | Ejemplo |
|---|---|---|---|---|
| `id_movimiento` | Código único del movimiento: código de la norma + # + orden dentro de la norma | DERIVADO | 100.0 % | 2538840-2#1 |
| `codigo_norma` | Código de El Peruano que figura al pie de la norma; une esta tabla con normas.csv | ÍNDICE / LISTADO | 100.0 % | 2538840-2 |
| `fecha_publicacion` | Fecha en que la norma salió en el diario | ÍNDICE / LISTADO | 100.0 % | 30/07/2026 |
| `fecha_emision` | Fecha en que la entidad emitió la resolución | PDF | 99.2 % | 2026-07-30 |
| `sector_ep` | Agrupación que usa El Peruano (Poder Ejecutivo, organismos autónomos...) | ÍNDICE; si falta, según la institución | 99.9 % | PODER EJECUTIVO |
| `institucion` | Institución que publica la norma | ÍNDICE / LISTADO | 100.0 % | DEFENSA |
| `dispositivo` | Tipo y número de la norma | ÍNDICE / LISTADO | 100.0 % | RESOLUCIÓN MINISTERIAL N° 00909-2026-DE |
| `sumilla` | Título breve con que se publica la norma | LISTADO | 100.0 % | Designan Jefa de Gabinete del Despacho Ministerial |
| `articulo` | Artículo de la norma del que sale el movimiento | PDF | 99.1 % | 1 |
| `tipo_movimiento` | designación, encargatura, renuncia, conclusión, dejar sin efecto, nombramiento, asignación de funciones, ratificación, rotación o reasignación, prórroga (según el primer verbo del artículo) | PDF | 100.0 % | renuncia |
| `temporal` | La norma dice 'temporal' o 'temporalmente' | PDF | 100.0 % | True |
| `objeto_conclusion` | En conclusiones: qué se da por concluido (designación, encargo, nombramiento, funciones) | PDF | 18.0 % | designación |
| `nombre_tal_cual` | Nombre de la persona tal como aparece en la norma (algunas tablas lo escriben APELLIDOS, NOMBRES) | PDF | 97.4 % | NOMBRE APELLIDO APELLIDO |
| `nombre_normalizado` | El mismo nombre en mayúsculas, sin tildes ni signos y siempre en orden NOMBRES APELLIDOS, para comparar entre normas | DERIVADO | 97.4 % | NOMBRE APELLIDO APELLIDO |
| `metodo_nombre` | Cómo se encontró el nombre. 'tratamiento' (después de señor/señora...) es lo más confiable; tablas y listas, menos | DERIVADO | 97.4 % | tratamiento |
| `tratamiento` | Palabras que preceden al nombre | PDF | 73.8 % | señora / abogado / servidor |
| `sexo_segun_norma` | F o M según el tratamiento y el artículo (la/el). No es autoidentificación; vacío si no se puede saber | DERIVADO | 73.8 % | F |
| `profesion_mencionada` | Profesión que la norma antepone al nombre | PDF | 29.3 % | abogada |
| `grado_militar_policial` | Grado militar, policial o rango diplomático | PDF | 1.6 % | Teniente General FAP |
| `dni` | DNI, solo cuando la norma lo publica (sobre todo tablas de subprefectos) | PDF | 13.8 % | (8 dígitos) |
| `ubicacion_tabla` | En tablas con DNI: distrito, provincia y departamento que siguen al DNI (subprefectos) o entidad que precede al nombre (Contraloría) | PDF | 11.8 % | HUANCAYO JUNIN |
| `cargo` | Cargo tal como lo escribe la norma (en tablas, la columna de cargo; en fiscales, 'cargo — despacho') | PDF | 92.5 % | Jefa de Gabinete del Despacho Ministerial del Ministerio de Defensa |
| `cargo_actual_mencionado` | Cargo que la persona ya ocupaba, si la norma lo menciona junto al nombre | PDF | 9.4 % | Viceministro de Pesca y Acuicultura |
| `en_adicion_a_funciones` | Asume el cargo sin dejar el que ya tenía | PDF | 100.0 % | True |
| `funciones_que_mantiene` | Funciones que conserva cuando es 'en adición' | PDF | 0.4 % | ejecutiva de recursos humanos |
| `fecha_efectividad` | Desde cuándo rige el movimiento, si la norma lo dice; vacío = rige desde su publicación | PDF | 17.5 % | 2025-11-05 |
| `fecha_fin` | Fin del encargo (del X al Y) o último día de labores, si la norma lo dice | PDF | 1.8 % | 2026-01-08 |
| `inicio_texto` | Frase original sobre el inicio | PDF | 23.9 % | a partir de la fecha de publicación |
| `condicion_texto` | Condiciones del movimiento | PDF | 2.7 % | en tanto se designe al titular |
| `agradecimiento` | La norma agradece los servicios prestados | PDF | 100.0 % | True |
| `norma_antecedente` | Norma con la que se había designado a la persona (o la que se deja sin efecto) | PDF | 22.7 % | Resolución Suprema N° 118-2026-PCM |
| `en_tabla_con_dni` | El nombre salió de una tabla con DNI | DERIVADO | 100.0 % | False |
| `texto_articulo` | Texto del artículo (hasta 1.500 caracteres), para verificar a mano | PDF | 100.0 % | Designar a la señora ... |
| `firmante1_nombre` | Primer firmante de la norma (2 y 3 si hay más, p. ej. el ministro que refrenda) | PDF | 99.2 % | NOMBRE APELLIDO APELLIDO |
| `firmante1_cargo` | Cargo del primer firmante | PDF | 99.1 % | Presidenta de la República |
| `enlace_pdf` | Enlace al PDF oficial | ÍNDICE / LISTADO | 100.0 % | https://epdoc2.elperuano.pe/... |
| `enlace_web` | Enlace a la ficha web de la norma | ÍNDICE / LISTADO | 100.0 % | https://busquedas.elperuano.pe/... |

## normas.csv — una fila por norma

(Las columnas de fecha, institución, dispositivo, sumilla, firmantes y enlaces son las mismas de movimientos.csv; el % se calcula sobre las normas con texto descargado.)

Filas: 27,183

| Columna | Qué significa | Fuente | % con dato | Ejemplo |
|---|---|---|---|---|
| `codigo_norma` | Código de El Peruano al pie de la norma (llave) | ÍNDICE / LISTADO | 100.0 % | 2538840-2 |
| `fuente` | De dónde vino la norma: 'índice' de designaciones o 'listado general' (normas que el índice no tenía) | DERIVADO | 100.0 % | listado general |
| `edicion` | Edición ordinaria, extraordinaria o publicación digital | LISTADO | 100.0 % | extraordinaria |
| `cargo_indice` | Cargo según el índice de El Peruano | ÍNDICE | 75.7 % | Jefa de Gabinete... |
| `tipo_indice` | Tipo según el índice: designación o renuncia/conclusión | ÍNDICE | 75.7 % | designación |
| `lugar_emision` | Ciudad o distrito donde se emitió | PDF | 99.2 % | Lima |
| `vistos_texto` | Texto de la sección VISTOS | PDF | 68.8 % | El Oficio N° ... de la Secretaría General... |
| `documentos_sustento` | Documentos citados como sustento, con la oficina que los emitió | PDF | 36.6 % | Informe N° ... de la Oficina de Recursos Humanos |
| `n_documentos_sustento` | Cuántos documentos de sustento cita | DERIVADO | 100.0 % | 3 |
| `visado_texto` | Frase de visado (oficinas que revisaron la norma) | PDF | 40.1 % | de la Secretaría General, de RR.HH. y de Asesoría Jurídica |
| `oficinas_visado` | Lista de oficinas que visaron, separadas por | | DERIVADO | 40.1 % | Secretaría General | Oficina de Asesoría Jurídica |
| `n_oficinas_visado` | Cuántas oficinas visaron | DERIVADO | 40.1 % | 3 |
| `propuesta_texto` | Quién propuso o solicitó la designación, si la norma lo dice | PDF | 15.1 % | Estando a lo propuesto por el Ministro de Defensa |
| `motivo_vacante` | Los considerandos dicen que el cargo está vacante | PDF | 100.0 % | True |
| `motivo_conveniente` | Los considerandos dicen 'por conveniente' (decisión discrecional) | PDF | 100.0 % | True |
| `menciona_renuncia` | Los considerandos mencionan una renuncia | PDF | 100.0 % | True |
| `motivo_texto` | Frase del motivo | PDF | 63.0 % | se encuentra vacante el cargo de... |
| `cita_ley_31419_idoneidad` | Cita la Ley 31419 (idoneidad de funcionarios de libre designación) | PDF | 100.0 % | True |
| `verificacion_perfil_texto` | Frase sobre el cumplimiento del perfil o requisitos | PDF | 34.4 % | cumple con los requisitos... |
| `tipo_cargo_mencionado` | Tipo de cargo que menciona: de confianza, libre designación y remoción, directivo superior, funcionario público | PDF | 48.7 % | cargo de confianza |
| `nivel_remunerativo` | Nivel remunerativo (escala de sueldo), si lo menciona | PDF | 4.1 % | F-5 |
| `menciona_cap` | Menciona el CAP (Cuadro para Asignación de Personal: lista oficial de plazas) | PDF | 100.0 % | True |
| `numero_plaza` | Número de plaza o de orden en el CAP | PDF | 0.7 % | 931 |
| `regimen_laboral_mencionado` | Régimen laboral citado (CAS 1057, 276, 728, Servicio Civil 30057) | PDF | 15.0 % | CAS (D. Leg. 1057) |
| `base_legal_texto` | Frase 'De conformidad con...' / 'En uso de...' | PDF | 93.6 % | De conformidad con la Ley N° 27594... |
| `leyes_citadas` | Leyes y decretos legislativos citados, separados por | | PDF | 92.8 % | Ley N° 27594 | Ley N° 31419 |
| `facultad_delegada` | Menciona facultades delegadas | PDF | 100.0 % | False |
| `refrendo` | Quién refrenda (en resoluciones supremas) | PDF | 8.4 % | Presidente del Consejo de Ministros |
| `personas_en_considerandos` | Personas nombradas en los considerandos (p. ej. quien ocupaba antes el cargo) | PDF | 64.3 % | NOMBRE APELLIDO |
| `firmante1_encargado` | El firmante firma como encargado (e) o interino (i) | PDF | 98.7 % | True |
| `n_movimientos` | Cuántos movimientos se extrajeron de la norma | DERIVADO | 100.0 % | 2 |
| `n_sin_nombre` | Cuántos de esos movimientos no tienen nombre | DERIVADO | 100.0 % | 0 |
| `estado_extraccion` | ok / revisar: movimiento sin nombre / sin movimientos detectados / sin texto descargado | DERIVADO | 100.0 % | ok |
| `fuente_reparada` | True si el PDF tenía la fuente antigua que lee algunas mayúsculas como minúsculas ("deSIGnaR") y el texto se reparó antes de extraer | DERIVADO | 100.0 % | False |
| `texto_norma` | Texto completo de la norma | PDF | 100.0 % | ... |
