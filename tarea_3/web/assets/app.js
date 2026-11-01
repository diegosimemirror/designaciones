// ============================================================
// Designaciones de El Peruano — lógica del dashboard
// Lee data/dashboard.json (cifras agregadas y códigos anónimos, script 08) y dibuja los gráficos con D3.
// Tres filtros globales (gobierno, ministerio, nivel) actualizan los indicadores y los gráficos.
// ============================================================
"use strict";

const ESTADO = { g: -1, m: -1, n: "todos" };
const GRUPOS = { todos: [0, 1, 2, 3, 4, 5, 6, 7], alta: [0, 1, 2], j4: [3], j5: [4], j67: [5, 6], sn: [7] };
const NOMBRE_GRUPO = { todos: "todos los niveles", alta: "alta dirección", j4: "directores generales y jefes de órgano",
  j5: "asesores", j67: "jefes de unidad y subunidad", sn: "cargos sin nivel" };
const local = d3.formatLocale({ decimal: ",", thousands: ".", grouping: [3], currency: ["S/", ""] });
const fmt = local.format(",d");
const fmt1 = local.format(",.1f");
const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "set", "oct", "nov", "dic"];
let D = null;
let GEO = null;
let vistaKM = "nivel";
let comunidadResaltada = null;
let vistaRank = "rotacion";
const TABLAS = {};          // id del gráfico -> {columnas, filas, abierta}
const tip = document.getElementById("tooltip");
const css = (nombre) => getComputedStyle(document.documentElement).getPropertyValue(nombre).trim();

// ---------- utilidades ----------
function el(etiqueta, clase, texto) {
  const nodo = document.createElement(etiqueta);
  if (clase) nodo.className = clase;
  if (texto !== undefined) nodo.textContent = texto;
  return nodo;
}
function mediana(valores) {
  const v = valores.filter((x) => x !== null && x !== undefined).sort((a, b) => a - b);
  if (!v.length) return null;
  const mitad = Math.floor(v.length / 2);
  return v.length % 2 ? v[mitad] : (v[mitad - 1] + v[mitad]) / 2;
}
function mesTexto(clave) { const [a, m] = clave.split("-"); return `${MESES[+m - 1]}-${a}`; }
function pct(x) { return x === null || x === undefined ? "—" : `${fmt1(x)} %`; }
function corta(texto, n) { return texto.length > n ? texto.slice(0, n - 1) + "…" : texto; }
function enFiltro(m, g, j) {
  return (ESTADO.m < 0 || m === ESTADO.m) && (ESTADO.g < 0 || g === ESTADO.g) && (j === null || GRUPOS[ESTADO.n].includes(j));
}

// Barras con extremo de dato redondeado (4px) y base recta
function barraH(x, y, w, h, r = 4) {
  if (w <= 0) return "";
  r = Math.min(r, w, h / 2);
  return `M${x},${y}H${x + w - r}Q${x + w},${y} ${x + w},${y + r}V${y + h - r}Q${x + w},${y + h} ${x + w - r},${y + h}H${x}Z`;
}
function barraV(x, y, w, h, r = 4) {
  if (h <= 0) return "";
  r = Math.min(r, h, w / 2);
  return `M${x},${y + h}V${y + r}Q${x},${y} ${x + r},${y}H${x + w - r}Q${x + w},${y} ${x + w},${y + r}V${y + h}Z`;
}

// ---------- tooltip (texto seguro: textContent) ----------
function mostrarTip(evento, titulo, filas) {
  tip.replaceChildren();
  if (titulo) tip.appendChild(el("div", "secundario", titulo));
  filas.forEach((f) => {
    const fila = el("div", "fila-tip");
    if (f.color) { const k = el("span", "clave"); k.style.background = f.color; fila.appendChild(k); }
    fila.appendChild(el("span", "valor-tip", f.valor));
    if (f.etiqueta) fila.appendChild(el("span", "secundario", f.etiqueta));
    tip.appendChild(fila);
  });
  const x = evento.clientX ?? (evento.target.getBoundingClientRect().left + 10);
  const y = evento.clientY ?? (evento.target.getBoundingClientRect().top);
  tip.style.opacity = 1;
  const ancho = tip.offsetWidth;
  tip.style.left = `${Math.min(x + 14, window.innerWidth - ancho - 8)}px`;
  tip.style.top = `${y + 14}px`;
}
function ocultarTip() { tip.style.opacity = 0; }

// ---------- tarjeta: título, subtítulo, leyenda, gráfico, vista de tabla y filtros que aplican ----------
function tarjeta(id, titulo, subtitulo, aplica) {
  const fig = document.querySelector(`[data-grafico="${id}"]`);
  fig.replaceChildren();
  const cab = el("div", "cabecera");
  const textos = el("div");
  textos.appendChild(el("h3", null, titulo));
  textos.appendChild(el("p", "subtitulo", subtitulo));
  cab.appendChild(textos);
  const boton = el("button", "boton-tabla", TABLAS[id]?.abierta ? "Ver gráfico" : "Ver tabla");
  boton.type = "button";
  boton.setAttribute("aria-expanded", TABLAS[id]?.abierta ? "true" : "false");
  cab.appendChild(boton);
  fig.appendChild(cab);
  const leyenda = el("div", "leyenda");
  fig.appendChild(leyenda);
  const grafico = el("div", "grafico");
  fig.appendChild(grafico);
  const tabla = el("div", "vista-tabla");
  tabla.hidden = !TABLAS[id]?.abierta;
  grafico.hidden = !!TABLAS[id]?.abierta;
  fig.appendChild(tabla);
  fig.appendChild(el("figcaption", null, `Filtros que aplican: ${aplica}`));
  boton.addEventListener("click", () => {
    TABLAS[id].abierta = !TABLAS[id].abierta;
    tabla.hidden = !TABLAS[id].abierta;
    grafico.hidden = TABLAS[id].abierta;
    boton.textContent = TABLAS[id].abierta ? "Ver gráfico" : "Ver tabla";
    boton.setAttribute("aria-expanded", TABLAS[id].abierta ? "true" : "false");
  });
  TABLAS[id] = TABLAS[id] || { abierta: false };
  return { fig, grafico, tabla, leyenda, ancho: Math.max(280, fig.clientWidth - 32) };
}
function ponerTabla(contenedor, columnas, filas) {
  const t = el("table");
  const cab = el("tr");
  columnas.forEach((c) => { const th = el("th", c.num ? "num" : null, c.nombre); cab.appendChild(th); });
  const thead = el("thead"); thead.appendChild(cab); t.appendChild(thead);
  const tbody = el("tbody");
  filas.forEach((f) => {
    const tr = el("tr");
    f.forEach((v, i) => {
      const td = el("td", columnas[i].num ? "num" : null);
      // Una celda puede traer enlaces: [{t: "texto", href: "https://..."}, ...] (normas de El Peruano)
      if (Array.isArray(v)) v.forEach((x, k) => {
        if (k) td.appendChild(document.createTextNode(" → "));
        if (x.href) { const a = el("a", null, x.t); a.href = x.href; a.target = "_blank"; a.rel = "noopener"; td.appendChild(a); }
        else td.appendChild(document.createTextNode(x.t));
      });
      else td.textContent = v === null ? "—" : String(v);
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  t.appendChild(tbody);
  contenedor.replaceChildren(t);
}
function ponerLeyenda(contenedor, items) {
  contenedor.replaceChildren();
  items.forEach((it) => {
    const s = el("span");
    const marca = el("i", it.tipo || "");
    marca.style.background = it.color;
    s.appendChild(marca);
    s.appendChild(document.createTextNode(it.texto));
    contenedor.appendChild(s);
  });
}
function vacio(contenedor, texto) { contenedor.replaceChildren(el("div", "vacio", texto)); }

// ---------- encabezado: fichas y cifra principal ----------
function renderPortada() {
  const fichas = document.getElementById("fichas");
  fichas.replaceChildren();
  [`Perú · nov-2022 a oct-2026`, `${fmt(D.meta.normas)} normas de personal`, `${fmt(D.meta.movimientos)} movimientos`,
   `${fmt(D.meta.personas_principal)} personas en el análisis principal`, `Fuente: Diario Oficial El Peruano`]
    .forEach((t) => fichas.appendChild(el("li", null, t)));
  const ultimo = D.gobiernos.length - 1;
  const fila = D.continuidad.find((r) => r[0] === ultimo && r[1] === "todos");
  const alta = D.continuidad.find((r) => r[0] === ultimo && r[1] !== "todos");
  const heroe = document.getElementById("heroe");
  heroe.replaceChildren();
  heroe.appendChild(el("div", "cifra", `${Math.round(fila[3])} %`));
  const p = el("p");
  p.append("de las ", el("strong", null, `${fmt(fila[2])} personas`),
    ` que designó el gobierno que asumió el ${D.gobiernos[ultimo].inicio.split("-").reverse().join("/")} ya había ocupado un cargo en el Estado entre 2022 y 2026. En los cargos altos (ministro a director general) es el `,
    el("strong", null, `${Math.round(alta[3])} %`), ".");
  heroe.appendChild(p);
  document.getElementById("generado").textContent = `Datos procesados el ${D.meta.generado}.`;
}

// ---------- indicadores ----------
function renderKpis() {
  const k = D.kpis[`${ESTADO.g}|${ESTADO.m}|${ESTADO.n}`] || [0, 0, null, null, 0, null];
  const otras = ESTADO.m === D.ministerios.length - 1;
  const tiles = [
    ["Designaciones", fmt(k[0]), "designaciones, nombramientos y encargos"],
    ["Personas distintas designadas", fmt(k[1]), "cada persona con un código anónimo (sin nombres dudosos)"],
    ESTADO.g >= 0
      ? ["Ya habían tenido un cargo en un gobierno anterior", pct(k[2]), ESTADO.g <= 1 ? "poco comparable: la base empieza en nov-2022" : "% de esas personas, según la base desde nov-2022"]
      : ["Tuvieron cargos en dos o más gobiernos", pct(k[2]), "% de esas personas (cinco gobiernos en la ventana)"],
    ["Mujeres entre los designados", pct(k[3]), "sexo según la norma o el nombre de pila"],
    ["Ministros que llegaron", otras ? "—" : fmt(k[4]), otras ? "no aplica a estas entidades" : (ESTADO.m < 0 ? "en todas las carteras" : "en esta cartera")],
    ["Duración mediana en el cargo", k[5] === null ? "—" : `${fmt(k[5])} días`,
      k[5] === null ? "aún no sale la mitad de los titulares, o hay pocos datos" : "titulares de puestos únicos (Kaplan-Meier)"],
  ];
  const cont = document.getElementById("kpis");
  cont.replaceChildren();
  tiles.forEach(([etq, valor, det]) => {
    const t = el("div", "kpi");
    t.appendChild(el("p", "etiqueta", etq));
    t.appendChild(el("p", "valor", valor));
    t.appendChild(el("p", "detalle", det));
    cont.appendChild(t);
  });
}

// ---------- 1. Continuidad del elenco entre gobiernos (barras agrupadas) ----------
function renderContinuidad() {
  const c = tarjeta("continuidad", "Designados por cada gobierno nuevo que ya habían tenido un cargo",
    "% de las personas designadas en sus primeros seis meses (o hasta el siguiente cambio de gobierno)", "gobierno (resalta)");
  const series = [{ clave: "todos", nombre: "Todos los designados", color: css("--series-1") },
                  { clave: "alta", nombre: "Ministro a director general (J1-J4)", color: css("--series-2") }];
  ponerLeyenda(c.leyenda, series.map((s) => ({ color: s.color, texto: s.nombre })));
  const datos = D.continuidad.map((r) => ({ g: r[0], serie: r[1] === "todos" ? "todos" : "alta", n: r[2], pct: r[3], inmediato: r[4] }));
  const gobs = [...new Set(datos.map((d) => d.g))];
  const W = c.ancho, H = 260, M = { t: 24, r: 8, b: 44, l: 36 };
  const x = d3.scaleBand().domain(gobs).range([M.l, W - M.r]).padding(0.3);
  const xi = d3.scaleBand().domain(["todos", "alta"]).range([0, x.bandwidth()]).padding(0.12);
  const y = d3.scaleLinear().domain([0, 100]).range([H - M.b, M.t]);
  const svg = d3.select(c.grafico).append("svg").attr("viewBox", `0 0 ${W} ${H}`).attr("role", "img")
    .attr("aria-label", "Barras: porcentaje de designados con cargo previo por gobierno entrante");
  svg.append("g").attr("class", "rejilla-linea").attr("transform", `translate(${M.l},0)`)
    .call(d3.axisLeft(y).ticks(4).tickSize(-(W - M.l - M.r)).tickFormat(""));
  svg.append("g").attr("class", "eje").attr("transform", `translate(${M.l},0)`)
    .call(d3.axisLeft(y).ticks(4).tickFormat((v) => `${v} %`).tickSize(0)).call((g) => g.select(".domain").remove());
  const ejeX = svg.append("g").attr("class", "eje").attr("transform", `translate(0,${H - M.b})`)
    .call(d3.axisBottom(x).tickSize(0).tickFormat((g) => D.gobiernos[g].corto));
  ejeX.selectAll("text").attr("dy", "1.2em");
  ejeX.append("g").selectAll("text").data(gobs).join("text").attr("x", (g) => x(g) + x.bandwidth() / 2).attr("y", 30)
    .attr("text-anchor", "middle").attr("class", "etiqueta-eje").text((g) => D.gobiernos[g].inicio.slice(0, 7).split("-").reverse().join("/"));
  const ancho = Math.min(24, xi.bandwidth());
  const destacado = ESTADO.g >= 1 ? ESTADO.g : gobs[gobs.length - 1];
  svg.append("g").selectAll("path").data(datos).join("path").attr("class", "marca").attr("tabindex", 0)
    .attr("d", (d) => barraV(x(d.g) + xi(d.serie) + (xi.bandwidth() - ancho) / 2, y(d.pct), ancho, y(0) - y(d.pct)))
    .attr("fill", (d) => series.find((s) => s.clave === d.serie).color)
    .attr("opacity", (d) => (ESTADO.g >= 0 && d.g !== ESTADO.g ? 0.35 : 1))
    .attr("aria-label", (d) => `${D.gobiernos[d.g].corto}, ${series.find((s) => s.clave === d.serie).nombre}: ${fmt1(d.pct)} %`)
    .on("pointermove focus", (e, d) => mostrarTip(e, `Gobierno de ${D.gobiernos[d.g].corto}`, [
      { valor: `${fmt1(d.pct)} %`, etiqueta: series.find((s) => s.clave === d.serie).nombre, color: series.find((s) => s.clave === d.serie).color },
      { valor: fmt(d.n), etiqueta: "personas designadas" },
      { valor: `${fmt1(d.inmediato)} %`, etiqueta: "con cargo en el gobierno inmediato anterior" }]))
    .on("pointerleave blur", ocultarTip);
  // Etiqueta solo en el gobierno destacado (selectiva)
  svg.append("g").selectAll("text").data(datos.filter((d) => d.g === destacado)).join("text").attr("class", "texto-fuerte")
    .attr("x", (d) => x(d.g) + xi(d.serie) + xi.bandwidth() / 2).attr("y", (d) => y(d.pct) - 6).attr("text-anchor", "middle")
    .text((d) => `${Math.round(d.pct)} %`);
  ponerTabla(c.tabla, [{ nombre: "Gobierno que entra" }, { nombre: "Grupo" }, { nombre: "Personas designadas", num: true },
    { nombre: "% con cargo previo", num: true }, { nombre: "% con cargo en el gobierno anterior", num: true }],
    datos.map((d) => [D.gobiernos[d.g].etiqueta, series.find((s) => s.clave === d.serie).nombre, fmt(d.n), fmt1(d.pct), fmt1(d.inmediato)]));
  const nota = c.fig.querySelector("figcaption");
  nota.textContent = `Gobierno de ${D.gobiernos[1].corto}: la base empieza en nov-2022, así que solo se ve un mes hacia atrás y su valor no es comparable. ` + nota.textContent;
}

// ---------- Serie mensual de designaciones (olas) ----------
function renderSerie() {
  const c = tarjeta("serie", "Designaciones por mes: el recambio llega en olas",
    `Análisis principal · ${ESTADO.m >= 0 ? D.ministerios[ESTADO.m] : "todas las entidades"} · ${NOMBRE_GRUPO[ESTADO.n]}`,
    "ministerio, nivel; gobierno (sombrea el periodo)");
  const suma = new Array(D.meses.length).fill(0);
  D.cubo.forEach(([mi, g, m, j, s, n]) => { if ((ESTADO.m < 0 || m === ESTADO.m) && GRUPOS[ESTADO.n].includes(j)) suma[mi] += n; });
  const datos = D.meses.map((mes, i) => ({ fecha: new Date(+mes.slice(0, 4), +mes.slice(5) - 1, 1), mes, n: suma[i] }));
  const W = c.ancho, H = 270, M = { t: 38, r: 12, b: 28, l: 40 };
  const x = d3.scaleTime().domain(d3.extent(datos, (d) => d.fecha)).range([M.l, W - M.r]);
  const y = d3.scaleLinear().domain([0, d3.max(datos, (d) => d.n) || 1]).nice().range([H - M.b, M.t]);
  const svg = d3.select(c.grafico).append("svg").attr("viewBox", `0 0 ${W} ${H}`).attr("role", "img")
    .attr("aria-label", "Línea: designaciones por mes");
  if (ESTADO.g >= 0) {
    const g = D.gobiernos[ESTADO.g];
    const x0 = x(Math.max(new Date(g.inicio), x.domain()[0])), x1 = x(Math.min(new Date(g.fin), x.domain()[1]));
    svg.append("rect").attr("x", x0).attr("y", M.t).attr("width", Math.max(0, x1 - x0)).attr("height", H - M.b - M.t).attr("fill", css("--wash"));
  }
  svg.append("g").attr("class", "rejilla-linea").attr("transform", `translate(${M.l},0)`)
    .call(d3.axisLeft(y).ticks(4).tickSize(-(W - M.l - M.r)).tickFormat(""));
  svg.append("g").attr("class", "eje").attr("transform", `translate(${M.l},0)`)
    .call(d3.axisLeft(y).ticks(4).tickFormat(fmt).tickSize(0)).call((g) => g.select(".domain").remove());
  svg.append("g").attr("class", "eje").attr("transform", `translate(0,${H - M.b})`)
    .call(d3.axisBottom(x).ticks(d3.timeMonth.every(W < 500 ? 12 : 6)).tickFormat((d) => `${MESES[d.getMonth()]}-${String(d.getFullYear()).slice(2)}`));
  // Cambios de gobierno: si una etiqueta queda muy cerca de la anterior, sube una línea (no se enciman)
  let xAnterior = -Infinity, alto = 0;
  D.gobiernos.slice(1).forEach((g) => {
    const xg = x(new Date(g.inicio));
    alto = xg - xAnterior < 62 ? 1 - alto : 0;
    xAnterior = xg;
    svg.append("line").attr("x1", xg).attr("x2", xg).attr("y1", M.t - 4 - alto * 12).attr("y2", H - M.b).attr("stroke", css("--axis"));
    svg.append("text").attr("class", "etiqueta-eje").attr("x", xg + 3).attr("y", M.t - 8 - alto * 12).text(g.corto);
  });
  const color = css("--series-1");
  svg.append("path").datum(datos).attr("fill", color).attr("opacity", 0.1)
    .attr("d", d3.area().x((d) => x(d.fecha)).y0(y(0)).y1((d) => y(d.n)).curve(d3.curveMonotoneX));
  svg.append("path").datum(datos).attr("fill", "none").attr("stroke", color).attr("stroke-width", 2)
    .attr("stroke-linejoin", "round").attr("stroke-linecap", "round")
    .attr("d", d3.line().x((d) => x(d.fecha)).y((d) => y(d.n)).curve(d3.curveMonotoneX));
  const pico = datos.reduce((a, b) => (b.n > a.n ? b : a), datos[0]);
  svg.append("circle").attr("cx", x(pico.fecha)).attr("cy", y(pico.n)).attr("r", 4).attr("fill", color)
    .attr("stroke", css("--surface-1")).attr("stroke-width", 2);
  // Etiqueta del pico a un costado del punto (arriba están los nombres de los gobiernos)
  const aLaIzquierda = x(pico.fecha) > W / 2;
  svg.append("text").attr("class", "texto-fuerte").attr("x", x(pico.fecha) + (aLaIzquierda ? -8 : 8)).attr("y", y(pico.n) + 4)
    .attr("text-anchor", aLaIzquierda ? "end" : "start").text(`${fmt(pico.n)} (${mesTexto(pico.mes)})`);
  // Cruz de lectura: sigue al puntero y se ajusta al mes más cercano
  const cruz = svg.append("line").attr("y1", M.t).attr("y2", H - M.b).attr("stroke", css("--text-muted")).attr("opacity", 0);
  const punto = svg.append("circle").attr("r", 4).attr("fill", color).attr("stroke", css("--surface-1")).attr("stroke-width", 2).attr("opacity", 0);
  svg.append("rect").attr("x", M.l).attr("y", M.t).attr("width", W - M.l - M.r).attr("height", H - M.t - M.b)
    .attr("fill", "transparent")
    .on("pointermove", (e) => {
      const [px] = d3.pointer(e);
      const i = d3.bisectCenter(datos.map((d) => +d.fecha), +x.invert(px));
      const d = datos[Math.max(0, Math.min(datos.length - 1, i))];
      cruz.attr("x1", x(d.fecha)).attr("x2", x(d.fecha)).attr("opacity", 1);
      punto.attr("cx", x(d.fecha)).attr("cy", y(d.n)).attr("opacity", 1);
      mostrarTip(e, mesTexto(d.mes), [{ valor: fmt(d.n), etiqueta: "designaciones", color }]);
    })
    .on("pointerleave", () => { cruz.attr("opacity", 0); punto.attr("opacity", 0); ocultarTip(); });
  ponerTabla(c.tabla, [{ nombre: "Mes" }, { nombre: "Designaciones", num: true }], datos.map((d) => [mesTexto(d.mes), fmt(d.n)]));
}

// ---------- 2. Armado del equipo (barras horizontales: días hasta la primera designación) ----------
function renderArmado() {
  const c = tarjeta("armado", "Días desde que llega el ministro hasta la primera designación en cada área",
    "Mediana entre las llegadas de ministros · sede central del ministerio", "gobierno, ministerio");
  const filas = D.armado.filter((r) => (ESTADO.m < 0 || r[0] === ESTADO.m) && (ESTADO.g < 0 || r[1] === ESTADO.g));
  c.fig.querySelector(".subtitulo").textContent =
    filas.length === 1 ? "Una llegada de ministro · sede central del ministerio"
      : `Mediana entre ${fmt(filas.length)} llegadas de ministros · sede central del ministerio`;
  if (filas.length < 1) { vacio(c.grafico, "No hay llegadas de ministros para esta selección."); ponerTabla(c.tabla, [{ nombre: "Sin datos" }], []); return; }
  const datos = D.familias.map((f, i) => {
    const v = filas.map((r) => r[2 + i]).filter((x) => x !== null);
    return { familia: f, dias: mediana(v), pct: (100 * v.length) / filas.length, n: v.length };
  }).filter((d) => d.dias !== null).sort((a, b) => a.dias - b.dias);
  const W = c.ancho, fila = 34, M = { t: 6, r: 150, b: 22, l: 8 }, H = M.t + M.b + fila * datos.length;
  const x = d3.scaleLinear().domain([0, Math.max(30, d3.max(datos, (d) => d.dias))]).nice().range([M.l, W - M.r]);
  const svg = d3.select(c.grafico).append("svg").attr("viewBox", `0 0 ${W} ${H}`).attr("role", "img")
    .attr("aria-label", "Barras: días hasta la primera designación por área");
  svg.append("g").attr("class", "rejilla-linea").attr("transform", `translate(0,${H - M.b})`)
    .call(d3.axisBottom(x).ticks(5).tickSize(-(H - M.t - M.b)).tickFormat(""));
  svg.append("g").attr("class", "eje").attr("transform", `translate(0,${H - M.b})`)
    .call(d3.axisBottom(x).ticks(5).tickFormat((v) => `${v} d`).tickSize(0)).call((g) => g.select(".domain").remove());
  const color = css("--series-1");
  const g = svg.append("g").selectAll("g").data(datos).join("g").attr("transform", (d, i) => `translate(0,${M.t + i * fila})`);
  g.append("text").attr("class", "texto-dato").attr("x", M.l).attr("y", 11).text((d) => d.familia);
  g.append("path").attr("class", "marca").attr("tabindex", 0).attr("fill", color)
    .attr("d", (d) => barraH(x(0), 16, Math.max(2, x(d.dias) - x(0)), 10))
    .attr("aria-label", (d) => `${d.familia}: ${fmt1(d.dias)} días`)
    .on("pointermove focus", (e, d) => mostrarTip(e, d.familia, [{ valor: `${fmt1(d.dias)} días`, etiqueta: "mediana", color },
      { valor: `${fmt1(d.pct)} %`, etiqueta: `de las llegadas renovó esta área (${fmt(d.n)})` }]))
    .on("pointerleave blur", ocultarTip);
  g.append("text").attr("class", "texto-fuerte").attr("x", (d) => x(d.dias) + 6).attr("y", 25).text((d) => `${fmt1(d.dias)} d`);
  g.append("text").attr("class", "etiqueta-eje").attr("x", (d) => x(d.dias) + 46).attr("y", 25).text((d) => `en ${Math.round(d.pct)} % de llegadas`);
  ponerTabla(c.tabla, [{ nombre: "Área" }, { nombre: "Días (mediana)", num: true }, { nombre: "% de llegadas que la renovó", num: true },
    { nombre: "Llegadas con renovación", num: true }], datos.map((d) => [d.familia, fmt1(d.dias), fmt1(d.pct), fmt(d.n)]));
}

// ---------- Rotación ministerial ----------
function renderRotacion() {
  const c = tarjeta("rotacion", "Ministros que llegaron a cada cartera", "Designaciones de ministros (y del Presidente del Consejo de Ministros)",
    "gobierno; ministerio (resalta)");
  const porM = d3.rollup(D.llegadas.filter((r) => ESTADO.g < 0 || r[1] === ESTADO.g), (v) => ({
    n: v.length, dias: mediana(v.filter((r) => r[3] === 0).map((r) => r[2])) }), (r) => r[0]);
  const datos = [...porM].filter(([m]) => m < D.ministerios.length - 1).map(([m, v]) => ({ m, nombre: D.ministerios[m], ...v }))
    .sort((a, b) => b.n - a.n);
  if (!datos.length) { vacio(c.grafico, "Sin llegadas de ministros en este periodo."); return; }
  const W = c.ancho, fila = 22, M = { t: 4, r: 40, b: 20, l: Math.min(250, W * 0.5) }, H = M.t + M.b + fila * datos.length;
  const x = d3.scaleLinear().domain([0, d3.max(datos, (d) => d.n)]).nice().range([M.l, W - M.r]);
  const y = d3.scaleBand().domain(datos.map((d) => d.m)).range([M.t, H - M.b]).padding(0.25);
  const svg = d3.select(c.grafico).append("svg").attr("viewBox", `0 0 ${W} ${H}`).attr("role", "img")
    .attr("aria-label", "Barras: ministros por cartera");
  const color = css("--series-1");
  svg.append("g").selectAll("text").data(datos).join("text").attr("class", "texto-dato").attr("x", M.l - 6)
    .attr("y", (d) => y(d.m) + y.bandwidth() / 2 + 4).attr("text-anchor", "end").text((d) => corta(d.nombre, Math.floor(M.l / 6.5)));
  svg.append("g").selectAll("path").data(datos).join("path").attr("class", "marca").attr("tabindex", 0).attr("fill", color)
    .attr("opacity", (d) => (ESTADO.m >= 0 && d.m !== ESTADO.m ? 0.35 : 1))
    .attr("d", (d) => barraH(x(0), y(d.m) + (y.bandwidth() - Math.min(14, y.bandwidth())) / 2, x(d.n) - x(0), Math.min(14, y.bandwidth())))
    .attr("aria-label", (d) => `${d.nombre}: ${d.n} ministros`)
    .on("pointermove focus", (e, d) => mostrarTip(e, d.nombre, [{ valor: fmt(d.n), etiqueta: "ministros que llegaron", color },
      { valor: d.dias === null ? "—" : `${fmt(d.dias)} días`, etiqueta: "duración mediana de cada ministro (terminados)" }]))
    .on("pointerleave blur", ocultarTip);
  svg.append("g").selectAll("text").data(datos).join("text").attr("class", "texto-fuerte")
    .attr("x", (d) => x(d.n) + 5).attr("y", (d) => y(d.m) + y.bandwidth() / 2 + 4).text((d) => d.n);
  ponerTabla(c.tabla, [{ nombre: "Cartera" }, { nombre: "Ministros", num: true }, { nombre: "Días por ministro (mediana)", num: true }],
    datos.map((d) => [d.nombre, d.n, d.dias === null ? null : fmt(d.dias)]));
}

// ---------- Puestos con más titulares ----------
function renderPuestos() {
  const c = tarjeta("puestos", "Puestos con más titulares", "Periodos de titulares que empezaron en la selección (12 puestos con más cambios)",
    "gobierno, ministerio, nivel");
  const cuenta = new Map();
  D.periodos.forEach(([m, g, j, s, dias, abierto, p]) => {
    if (!enFiltro(m, g, j)) return;
    const v = cuenta.get(p) || { n: 0, dias: [] };
    v.n += 1; v.dias.push(dias);
    cuenta.set(p, v);
  });
  const datos = [...cuenta].map(([p, v]) => ({ nombre: D.puestos[p], n: v.n, dias: mediana(v.dias) }))
    .sort((a, b) => b.n - a.n || a.dias - b.dias).slice(0, 12);
  if (!datos.length) { vacio(c.grafico, "Sin puestos para esta selección."); ponerTabla(c.tabla, [{ nombre: "Sin datos" }], []); return; }
  const W = c.ancho, fila = 36, M = { t: 4, r: 40, b: 4, l: 8 }, H = M.t + M.b + fila * datos.length;
  const x = d3.scaleLinear().domain([0, d3.max(datos, (d) => d.n)]).nice().range([M.l, W - M.r]);
  const color = css("--series-1");
  const svg = d3.select(c.grafico).append("svg").attr("viewBox", `0 0 ${W} ${H}`).attr("role", "img")
    .attr("aria-label", "Barras: puestos con más titulares");
  const g = svg.append("g").selectAll("g").data(datos).join("g").attr("transform", (d, i) => `translate(0,${M.t + i * fila})`);
  g.append("text").attr("class", "texto-dato").attr("x", M.l).attr("y", 12).text((d) => corta(d.nombre, Math.floor(W / 6.6)));
  g.append("path").attr("class", "marca").attr("tabindex", 0).attr("fill", color)
    .attr("d", (d) => barraH(x(0), 18, x(d.n) - x(0), 10))
    .attr("aria-label", (d) => `${d.nombre}: ${d.n} titulares`)
    .on("pointermove focus", (e, d) => mostrarTip(e, d.nombre, [{ valor: fmt(d.n), etiqueta: "periodos de titulares", color },
      { valor: `${fmt(d.dias)} días`, etiqueta: "duración mediana de cada periodo" }]))
    .on("pointerleave blur", ocultarTip);
  g.append("text").attr("class", "texto-fuerte").attr("x", (d) => x(d.n) + 5).attr("y", 27).text((d) => d.n);
  ponerTabla(c.tabla, [{ nombre: "Puesto" }, { nombre: "Titulares", num: true }, { nombre: "Días por titular (mediana)", num: true }],
    datos.map((d) => [d.nombre, d.n, fmt(d.dias)]));
}

// ---------- Supervivencia en el cargo (Kaplan-Meier) ----------
function kaplanMeier(periodos, maximo = 1100) {
  const ordenados = periodos.slice().sort((a, b) => a.dias - b.dias);
  let enRiesgo = ordenados.length, sigue = 1;
  const puntos = [{ dia: 0, pct: 100 }];
  let i = 0;
  while (i < ordenados.length) {
    const dia = ordenados[i].dias;
    let eventos = 0, total = 0;
    while (i < ordenados.length && ordenados[i].dias === dia) { if (!ordenados[i].abierto) eventos += 1; total += 1; i += 1; }
    if (eventos) { sigue *= 1 - eventos / enRiesgo; if (dia <= maximo) puntos.push({ dia, pct: 100 * sigue }); }
    enRiesgo -= total;
  }
  const med = puntos.find((p) => p.pct <= 50);
  return { puntos, mediana: med ? med.dia : null };
}
function renderSupervivencia() {
  const c = tarjeta("supervivencia", "¿Cuánto duran en el cargo?", "% de titulares que siguen en el puesto después de cierto número de días",
    vistaKM === "nivel" ? "gobierno, ministerio (el nivel es la comparación)" : "gobierno, ministerio, nivel");
  const selector = el("div", "selector-vista");
  [["nivel", "Comparar por nivel"], ["sexo", "Comparar mujeres y hombres"]].forEach(([v, t]) => {
    const b = el("button", null, t); b.type = "button"; b.setAttribute("aria-pressed", vistaKM === v ? "true" : "false");
    b.addEventListener("click", () => { vistaKM = v; renderSupervivencia(); });
    selector.appendChild(b);
  });
  c.fig.insertBefore(selector, c.leyenda);
  const base = D.periodos.filter(([m, g, j]) => (ESTADO.m < 0 || m === ESTADO.m) && (ESTADO.g < 0 || g === ESTADO.g)
    && (vistaKM === "nivel" || GRUPOS[ESTADO.n].includes(j)))
    .map(([m, g, j, s, dias, abierto]) => ({ j, s, dias, abierto }));
  const colores = [css("--series-1"), css("--series-2"), css("--series-3")];
  const grupos = vistaKM === "nivel"
    ? [["Alta dirección (J1-J3)", (p) => p.j <= 2], ["Directores generales y jefes de órgano (J4)", (p) => p.j === 3], ["Jefes de unidad y subunidad (J6-J7)", (p) => p.j === 5 || p.j === 6]]
    : [["Mujeres", (p) => p.s === 0], ["Hombres", (p) => p.s === 1]];
  const curvas = grupos.map(([nombre, f], i) => ({ nombre, color: colores[i], ...kaplanMeier(base.filter(f)), n: base.filter(f).length }))
    .filter((cv) => cv.n >= 20);
  ponerLeyenda(c.leyenda, curvas.map((cv) => ({ color: cv.color, tipo: "linea",
    texto: `${cv.nombre} · mediana ${cv.mediana === null ? "más de 1.100" : fmt(cv.mediana)} días` })));
  if (!curvas.length) { vacio(c.grafico, "Muy pocos periodos para esta selección."); return; }
  const W = c.ancho, H = 260, M = { t: 10, r: 14, b: 30, l: 40 };
  const x = d3.scaleLinear().domain([0, 1100]).range([M.l, W - M.r]);
  const y = d3.scaleLinear().domain([0, 100]).range([H - M.b, M.t]);
  const svg = d3.select(c.grafico).append("svg").attr("viewBox", `0 0 ${W} ${H}`).attr("role", "img")
    .attr("aria-label", "Líneas escalonadas: porcentaje que sigue en el cargo");
  svg.append("g").attr("class", "rejilla-linea").attr("transform", `translate(${M.l},0)`)
    .call(d3.axisLeft(y).ticks(4).tickSize(-(W - M.l - M.r)).tickFormat(""));
  svg.append("g").attr("class", "eje").attr("transform", `translate(${M.l},0)`)
    .call(d3.axisLeft(y).ticks(4).tickFormat((v) => `${v} %`).tickSize(0)).call((g) => g.select(".domain").remove());
  svg.append("g").attr("class", "eje").attr("transform", `translate(0,${H - M.b})`)
    .call(d3.axisBottom(x).tickValues([0, 180, 365, 730, 1095]).tickFormat((v) => ({ 0: "0", 180: "6 meses", 365: "1 año", 730: "2 años", 1095: "3 años" }[v])));
  const linea = d3.line().x((p) => x(p.dia)).y((p) => y(p.pct)).curve(d3.curveStepAfter);
  curvas.forEach((cv) => {
    const pts = cv.puntos.concat([{ dia: 1100, pct: cv.puntos[cv.puntos.length - 1].pct }]);
    svg.append("path").datum(pts).attr("fill", "none").attr("stroke", cv.color).attr("stroke-width", 2).attr("d", linea);
  });
  const cruz = svg.append("line").attr("y1", M.t).attr("y2", H - M.b).attr("stroke", css("--text-muted")).attr("opacity", 0);
  const valorEn = (cv, dia) => { let v = 100; for (const p of cv.puntos) { if (p.dia <= dia) v = p.pct; else break; } return v; };
  svg.append("rect").attr("x", M.l).attr("y", M.t).attr("width", W - M.l - M.r).attr("height", H - M.t - M.b).attr("fill", "transparent")
    .on("pointermove", (e) => {
      const dia = Math.round(Math.max(0, x.invert(d3.pointer(e)[0])));
      cruz.attr("x1", x(dia)).attr("x2", x(dia)).attr("opacity", 1);
      mostrarTip(e, `Después de ${fmt(dia)} días`, curvas.map((cv) => ({ valor: `${fmt1(valorEn(cv, dia))} %`, etiqueta: cv.nombre, color: cv.color })));
    })
    .on("pointerleave", () => { cruz.attr("opacity", 0); ocultarTip(); });
  ponerTabla(c.tabla, [{ nombre: "Grupo" }, { nombre: "Periodos", num: true }, { nombre: "Mediana (días)", num: true },
    { nombre: "Siguen a 6 meses", num: true }, { nombre: "Siguen al año", num: true }],
    curvas.map((cv) => [cv.nombre, fmt(cv.n), cv.mediana === null ? null : fmt(cv.mediana), `${fmt1(valorEn(cv, 180))} %`, `${fmt1(valorEn(cv, 365))} %`]));
}

// ---------- Mujeres por nivel ----------
function renderGenero() {
  const c = tarjeta("genero", "Mujeres entre los designados, por nivel del cargo", "% de mujeres entre las designaciones con sexo conocido",
    "gobierno, ministerio");
  const f = new Array(7).fill(0), t = new Array(7).fill(0);
  D.cubo.forEach(([mi, g, m, j, s, n]) => {
    if (j > 6 || s < 0 || (ESTADO.m >= 0 && m !== ESTADO.m) || (ESTADO.g >= 0 && g !== ESTADO.g)) return;
    t[j] += n; if (s === 0) f[j] += n;
  });
  const datos = D.niveles.slice(0, 7).map((nombre, j) => ({ nombre, n: t[j], pct: t[j] ? (100 * f[j]) / t[j] : null })).filter((d) => d.n >= 5);
  if (!datos.length) { vacio(c.grafico, "Sin datos para esta selección."); return; }
  const W = c.ancho, fila = 34, M = { t: 16, r: 50, b: 22, l: 8 }, H = M.t + M.b + fila * datos.length;
  const x = d3.scaleLinear().domain([0, 100]).range([M.l, W - M.r]);
  const color = css("--series-1");
  const svg = d3.select(c.grafico).append("svg").attr("viewBox", `0 0 ${W} ${H}`).attr("role", "img").attr("aria-label", "Barras: porcentaje de mujeres por nivel");
  svg.append("g").attr("class", "eje").attr("transform", `translate(0,${H - M.b})`)
    .call(d3.axisBottom(x).tickValues([0, 25, 50, 75, 100]).tickFormat((v) => `${v} %`).tickSize(0)).call((g) => g.select(".domain").remove());
  svg.append("line").attr("x1", x(50)).attr("x2", x(50)).attr("y1", M.t - 4).attr("y2", H - M.b).attr("stroke", css("--axis"));
  svg.append("text").attr("class", "etiqueta-eje").attr("x", x(50) + 4).attr("y", M.t - 6).text("paridad");
  const g = svg.append("g").selectAll("g").data(datos).join("g").attr("transform", (d, i) => `translate(0,${M.t + i * fila})`);
  g.append("text").attr("class", "texto-dato").attr("x", M.l).attr("y", 11).text((d) => d.nombre);
  g.append("path").attr("class", "marca").attr("tabindex", 0).attr("fill", color).attr("d", (d) => barraH(x(0), 16, x(d.pct) - x(0), 10))
    .attr("aria-label", (d) => `${d.nombre}: ${fmt1(d.pct)} % mujeres`)
    .on("pointermove focus", (e, d) => mostrarTip(e, d.nombre, [{ valor: `${fmt1(d.pct)} %`, etiqueta: "mujeres", color },
      { valor: fmt(d.n), etiqueta: "designaciones con sexo conocido" }]))
    .on("pointerleave blur", ocultarTip);
  g.append("text").attr("class", "texto-fuerte").attr("x", (d) => x(d.pct) + 5).attr("y", 25).text((d) => `${Math.round(d.pct)} %`);
  ponerTabla(c.tabla, [{ nombre: "Nivel" }, { nombre: "Designaciones", num: true }, { nombre: "% mujeres", num: true }],
    datos.map((d) => [d.nombre, fmt(d.n), fmt1(d.pct)]));
}

// ---------- Mapa de subprefectos ----------
function renderMapa() {
  // Designaciones divididas entre los puestos de cada departamento (un puesto por distrito más la prefectura regional):
  // así se compara Áncash (166 distritos) con Tumbes (13) sin que gane el que tiene más distritos
  const c = tarjeta("mapa", "Cambios de subprefecto por subprefectura, por departamento",
    `${ESTADO.g >= 0 ? `Gobierno de ${D.gobiernos[ESTADO.g].corto}` : "Cuatro años (nov-2022 a oct-2026)"} · designaciones de subprefectos y prefectos ÷ número de subprefecturas (un puesto por distrito, más la prefectura)`,
    "gobierno");
  const puestos = new Map(D.puestos_subprefecto.map(([dep, distritos, provincias, p]) => [dep, { distritos, provincias, p }]));
  const cuenta = new Map();
  D.subprefectos.forEach(([dep, g, n]) => { if (ESTADO.g < 0 || g === ESTADO.g) cuenta.set(dep, (cuenta.get(dep) || 0) + n); });
  const tasa = new Map([...cuenta].filter(([d]) => puestos.has(d)).map(([d, n]) => [d, n / puestos.get(d).p]));
  // Escala del valor más bajo al más alto (todos los departamentos están entre 1 y 2,5 en los cuatro años)
  const [minimo, maximo] = d3.extent([...tasa.values()]);
  const pasos = [css("--seq-200"), css("--seq-300"), css("--seq-400"), css("--seq-500"), css("--seq-700")];
  const escala = d3.scaleQuantize().domain([minimo ?? 0, maximo ?? 1]).range(pasos);
  const W = c.ancho, H = Math.min(560, Math.round(W * 1.25));
  const proy = d3.geoMercator().fitSize([W, H - 10], GEO);
  const ruta = d3.geoPath(proy);
  const svg = d3.select(c.grafico).append("svg").attr("viewBox", `0 0 ${W} ${H}`).attr("role", "img")
    .attr("aria-label", "Mapa: cambios de subprefecto por subprefectura en cada departamento");
  const dep = (f) => f.properties.NOMBDEP;
  svg.append("g").selectAll("path").data(GEO.features).join("path").attr("class", "marca").attr("tabindex", 0).attr("d", ruta)
    .attr("fill", (f) => (tasa.has(dep(f)) ? escala(tasa.get(dep(f))) : css("--empty")))
    .attr("stroke", css("--surface-1")).attr("stroke-width", 1)
    .attr("aria-label", (f) => `${dep(f)}: ${fmt1(tasa.get(dep(f)) || 0)} cambios por subprefectura`)
    .on("pointermove focus", (e, f) => {
      const pu = puestos.get(dep(f)) || { distritos: 0, p: 0 };
      mostrarTip(e, dep(f), [
        { valor: fmt1(tasa.get(dep(f)) || 0), etiqueta: "cambios por subprefectura (en promedio)" },
        { valor: fmt(cuenta.get(dep(f)) || 0), etiqueta: `designaciones en ${fmt(pu.p)} puestos (${fmt(pu.distritos)} distritos + prefectura)` }]);
    })
    .on("pointerleave blur", ocultarTip);
  const umbrales = escala.thresholds();
  ponerLeyenda(c.leyenda, pasos.map((p, i) => ({ color: p, texto: i === 0 ? `menos de ${fmt1(umbrales[0])}`
    : i === pasos.length - 1 ? `${fmt1(umbrales[i - 1])} o más` : `${fmt1(umbrales[i - 1])} a ${fmt1(umbrales[i])}` })));
  const filas = [...tasa].sort((a, b) => b[1] - a[1]);
  ponerTabla(c.tabla, [{ nombre: "Departamento" }, { nombre: "Distritos", num: true }, { nombre: "Designaciones", num: true },
    { nombre: "Cambios por subprefectura", num: true }],
    filas.map(([d, r]) => [d, fmt(puestos.get(d).distritos), fmt(cuenta.get(d)), fmt1(r)]));
}

// ---------- Rankings de personas: rotación y permanencia ----------
const PDF_NORMA = "https://epdoc2.elperuano.pe/EpPo/DescargaIN.asp?Referencias=";
const enlaceNorma = (ref) => (ref ? PDF_NORMA + ref : null);
function duracionTexto(dias) {
  return dias < 60 ? `${fmt(dias)} días` : dias < 730 ? `${fmt1(dias / 30.44)} meses` : `${fmt1(dias / 365.25)} años`;
}
function renderTrayectorias() {
  const R = D.rankings, esRot = vistaRank === "rotacion";
  const c = tarjeta("trayectorias",
    esRot ? "Quiénes pasaron por más cargos en menos tiempo" : "Quiénes permanecieron más tiempo en el mismo puesto",
    esRot ? "Los 20 con más cargos distintos iniciados en 12 meses (desempate: más cargos en total y menos días por cargo) · cada barra es un cargo: clic para abrir su norma en El Peruano"
          : "Los 20 titulares con más tiempo en el mismo puesto (la base empieza en noviembre de 2022: el máximo observable es unos 4 años) · en ministerios, cuántos ministros vieron pasar · clic en una barra para abrir su norma",
    "ministerio (personas que pasaron por él)");
  const selector = el("div", "selector-vista");
  [["rotacion", "Más rotación"], ["permanencia", "Más permanencia"]].forEach(([v, t]) => {
    const b = el("button", null, t); b.type = "button"; b.setAttribute("aria-pressed", vistaRank === v ? "true" : "false");
    b.addEventListener("click", () => { vistaRank = v; renderTrayectorias(); });
    selector.appendChild(b);
  });
  c.fig.insertBefore(selector, c.leyenda);
  const filas = (esRot ? R.rotacion : R.permanencia)[String(ESTADO.m)] || [];
  const azul = css("--series-1"), azulClaro = `color-mix(in srgb, ${azul} 40%, transparent)`;
  ponerLeyenda(c.leyenda, [{ color: azul, texto: esRot ? "Cargo (de la designación a la salida)" : "Tiempo en el puesto" },
    { color: azulClaro, texto: "Sigue al cierre de la base (octubre de 2026)" }]);
  if (!filas.length) { vacio(c.grafico, "No hay personas para este filtro."); return; }
  const inicio = new Date(R.inicio + "T00:00:00"), fin = new Date(R.fin + "T00:00:00");
  const dia = (d) => new Date(inicio.getTime() + d * 864e5);
  const W = c.ancho, etiqueta = Math.max(118, Math.min(250, W * 0.3)), alto = 38, P = { t: 24, r: 10, b: 6 };
  const H = P.t + filas.length * alto + P.b;
  const x = d3.scaleTime().domain([inicio, fin]).range([etiqueta, W - P.r]);
  const svg = d3.select(c.grafico).append("svg").attr("viewBox", `0 0 ${W} ${H}`).attr("role", "img")
    .attr("aria-label", esRot ? "Cargos de las 20 personas con más rotación, en el tiempo" : "Puesto de las 20 personas con más permanencia, en el tiempo");
  const anios = d3.timeYear.range(d3.timeYear.ceil(inicio), fin);
  svg.append("g").selectAll("line").data(anios).join("line").attr("x1", x).attr("x2", x).attr("y1", P.t - 4).attr("y2", H - P.b)
    .attr("stroke", css("--grid"));
  svg.append("g").selectAll("text").data(anios).join("text").attr("x", (d) => x(d) + 4).attr("y", P.t - 10)
    .attr("font-size", 11).attr("fill", css("--text-muted")).text(d3.timeFormat("%Y"));
  const textoTabla = [];
  filas.forEach((f, i) => {
    const y0 = P.t + i * alto, g = svg.append("g");
    const metrica = esRot ? `${f[1]} cargos en 12 meses · ${f[2]} en total` : `${duracionTexto(f[4])}${f[6] >= 0 ? ` · vio pasar ${f[6]} ministros` : ""}`;
    g.append("text").attr("x", 0).attr("y", y0 + 15).attr("font-size", 12).attr("font-weight", 700).attr("fill", css("--text-primary"))
      .text(`${i + 1}. ${f[0]}`);
    g.append("text").attr("x", 0).attr("y", y0 + 30).attr("font-size", 11).attr("fill", css("--text-secondary")).text(metrica);
    const cargos = esRot ? f[5] : [[f[1], f[2], f[3], f[4], f[5], f[8], f[9]]];
    cargos.forEach(([inst, nivel, desde, dias, abierto, norma, ref]) => {
      const x1 = x(dia(desde)), x2 = Math.max(x1 + 3, x(dia(desde + dias)));
      g.append("rect").attr("class", "marca").attr("tabindex", 0).attr("x", x1).attr("y", y0 + 9).attr("width", x2 - x1).attr("height", 18)
        .attr("rx", 3).attr("fill", abierto ? azulClaro : azul).attr("stroke", css("--surface-1")).attr("stroke-width", 1.5)
        .attr("aria-label", `${f[0]}: ${R.instituciones[inst]}, ${duracionTexto(dias)}, norma ${norma}`)
        .style("cursor", ref ? "pointer" : null)
        .on("pointermove focus", (e) => mostrarTip(e, `Persona ${f[0]}`, [
          { valor: R.instituciones[inst], etiqueta: D.niveles[nivel] },
          { valor: duracionTexto(dias), etiqueta: abierto ? "y sigue al cierre de la base" : "en el cargo" },
          { valor: d3.timeFormat("%d/%m/%Y")(dia(desde)), etiqueta: "inicio" },
          { valor: `Norma ${norma}`, etiqueta: ref ? "clic para abrirla en El Peruano" : "" }]))
        .on("pointerleave blur", ocultarTip)
        .on("click keydown", (e) => {
          if (e.type === "keydown" && e.key !== "Enter") return;
          if (ref) window.open(enlaceNorma(ref), "_blank", "noopener");
        });
      if (!esRot && x2 - x1 > 120) {
        g.append("text").attr("x", x1 + 8).attr("y", y0 + 22).attr("font-size", 11).attr("fill", abierto ? css("--text-primary") : "#fff").attr("pointer-events", "none")
          .text(`${R.instituciones[inst]} · ${D.niveles[nivel].slice(0, 2)}`);
      }
    });
    textoTabla.push(esRot
      ? [i + 1, f[0], f[1], f[2], cargos.map(([inst, nivel, , dias, abierto, norma, ref]) =>
          ({ t: `${R.instituciones[inst]} · ${D.niveles[nivel].slice(0, 2)} · ${duracionTexto(dias)}${abierto ? " (sigue)" : ""}`, href: enlaceNorma(ref) }))]
      : [i + 1, f[0], R.instituciones[f[1]], D.niveles[f[2]], duracionTexto(f[4]), f[6] >= 0 ? f[6] : "— (organismo)", f[5] ? "sí" : "no",
         [{ t: f[8], href: enlaceNorma(f[9]) }]]);
  });
  ponerTabla(c.tabla, esRot
    ? [{ nombre: "#" }, { nombre: "Persona" }, { nombre: "Cargos en 12 meses", num: true }, { nombre: "Cargos en total", num: true }, { nombre: "Recorrido (institución · nivel · duración) · cada tramo enlaza a su norma" }]
    : [{ nombre: "#" }, { nombre: "Persona" }, { nombre: "Institución" }, { nombre: "Nivel" }, { nombre: "Tiempo" }, { nombre: "Ministros que vio pasar" }, { nombre: "Sigue" }, { nombre: "Norma" }],
    textoTabla);
}

// ---------- Guía "Cómo leer la red": diálogo de 4 pasos con diagramas propios (colores del sitio, modo claro y oscuro) ----------
// Se abre con el botón del gráfico, con el enlace de la sección o directamente con index.html#como-leer-la-red
// Caso del ministro B (grupo 4 de la red; sin nombres): 1 = designado allí después del jefe; "J" = ahora es la jefa
const CASO_B = [
  ["Secretaria general", 1, 1, 1, "J"], ["Jefa de gabinete de asesores", 1, 1, 1, 0], ["Asesora del despacho", 1, 1, 1, 0],
  ["Asesora del despacho", 1, 1, 1, 0], ["Asesor → director general", 1, 1, 1, 0], ["Asesoría jurídica", 0, 1, 1, 1],
  ["Tecnologías de la información", 0, 1, 1, 1], ["Asesora de secretaría general", 0, 1, 1, 1], ["Jefe de gabinete", 0, 1, 1, 0],
  ["Administración", 0, 1, 1, 0], ["Comunicaciones", 1, 0, 1, 0], ["Atención al ciudadano", 1, 1, 0, 0]];
let pasoAyuda = 1;
function svgAyuda(contenedor, ancho, alto, etiqueta) {
  contenedor.replaceChildren();
  return d3.select(contenedor).append("svg").attr("viewBox", `0 0 ${ancho} ${alto}`).attr("role", "img").attr("aria-label", etiqueta);
}
function puntasAyuda(svg, id) {
  const defs = svg.append("defs");
  [["n", 8], ["g", 11]].forEach(([k, t]) => defs.append("marker").attr("id", `${id}-${k}`).attr("viewBox", "0 0 10 10")
    .attr("refX", 9).attr("refY", 5).attr("markerWidth", t).attr("markerHeight", t).attr("markerUnits", "userSpaceOnUse")
    .attr("orient", "auto").append("path").attr("d", "M0,0 L10,5 L0,10 z").attr("fill", css("--text-secondary")));
}
function flechaAyuda(svg, id, a, b, gruesa) {
  // de borde a borde, para que la punta no quede tapada por el punto
  const dx = b.x - a.x, dy = b.y - a.y, L = Math.hypot(dx, dy), ux = dx / L, uy = dy / L;
  svg.append("line").attr("x1", a.x + ux * (a.r + 3)).attr("y1", a.y + uy * (a.r + 3))
    .attr("x2", b.x - ux * (b.r + 3)).attr("y2", b.y - uy * (b.r + 3)).attr("stroke", css("--text-secondary"))
    .attr("stroke-width", gruesa ? 3.5 : 1.4).attr("stroke-linecap", "round").attr("marker-end", `url(#${id}-${gruesa ? "g" : "n"})`);
}
function puntoAyuda(svg, p, color) {
  svg.append("circle").attr("cx", p.x).attr("cy", p.y).attr("r", p.r).attr("fill", color)
    .attr("stroke", css("--page")).attr("stroke-width", 2);
}
function rotuloAyuda(svg, x, y, lineas, ancla = "start", tam = 13) {
  const t = svg.append("text").attr("x", x).attr("y", y).attr("font-size", tam).attr("text-anchor", ancla);
  lineas.forEach((l, i) => t.append("tspan").attr("x", x).attr("dy", i ? tam * 1.3 : 0).attr("font-weight", i ? 400 : 700)
    .attr("fill", i ? css("--text-secondary") : css("--text-primary")).text(l));
}
function guiaAyuda(svg, x1, y1, x2, y2) {
  svg.append("line").attr("x1", x1).attr("y1", y1).attr("x2", x2).attr("y2", y2)
    .attr("stroke", css("--text-muted")).attr("stroke-width", 1).attr("stroke-dasharray", "2 3");
}
const pantallaAngosta = () => window.matchMedia("(max-width: 640px)").matches;
function figuraLeer(cont) {
  // En celular: la estrella sola y centrada (la leyenda de al lado explica cada elemento); en pantalla ancha, con rótulos
  const angosta = pantallaAngosta();
  const svg = svgAyuda(cont, angosta ? 340 : 520, 300, "Un jefe en el centro con flechas hacia siete acompañantes; una flecha más gruesa indica que lo siguió en tres o más instituciones");
  puntasAyuda(svg, "al");
  const jefe = { x: angosta ? 170 : 170, y: angosta ? 150 : 165, r: 32 };
  const radio = angosta ? 112 : 115;
  const gente = d3.range(7).map((i) => {
    const ang = -Math.PI / 2 + (2 * Math.PI * i) / 7;
    return { x: jefe.x + radio * Math.cos(ang), y: jefe.y + radio * Math.sin(ang), r: angosta ? 13 : 11 };
  });
  gente.forEach((p, i) => flechaAyuda(svg, "al", jefe, p, i === 2));
  gente.forEach((p) => puntoAyuda(svg, p, css("--series-1")));
  puntoAyuda(svg, jefe, css("--series-2"));
  if (angosta) return;
  guiaAyuda(svg, 272, 86, 296, 70); rotuloAyuda(svg, 300, 64, ["Acompañante", "llegó después que el jefe"]);
  guiaAyuda(svg, 204, 156, 296, 146); rotuloAyuda(svg, 300, 140, ["Jefe", "ministro, viceministro,", "secretario general o director"]);
  guiaAyuda(svg, 240, 181, 296, 244); rotuloAyuda(svg, 300, 248, ["Flecha gruesa", "lo siguió en 3 o más", "instituciones"]);
}
function figuraFormas(cont) {
  // Cada forma se define en su propia caja de 200 x 160; en pantalla ancha van en fila (texto debajo) y en celular en columna (texto al lado)
  const angosta = pantallaAngosta();
  const svg = svgAyuda(cont, angosta ? 360 : 600, angosta ? 495 : 236, "Tres formas: estrella (un jefe con su gente), cadena (quien siguió a un jefe luego lleva a su gente) y puente (une dos equipos)");
  puntasAyuda(svg, "af");
  const azul = css("--series-1"), naranja = css("--series-2"), verde = css("--series-3");
  const formas = [
    ["Estrella", "un jefe con su gente", ["un jefe con", "su gente"], (o) => {
      const c = o({ x: 100, y: 80, r: 16 });
      const est = d3.range(6).map((i) => { const ang = -Math.PI / 2 + (2 * Math.PI * i) / 6; return o({ x: 100 + 58 * Math.cos(ang), y: 80 + 58 * Math.sin(ang), r: 7 }); });
      est.forEach((p) => flechaAyuda(svg, "af", c, p)); est.forEach((p) => puntoAyuda(svg, p, azul)); puntoAyuda(svg, c, naranja);
    }],
    ["Cadena", "quien lo siguió, luego lleva", ["quien siguió a", "un jefe, luego", "lleva a su gente"], (o) => {
      const A = o({ x: 28, y: 80, r: 13 }), B = o({ x: 100, y: 80, r: 13 });
      const cad = [o({ x: 168, y: 34, r: 7 }), o({ x: 176, y: 80, r: 7 }), o({ x: 168, y: 126, r: 7 })];
      flechaAyuda(svg, "af", A, B); cad.forEach((p) => flechaAyuda(svg, "af", B, p)); cad.forEach((p) => puntoAyuda(svg, p, azul));
      puntoAyuda(svg, A, naranja); puntoAyuda(svg, B, naranja);
    }],
    ["Puente", "une dos equipos", ["siguió a jefes", "de dos equipos", "y los une"], (o) => {
      const J1 = o({ x: 52, y: 42, r: 12 }), J2 = o({ x: 152, y: 42, r: 12 }), P = o({ x: 102, y: 96, r: 9 });
      const g1 = [o({ x: 32, y: 130, r: 7 }), o({ x: 70, y: 138, r: 7 })], g2 = [o({ x: 134, y: 138, r: 7 }), o({ x: 172, y: 130, r: 7 })];
      g1.forEach((p) => flechaAyuda(svg, "af", J1, p)); g2.forEach((p) => flechaAyuda(svg, "af", J2, p));
      flechaAyuda(svg, "af", J1, P); flechaAyuda(svg, "af", J2, P);
      [...g1, ...g2].forEach((p) => puntoAyuda(svg, p, azul)); puntoAyuda(svg, P, verde); puntoAyuda(svg, J1, naranja); puntoAyuda(svg, J2, naranja);
    }]];
  formas.forEach(([nombre, corto, lineas, dibujar], i) => {
    const dx = angosta ? 0 : 200 * i, dy = angosta ? 165 * i : 0;
    dibujar((p) => ({ x: p.x + dx, y: p.y + dy, r: p.r }));
    if (angosta) {
      const t = svg.append("text").attr("x", 210).attr("y", dy + 58);
      [nombre, ...lineas].forEach((l, j) => t.append("tspan").attr("x", 210).attr("dy", j ? 20 : 0).attr("font-size", j ? 14 : 17)
        .attr("font-weight", j ? 400 : 700).attr("fill", j ? css("--text-secondary") : css("--text-primary")).text(l));
    } else {
      rotuloAyuda(svg, dx + 100, 194, [nombre, corto], "middle", 16);
    }
  });
}
function figuraAzar(cont) {
  const angosta = pantallaAngosta();
  const r = D.red.seg, max = r.parejas_3_o_mas, x0 = angosta ? 112 : 104, ancho = angosta ? 170 : 270, tam = angosta ? 16 : 13;
  const svg = svgAyuda(cont, angosta ? 340 : 440, 100, `Parejas que se repiten en 3 o más instituciones: ${r.parejas_3_o_mas} en los datos y ${fmt1(r.parejas_3_o_mas_azar)} por azar`);
  [["En los datos", r.parejas_3_o_mas, css("--series-1"), 10], ["Por azar", r.parejas_3_o_mas_azar, css("--text-muted"), 54]].forEach(([nombre, v, color, y]) => {
    const w = Math.max(4, (v / max) * ancho);
    svg.append("path").attr("d", `M${x0},${y} h${w - 4} a4,4 0 0 1 4,4 v${28} a4,4 0 0 1 -4,4 h${-(w - 4)} z`).attr("fill", color);
    svg.append("text").attr("x", 0).attr("y", y + 22).attr("font-size", tam).attr("fill", css("--text-secondary")).text(nombre);
    svg.append("text").attr("x", x0 + w + 8).attr("y", y + 23).attr("font-size", tam + 3).attr("font-weight", 700)
      .attr("fill", css("--text-primary")).text(Number.isInteger(v) ? fmt(v) : fmt1(v));
  });
  svg.append("line").attr("x1", x0).attr("x2", x0).attr("y1", 4).attr("y2", 96).attr("stroke", css("--axis"));
}
function figuraCaso(cont) {
  cont.replaceChildren();
  const tabla = el("div", "ayuda-matriz");
  tabla.setAttribute("role", "img");
  tabla.setAttribute("aria-label", "Doce personas del equipo del ministro B y en cuáles de sus tres ministerios llegaron detrás de él; en 2026 la secretaria general es la jefa y tres personas la siguen");
  ["", "Min. 1\n2023", "Min. 2\n2023-25", "Min. 3\n2025", "Sin él\n2026"].forEach((t, i) => tabla.appendChild(el("div", i === 4 ? "cab sin" : "cab", t)));
  CASO_B.forEach(([rol, ...cols]) => {
    tabla.appendChild(el("div", "rol", rol));
    cols.forEach((v, i) => { const celda = el("div", i === 3 ? "celda sin" : "celda"); celda.appendChild(el("i", v === "J" ? "jefa" : v ? "si" : "no")); tabla.appendChild(celda); });
  });
  cont.appendChild(tabla);
  const ley = el("div", "ayuda-matriz-ley");
  [["var(--series-1)", 12, "llegó después del jefe"], ["var(--series-2)", 14, "ahora es la jefa"]].forEach(([color, t, texto]) => {
    const s = el("span"); const i = el("i"); i.style.background = color; i.style.width = `${t}px`; i.style.height = `${t}px`;
    s.appendChild(i); s.appendChild(document.createTextNode(texto)); ley.appendChild(s);
  });
  cont.appendChild(ley);
}
function dibujarAyudaRed(dialogo) {
  figuraLeer(dialogo.querySelector('[data-figura="leer"]'));
  figuraFormas(dialogo.querySelector('[data-figura="formas"]'));
  figuraAzar(dialogo.querySelector('[data-figura="azar"]'));
  figuraCaso(dialogo.querySelector('[data-figura="caso"]'));
  dialogo.querySelectorAll("[data-cifra]").forEach((e) => { e.textContent = fmt(D.red.seg[e.dataset.cifra]); });
  dialogo.querySelectorAll("[data-meta]").forEach((e) => { e.textContent = fmt(D.meta[e.dataset.meta]); });
}
function mostrarPasoAyuda(n) {
  pasoAyuda = n;
  const d = document.getElementById("como-leer-la-red");
  d.querySelectorAll('[role="tab"]').forEach((b) => {
    const activo = +b.dataset.paso === n;
    b.setAttribute("aria-selected", activo ? "true" : "false");
    b.tabIndex = activo ? 0 : -1;
  });
  d.querySelectorAll(".ayuda-paso").forEach((p) => { p.hidden = +p.dataset.paso !== n; });
  d.querySelector("[data-anterior]").disabled = n === 1;
  d.querySelector("[data-siguiente]").textContent = n === 4 ? "Ver la red" : "Siguiente →";
  d.querySelector(".ayuda-progreso").textContent = `Paso ${n} de 4`;
}
function abrirAyudaRed(evento) {
  if (evento) evento.preventDefault();
  const dialogo = document.getElementById("como-leer-la-red");
  if (!dialogo || dialogo.open) return;
  dibujarAyudaRed(dialogo);          // se dibuja al abrir: toma los colores del tema (claro u oscuro) vigente
  mostrarPasoAyuda(1);
  dialogo.showModal();
  history.replaceState(null, "", `${location.pathname}${location.search}#como-leer-la-red`);
}
function iniciarAyudaRed() {
  const dialogo = document.getElementById("como-leer-la-red");
  if (!dialogo) return;
  document.querySelectorAll('a[href="#como-leer-la-red"]').forEach((a) => a.addEventListener("click", abrirAyudaRed));
  dialogo.querySelector("[data-cerrar-ayuda]").addEventListener("click", () => dialogo.close());
  dialogo.addEventListener("click", (e) => { if (e.target === dialogo) dialogo.close(); });     // clic en el fondo oscuro
  dialogo.querySelectorAll('[role="tab"]').forEach((b) => b.addEventListener("click", () => mostrarPasoAyuda(+b.dataset.paso)));
  dialogo.querySelector('[role="tablist"]').addEventListener("keydown", (e) => {
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
    const n = Math.min(4, Math.max(1, pasoAyuda + (e.key === "ArrowRight" ? 1 : -1)));
    mostrarPasoAyuda(n);
    dialogo.querySelector(`[role="tab"][data-paso="${n}"]`).focus();
  });
  dialogo.querySelector("[data-anterior]").addEventListener("click", () => mostrarPasoAyuda(Math.max(1, pasoAyuda - 1)));
  dialogo.querySelector("[data-siguiente]").addEventListener("click", () => {
    if (pasoAyuda < 4) mostrarPasoAyuda(pasoAyuda + 1);
    else dialogo.close();
  });
  dialogo.addEventListener("close", () => {
    if (location.hash === "#como-leer-la-red") history.replaceState(null, "", `${location.pathname}${location.search}#s-red`);
  });
  if (location.hash === "#como-leer-la-red") abrirAyudaRed();
}

// ---------- 3. Red de seguimiento: quién llega detrás de quién ----------
function renderRedCifras() {
  const s = D.red.seg;
  const cont = document.getElementById("red-cifras");
  cont.replaceChildren();
  [[fmt(s.parejas_3_o_mas), `parejas jefe–acompañante se repiten en 3 o más instituciones (por azar: ${fmt1(s.parejas_3_o_mas_azar)})`],
   [fmt(s.parejas_2_o_mas), `se repiten en 2 o más instituciones (por azar: ${fmt(Math.round(s.parejas_2_o_mas_azar))})`],
   [fmt(s.parejas_firmadas_por_el_jefe), "de esas parejas: el propio jefe firmó la designación de su acompañante"],
   [fmt(s.jefes_con_3_o_mas), "jefes con tres o más personas que llegan detrás de ellos una y otra vez"]]
    .forEach(([v, t]) => { const d = el("div"); d.appendChild(el("b", null, v)); d.appendChild(el("span", null, t)); cont.appendChild(d); });
}
function renderRed() {
  const c = tarjeta("red", "Red de seguimiento: quién llega detrás de quién",
    "Cada flecha va de un jefe a una persona que llegó después que él en 2 o más instituciones · grupos de 4 o más personas · pasa el cursor por un punto para ver sus instituciones; clic para resaltar su grupo y ver con qué otros grupos se conecta",
    "ministerio (resalta a quienes pasaron por él)");
  const ayuda = el("button", "boton-ayuda", "¿Cómo leer esta red? Ver la explicación");
  ayuda.type = "button";
  ayuda.setAttribute("aria-haspopup", "dialog");
  ayuda.addEventListener("click", abrirAyudaRed);
  c.fig.insertBefore(ayuda, c.leyenda);
  const nodos = D.red.nodos.map((n) => ({ id: n[0], x: n[1], y: n[2], grupo: n[3], rol: n[4], lleva: n[5], sigue: n[6], mins: n[7],
    inst: n[8].map((i) => D.red.instituciones[i]) }));
  const institucionesGrupo = new Map(D.red.grupos.map(([g, l]) => [g, l.map((i) => D.red.instituciones[i]).join(", ")]));
  const porId = new Map(nodos.map((n) => [n.id, n]));
  // Misma escala en los dos ejes: el alto sigue la proporción del dibujo (no deforma los grupos)
  const P = 18, W = c.ancho, H = Math.round((W - 2 * P) * D.red.aspecto + 2 * P);
  const x = d3.scaleLinear().domain([0, 1]).range([P, W - P]);
  const y = d3.scaleLinear().domain([0, D.red.aspecto]).range([P, H - P]);
  const color = { jefe: css("--series-2"), "acompañante": css("--series-1"), puente: css("--series-3") };
  const pasa = (n) => ESTADO.m < 0 || n.mins.includes(ESTADO.m);
  // Al resaltar un grupo se ven también las personas de otros grupos con las que se conecta
  const vecinos = new Set();
  if (comunidadResaltada !== null) D.red.aristas.forEach((a) => {
    const j = porId.get(a[0]), s = porId.get(a[1]);
    if (j && s && (j.grupo === comunidadResaltada || s.grupo === comunidadResaltada)) { vecinos.add(a[0]); vecinos.add(a[1]); }
  });
  const visible = (n) => (comunidadResaltada === null ? pasa(n) : n.grupo === comunidadResaltada || vecinos.has(n.id));
  const base = Math.max(3, W / 280);
  const radio = (n) => (n.rol === "jefe" ? base + Math.sqrt(n.lleva) * Math.max(1.4, W / 520) : base);
  ponerLeyenda(c.leyenda, [
    { color: color.jefe, tipo: "punto", texto: "Jefe (tamaño: cuántas personas llegan detrás de él)" },
    { color: color["acompañante"], tipo: "punto", texto: "Acompañante" },
    { color: color.puente, tipo: "punto", texto: "Puente: siguió a jefes de equipos distintos" },
    { color: css("--text-muted"), tipo: "linea", texto: "Llegó detrás del jefe en 2 instituciones (más gruesa: 3 o más)" }]);
  const svg = d3.select(c.grafico).append("svg").attr("viewBox", `0 0 ${W} ${H}`).attr("role", "img")
    .attr("aria-label", "Red de seguimiento: jefes y las personas que llegan detrás de ellos en varias instituciones");
  const punta = Math.max(6, W / 160);
  svg.append("defs").append("marker").attr("id", "punta-red").attr("viewBox", "0 0 10 10").attr("refX", 9).attr("refY", 5)
    .attr("markerWidth", punta).attr("markerHeight", punta).attr("markerUnits", "userSpaceOnUse").attr("orient", "auto")
    .append("path").attr("d", "M0,0 L10,5 L0,10 z").attr("fill", css("--text-secondary"));
  // Cada flecha va de borde a borde, para que la punta no quede bajo el punto
  const extremo = (a, b, desde) => {
    const dx = x(b.x) - x(a.x), dy = y(b.y) - y(a.y), L = Math.hypot(dx, dy) || 1;
    return desde ? [x(a.x) + (dx / L) * (radio(a) + 1), y(a.y) + (dy / L) * (radio(a) + 1)]
                 : [x(b.x) - (dx / L) * (radio(b) + 2), y(b.y) - (dy / L) * (radio(b) + 2)];
  };
  // Flechas dentro de cada grupo; las que unen grupos distintos solo se ven al resaltar un grupo (si no, cruzan todo el dibujo)
  const mismoGrupo = (a) => porId.get(a[0]).grupo === porId.get(a[1]).grupo;
  const tocaResaltado = (a) => comunidadResaltada !== null && (porId.get(a[0]).grupo === comunidadResaltada || porId.get(a[1]).grupo === comunidadResaltada);
  svg.append("g").selectAll("line").data(D.red.aristas.filter((a) => porId.has(a[0]) && porId.has(a[1]) && (mismoGrupo(a) || tocaResaltado(a)))).join("line")
    .each(function (a) {
      const j = porId.get(a[0]), s = porId.get(a[1]);
      const [x1, y1] = extremo(j, s, true), [x2, y2] = extremo(j, s, false);
      d3.select(this).attr("x1", x1).attr("y1", y1).attr("x2", x2).attr("y2", y2);
    })
    .attr("stroke", css("--text-secondary")).attr("stroke-width", (a) => (a[2] >= 3 ? 2.6 : 1.1)).attr("marker-end", "url(#punta-red)")
    .attr("opacity", (a) => (tocaResaltado(a) || (comunidadResaltada === null && pasa(porId.get(a[0])) && pasa(porId.get(a[1]))) ? (a[2] >= 3 ? 0.95 : 0.6) : 0.07));
  const orden = { "acompañante": 0, puente: 1, jefe: 2 };
  const textoRol = { jefe: "jefe: llegan personas detrás de él", "acompañante": "acompañante", puente: "puente: siguió a jefes de equipos distintos" };
  svg.append("g").selectAll("circle").data([...nodos].sort((a, b) => orden[a.rol] - orden[b.rol] || a.lleva - b.lleva)).join("circle")
    .attr("class", "marca").attr("tabindex", 0)
    .attr("cx", (n) => x(n.x)).attr("cy", (n) => y(n.y)).attr("r", radio)
    .attr("fill", (n) => color[n.rol]).attr("stroke", css("--surface-1")).attr("stroke-width", 1.5)
    .attr("opacity", (n) => (visible(n) ? 1 : 0.15))
    .attr("aria-label", (n) => `Persona ${n.id}, ${textoRol[n.rol]}, grupo ${n.grupo}`)
    .on("pointermove focus", (e, n) => mostrarTip(e, `Persona ${n.id} · grupo ${n.grupo} (${institucionesGrupo.get(n.grupo)})`, [
      { valor: textoRol[n.rol], etiqueta: "" },
      { valor: n.inst.join(", "), etiqueta: "" },
      { valor: fmt(n.lleva), etiqueta: "personas llegaron detrás de él o ella en 2+ instituciones" },
      { valor: fmt(n.sigue), etiqueta: "jefes a los que siguió en 2+ instituciones" }]))
    .on("pointerleave blur", ocultarTip)
    .on("click keydown", (e, n) => {
      if (e.type === "keydown" && e.key !== "Enter") return;
      comunidadResaltada = comunidadResaltada === n.grupo ? null : n.grupo;
      renderRed();
    });
  const grupos = d3.rollups(nodos, (v) => ({ personas: v.length, jefes: v.filter((n) => n.rol === "jefe").length,
    max: d3.max(v, (n) => n.lleva), puentes: v.filter((n) => n.rol === "puente").length }), (n) => n.grupo).sort((a, b) => a[0] - b[0]);
  ponerTabla(c.tabla, [{ nombre: "Grupo" }, { nombre: "Personas", num: true }, { nombre: "Jefes", num: true },
    { nombre: "Máx. acompañantes de un jefe", num: true }, { nombre: "Puentes", num: true }, { nombre: "Instituciones principales" }],
    grupos.map(([g, v]) => [g, v.personas, v.jefes, v.max, v.puentes, institucionesGrupo.get(g)]));
}

// ---------- Hallazgos (con las cifras de los mismos datos) ----------
function renderHallazgos() {
  const ultimo = D.gobiernos.length - 1;
  const fila = D.continuidad.find((r) => r[0] === ultimo && r[1] === "todos");
  const alta = D.continuidad.find((r) => r[0] === ultimo && r[1] !== "todos");
  const iSG = D.familias.indexOf("Secretaría General"), iVM = D.familias.indexOf("Viceministerio");
  const sg = mediana(D.armado.map((r) => r[2 + iSG]));
  const sgUlt = mediana(D.armado.filter((r) => r[1] === ultimo).map((r) => r[2 + iSG]));
  const vmUlt = mediana(D.armado.filter((r) => r[1] === ultimo).map((r) => r[2 + iVM]));
  const r = D.red.resumen, s = D.red.seg;
  const textos = [
    ["Hallazgo 1", "La mitad del elenco ya estaba en el Estado",
      `De las ${fmt(fila[2])} personas que designó el gobierno que asumió en julio de 2026, el ${Math.round(fila[3])} % ya había tenido un cargo entre 2022 y 2026; en los cargos altos, el ${Math.round(alta[3])} %. En los gobiernos de 2025 y febrero de 2026 la proporción fue similar: cambia el mando, no tanto el elenco.`],
    ["Hallazgo 2", "Primero se asegura el control administrativo",
      `Cuando llega un ministro, el secretario general cambia a los ${fmt(sg)} días (mediana de 168 llegadas), antes que asesoría jurídica, administración y recursos humanos; viceministros y planeamiento vienen después. Con el gobierno de julio de 2026: secretario general a los ${fmt(sgUlt)} días y viceministros a los ${fmt(vmUlt)}.`],
    ["Hallazgo 3", "El \"desorden\" tiene estructura: gente que sigue a su jefe",
      `Cuando alguien asume un cargo de decisión, llegan detrás de él personas que ya lo habían seguido en otra institución: ${fmt(s.parejas_3_o_mas)} parejas jefe–acompañante se repiten en 3 o más instituciones (por azar, ${fmt1(s.parejas_3_o_mas_azar)}) y ${fmt(s.jefes_con_3_o_mas)} jefes tienen tres o más acompañantes que los siguen. En ${fmt(s.parejas_firmadas_por_el_jefe)} parejas el propio jefe firmó la designación. Y cuando un jefe se muda, el ${fmt1(r.arrastre_pct)} % de su equipo que también se mueve llega adonde fue él (por azar, ${fmt1(r.arrastre_pct_azar)} %).`]];
  const cont = document.getElementById("hallazgos");
  cont.replaceChildren();
  textos.forEach(([n, t, p]) => {
    const d = el("article", "hallazgo");
    d.appendChild(el("p", "numero", n)); d.appendChild(el("h3", null, t)); d.appendChild(el("p", null, p));
    cont.appendChild(d);
  });
}

// ---------- filtros y renderizado general ----------
function llenarFiltros() {
  const sg = document.getElementById("f-gobierno");
  sg.replaceChildren(new Option("Todos (nov-2022 a oct-2026)", "-1"));
  D.gobiernos.forEach((g) => sg.appendChild(new Option(`Gobierno de ${g.etiqueta}`, String(g.id))));
  const sm = document.getElementById("f-ministerio");
  sm.replaceChildren(new Option("Todos", "-1"));
  D.ministerios.forEach((m, i) => sm.appendChild(new Option(m, String(i))));
  sg.addEventListener("change", () => { ESTADO.g = +sg.value; renderTodo(); });
  sm.addEventListener("change", () => { ESTADO.m = +sm.value; comunidadResaltada = null; renderTodo(); });
  const sn = document.getElementById("f-nivel");
  sn.addEventListener("change", () => { ESTADO.n = sn.value; renderTodo(); });
  document.getElementById("f-limpiar").addEventListener("click", () => {
    ESTADO.g = -1; ESTADO.m = -1; ESTADO.n = "todos"; comunidadResaltada = null;
    sg.value = "-1"; sm.value = "-1"; sn.value = "todos"; renderTodo();
  });
  // Filtros desde el enlace (para compartir una vista): ?g=4&m=6&n=alta&tema=oscuro&grupo=2
  const parametros = new URLSearchParams(window.location.search);
  if (parametros.has("g") && sg.querySelector(`option[value="${+parametros.get("g")}"]`)) { ESTADO.g = +parametros.get("g"); sg.value = String(ESTADO.g); }
  if (parametros.has("m") && sm.querySelector(`option[value="${+parametros.get("m")}"]`)) { ESTADO.m = +parametros.get("m"); sm.value = String(ESTADO.m); }
  if (GRUPOS[parametros.get("n")]) { ESTADO.n = parametros.get("n"); sn.value = ESTADO.n; }
  if (parametros.get("tema") === "oscuro") document.documentElement.dataset.theme = "dark";
  // ?ranking=permanencia abre los rankings de personas en la vista de permanencia
  if (parametros.get("ranking") === "permanencia") vistaRank = "permanencia";
  // ?grupo=2 abre la red con ese grupo resaltado (útil para capturas del reel)
  if (parametros.has("grupo") && Number.isInteger(+parametros.get("grupo"))) comunidadResaltada = +parametros.get("grupo");
  document.getElementById("f-tema").addEventListener("click", () => {
    const raiz = document.documentElement;
    const oscuroAhora = raiz.dataset.theme ? raiz.dataset.theme === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches;
    raiz.dataset.theme = oscuroAhora ? "light" : "dark";
    renderTodo();
  });
}
function renderTodo() {
  renderKpis(); renderContinuidad(); renderSerie(); renderArmado(); renderRotacion();
  renderPuestos(); renderSupervivencia(); renderTrayectorias(); renderRed(); renderGenero(); renderMapa();
}

Promise.all([d3.json("data/dashboard.json"), d3.json("data/peru_departamentos.geojson")]).then(([datos, geo]) => {
  D = datos; GEO = geo;
  llenarFiltros(); renderPortada(); renderRedCifras(); renderHallazgos(); renderTodo(); iniciarAyudaRed();
  let espera;
  window.addEventListener("resize", () => { clearTimeout(espera); espera = setTimeout(renderTodo, 200); });
}).catch((error) => {
  document.getElementById("kpis").replaceChildren(el("div", "vacio", `No se pudieron cargar los datos (${error.message}). Abra la página desde un servidor web.`));
});
