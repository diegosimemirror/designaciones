# Validación de la ubicación de los cargos con el ROF

Generado por `scripts/06b_validar_con_rof.py`. Compara la unidad orgánica y el nivel que el script 06 deduce del texto del cargo con la estructura orgánica del texto integrado del ROF vigente (descargado de gob.pe el 30/10/2026).
Solo se comparan movimientos de la **sede central** del ministerio (sin programas, organismos adscritos ni órganos desconcentrados). Nivel del ROF: 01.x = N1 (alta dirección), 05.2 = N2 (órgano), 05.2.1 = N3 (unidad orgánica).

## Resumen

| Ministerio                    |   Movimientos (sede central) | Unidad encontrada en el ROF   | Nivel igual al del ROF   |
|:------------------------------|-----------------------------:|:------------------------------|:-------------------------|
| DESARROLLO E INCLUSIÓN SOCIAL |                          383 | 307 (80%)                     | 293 de 307 (95%)         |
| INTERIOR                      |                          564 | 548 (97%)                     | 543 de 548 (99%)         |

## DESARROLLO E INCLUSIÓN SOCIAL

ROF: `midis_rof_texto_integrado_rm026-2025.pdf` — 43 órganos y unidades orgánicas en las secciones 01 a 07.

**Nivel de la base (filas) frente al nivel del ROF (columnas)**

| nivel_organizacional   |   N1 |   N2 |   N3 |   Total |
|:-----------------------|-----:|-----:|-----:|--------:|
| N1                     |  136 |    0 |    0 |     136 |
| N2                     |    0 |   79 |    0 |      79 |
| N3                     |    0 |    0 |   78 |      78 |
| N4                     |    0 |    2 |   12 |      14 |
| Total                  |  136 |   81 |   90 |     307 |

**Unidades de la base que no se encontraron en el ROF (las 15 más frecuentes)**

| unidad_organica                                                                                                                |   movimientos |
|:-------------------------------------------------------------------------------------------------------------------------------|--------------:|
| Unidad de Comunicación e Imagen                                                                                                |             8 |
| Unidad de Administración                                                                                                       |             5 |
| Unidad de Recursos Humanos                                                                                                     |             4 |
| Coordinación Parlamentaria                                                                                                     |             4 |
| Unidad de Gestión de Proyectos Productivos                                                                                     |             3 |
| Unidad de Gestión de Proyectos Especiales                                                                                      |             3 |
| Recursos Humanos                                                                                                               |             2 |
| Unidad de Gestión de Proyectos de Infraestructura                                                                              |             2 |
| Unidad de Acompañamiento                                                                                                       |             2 |
| Dirección General de Seguimiento y Evaluación Resolución Ministerial N° 115-2018-MIDIS [nombre de persona] Director |             2 |
| Subunidad de Seguimiento Contractual y Rendición de Cuentas                                                                    |             2 |
| Unidad de Educación Alimentaria y Nutricional, Fortalecimiento de Capacidades y Articulación                                   |             2 |
| Unidad de Asesoría Jurídica                                                                                                    |             2 |
| Diseño y Articulación de las Prestaciones Sociales                                                                             |             2 |
| Políticas y Estrategias                                                                                                        |             1 |

**Desacuerdos de nivel más frecuentes**

| organo_rof                                                            | nivel_rof   | nivel_organizacional   |   movimientos |
|:----------------------------------------------------------------------|:------------|:-----------------------|--------------:|
| 07.4.1 Dirección de Articulación de las Prestaciones Sociales         | N3          | N4                     |             4 |
| 07.3.2 Dirección de Evaluación                                        | N3          | N4                     |             3 |
| 07.4.2 Dirección de Prestaciones Sociales Complementarias             | N3          | N4                     |             3 |
| 07.3.1 Dirección de Seguimiento                                       | N3          | N4                     |             2 |
| 07.3 Dirección General de Seguimiento, Evaluación e Innovación Social | N2          | N4                     |             1 |
| 07.4 Dirección General de Articulación de las Prestaciones Sociales   | N2          | N4                     |             1 |

## INTERIOR

ROF: `mininter_rof_texto_integrado_vigente.pdf` — 68 órganos y unidades orgánicas en las secciones 01 a 07.

**Nivel de la base (filas) frente al nivel del ROF (columnas)**

| nivel_organizacional   |   N1 |   N2 |   N3 |   Total |
|:-----------------------|-----:|-----:|-----:|--------:|
| N1                     |  199 |    0 |    0 |     199 |
| N2                     |    0 |  135 |    1 |     136 |
| N3                     |    0 |    4 |  209 |     213 |
| Total                  |  199 |  139 |  210 |     548 |

**Unidades de la base que no se encontraron en el ROF (las 15 más frecuentes)**

| unidad_organica                                                                                                                                        |   movimientos |
|:-------------------------------------------------------------------------------------------------------------------------------------------------------|--------------:|
| Dirección de Rondas Campesinas                                                                                                                         |             4 |
| Estado Mayor General de la Policía Nacional del Perú                                                                                                   |             3 |
| Peru Dirección de Prevención y Gestión de Conflictos Sociales                                                                                          |             1 |
| Peru la Oficina de Servicios de Tecnología y Comunicaciones                                                                                            |             1 |
| Intendencia Nacional de Bomberos del Perú                                                                                                              |             1 |
| Secretaría Técnica de la Cuarta Sala                                                                                                                   |             1 |
| Secretaría Técnica de la Segunda Sala                                                                                                                  |             1 |
| USO DEL SISTEMA PGA PARA PUBLICACIÓN DE NORMAS LEGALES Se comunica a las entidades que conforman el Poder Legislativo, Poder Ejecutivo, Poder Judicial |             1 |
| Soluciones Informáticas y Gestión de Proyectos                                                                                                         |             1 |
| Servicios de Tecnología y Comunicaciones                                                                                                               |             1 |
| Coordinación Parlamentaria                                                                                                                             |             1 |

**Desacuerdos de nivel más frecuentes**

| organo_rof                                       | nivel_rof   | nivel_organizacional   |   movimientos |
|:-------------------------------------------------|:------------|:-----------------------|--------------:|
| 07.3 Oficina de Seguridad y Defensa Nacional     | N2          | N3                     |             4 |
| 05.3.1 Oficina de Desarrollo de Recursos Humanos | N3          | N2                     |             1 |
