# Resultados de la exploración (generado por scripts/05_explorar_base.py)

## 1. Tamaño
- normas.csv: 27,183 filas × 54 columnas (una fila por norma)
- movimientos.csv: 46,892 filas × 41 columnas (una fila por persona y movimiento)

Estado de la extracción por norma:
| estado_extraccion              |     n |
|:-------------------------------|------:|
| ok                             | 25942 |
| revisar: movimiento sin nombre |  1043 |
| sin movimientos detectados     |   195 |
| código no encontrado en el PDF |     3 |

## 2-3. Muestra y tipos de columna
|       | codigo_norma   | fecha_publicacion   | institucion                                                            | tipo_movimiento   | metodo_nombre   | cargo                                                                  |
|------:|:---------------|:--------------------|:-----------------------------------------------------------------------|:------------------|:----------------|:-----------------------------------------------------------------------|
| 13929 | 2290732-1      | 22/05/2024          | MINISTERIO PUBLICO                                                     | renuncia          | tratamiento     | fiscal adjunto provincial provisional del Distrito Fiscal de Lima Noro |
| 30912 | 2541410-1      | 08/08/2026          | TRANSPORTES Y COMUNICACIONES                                           | designación       | tratamiento     | Director Ejecutivo del Proyecto Especial de Infraestructura de Transpo |
| 19723 | 2392437-1      | 21/04/2025          | ECONOMIA Y FINANZAS                                                    | conclusión        | tratamiento     | Vocal del Tribunal de Contrataciones del Estado del Organismo Supervis |
| 43981 | 2453451-2      | 30/10/2025          | RELACIONES EXTERIORES                                                  | nombramiento      | tratamiento     | Embajador Extraordinario y Plenipotenciario del Perú en los Estados Un |
| 27885 | 2507564-1      | 18/04/2026          | MUJER Y POBLACIONES VULNERABLES                                        | designación       | tratamiento     | Directora General de la Oficina General de Asesoría Jurídica del Minis |
| 29273 | 2527336-1      | 19/06/2026          | ORGANISMO TÉCNICO DE LA ADMINISTRACIÓN DE LOS SERVICIOS DE SANEAMIENTO | designación       | tratamiento     | Subdirector de la Subdirección de Gestión del RAT del Organismo Técnic |
|  1974 | 2140199-10     | 04/01/2023          | JUSTICIA Y DERECHOS HUMANOS                                            | renuncia          | tratamiento     | Superintendente Nacional de la Superintendencia Nacional de los Regist |
| 29377 | 2523941-6      | 10/06/2026          | MINISTERIO PÚBLICO                                                     | renuncia          | tratamiento     | fiscal provincial provisional del Distrito Fiscal de Madre de Dios, y  |

Tipos en movimientos.csv: str: 36, bool: 4, float64: 1
Las fechas se leen como texto: fecha_publicacion viene como dd/mm/aaaa y fecha_emision como aaaa-mm-dd; hay que convertirlas a fecha antes de analizarlas.

## 4. Duplicados
- Códigos de norma repetidos en normas.csv: 0
- id_movimiento repetidos: 0
- Filas idénticas en todo menos el id: 0
- Misma norma + misma persona + mismo tipo de movimiento: 0 (en 0 normas)
- Misma persona con dos movimientos distintos en la misma norma (p. ej. concluye y se designa en otro cargo): 2674 normas
- Misma persona + mismo tipo + mismo cargo en normas distintas: 1513 filas (684 casos); se revisan a mano, no se borran: pueden ser hechos reales repetidos (dos encargos del mismo puesto)

## 5. Faltantes (% de filas sin dato)
|                         |   % vacío |
|:------------------------|----------:|
| funciones_que_mantiene  |      99.6 |
| firmante3_nombre        |      99.6 |
| firmante3_cargo         |      99.6 |
| grado_militar_policial  |      98.4 |
| fecha_fin               |      98.2 |
| condicion_texto         |      97.3 |
| firmante2_cargo         |      91   |
| firmante2_nombre        |      91   |
| cargo_actual_mencionado |      90.6 |
| ubicacion_tabla         |      88.2 |
| dni                     |      86.2 |
| fecha_efectividad       |      82.5 |
| objeto_conclusion       |      82   |
| norma_antecedente       |      77.3 |
| inicio_texto            |      76.1 |
| profesion_mencionada    |      70.7 |
| sexo_segun_norma        |      26.2 |
| tratamiento             |      26.2 |
| cargo                   |       7.5 |
| metodo_nombre           |       2.6 |
| nombre_tal_cual         |       2.6 |
| nombre_normalizado      |       2.6 |
| articulo                |       0.9 |
| firmante1_cargo         |       0.9 |
| fecha_emision           |       0.8 |
| firmante1_nombre        |       0.8 |
| sector_ep               |       0.1 |

Faltantes disfrazados ("-", "S/N", "ND"...): nombre_tal_cual: 0, cargo: 0, dni: 0, ubicacion_tabla: 0, firmante1_nombre: 0, firmante1_cargo: 0

## 6. Estadísticos
|       |   movimientos por norma |   días de emisión a publicación |   palabras del nombre |   caracteres del cargo |
|:------|------------------------:|--------------------------------:|----------------------:|-----------------------:|
| count |                 27180   |                         26960   |               45653   |                43392   |
| mean  |                     1.7 |                             3.3 |                   4   |                  126.5 |
| std   |                     7.3 |                            76.3 |                   0.9 |                   95   |
| min   |                     0   |                          -729   |                   2   |                    4   |
| 25%   |                     1   |                             1   |                   4   |                   67   |
| 50%   |                     1   |                             1   |                   4   |                  120   |
| 75%   |                     2   |                             2   |                   4   |                  170   |
| max   |                  1076   |                          8403   |                  12   |                 3446   |

## 7. Frecuencias
**tipo_movimiento**
| tipo_movimiento         |     n |
|:------------------------|------:|
| designación             | 24538 |
| conclusión              | 10694 |
| nombramiento            |  5988 |
| renuncia                |  3559 |
| dejar sin efecto        |  1287 |
| encargatura             |   489 |
| rotación o reasignación |   139 |
| asignación de funciones |   139 |
| ratificación            |    45 |
| prórroga                |    14 |

**sector_ep**
| sector_ep                          |     n |
|:-----------------------------------|------:|
| PODER EJECUTIVO                    | 21715 |
| ORGANISMOS AUTÓNOMOS               | 15199 |
| ORGANISMOS TÉCNICOS ESPECIALIZADOS |  4421 |
| ORGANISMOS EJECUTORES              |  2605 |
| PODER JUDICIAL                     |   865 |
| GOBIERNOS LOCALES                  |   655 |
| ORGANISMOS AUTONOMOS               |   629 |
| ORGANISMOS TECNICOS ESPECIALIZADOS |   436 |
| ORGANISMOS REGULADORES             |   273 |
| GOBIERNOS REGIONALES               |    56 |
| (vacío)                            |    38 |

**metodo_nombre**
| metodo_nombre              |     n |
|:---------------------------|------:|
| tratamiento                | 34584 |
| tabla con DNI              |  5921 |
| lista con viñetas          |  1779 |
| mayúsculas sin tratamiento |  1628 |
| (vacío)                    |  1239 |
| tabla nombres y apellidos  |   601 |
| rango diplomático          |   593 |
| lista numerada             |   405 |
| después del verbo          |   142 |

**sexo_segun_norma**
| sexo_segun_norma   |     n |
|:-------------------|------:|
| M                  | 20525 |
| F                  | 14059 |
| (vacío)            | 12308 |

**temporal**
| temporal   |     n |
|:-----------|------:|
| False      | 45675 |
| True       |  1217 |

**objeto_conclusion**
| objeto_conclusion   |     n |
|:--------------------|------:|
| (vacío)             | 38454 |
| designación         |  5582 |
| nombramiento        |  2547 |
| encargo             |   125 |
| encargatura         |   123 |
| asignación          |    60 |
| funciones           |     1 |

**fuente** (normas)
| fuente          |     n |
|:----------------|------:|
| índice          | 20572 |
| listado general |  6611 |

**edicion** (normas)
| edicion        |     n |
|:---------------|------:|
| ordinaria      | 23765 |
| extraordinaria |  3336 |
| digital        |    82 |

**Tipo de dispositivo** (normas; sin tildes para no contar dos veces la misma categoría)
| tipo_dispositivo            |     n |
|:----------------------------|------:|
| RESOLUCION                  | 13045 |
| RESOLUCION MINISTERIAL      |  6953 |
| RESOLUCION SUPREMA          |  2723 |
| RESOLUCION DIRECTORAL       |  1874 |
| RESOLUCION JEFATURAL        |  1351 |
| RESOLUCION ADMINISTRATIVA   |   482 |
| RESOLUCION DE ALCALDIA      |   321 |
| RESOLUCION VICE MINISTERIAL |   217 |
| RES. ALCALDIA               |    58 |
| ACUERDO                     |    54 |
| RESOLUCION SBS              |    39 |
| RESOLUCION  SBS             |    16 |
| DECRETO DE ALCALDIA         |     9 |
| RESOLUCION RDE              |     7 |
| RESOLUCION JEFATURAL -D     |     5 |

## 8. Valores únicos y variantes de escritura
- institucion: 216 valores distintos; 27 grupos que solo cambian en tildes o mayúsculas
  - AGENCIA DE PROMOCION DE LA INVERSION PRIVADA | AGENCIA DE PROMOCIÓN DE LA INVERSIÓN PRIVADA
  - AGENCIA PERUANA DE COOPERACION INTERNACIONAL | AGENCIA PERUANA DE COOPERACIÓN INTERNACIONAL
  - ARCHIVO GENERAL DE LA NACION | ARCHIVO GENERAL DE LA NACIÓN
  - BIBLIOTECA NACIONAL DEL PERU | BIBLIOTECA NACIONAL DEL PERÚ
  - COMISION DE PROMOCION DEL PERU PARA LA EXPORTACION Y EL TURISMO | COMISIÓN DE PROMOCIÓN DEL PERÚ PARA LA EXPORTACIÓN Y EL TURISMO
- tratamiento: 105 valores distintos; 2 grupos que solo cambian en tildes o mayúsculas
  - magister | magíster
  - señor magister | señor magíster
- firmante1_cargo: 870 valores distintos; 71 grupos que solo cambian en tildes o mayúsculas
  - Contralmirante CJ (r) Presidente del Fuero Militar Policial | Contralmirante CJ (R) Presidente del Fuero Militar Policial
  - Contralor General de la República | Contralor General de la República
  - Dirección Ejecutiva | Direccion Ejecutiva
  - Direccion Ejecutiva Programa Subsectorial de Irrigaciones | Dirección Ejecutiva Programa Subsectorial de Irrigaciones
  - Director Ejecutivo (e) PROVÍAS NACIONAL | Director Ejecutivo (e) PROVIAS NACIONAL | Director Ejecutivo (e) Provías Nacional | Director Ejecutivo (e) Provias Nacional
- Celdas con caracteres mal codificados (Ã o �): 0

## 9. Fechas
- Publicación: del 01/11/2022 al 29/10/2026
- Emisión: del 17/01/2002 al 28/10/2026; sin fecha de emisión: 223 normas
- Emitidas después de publicarse (imposible): 2
- Publicadas más de 60 días después de emitirse: 83
Normas por mes de publicación:
| f_pub   |    n |
|:--------|-----:|
| 2022-11 |  546 |
| 2022-12 |  850 |
| 2023-01 |  907 |
| 2023-02 |  715 |
| 2023-03 |  609 |
| 2023-04 |  540 |
| 2023-05 |  559 |
| 2023-06 |  462 |
| 2023-07 |  543 |
| 2023-08 |  505 |
| 2023-09 |  564 |
| 2023-10 |  533 |
| 2023-11 |  588 |
| 2023-12 |  445 |
| 2024-01 |  477 |
| 2024-02 |  532 |
| 2024-03 |  563 |
| 2024-04 |  517 |
| 2024-05 |  570 |
| 2024-06 |  446 |
| 2024-07 |  399 |
| 2024-08 |  396 |
| 2024-09 |  431 |
| 2024-10 |  474 |
| 2024-11 |  421 |
| 2024-12 |  353 |
| 2025-01 |  468 |
| 2025-02 |  557 |
| 2025-03 |  552 |
| 2025-04 |  543 |
| 2025-05 |  514 |
| 2025-06 |  519 |
| 2025-07 |  498 |
| 2025-08 |  497 |
| 2025-09 |  502 |
| 2025-10 |  565 |
| 2025-11 |  730 |
| 2025-12 |  526 |
| 2026-01 |  669 |
| 2026-02 |  546 |
| 2026-03 |  718 |
| 2026-04 |  680 |
| 2026-05 |  541 |
| 2026-06 |  498 |
| 2026-07 |  516 |
| 2026-08 | 1202 |
| 2026-09 |  806 |
| 2026-10 |  591 |
- Días del periodo sin ninguna norma de personal: 10

## 10. Atípicos
Normas con más movimientos:
| codigo_norma   | institucion                 |   n_movimientos |
|:---------------|:----------------------------|----------------:|
| 2137871-1      | INTERIOR                    |            1076 |
| 2137613-1      | INTERIOR                    |             312 |
| 2471572-8      | DEFENSA                     |             113 |
| 2357349-4      | DEFENSA                     |             106 |
| 2251224-3      | DEFENSA                     |             101 |
| 2245581-1      | INSTITUTO NACIONAL DE SALUD |              86 |
| 2187593-1      | INTERIOR                    |              62 |
| 2185685-1      | INTERIOR                    |              60 |
- Nombres de 2 palabras (posible nombre incompleto): 163
- Nombres de 7 o más palabras (posibles dos personas unidas o apellidos compuestos): 833
- Cargos de más de 250 caracteres (el cargo arrastró texto de más): 2376
- Movimientos sin nombre: 1239; sin cargo (con nombre): 2261