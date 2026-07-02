// Modal de comparativa: consulta /api/comparativa y arma dos tablas (planificadores
// y estrategias de memoria), resaltando el mejor valor de cada metrica y con
// exportacion a CSV.
const $ = (id) => document.getElementById(id);
let datos = null;   // ultima comparativa cargada

// metrica -> [etiqueta, "min"|"max"]  (direccion del "mejor")
const MET_SCHED = {
  espera: ["Espera promedio", "min"], retorno: ["Turnaround promedio", "min"],
  respuesta: ["Respuesta promedio", "min"], con_error: ["Procesos con error", "min"],
};
const MET_MEM = {
  asignaciones_ok: ["Asignaciones exitosas", "max"],
  fallos_externos: ["Fallos por fragmentación externa", "min"],
  fragmentacion_interna: ["Fragmentación interna (KB)", "min"],
  huecos_finales: ["Huecos libres finales", "min"],
};

function tablaTranspuesta(titulo, filas, claveCol, mets) {
  const cols = filas.map(f => f.nombre);
  let html = `<div class="comp-tabla"><h3>${titulo}</h3><table><tr><th>Métrica</th>`;
  html += cols.map(c => `<th>${c}</th>`).join("") + `</tr>`;
  for (const [met, [etq, dir]] of Object.entries(mets)) {
    const vals = filas.map(f => f[met]);
    const validos = vals.filter(v => v !== null && v !== undefined);
    const mejor = validos.length ? (dir === "min" ? Math.min(...validos) : Math.max(...validos)) : null;
    html += `<tr><td style="text-align:left">${etq}</td>`;
    html += vals.map(v => {
      const txt = (v === null || v === undefined) ? "—" : v;
      const clase = (v !== null && v === mejor) ? " class=\"mejor\"" : "";
      return `<td${clase}>${txt}</td>`;
    }).join("");
    html += `</tr>`;
  }
  html += `</table></div>`;
  return html;
}

function toCSV(filas, mets, claveId) {
  const cabecera = ["algoritmo/estrategia", ...Object.keys(mets)].join(",");
  const lineas = filas.map(f => [f[claveId], ...Object.keys(mets).map(m => f[m])].join(","));
  return [cabecera, ...lineas].join("\n");
}

function descargar(nombre, contenido) {
  const blob = new Blob([contenido], { type: "text/csv;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = nombre;
  a.click();
  URL.revokeObjectURL(a.href);
}

export async function abrirComparativa() {
  $("comp-tablas").innerHTML = "<p>Calculando…</p>";
  $("modal-comp").classList.remove("oculto");
  try {
    datos = await (await fetch("/api/comparativa")).json();
    $("comp-tablas").innerHTML =
      tablaTranspuesta("🧠 Planificadores (mismo conjunto de procesos)", datos.schedulers, "algoritmo", MET_SCHED) +
      tablaTranspuesta("💾 Estrategias de asignación (benchmark de fragmentación)", datos.estrategias, "estrategia", MET_MEM);
  } catch (e) {
    $("comp-tablas").innerHTML = `<p style="color:var(--bad)">Error al calcular: ${e.message}</p>`;
  }
}

export function initComparativa() {
  $("comp-cerrar").onclick = () => $("modal-comp").classList.add("oculto");
  $("modal-comp").addEventListener("click", e => { if (e.target.id === "modal-comp") $("modal-comp").classList.add("oculto"); });
  $("comp-csv-sched").onclick = () => { if (datos) descargar("comparativa_planificadores.csv", toCSV(datos.schedulers, MET_SCHED, "algoritmo")); };
  $("comp-csv-mem").onclick = () => { if (datos) descargar("comparativa_estrategias.csv", toCSV(datos.estrategias, MET_MEM, "estrategia")); };
}
