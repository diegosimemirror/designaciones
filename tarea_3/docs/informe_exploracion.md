# Informe de exploración — Designaciones de El Peruano

Periodo: normas publicadas del **01/11/2022 al 29/10/2026** (cuatro años). Fuente: diario oficial El Peruano
(índice de designaciones + listado general de normas + texto de cada PDF oficial).
Los números detallados están en `exploracion_resultados.md` (generado por `scripts/05_explorar_base.py`).
Las columnas nuevas están en `movimientos_analisis.csv` (script `06_preparar_analisis.py`): ninguna columna original
se modificó.

Los periodos van de noviembre a octubre: **nov22-oct23**, **nov23-oct24**, **nov24-oct25** y **nov25-oct26**.
La base se construyó en tres tramos (primero nov24-oct26, luego nov23-oct24 y por último nov22-oct23); en cada
ampliación se comprobó que los periodos ya revisados salieran idénticos, salvo las mejoras indicadas en la sección 3.

## 1. Qué hay en la base

| Tabla | Filas | Columnas | Qué es cada fila |
|---|---|---|---|
| `normas.csv` | 27.183 | 54 | una norma (resolución, decreto, acuerdo) |
| `movimientos.csv` | 46.892 | 41 | una persona en un movimiento (una norma puede tener varios) |
| `movimientos_analisis.csv` | 46.892 | 63 | lo mismo + 22 columnas nuevas para el análisis |

| | nov22-oct23 | nov23-oct24 | nov24-oct25 | nov25-oct26 | Total |
|---|---|---|---|---|---|
| Normas de personal | 7.333 | 5.838 | 5.989 | 8.023 | 27.183 |
| … del índice de designaciones | 5.578 | 4.209 | 4.425 | 6.360 | 20.572 |
| … que el índice omite (solo en el listado general) | 1.755 | 1.629 | 1.564 | 1.663 | 6.611 |
| Movimientos | 14.681 | 9.541 | 10.693 | 11.977 | 46.892 |
| Normas extraídas completas | 93,5 % | 94,4 % | 96,2 % | 97,4 % | 95,4 % |
| PDF con la fuente antigua reparada | 76 | 25 | 0 | 0 | 101 |

- **Tipos de movimiento (4 años):** designación 24.538 · conclusión 10.694 · nombramiento 5.988 · renuncia 3.559 · dejar sin efecto 1.287 · encargatura 489 · otros 337.
- **Picos de normas de personal:** agosto de 2026 (1.202, cambio de gobierno del 28/07/2026), enero de 2023 (907) y diciembre de 2022 (850, tras el cambio de gobierno del 07/12/2022). Un mes normal tiene ≈ 450-600.

### La base mezcla grupos muy distintos (columna `ambito`)

| Ámbito | Movimientos | Normas | ¿Análisis principal? |
|---|---|---|---|
| Cargos de confianza y directivos | 19.893 | — | sí |
| Subprefectos y prefectos | 4.792 | 571 | sí |
| Directorios y consejos (miembros, representantes) | 2.757 | — | sí |
| Servicio diplomático (embajadores, cónsules) | 621 | 585 | sí |
| Procuradores públicos | 112 | 77 | sí |
| Fiscales (Ministerio Público) | 13.168 | 6.723 | no: carrera fiscal |
| Fedatarios, ejecutores coactivos y funcionarios responsables | 1.774 | 834 | no: funciones administrativas |
| Jefes de Órganos de Control Institucional (Contraloría) | 1.714 | 600 | no: carrera de control |
| Fuerzas Armadas y Policía (empleos, comandantes generales) | 933 | 111 | no: carrera militar |
| Poder Judicial y fuero militar | 731 | 347 | no: carrera judicial |
| Comités, comisiones y consejos consultivos | 302 | — | no: funciones encargadas |
| Notarios | 95 | 95 | no: concurso público |

**Análisis principal: 28.175 movimientos de 16.488 personas** (nov22-oct23: 9.885 · nov23-oct24: 5.236 ·
nov24-oct25: 5.481 · nov25-oct26: 7.574). Los subprefectos se concentran en nov22-oct23 (3.437 movimientos, la mayor
parte en diciembre de 2022). Los procuradores no estaban en las listas aprobadas al inicio; se incluyeron porque se
designan como los cargos de confianza.

## 2. Lista de revisión

| # | Qué se revisó | Resultado |
|---|---|---|
| 1 | Tamaño | 27.183 normas y 46.892 movimientos |
| 2 | Muestra de filas | coherentes con el PDF (verificadas a mano en varias rondas, en cada periodo) |
| 3 | Tipos de columna | las fechas venían como texto; en `movimientos_analisis.csv` ya son fechas |
| 4 | Duplicados | 0 normas repetidas; 0 filas repetidas; 684 casos (1.513 filas) de misma persona, mismo tipo y mismo cargo en **dos normas distintas** |
| 5 | Faltantes | nombre 2,6 % · cargo 7,5 % · sexo 26,2 % (11,9 % después de inferirlo) · firmante 0,8 % · fecha de emisión 0,8 %. Sin faltantes disfrazados |
| 6 | Estadísticos | mediana de 1 movimiento por norma (máximo 1.076: subprefectos, diciembre de 2022); mediana de 1 día entre la firma y la publicación |
| 7 | Frecuencias | ver las tablas del punto 1 |
| 8 | Valores únicos | 27 instituciones y 2 sectores escritos con y sin tilde; sin caracteres mal codificados |
| 9 | Fechas | sin huecos; 2 normas "emitidas" después de publicarse y 4 con años imposibles: todas por errores de tipeo del original |
| 10 | Atípicos | 83 normas publicadas más de 60 días después de firmarse; nombres de 7 o más palabras; cargos muy largos |

## 3. Problemas encontrados y qué se hizo

| N.º | Problema | Registros | Qué se hizo | ¿Cambió datos? |
|---|---|---|---|---|
| P1 | Normas ilegibles: 2 PDF escaneados (ATU y MIDIS) y 1 norma de Migraciones cuyo PDF no trae la página donde está | 3 normas | Se dejan marcadas | No |
| P1b | Publicaciones digitales de municipalidades de Lima: el código va en la cabecera ("OP N°"), no al final; en 2024 además sin la cabecera "FUNDADO EL 22 DE OCTUBRE" y con numeración de líneas | 50 normas (nov24-oct25) + 19 (nov23-oct24) | **Corregido en el extractor**: ahora se leen | No (se recuperaron) |
| P2 | Normas sin movimientos: comités sin nombres, ratificaciones genéricas y textos desordenados por las columnas del diario | 195 normas | Dejar | No |
| P3 | Movimientos sin nombre: el artículo no menciona a la persona ("Designar al Gerente de TI como responsable…") | 1.239 (2,6 %) | Se cuentan por institución y fecha; no entran al análisis de personas | No |
| P4 | Fuerzas Armadas: tablas de empleos con abreviaturas (GRAL BRIG, CMDTE) de las que salen nombres equivocados | 933 movimientos (111 normas) | Ámbito aparte, fuera del análisis principal | No |
| P5 | Sexo vacío (tablas y listas sin "señor/señora") | 12.308 (26,2 %) | Columna nueva `sexo_inferido` con el nombre de pila (ver punto 4). Se completaron 6.718; 5.590 quedan sin dato | Agrega columna |
| P6 | Institución escrita de dos formas o con "Publicación Digital" | 4.693 filas (216 → 184 instituciones) | Columna nueva `institucion_normalizada` | Agrega columna |
| P7 | Sector vacío; y sector escrito sin tilde en el índice de 2022-2023 ("ORGANISMOS AUTONOMOS") | 38 vacíos; 1.065 sin tilde | Columna nueva `sector_completado`: regla aprobada para los vacíos (gobierno regional, municipalidad, organismos autónomos) y una sola escritura por sector | Agrega columna |
| P8 | Fechas de firma imposibles por errores de tipeo del original: SUSALUD ("2021" en una resolución de 2026), INIA ("20025"), Interior ("20024"), MIDIS (dos con "2024" en resoluciones de 2022 y 2023) y MIDAGRI ("2013" en una de 2023) | 6 normas | Columna nueva `fecha_emision_corregida` + `nota_fecha`, verificadas en el texto del PDF | Agrega columna |
| P9 | Publicaciones tardías (sobre todo municipalidades: San Martín de Porres publicó en 2026 resoluciones de 2023) | 83 normas | Dejar: es un hecho real | No |
| P10 | Subprefectos: el nombre quedaba pegado a la ubicación. (a) 2024-2026: la tabla pierde la numeración ("COTAHUASI LA UNION AREQUIPA + nombre"); (b) 2022-2023: cada celda va en su línea (Región, Provincia, Distrito, Nombre, Apellidos, DNI) y algunas celdas se parten en dos líneas ("SAN JUAN DE" / "LOPECANCHA") | (a) 111 nombres; (b) ≈ 1.450 nombres en 13 normas | **Corregido en el extractor**: (a) se corta en el departamento; (b) se reordena cada fila antes de unir las líneas y se reconstruyen las celdas partidas comparando con las regiones y provincias ya vistas. Quedan ≈ 60 nombres dudosos (celdas partidas a mitad de palabra) | No (se corrigieron) |
| P11 | Cargos muy largos (sobre todo fiscales) o mal recortados ("Regístrese…", "en el cargo de confianza de las EPS…") | ≈ 2.000 largos | El nivel del cargo usa el comienzo del texto | No |
| P12 | Nombres dudosos: empiezan con un cargo ("GERENTE DE … + nombre"), tienen 7 o más palabras o una sola | 871 filas (139 en el análisis principal) | Columna `nombre_dudoso` para excluirlos del análisis de redes o revisarlos | Agrega columna |
| P13 | Misma persona, mismo tipo y mismo cargo en dos normas distintas | 684 casos (1.513 filas) | No borrar: pueden ser encargos repetidos o normas que se dejan sin efecto y se vuelven a emitir | No |
| P14 | Grupos de distinta naturaleza mezclados | toda la base | Columnas `ambito` y `en_analisis_principal` | Agrega columna |
| P15 | Tablas de Contraloría de nov24-oct25 sin coma entre entidad y nombre ("MUNICIPALIDAD DISTRITAL DE LA JOYA + apellidos y nombres") | ≈ 120 filas | Quedan en el ámbito OCI, fuera del análisis principal; el DNI sí identifica a la persona | No |
| P16 | Representantes y miembros ante comisiones o directorios clasificados como cargos de confianza: el "cargo" extraído es su oficina de origen ("de la Dirección General de Contabilidad Pública") | 72 movimientos (27 normas) en nov24-oct26; la regla se aplica a los cuatro años | **Reclasificados por función (aprobado el 30/10/2026)**: 59 a "comités y comisiones" (comisiones evaluadoras y especiales, cuerpos colegiados ad hoc, consejos consultivos u honoríficos) y 13 a "directorios y consejos" (directorios y consejos directivos que gobiernan una entidad). Caso revisado a mano: Comité Directivo Nacional del Trabajo Infantil → comités | Cambia `ambito` |
| P17 | Comisiones organizadoras de universidades cuyo cargo solo dice "Presidente" o "Vicepresidente Académico" (la comisión está en la sumilla) | 42 movimientos en nov24-oct26; la regla se aplica a los cuatro años | Pasan de "confianza y directivos" a "directorios y consejos": la comisión organizadora gobierna la universidad (mismo criterio de P16). Siguen en el análisis principal | Cambia `ambito` |
| P18 | Fuente antigua del diario (2022-2024): las mayúsculas A, D, E, N, O, U se leen como minúsculas ("deSIGnaR", "Se ReSueLVe", "RoSa eLena", "a la profesional andrea Matos") | 101 normas (76 de nov22-oct23 y 25 de nov23-oct24); ninguna desde nov-2024 | **Reparado antes de extraer**, solo en los textos con 5 o más palabras distintas dañadas; columna `fuente_reparada` en `normas.csv` | No (se recuperaron) |
| P19 | El listado general cambió el formato de sus enlaces (hasta 2023: `/normaslegales/<título>-<código>/`, `/download/url/…` y `/NormasElperuano/<fecha>/<código>/<código>.htm`) | todo nov22-oct23 | **Corregido en el script 01b**: el código se lee al final del enlace; la edición, del enlace "Todo el cuadernillo" | No |
| P20 | Tratamientos que el extractor no reconocía: "médico cirujano", "colaborador(a)", "magistrado(a)", "consejero(a)" | ≈ 190 nombres recuperados o limpiados (11 decían "CIRUJANO …" en nov24-oct26) | **Agregados al extractor** | Mejora nombres ya revisados |
| P21 | "Presidencia del Consejo de Ministros" se confundía con un consejo directivo: asesores, viceministros, el Secretario General y el propio Presidente del Consejo de Ministros quedaban como "directorios y consejos" | 266 movimientos | **Corregido (aprobado el 31/10/2026)**: 265 pasan a "confianza y directivos" y 1 a comités | Cambia `ambito` |
| P22 | Nombres genéricos tomados como oficina: categorías de plaza ("Jefa de Oficina I", "Jefe de Unidad II"), "Director de Órgano Desconcentrado de la Dirección Desconcentrada de Cultura de Ucayali", oficinas desconcentradas sin la ciudad, títulos como "administrador II del Centro Juvenil…" o "jefe/a de Seguridad del…"; organismos del sector (CENEPRED, CAEN) leídos como oficinas | ≈ 400 movimientos | **Corregido en la ubicación** (`unidad_organica`, `nivel_organizacional`, `jerarquia_puesto`) y nueva columna `entidad_del_cargo` (programa u organismo del puesto) | Cambia columnas nuevas |

## 4. Columnas nuevas (`movimientos_analisis.csv`)

| Columna | Qué es | Cómo se obtuvo |
|---|---|---|
| `institucion_normalizada` | una sola escritura por institución | la escritura más frecuente entre las que solo cambian en tildes |
| `sector_completado` | sector de El Peruano, sin vacíos | `sector_ep` + regla para 33 filas |
| `fecha_publicacion_dt`, `fecha_emision_corregida`, `nota_fecha` | fechas como fecha | conversión + 2 correcciones verificadas en el PDF |
| `ambito`, `en_analisis_principal` | tipo de designación y si entra al análisis principal | reglas sobre cargo, institución, artículo y sumilla |
| `primer_nombre`, `sexo_inferido`, `sexo_analisis`, `sexo_origen` | sexo para el análisis de género | se aprende de la misma base: un nombre de pila se usa si aparece 3 o más veces con "señor/señora" y el 95 % o más coincide. `sexo_origen` dice si viene de la norma o es inferido |
| `clave_persona`, `id_persona`, `nombre_dudoso` | identificador de persona | nombre sin tildes ni signos; homónimos con DNI distinto se separan (no hubo). `id_persona` es un código de persona (P-XXXXX) tomado del registro maestro privado: aleatorio y estable, sirve para publicar sin nombres |
| `nivel_cargo` | nivel jerárquico | reglas sobre el comienzo del cargo con tus categorías: MIN, VMIN, SECGEN, JEFEGAB, ASES, DIRGEN, DIR, JEFE, GERGEN, PRES, SUPER, MIEMBRO (+ OTRO y SIN CARGO). Supuestos: "Director Ejecutivo" = DIRGEN; gerente (no general), subgerente, coordinador, supervisor, ejecutivo e intendente = JEFE |
| `institucion_del_cargo` | ministerio al que pertenece el puesto | igual a `institucion_normalizada`, salvo los 225 ministros, que se publican bajo la PCM y se leen del cargo ("Ministro de Estado en el Despacho de Salud" → SALUD) |
| `nivel_organizacional` | nivel dentro de su entidad: N1 alta dirección, N2 órganos que dependen de ella, N3 unidades orgánicas, N4 subunidades; además "órgano colegiado" (directorios), "territorial o exterior" (subprefectos, embajadores) y "sin dato" | cadena de órganos que trae el cargo; si el cargo nombra un solo órgano que no es "General", se asume su nivel típico (en ministerios, una dirección u oficina es N3). Validado con el ROF de MIDIS e Interior (`docs/validacion_rof.md`) |
| `unidad_organica`, `unidad_superior` | oficina donde está el puesto y la oficina de la que depende | primer y segundo órgano de la cadena del cargo |
| `ubicacion` | tipo de entidad: sede central del ministerio, programa o proyecto, órgano desconcentrado, organismo público, empresa pública, gobierno regional, municipalidad, organismo autónomo, prefecturas, servicio exterior | sector de El Peruano, ámbito y entidades nombradas en el cargo |
| `jerarquia_puesto` | peso del puesto **sobre el papel** (distinto de dónde está): J1 ministro, J2 viceministro, J3 secretario general, jefe de gabinete o titular de un organismo o programa, J4 director general o jefe de órgano, J5 asesor o apoyo de alta dirección, J6 jefe de unidad orgánica, J7 subunidad o apoyo. Es referencial: en la práctica el peso depende de más cosas | nivel_cargo + nivel_organizacional + si el título es de apoyo ("Adjunto", "Asesor", "Especialista"). Contraste con el nivel remunerativo que traen 1.158 movimientos (4 años): J3 F-5,8 · J4 F-4,9 · J5 F-4,8 · J6 F-3,8 · J7 F-2,8. **J4 y J5 casi no se distinguen por remuneración** (en Trabajo los asesores tienen F-5,0 y los directores generales F-4,4): que un director general pese más que un asesor se sostiene en que dirige un órgano, no en lo que gana |
| `nivel_remunerativo` | nivel F-1 a F-8, tal como lo dice la norma | solo 1.158 movimientos del análisis principal lo mencionan (sobre todo MINSA, Justicia y Trabajo) |

Nivel del cargo en el análisis principal: JEFE 4.089 · DIR 1.855 · ASES 1.456 · DIRGEN 913 · MIEMBRO 737 · PRES 275 ·
VMIN 246 · MIN 227 · GERGEN 147 · SECGEN 119 · JEFEGAB 70 · SUPER 55 · OTRO 2.076 (subprefectos, embajadores,
procuradores y cargos sin categoría) · SIN CARGO 852.

## 5. Limitaciones que no se pueden corregir con estos datos

- **Homónimos:** solo el 8,6 % de los movimientos trae DNI. Dos personas con el mismo nombre completo se cuentan como una.
- **Variantes del mismo nombre** ("MARÍA DEL PILAR" / "MARIA PILAR", con o sin segundo nombre) se cuentan como personas distintas.
- **Nombres de tablas y listas** (`metodo_nombre` distinto de "tratamiento", 20 % de los movimientos) son menos confiables.
- **Sexo inferido:** 2.327 movimientos quedan sin dato (nombres poco frecuentes o ambiguos); en tablas "APELLIDOS NOMBRES" sin coma la primera palabra es un apellido y casi siempre queda sin dato.
- **Ubicación en la estructura (etapa 1):** se deduce del texto del cargo, no del ROF de cada entidad. Validada en MIDIS e Interior; en otros ministerios puede fallar donde la nomenclatura es distinta (el ROF de Educación, anterior a los Lineamientos, usa "Unidades" en la sede central). 106 cargos con "Unidad" quedaron como sede central; en MIDIS son, casi seguro, unidades de programas cuyo cargo no nombra el programa. El ROF cambia con frecuencia (426 normas sobre ROF en tres años): se usó la versión vigente, no la de cada fecha. 999 movimientos del análisis principal quedan "sin dato" (la mayoría sin cargo o con cargo ilegible).
- **Los visados** identifican oficinas, no personas: la red "quién propone a quién" solo se puede armar con los **firmantes**.
- **El índice oficial omite** las resoluciones supremas de ministros y otros cargos altos; por eso se usó también el listado general.
