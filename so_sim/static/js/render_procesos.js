// Tabla de PCB (coloreada por estado) + las 4 colas de procesos.
import { mapProc, chip, esc } from "./state.js";

const $ = (id) => document.getElementById(id);

export function renderProcesos(snap) {
  $("proc-cont").textContent = `${snap.procesos.length} procesos`;
  const tb = $("tbody-procesos");
  tb.innerHTML = snap.procesos.map(p => {
    const prog = p.rafaga_total ? Math.round(100 * p.cpu_consumido / p.rafaga_total) : 0;
    const dir = p.direccion_inicial !== null && p.direccion_inicial !== undefined
      ? p.direccion_inicial + "K" : "—";
    const err = p.codigo_error ? ` title="${esc(p.codigo_error)}"` : "";
    return `<tr${err}>
      <td><span class="dotpid" style="background:${p.color}"></span>${p.pid}</td>
      <td>${esc(p.nombre)}</td>
      <td><span class="pill estado-${p.estado}">${p.estado}</span></td>
      <td class="mono">${p.pc}</td>
      <td>${p.prioridad}${p.nivel_mlq === "BAJA" ? "·B" : ""}</td>
      <td class="mono">${p.rafaga_restante}/${p.rafaga_total}</td>
      <td class="mono">${p.tam_total}K</td>
      <td class="mono">${dir}</td>
      <td><div class="barra-prog"><i style="width:${prog}%;background:${p.color}"></i></div></td>
    </tr>`;
  }).join("");

  const map = mapProc(snap);
  const c = snap.colas;
  const bloque = (etq, arr) =>
    `<div class="cola"><div class="etq">${etq} (${arr.length})</div>
     <div class="chips">${arr.length ? arr.map(pid => chip(map, pid)).join("")
                                       : '<span class="chip vacio">vacío</span>'}</div></div>`;

  let html = bloque("🔵 Nuevos", c.nuevos);
  if (c.mlq) {
    html += bloque("🟡 Listos · ALTA (RR)", c.mlq.alta);
    html += bloque("🟡 Listos · BAJA (FCFS)", c.mlq.baja);
  } else {
    html += bloque("🟡 Listos", c.listos);
  }
  html += bloque("🔴 Bloqueados (E/S)", c.bloqueados);
  html += bloque("⚫ Terminados", c.terminados);
  $("colas").innerHTML = html;
}
