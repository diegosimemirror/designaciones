# Reglas de método para los indicadores (acordadas el 31/10/2026)

Este documento registra las decisiones de método para el proceso 16 (indicadores). Cada regla dice qué se supone,
por qué y qué excepciones tiene.

## R1. Regla de sucesión: una nueva designación en el mismo puesto cierra la anterior

Si la persona X ocupa un puesto y luego El Peruano publica la designación de la persona Y en **ese mismo puesto**,
se asume que la designación de X terminó en la fecha en que Y asume, aunque el cese de X no se haya publicado en
El Peruano (muchas veces solo se publica en la sede digital de la entidad).

- **Por qué:** dos titulares no pueden ocupar a la vez la misma jefatura; la designación pasa por varios filtros
  (visados de recursos humanos, asesoría jurídica, secretaría general), así que no se superponen. Criterio del autor,
  basado en su experiencia en el sector público.
- **Para qué sirve:** permite calcular cuánto duró cada titular sin buscar las resoluciones de cese.
- **Excepciones:**
  1. **Encargos temporales** (vacaciones, licencia, comisión de servicio: columna `temporal` = True, o texto "en tanto dure
     la ausencia del titular"): no cierran la designación del titular; solo cubren su ausencia.
  2. **Puestos con varios ocupantes a la vez** (asesores, ejecutivos adjuntos, miembros de directorio, representantes,
     vocales): la regla no se aplica, porque la llegada de uno no implica la salida de otro.
- **Otro cierre (corregido el 31/10/2026):** el periodo también termina cuando la misma persona es designada en **otro
  cargo** (de confianza, subprefecto o diplomático; no directorios ni comisiones, que pueden ser simultáneos). Antes, quien
  se iba a otra institución sin que se publicara su salida quedaba "abierto" y su duración se alargaba (por ejemplo,
  figuraba "siguiendo" en la PCM alguien que ya trabajaba en el MTC y luego en el MEF). Dos designaciones el mismo día son
  simultáneas y no cierran nada.
- **Fecha de cierre:** fecha de efectividad de la nueva designación si la norma la indica; si no, su fecha de firma.

## R2. "Dejar sin efecto" no es, en general, improvisación

En la base hay 1.287 movimientos "dejar sin efecto". Al revisarlos:

- 364 dejan sin efecto **una designación o un encargo** ("Dejar sin efecto, a partir del 18 de julio de 2026, la
  encargatura del señor …"): es otra forma de **terminarla**, equivalente a una conclusión.
- 422 dejan sin efecto **una resolución o un artículo anterior**, muchas veces antiguos (resoluciones de 2003 a 2022 que
  designaban fedatarios o responsables): es **orden administrativo**.
- Ninguno menciona un error material ni que la persona no llegó a asumir.
- De los 324 que tienen la designación previa en la base, 131 ocurren dentro de los 30 días; varios son encargos cortos
  que terminan, no marchas atrás.

**Decisión:** para medir duraciones, "dejar sin efecto la designación / el encargo" se trata como **fin del periodo**.
No se usa como indicador de improvisación. Una marcha atrás solo podría medirse en los casos de menos de una semana,
y habría que leerlos uno por uno.

## R3. Qué es un "puesto" para contar cuántos titulares tuvo

Para la pregunta "¿qué puestos cambian más?" (por ejemplo, un puesto con 18 jefes en un año) no hace falta el universo
de puestos (CAP): basta contar cuántas personas distintas fueron designadas en el mismo puesto. Pero el puesto debe
identificarse bien:

- **Clave del puesto:** institución + entidad o programa (Juntos, Pensión 65, SUNAT…) + unidad orgánica + lugar, cuando la
  unidad es desconcentrada ("Jefatura Zonal de Chiclayo"). Sin la entidad, "MIDIS | Unidad de Administración" junta las
  unidades de administración de todos los programas del MIDIS y exagera la rotación.
- **Solo puestos de titular** (un ocupante): jefes, directores, gerentes, secretarios generales; se excluyen los cargos de
  apoyo (asesores, adjuntos, especialistas), por la excepción 2 de R1.
- **Indicadores:** titulares distintos por puesto y por año; duración mediana de cada titular (con R1).

## R4. Fecha de referencia

Se usa la **fecha de firma** de la norma (`fecha_emision_corregida`, 99 % con dato); si la norma dice "a partir del …",
la fecha de efectividad. La fecha de publicación se usa solo cuando falta la de firma (la mediana de diferencia es 1 día).

## R5. Gobiernos y "fecha cero"

Los cambios de gobierno se toman de los propios datos: el Presidente firma las resoluciones supremas, y el cambio de
firmante marca el cambio de gobierno (se cuentan solo quienes firman 50 o más, para descartar encargos breves del
despacho presidencial). La "fecha cero" de cada gobierno es su primera resolución suprema; la de cada ministro, la fecha
de su designación.

## R6. La red

- **Equipo:** las personas designadas en una entidad (ministerio, o programa u organismo) durante la gestión de un mismo
  jefe (el ministro, o el titular de la entidad); si la entidad no tiene jefes registrados, el año calendario. Una gestión
  nueva empieza solo cuando cambia la PERSONA al mando: si el mismo ministro es redesignado (recomposición del gabinete),
  sigue siendo el mismo equipo (corregido el 31/10/2026; antes cada redesignación abría un equipo nuevo: 1.872 → 1.795 equipos).
- **Traslado conjunto:** dos personas que salen del mismo equipo y llegan a la misma otra entidad con menos de 180 días de
  diferencia. Se compara con el azar sorteando el equipo de origen entre quienes llegan a cada entidad (20 sorteos).
- **Comunidades:** método de Louvain sobre la red de traslados conjuntos (peso = número de traslados juntos).
- **Intermediación:** centralidad de intermediación exacta (todos los nodos) en la red persona–equipo: cuántas veces la
  persona está en el camino más corto entre dos equipos. Mide qué tanto conecta equipos distintos, no poder ni importancia
  del cargo. Ranking privado con nombres: `scripts/07b_ranking_intermediacion.py` → `datos/privado/ranking_intermediacion.xlsx`.
- **Permanencia:** cuántos ministros llegaron a su ministerio mientras la persona seguía en el mismo puesto.
- **Tasa de arrastre:** cuando un líder (J1-J3) cambia de entidad, de los integrantes de su equipo anterior que cambian de
  entidad entre 30 días antes y 180 días después, qué porcentaje llega a la misma entidad que el líder; se compara con el
  peso de esa entidad entre todas las llegadas del periodo (lo esperable por azar).
- **Clave de entidad (corregida el 31/10/2026):** "SUSALUD | SUSALUD" y "SUSALUD | " son la misma entidad (35 instituciones
  estaban escritas de las dos formas), y un organismo escrito dentro de su ministerio ("SALUD | Instituto Nacional de Salud",
  138 designaciones) se asigna al propio organismo. Antes, esas diferencias partían un mismo equipo en dos.

### R6b. Red de seguimiento: quién llega detrás de quién (gráfico principal del hallazgo 3; idea del usuario, aprobada el 31/10/2026)

La red de co-traslado (arriba) dice quiénes se mueven juntos, pero no quién lleva a quién: un jefe con su equipo aparece
como una "bola" donde todos se unen con todos. La red de seguimiento pone al jefe en el centro:

- **Llegada del jefe a una entidad:** su primera designación allí en un cargo de decisión (J1-J4: ministro, viceministro,
  secretario general o titular, director general o jefe de órgano), **o** la primera designación que firma allí (sin contar
  resoluciones supremas, que firma el Presidente; en ellas cuenta el ministro que refrenda). La firma permite ver a jefes
  cuya propia designación es anterior a noviembre de 2022 o no se publicó en la base.
- **Quién firma:** el nombre del firmante se une a la persona designada si coinciden el primer nombre y los dos apellidos y
  hay un solo candidato (un firmante "Juan Pérez López" se une a "Juan Carlos Pérez López", como fue designado).
- **Acompañante:** persona **nueva** en esa entidad (su primera designación allí) que llega entre 0 y 180 días después del jefe.
- **Seguimiento:** la pareja jefe → acompañante cuenta solo si se repite en **2 o más entidades distintas**. Una sola vez
  puede ser casualidad o personal que el jefe encontró ("impuesto"); repetida, es un patrón. 3 o más es la señal fuerte.
- **Firma:** se marca si el jefe firmó la designación del acompañante al menos una vez (evidencia adicional, no requisito).
- **Azar:** dentro de cada entidad se sortea quién llega (mismas fechas y cantidades; los jefes no cambian), 10 sorteos.
- **Formas:** estrella = un jefe con su gente; cadena = un acompañante que luego es jefe de otros; puente = persona que
  siguió a dos jefes que NO están unidos entre sí (ninguno siguió al otro). Si siguió al ministro y a su secretaria general,
  que llegan juntos, es parte del mismo equipo y no cuenta como puente (corregido el 31/10/2026). Grupos = comunidades de Louvain de esta red; el dashboard muestra los de 3+ personas.
- **Códigos:** los jefes que solo aparecen como firmantes (sin designación propia en la base) también reciben su código del registro maestro (R10).
- **Límites:** la ventana de 180 días no capta a quien se suma más tarde durante la gestión; en ministerios grandes llegan
  muchas personas en 6 meses, por eso se exige la repetición y se compara con el azar; no dice por qué lo siguen.

## R8. Rankings de personas: rotación y permanencia (pedido del usuario, 31/10/2026; script 07c, proceso 16.11)

- **Cargo:** cada designación de confianza o directiva (sin directorios, comisiones, subprefectos ni diplomáticos; sin
  encargos temporales). Si la misma persona es designada otra vez en el mismo cargo (misma institución y mismo texto de
  cargo, sin números ni paréntesis), es el mismo periodo. Dos designaciones el mismo día son simultáneas (no es un cambio).
- **Fin de cada cargo:** lo primero que ocurra entre su siguiente cargo, su conclusión, renuncia o "dejar sin efecto" en esa
  institución, o la designación de un sucesor en ese puesto (R1). Si nada ocurre, sigue abierto al 29/10/2026.
- **Rotación:** se ordena por el **máximo de cargos distintos iniciados en 12 meses**; a igualdad, más cargos en total y
  menos días por cargo (mediana). Muestra dónde estuvo y cuánto duró en cada cargo.
- **Permanencia:** periodos de **titular** (R1) de **3 años o más** en el mismo puesto, ordenados por **días en el puesto**;
  a igualdad, por cuántos **ministros** llegaron mientras la persona seguía. Ese dato solo se calcula en ministerios: en los
  organismos (que El Peruano clasifica como "técnicos especializados", "ejecutores", etc., no por ministerio) no es confiable
  contar sus cambios de jefe con estos datos: designaciones J3 que no son del organismo (OTASS designa gerentes de empresas de
  agua) y firmantes que no son el titular (en SUNAT firman adjuntos, encargados e intendentes). Como la base empieza en
  noviembre de 2022, el máximo observable es unos 4 años y muchos empatan cerca de ese tope. El Excel privado tiene además
  una hoja ordenada por ministros vistos pasar (solo ministerios).
- **Limpieza solo para estos rankings:** se excluyen claves que no son personas (textos de la norma leídos como nombre:
  "Inicio de labores", "Ley de Transparencia", "Portal de Transparencia") y se quitan prefijos pegados al nombre ("Señor",
  "Ingeniero", "Y Finanzas"). "Portal" y "Portales" son apellidos reales y se conservan. La base no se cambia: estos casos quedan
  en la lista de revisión del registro maestro (R10) para que el autor decida si son la misma persona.
- **Límites:** "sigue" significa que no se publicó su salida, un sucesor ni otro cargo; puede haber salidas publicadas solo en
  la sede digital de la entidad. La permanencia anterior a noviembre de 2022 no se observa.

## R9. Subprefectos y prefectos: cambios por subprefectura (sugerencia del usuario, 31/10/2026)

Contar designaciones por departamento favorece a los que tienen más distritos (Áncash tiene 166; Tumbes, 13). Por eso el
mapa divide las designaciones de subprefectos y prefectos entre el **número aproximado de puestos**: un puesto por distrito
(subprefectura distrital o, en el distrito capital de la provincia, la subprefectura provincial) más la prefectura regional.
El resultado se lee como "cuántas veces cambió de titular, en promedio, cada subprefectura" (1,5 = una vez y media).

- **Fuente de los distritos:** UBIGEO de INEI y RENIEC compilado en github.com/jmcastagnetto/ubigeo-peru-aumentado
  (licencia MIT; 1.893 distritos y 196 provincias; última actualización en 2021). Archivo: `datos/crudos/ubigeo/`.
- **Límites:** es una aproximación (no todos los distritos tienen subprefecto designado en todo momento; Lima tiene además
  la prefectura de Lima Metropolitana); los distritos creados después de 2021 no se cuentan; en departamentos pequeños
  (Callao, 8 puestos; Tumbes, 14) pocas designaciones mueven mucho la tasa.

## R10. Códigos de persona: registro maestro de seudónimos (acordado con el autor el 01/11/2026)

- **Qué es:** cada persona recibe un código (por ejemplo, P-7K3QF). La tabla que une código y nombre completo es privada
  (`datos/privado/registro_personas.csv`, fuera de GitHub). El resto se publica completo: instituciones, cargos, fechas
  exactas y el **enlace a la norma** de cada caso en El Peruano, porque todas las resoluciones son públicas. El código
  sirve para concentrarse en estructuras y patrones sin señalar a nadie en particular.
- **Reglas:** (1) un código se asigna una sola vez y nunca cambia ni se reutiliza; el registro solo crece, así que los
  códigos publicados siguen valiendo al ampliar el periodo (por ejemplo, 2018-2022). (2) Códigos aleatorios, sin 0/O ni
  1/I: no revelan orden ni fecha. (3) Misma persona = misma clave normalizada o un alias registrado; el DNI se usa solo si
  la propia norma lo trae (29 % de las personas, casi todas subprefectos): un DNI distinto separa homónimos y un mismo
  DNI con otra escritura se registra como alias. (4) Si dos códigos resultan ser la misma persona, no se renumera: se
  marca "fusionado" y se indica el código que queda. (5) Solo `scripts/registro_personas.py` crea códigos.
  (6) Los casos dudosos (tratamiento pegado al nombre, textos que no son personas, homónimos) van a
  `datos/privado/revision_personas.csv` para que el autor decida.
- **Respaldo:** el registro debe guardarse también en un lugar privado; si se pierde, los códigos nuevos no coincidirían
  con los publicados.

## R7. Límites que valen para todos los indicadores

- Solo se ven las designaciones publicadas en El Peruano (no los CAS ni las órdenes de servicio).
- Ventana de cuatro años (nov-2022 a oct-2026): quien parece "nuevo" al inicio pudo tener cargos antes.
- Personas identificadas por nombre (solo el 13 % de los movimientos trae DNI): se excluyen los `nombre_dudoso`.
- Los datos muestran **quién se mueve con quién**, no por qué: no permiten distinguir un equipo técnico cohesionado de
  una red clientelar.
