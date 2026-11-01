# Designaciones de El Peruano: ¿cambia todo para que no cambie nada?

> Tarea 3 del curso Python Intermedio (D2CML) — *Del dato a la historia: dashboard interactivo y reel con IA*.
> **Estado: en construcción.** Las secciones marcadas como *pendiente* se completan al cerrar el análisis.

## 1. Tema y pregunta de investigación

**Tema:** rotación de funcionarios de confianza en el Estado peruano, a partir de las normas de designación,
conclusión y renuncia publicadas en el diario oficial *El Peruano*.

**Pregunta:** la alta rotación de cargos de confianza, ¿renueva el elenco de funcionarios o hace circular a las
mismas personas entre cargos e instituciones? ¿Quién designa a quién?

**Cobertura:** Perú, normas publicadas desde noviembre de 2022 hasta octubre de 2026 (cuatro años, que incluyen
cinco presidentes y cuatro cambios de gobierno: diciembre de 2022, octubre de 2025, febrero de 2026 y julio de 2026):
27.183 normas de personal y 46.892 movimientos.
Unidad de análisis: una persona en un movimiento (designación, conclusión, renuncia, encargo, nombramiento).

## 2. Descripción del proyecto

1. Se descargan, con código, el índice de designaciones y el listado general de normas del diario oficial.
2. Se baja el PDF oficial de cada norma de personal y se extraen, con reglas de texto, la persona, el cargo, el
   tipo de movimiento, las fechas, la norma anterior y quién firma.
3. Se clasifica cada movimiento: ámbito (cargos de confianza, directorios, subprefectos, diplomáticos, y aparte
   fiscales, Poder Judicial, control institucional, etc.), ubicación en la estructura del Estado (N1-N4) y peso del
   puesto sobre el papel (J1-J7).
4. Se calculan indicadores: continuidad del elenco entre gobiernos, velocidad con que un ministro arma su equipo,
   titulares por puesto y duración en el cargo (regla de sucesión), género por nivel, olas de designaciones,
   subprefectos por departamento y una red de personas que se trasladan juntas entre instituciones.
5. Se publica un dashboard interactivo (`web/`) con datos anonimizados (códigos en lugar de nombres).

## 3. Fuentes de datos y metodología

| Fuente | Qué aporta | Enlace |
|---|---|---|
| Índice de designaciones de El Peruano | normas de designación y renuncia por mes (sector, institución, cargo, enlace al PDF) | https://diariooficial.elperuano.pe/Normas/designaciones |
| Listado general de normas legales de El Peruano | todas las normas del día con su sumilla: recupera resoluciones supremas que el índice omite (ministros, embajadores, etc.) | https://diariooficial.elperuano.pe/Normas |
| PDF oficial de cada norma | nombre de la persona, cargo, firmantes, fechas, norma anterior | enlaces `epdoc2.elperuano.pe` incluidos en la base |
| Reglamentos de Organización y Funciones (ROF) de MIDIS e Interior | validación de la ubicación de los cargos en la estructura | https://www.gob.pe/midis · https://www.gob.pe/mininter |
| Lineamientos de Organización del Estado (D.S. 054-2018-PCM) | nomenclatura común de órganos (niveles organizacionales) | https://busquedas.elperuano.pe/normaslegales/decreto-supremo-que-aprueba-los-lineamientos-de-organizacion-decreto-supremo-n-054-2018-pcm-1649413-1/ |
| UBIGEO de INEI y RENIEC (compilación de J. M. Castagnetto, licencia MIT, actualizada en 2021) | número de distritos y provincias por departamento: divide las designaciones de subprefectos entre el número de subprefecturas | https://github.com/jmcastagnetto/ubigeo-peru-aumentado |

La descarga usa pausas entre consultas y un *user-agent* que identifica el proyecto. El detalle de cada paso está en:

- [`docs/mapa_de_procesos.md`](docs/mapa_de_procesos.md): procesos numerados (insumo → método → resultado).
- [`docs/informe_exploracion.md`](docs/informe_exploracion.md): exploración, problemas encontrados (P1-P22) y decisiones de limpieza.
- [`docs/diccionario_de_datos.md`](docs/diccionario_de_datos.md): significado de cada columna.
- [`docs/validacion_rof.md`](docs/validacion_rof.md): comparación de la ubicación de los cargos con el ROF.
- [`docs/preguntas_y_metodologia.md`](docs/preguntas_y_metodologia.md): preguntas, por qué importan y con qué método se responden.
- [`docs/metodologia_indicadores.md`](docs/metodologia_indicadores.md): reglas de método (regla de sucesión, red, gobiernos).

## 4. Hallazgos principales

1. **La mitad del elenco ya estaba en el Estado.** De las personas que designó en sus primeros meses el gobierno que
   asumió el 28/07/2026, el 50 % ya había tenido un cargo entre 2022 y 2026; en los cargos altos (ministro a director
   general), el 61 %. Con los gobiernos que asumieron en octubre de 2025 y febrero de 2026 la proporción fue similar
   (44 % y 50 %): cambia el mando, no tanto el elenco.
2. **Lo primero que asegura un ministro es el control administrativo.** En 168 llegadas de ministros, el secretario
   general se renueva a los 5 días (mediana), antes que asesoría jurídica (13), administración y recursos humanos (14),
   viceministros (16,5) y planeamiento (18). Con el gobierno de julio de 2026: secretario general a los 3 días y
   viceministros a los 9.
3. **El "desorden" tiene estructura: gente que sigue a su jefe.** Cuando alguien asume un cargo de decisión, llegan
   detrás de él personas que ya lo habían acompañado en otra institución. 41 parejas jefe–acompañante se repiten en 3 o
   más instituciones (por azar se esperarían 6) y 806 en 2 o más (por azar, 364); en 310 de ellas el propio jefe firmó la
   designación, y 88 jefes tienen tres o más acompañantes que los siguen. Las formas de la red (estrellas, cadenas y
   puentes) muestran un sistema con reglas propias, no improvisación. Además, cuando un jefe se muda, el 17,5 % de su
   equipo que también se mueve llega adonde fue él (por azar, 2 %).

Otros resultados en el dashboard: hasta 14 ministros por cartera en cuatro años; 361 puestos con 6 o más titulares;
duración mediana en el cargo de 175 días para secretarios generales y titulares de entidad; las mujeres son el 26 % de
los ministros y el 46 % de los asesores. Son resultados de esta versión de la base; los criterios están en `docs/`.

## 5. Limitaciones

- La información sale del texto de las normas mediante reglas: el 4,6 % de las normas no se pudo leer completa (más en
  2022-2024, por la fuente antigua del diario) y algunos nombres de tablas quedan marcados como dudosos.
- Sin DNI en la mayoría de normas (solo el 29 % de las personas lo tiene en la norma, casi todas subprefectos), dos
  personas con el mismo nombre completo se cuentan como una, y variantes del mismo nombre como personas distintas.
- Las personas aparecen con un código estable (registro maestro privado, ver `docs/metodologia_indicadores.md`, R10);
  todo lo demás es público y cada cargo de los rankings enlaza a su norma en El Peruano.
- El sexo se completa con el nombre de pila cuando la norma no dice "señor/señora" (columna marcada como inferida).
- La ubicación en la estructura se deduce del nombre del cargo y se validó solo con el ROF vigente de dos ministerios.
- La jerarquía J1-J7 es referencial: describe el peso formal del puesto, no el poder real.
- Solo se ven las designaciones publicadas en El Peruano (no CAS ni órdenes de servicio), y la ventana es de cuatro
  años: quien parece "nuevo" al inicio pudo tener cargos antes.
- La red muestra quién se mueve con quién, no por qué: no distingue un equipo técnico cohesionado de una red clientelar.
- Más detalle en [`docs/informe_exploracion.md`](docs/informe_exploracion.md) (sección 5).

## 6. Enlaces

- Dashboard: *pendiente de publicar* (código en [`web/`](web/))
- Publicación de LinkedIn: *pendiente*
- Reel (75 s, 9:16): [`reel/reel.mp4`](reel/reel.mp4) · guion: [`reel/guion.json`](reel/guion.json) · subtítulos: [`reel/subtitulos.srt`](reel/subtitulos.srt)

## 7. Cómo reproducir el proyecto

Requisitos: Python 3.11 o superior.

```bash
pip install -r requirements.txt            # una sola vez por computadora

# Desde la carpeta tarea_3/
python scripts/01_descargar_indice.py 2022-11 2026-10              # índice de designaciones (por mes)
python scripts/01b_descargar_listado_general.py 2022-11-01 2026-10-30   # listado general (por día)
python scripts/01c_unir_normas_personal.py   # normas de personal = índice + las que solo están en el listado
python scripts/02_descargar_pdf.py           # PDF oficiales y su texto (se puede interrumpir y reanudar)
python scripts/03_extraer_campos.py          # normas.csv y movimientos.csv
python scripts/04_diccionario_datos.py       # docs/diccionario_de_datos.md
python scripts/05_explorar_base.py           # docs/exploracion_resultados.md
python scripts/06_preparar_analisis.py       # movimientos_analisis.csv (ámbito, sexo, persona, ubicación, jerarquía)
python scripts/06b_validar_con_rof.py        # docs/validacion_rof.md (requiere los PDF del ROF en datos/crudos/rof/)
python scripts/07_indicadores.py            # datos/procesados/indicadores/*.csv (con nombres; no se publican)
python scripts/08_datos_dashboard.py        # web/data/dashboard.json (anonimizado)

# Ver el dashboard en la computadora
cd web && python -m http.server 8000         # y abrir http://localhost:8000
```

Los PDF descargados se guardan fuera del repositorio (`~/designaciones_cache/pdf`). Los datos con nombres de
personas (`datos/crudos/` y `datos/procesados/`) no se suben al repositorio.

## 8. Uso de inteligencia artificial

El proyecto se desarrolló con apoyo de Claude Code (Anthropic) para escribir y revisar el código, explorar los datos
y redactar la documentación. Las decisiones de alcance, los criterios de clasificación y la verificación de los
resultados contra los PDF oficiales fueron revisados por el autor.

**Reel** (`reel/reel.mp4`, 75 s, 9:16): la narración es la **voz propia del autor, grabada**; no se usó voz clonada ni
sintética. Fue una decisión del autor: para un video tan corto prefirió la entonación y los silencios de su voz real
(el issue pedía generar la narración con IA a partir de la voz propia). Herramientas: Whisper large-v3-turbo
(faster-whisper) para transcribir y sincronizar los subtítulos; Python (Pillow, pandas) para dibujar las animaciones con
los datos; ffmpeg para editar el audio y armar el video; Claude para condensar el guion del autor y programar el reel.
Música: «Clean Soul», Kevin MacLeod (incompetech.com), licencia CC BY 4.0. Detalle en `reel/recursos/CREDITOS.md`.
