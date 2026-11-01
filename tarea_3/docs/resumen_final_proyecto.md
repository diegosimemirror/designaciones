# Resumen final del proyecto — Designaciones de El Peruano

> Tarea 3 del curso Python Intermedio (D2CML), cerrada el 01/11/2026. Este documento sigue la guía de trabajo del autor
> (sección 5): paquetes, objetos creados, mapa de procesos ejecutado, decisiones de preprocesamiento y limitaciones.
>
> **Pregunta:** la alta rotación de funcionarios de confianza, ¿renueva el elenco del Estado o hace circular a las mismas
> personas entre cargos, instituciones y gobiernos? **Fuente:** normas de personal del Diario Oficial El Peruano,
> noviembre de 2022 a octubre de 2026 (cinco gobiernos). **Resultado público:** repositorio, dashboard y reel.

| Producto | Dónde |
|---|---|
| Repositorio | https://github.com/diegosimemirror/designaciones/tree/main/tarea_3 |
| Dashboard | https://diegosimemirror.github.io/designaciones/tarea_3/web/ |
| Reel (79 s, 1080 × 1920, voz del autor) | [`reel/reel.mp4`](../reel/reel.mp4) |

---

## 5.1 Paquetes y librerías

**Instalar** se hace una sola vez por computadora (`pip install …`); **cargar** (`import …`) se hace en cada script
que lo usa. El proyecto usa dos entornos de Python: el de Anaconda (Python 3.14) para los datos y uno aparte para el
reel (Python 3.12, creado con `uv`), para que los paquetes de audio y video no se mezclen con los del análisis.

### Entorno principal (Anaconda, Python 3.14)

| Paquete | ¿Se instaló en este proyecto o ya existía? | Para qué se usó | Funciones principales usadas |
|---|---|---|---|
| pandas 3.0.3 | Ya existía (Anaconda) | Todas las tablas: leer, unir, agrupar, guardar | `read_csv`, `merge`, `groupby`, `value_counts`, `to_csv`, `to_excel`, `to_markdown` |
| numpy 2.4.6 | Ya existía | Cálculos con vectores, sorteos al azar de la comparación, posiciones del dibujo de la red | `array`, `random.default_rng`, `sqrt` |
| requests 2.34.2 | Ya existía | Descargar el índice, el listado general y los 27.183 PDF (con *user-agent* honesto) | `get`, `post` |
| beautifulsoup4 4.15.0 | Ya existía | Leer el HTML del listado general de normas de cada día | `BeautifulSoup`, `find_all` |
| **pymupdf 2.0** | **Se instaló (30/10/2026)** | Sacar el texto de los PDF de las normas y del ROF | `pymupdf.open`, `page.get_text` |
| networkx 3.6.1 | Ya existía | Redes de personas: comunidades, intermediación, dibujo | `Graph`, `DiGraph`, `community.louvain_communities`, `betweenness_centrality`, `spring_layout` |
| openpyxl 3.1.5 | Ya existía | Lo usa pandas para escribir los Excel privados con nombres | (a través de `DataFrame.to_excel`) |
| tabulate 0.10.0 | Ya existía | Lo usa pandas para escribir tablas en Markdown en `docs/` | (a través de `DataFrame.to_markdown`) |
| Biblioteca estándar | Viene con Python | `re` (patrones de texto), `unicodedata` (quitar tildes), `pathlib` (rutas), `json`, `datetime`, `time` (pausas entre descargas), `base64` (decodificar enlaces), `collections.Counter`, `itertools`, `secrets` (códigos aleatorios de persona) | — |

### Entorno del reel (`venv_reel`, Python 3.12, se creó en este proyecto)

| Paquete | ¿Se instaló o ya existía? | Para qué se usó | Funciones principales usadas |
|---|---|---|---|
| faster-whisper 1.2.1 (con ctranslate2 4.8.4) | Se instaló | Transcribir la narración con el modelo Whisper large-v3-turbo y tiempos por palabra | `WhisperModel`, `transcribe(word_timestamps=True)` |
| imageio-ffmpeg 0.7.0 (ffmpeg 7.1) | Se instaló | Cortar, acelerar 8 % sin cambiar el tono (`atempo`), nivelar volumen a -16 LUFS (`loudnorm`), mezclar música y codificar el video (libx264) | `get_ffmpeg_exe` |
| Pillow 13.0.0 | Se instaló | Dibujar cada cuadro del video (gráficos, texto, subtítulos) | `Image.new`, `ImageDraw`, `ImageFont` |
| soundfile 0.14.0 | Se instaló | Leer y escribir el audio WAV | `read`, `write` |
| numpy 2.5.4, pandas 3.1.0 | Se instalaron en este entorno | Detección de silencios (energía por ventanas de 20 ms) y datos de las escenas | — |

### Fuera de Python

| Herramienta | Para qué |
|---|---|
| D3.js 7.9.0 (desde cdnjs, se carga en el navegador; no se instala) | Dibujar los gráficos, el mapa y la red del dashboard |
| Google Chrome sin ventana (*headless*) | Capturas del dashboard y comprobar que la página se dibuja |
| Git y GitHub Pages | Publicar el repositorio y el dashboard |

---

## 5.2 Objetos creados

**Total de objetos creados: 80** archivos de resultado (tablas, colecciones, páginas, documentos y medios), más
**127 funciones** de Python definidas en los scripts (al final de esta sección). Las variables temporales dentro de
cada script no se cuentan. "Privado" = no se publica (contiene nombres o la voz cruda).

### Tablas de la base (6)

| Objeto | Tipo | Tamaño | Qué contiene | Proceso | ¿Final o intermedio? |
|---|---|---|---|---|---|
| `indice_normas.csv` | tabla | 20.572 × 12 | Índice oficial de designaciones y renuncias | 1 | Intermedio |
| `listado_general.csv` | tabla | 86.975 × 10 | Todas las normas publicadas, con sumilla | 2 | Intermedio |
| `normas_personal.csv` | tabla | 27.183 × 12 | Normas de personal (índice + 6.611 que el índice omite) | 3 | Intermedio |
| `normas.csv` | tabla | 27.183 × 54 | Una fila por norma: fechas, firmantes, vistos, motivo, texto | 5-9 | Intermedio (base) |
| `movimientos.csv` | tabla | 46.892 × 41 | Una fila por persona y movimiento | 8-9 | Intermedio |
| `movimientos_analisis.csv` | tabla | 46.892 × 64 | Lo anterior + ámbito, sexo, persona, nivel, ubicación, jerarquía | 12-15 | **Final** (base del análisis) |

### Colecciones descargadas (4, privadas por tamaño)

| Objeto | Tipo | Tamaño | Qué contiene | Proceso | ¿Final o intermedio? |
|---|---|---|---|---|---|
| `datos/crudos/indice/` | archivos JSON | 48 | Respuesta mensual del índice | 1 | Intermedio |
| `datos/crudos/listado_general/` | archivos HTML | 1.460 | Listado de normas de cada día | 2 | Intermedio |
| `datos/crudos/textos/` | archivos de texto | 27.183 | Texto de cada norma (desde su PDF) | 4 | Intermedio |
| `registro_descargas.csv` | tabla | 1 archivo | Resultado de cada descarga de PDF | 4 | Intermedio |

### Indicadores (27 tablas en `datos/procesados/indicadores/`)

| Objeto | Tamaño | Qué contiene | Proceso |
|---|---|---|---|
| `gobiernos.csv` | 5 × 4 | Gobiernos detectados por el firmante de las resoluciones supremas | 16.1 |
| `llegadas_ministros.csv` | 168 × 7 | Cada llegada de un ministro | 16.1 |
| `rotacion_ministerial.csv` | 19 × 4 | Ministros por cartera | 16.2 |
| `continuidad_gobiernos.csv` | 8 × 9 | % de designados que ya tenían cargo antes | 16.3 |
| `armado_equipo_por_llegada.csv`, `armado_equipo_resumen.csv`, `armado_equipo_vitrina.csv`, `secuencia_vitrina.csv` | 168 × 16, 10 × 4, 19 × 16, 238 × 8 | Qué puestos cambian y en cuántos días tras llegar un ministro | 16.4 |
| `periodos_titulares.csv`, `puestos_titulares.csv`, `supervivencia_curvas.csv` | 12.391 × 18, 5.449 × 7, 4.610 × 5 | Periodos de cada titular, titulares por puesto y curvas de duración (Kaplan-Meier) | 16.5 |
| `genero_jerarquia.csv`, `genero_jerarquia_gobierno.csv` | 7 × 3, 35 × 4 | % de mujeres por nivel y gobierno | 16.6 |
| `olas_semanas.csv`, `olas_semanal_sector.csv` | 11 × 3, 1.013 × 3 | Semanas con oleadas de designaciones | 16.7 |
| `subprefectos_departamento_mes.csv` | 788 × 5 | Designaciones de subprefectos por departamento y mes | 16.8 |
| `red_pares.csv`, `red_comunidades.csv`, `red_perfil_personas.csv`, `red_arrastre.csv`, `red_resumen.csv` | 1.247 × 3, 223 × 8, 13.443 × 12, 179 × 10, 1 × 18 | Red de co-traslado: pares, grupos, intermediación y arrastre | 16.9 |
| `seguimiento_parejas.csv`, `seguimiento_jefes.csv`, `seguimiento_resumen.csv` | 806 × 7, 341 × 5, 1 × 11 | Red de seguimiento: quién llega detrás de quién | 16.10 |
| `trayectorias.csv`, `ranking_rotacion.csv`, `ranking_permanencia.csv` | 14.776 × 13, 9.322 × 10, 316 × 17 | Cargos de cada persona y rankings de rotación y permanencia | 16.11 |

Todas son **finales** para el dashboard (las lee el proceso 17).

### Archivos privados con nombres (5, en `datos/privado/`)

| Objeto | Tipo | Tamaño | Qué contiene | Proceso | ¿Final o intermedio? |
|---|---|---|---|---|---|
| `registro_personas.csv` | tabla | 26.154 × 10 | **Registro maestro**: código P-XXXXX ↔ nombre completo | 15 y 16.10 | **Final** (respaldar) |
| `alias_personas.csv` | tabla | 303 × 4 | Otras escrituras del mismo nombre con el mismo DNI | 15 | Final |
| `revision_personas.csv` | tabla | 172 × 4 | Casos dudosos para revisar a mano | 15 | Intermedio |
| `ranking_intermediacion.xlsx` | Excel | 2 hojas (200 × 14; 13.443 × 14) | Ranking de intermediación con nombres y recorrido | 16b | Final |
| `rankings_rotacion_permanencia.xlsx` | Excel | 4 hojas (50 filas cada una; 368 cargos) | Rankings con nombres | 16d | Final |

### Dashboard (4, en `web/`)

| Objeto | Tipo | Tamaño | Qué contiene | Proceso | ¿Final o intermedio? |
|---|---|---|---|---|---|
| `dashboard.json` | datos (lista anidada) | 1,07 MB, 18 bloques | Todo lo que dibuja la página, con códigos y sin nombres | 17 | Final |
| `index.html` | página | 1 | Estructura del dashboard y guía "¿Cómo leer esta red?" | 18 | Final |
| `app.js` | programa del navegador | 15 funciones de dibujo | 6 indicadores, 10 visualizaciones, 3 filtros, tablas, enlaces a normas | 18 | Final |
| `style.css` | estilos | 1 | Modo claro y oscuro, diseño para celular | 18 | Final |

### Reel y material visual (25, en `reel/`)

| Objeto | Tipo | Tamaño | Qué contiene | Proceso | ¿Final o intermedio? |
|---|---|---|---|---|---|
| `reel.mp4` | video | 79 s, 1080 × 1920, 30 cuadros/s, 6 MB | El reel entregado | 19 | **Final** |
| `subtitulos.srt`, `guion.json`, `portada.png` | texto, datos, imagen | 1 c/u | Subtítulos, narración por escena, portada | 19 | Final |
| `guion_para_grabar.md` | texto | 1 | Guion v3 a partir del texto del autor | 19 | Intermedio |
| `voz/transcripcion.json`, `voz/narracion_corta.wav`, `voz/palabras_corta.json`, `voz/narracion_completa.wav`, `voz/palabras_completa.json` | datos y audio | 5 | Transcripción y audio editado (versión corta usada; completa descartada) | 19 | Intermedio (privado) |
| `capturas/*.png` | imágenes | 4 | Red completa, grupos 2 y 4 resaltados, ranking de rotación | 18 | Final |
| `infografia_red/` (HTML + 3 láminas) | página e imágenes | 4 | Cómo leer la red de seguimiento | 18-19 | Final |
| `infografia_caso/` (HTML + 3 láminas) | página e imágenes | 4 | Caso "ministro B" (grupo 4) | 18-19 | Final |
| `recursos/CREDITOS.md`, `musica_clean_soul_extracto.mp3`, `dashboard_movil.png` | texto, audio, imagen | 3 | Créditos y licencias, música CC BY 4.0, captura móvil | 19 | Final |

### Documentación (9)

`README.md` (8 secciones) y en `docs/`: `diccionario_de_datos.md` (proceso 10), `exploracion_resultados.md` (11),
`informe_exploracion.md` (P1-P22), `validacion_rof.md` (15c), `metodologia_indicadores.md` (reglas R1-R10),
`preguntas_y_metodologia.md`, `mapa_de_procesos.md` y `entrega_linkedin_y_issue.md`. Todos son finales.

### Funciones de Python (127)

| Script | N.º | Funciones |
|---|---|---|
| `01_descargar_indice.py` | 4 | `lista_de_meses`, `descargar_mes`, `codigo_desde_enlace`, `main` |
| `01b_descargar_listado_general.py` | 4 | `descargar_dia`, `enlace_pdf`, `leer_normas`, `main` |
| `01c_unir_normas_personal.py` | 1 | `sin_tildes` |
| `02_descargar_pdf.py` | 4 | `normas_pendientes`, `descargar_pdf`, `extraer_texto`, `main` |
| `03_extraer_campos.py` | 24 | `recortar_norma`, `reparar_fuente_antigua`, `tablas_por_celda`, `separar_partes`, `datos_de_norma`, `buscar_personas`, `tipo_de`, `cargo_de`, `movimientos_de_norma`… |
| `04_diccionario_datos.py` | 3 | `porcentaje_lleno`, `tabla_markdown`, `main` |
| `05_explorar_base.py` | 4 | `escribir`, `tabla_md`, `vacio`, `sin_tildes` |
| `06_preparar_analisis.py` | 13 | `ambito_de`, `ambito_por_sumilla`, `nivel_de`, `ministerio_del_ministro`, `ubicar_cargo`, `jerarquia_de`… |
| `06b_validar_con_rof.py` | 3 | `estructura_del_rof`, `buscar_en_rof`, `sin_tildes` |
| `07_indicadores.py` | 14 | `gobierno_de`, `kaplan_meier`, `clave_entidad`, `equipo_de`, `pares_que_se_mueven_juntos`, `clave_de_firmante`, `acompanamientos`… |
| `07b_ranking_intermediacion.py` | 2 | `recorrido`, `cargo_mas_alto` |
| `07c_trayectorias_rankings.py` | 6 | `duracion`, `limpiar_clave`, `maximo_en_12_meses`, `recorrido`, `jefes_que_llegaron`, `sin_tildes` |
| `08_datos_dashboard.py` | 16 | `ubicacion_sin_nombres`, `sin_nombres`, `primer_nombre_en`, `nombre_puesto`, `mediana_km`, `es_puente`, `referencia_pdf`… |
| `registro_personas.py` | 4 | `asignar` (única que crea códigos), `_codigo_nuevo`, `_lista_de_revision`, `_leer` |
| `reel/02_editar_audio.py` | 2 | `a_final`, `conservada` |
| `reel/03_hacer_video.py` | 23 | 11 escenas (`escena_gancho` … `escena_cierre`), `subtitulo`, `cuadro`, `mezclar`… |

---

## 5.3 Mapa de procesos ejecutado

El detalle completo (con script y número de proceso dentro de cada script) está en
[`mapa_de_procesos.md`](mapa_de_procesos.md). Resumen de lo que realmente se hizo:

| N.º | Proceso | Insumo | Método | Resultado |
|---|---|---|---|---|
| 1 | Descargar el índice | Servicio `LoadRenunciasFiltro` (un mes por consulta) | `requests` + decodificar el enlace del PDF | 20.572 normas |
| 2 | Descargar el listado general | Página de normas de cada día | HTML con BeautifulSoup; 4 formatos de enlace | 86.975 normas |
| 3 | Elegir las normas de personal | Índice + listado | Filtro por el verbo inicial de la sumilla; unión por código | 27.183 normas (6.611 que el índice omite, entre ellas los ministros) |
| 4 | Descargar PDF y sacar el texto | Enlace de cada norma | Pausa de 1 s, *user-agent* honesto, PyMuPDF | 27.183 textos, 0 errores |
| 4b-9 | Extraer los campos | Texto de la página | Reparar fuente antigua; recortar la norma; reordenar tablas; partes, firmantes, personas, cargos | `normas.csv` y `movimientos.csv` (95,4 % de normas leídas completas) |
| 10-11 | Diccionario y exploración | Las dos tablas | % con dato; lista de revisión de la fase 3 sin modificar datos | `docs/` |
| 12-15d | Preparar el análisis | `movimientos.csv` | Institución, sector, fechas, ámbito, sexo, persona (registro maestro), nivel, ubicación, jerarquía | `movimientos_analisis.csv` |
| 16-16d | Indicadores | Base de análisis y normas | Reglas R1-R10: gobiernos, continuidad, armado del equipo, duración, género, olas, subprefectos, redes, trayectorias | 27 tablas de indicadores y 2 Excel privados |
| 17 | Datos del dashboard | Indicadores | Códigos en vez de nombres, enlaces a cada norma, cortes de nombres pegados a oficinas y a ubicaciones, control final de privacidad, dibujo de la red reproducible | `dashboard.json` |
| 18 | Dashboard | `dashboard.json` | D3: 6 indicadores, 10 visualizaciones, 3 filtros, tablas, modo oscuro | Página publicada en GitHub Pages |
| 19 | Reel | Voz del autor + indicadores | Whisper; recortes solo de frases completas; escenas dibujadas con los datos; música CC BY | `reel.mp4` (79 s) |
| 20 | Publicación | Repositorio y `web/` | Control de privacidad (0 nombres, 0 DNI); 2 commits; GitHub Pages | Repositorio y dashboard públicos |

**Cambios de último momento (01/11/2026, proceso 17):** el control previo al push encontró 3 nombres de subprefectos
pegados a la ubicación en el dashboard (Huancavelica); la ubicación ahora se corta después del último departamento del
UBIGEO. Además, el dibujo de la red se volvió reproducible (antes cambiaba en cada corrida por el orden aleatorio de los
conjuntos de Python): tres corridas dan hoy el mismo archivo.

---

## 5.4 Decisiones de preprocesamiento

Ningún dato original se borró: las correcciones se guardan en **columnas nuevas** y los casos dudosos se **marcan**.

| Decisión | Registros afectados | Por qué |
|---|---|---|
| Usar el listado general además del índice | +6.611 normas | El índice oficial omite ministros, embajadores, fiscales y otros cargos altos |
| Reparar la fuente antigua del diario ("deSIGnaR") | 101 normas (2022-2024) | Las mayúsculas A, D, E, N, O, U se leían como minúsculas y rompían los nombres |
| Reordenar tablas de subprefectos y cortar la ubicación pegada al nombre | ≈ 1.450 + 111 nombres | Una celda por línea (2022-2023) y tablas sin numeración (2024-2026) |
| Uniformar la institución | 4.693 filas (216 → 184 instituciones) | Una misma institución escrita de varias formas |
| Completar el sector y unificar la tilde | 38 vacíos y 1.065 sin tilde | Sector vacío o escrito distinto según el año |
| Corregir fechas imposibles | 7 movimientos (6 normas) | Errores de tipeo del original ("20025"), verificados en el PDF |
| Marcar el ámbito y elegir el análisis principal | 46.892 → 28.175 movimientos | Fiscales, jueces, FF.AA., OCI, notarios y fedatarios no son cargos de confianza del Ejecutivo |
| Reclasificar representantes ante comisiones y comisiones organizadoras de universidades | 72 + 42 movimientos | Se clasifican por la función del órgano, no por la oficina de origen |
| Corregir la PCM leída como "consejo directivo" | 266 movimientos | Ministros, viceministros y asesores de la PCM son cargos de confianza |
| Completar el sexo con el nombre de pila | 6.718 movimientos | La norma no dice "señor/señora" en tablas y listas; queda marcado como inferido |
| Marcar nombres dudosos | 871 filas (139 en el análisis principal) | Empiezan con un cargo, tienen una sola palabra o 7 o más; se excluyen de redes y conteos |
| No borrar repeticiones | 684 casos (1.513 filas) | Pueden ser encargos repetidos o normas que se dejan sin efecto y se reemiten |
| Fin de un periodo = siguiente titular, salida propia u otro cargo de la persona | Todos los periodos (12.391) | Evita periodos "abiertos" de quien ya se fue a otro puesto |
| Unificar firmantes con su persona | Firmantes con el mismo nombre y dos apellidos | Un mismo ministro aparecía con dos escrituras |
| Códigos de persona del registro maestro | 26.154 códigos, 303 alias por mismo DNI | Publicar estructuras sin señalar a nadie; códigos estables al ampliar el periodo |
| Quitar nombres y DNI pegados a nombres de oficina y ubicación | Oficinas con nombres de personas conocidos, 3 ubicaciones de subprefecturas, DNI de 8 cifras | Privacidad: ninguna secuencia de 3 a 7 palabras del dashboard coincide con un nombre real |

---

## 5.5 Limitaciones y pendientes

### Lo que estos datos no permiten responder

- **Por qué** se mueve la gente junta: la red muestra quién llega detrás de quién, no si es un equipo técnico
  cohesionado o una red clientelar.
- **Quién no aparece en El Peruano:** CAS, órdenes de servicio y cargos que no se publican.
- **Antes de noviembre de 2022:** quien parece "nuevo" al inicio de la ventana pudo tener cargos antes.
- **Homónimos:** solo el 29 % de las personas trae DNI en la norma (casi todas subprefectos); dos personas con el mismo
  nombre se cuentan como una, y variantes del mismo nombre, como dos.
- **Peso real del puesto:** la jerarquía J1-J7 es formal (sobre el papel), y la ubicación en la estructura se deduce del
  cargo; solo se validó con el ROF vigente de MIDIS e Interior.
- El 4,6 % de las normas no se pudo leer completa (más en 2022-2024).

### Pendientes recomendados

1. **Respaldar `registro_personas.csv`** en un lugar privado (si se pierde, los códigos nuevos no coincidirían).
2. Revisar `alias_personas.csv` (303) y `revision_personas.csv` (172) y aplicar los alias al análisis.
3. Ampliar el periodo hacia 2018 (el servicio lo permite); los códigos publicados seguirán valiendo.
4. Medir el "cierre de triángulos" (A designa a B, B a C, ¿A llega a C?) como siguiente paso del análisis de redes.
5. ROF y CAP completos por entidad (etapa 2 de la ubicación) y acefalía de puestos.
6. Enlazar las normas también desde la red y la tabla de puestos (hoy solo desde los rankings).
7. El reel usa la disposición anterior del dibujo de la red (mismas cifras); si se regenera, saldrá con la nueva.
