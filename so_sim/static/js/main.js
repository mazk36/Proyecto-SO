// Punto de entrada: conecta el stream y re-renderiza TODO de forma idempotente
// a partir de cada snapshot (sin estado oculto en el cliente).
import { iniciarStream } from "./api.js";
import { initControls, syncControls } from "./controls.js";
import { initEditor } from "./editor.js";
import { renderProcesos } from "./render_procesos.js";
import { renderGantt } from "./render_gantt.js";
import { renderMemoria } from "./render_memoria.js";
import { renderIO } from "./render_io.js";
import { renderMetricas } from "./render_metricas.js";
import { esc } from "./state.js";

const $ = (id) => document.getElementById(id);

function renderTop(snap) {
  $("tick-actual").textContent = snap.tick;
  const b = $("estado-sim");
  if (snap.terminado) { b.className = "badge terminado"; b.textContent = "TERMINADO"; }
  else if (snap.corriendo) { b.className = "badge corriendo"; b.textContent = "EN EJECUCIÓN"; }
  else { b.className = "badge pausado"; b.textContent = "PAUSADO"; }
}

function renderCPU(snap) {
  const c = snap.cpu;
  let box;
  if (c.pid_ejecutando !== null) {
    const p = snap.procesos.find(x => x.pid === c.pid_ejecutando);
    box = `<div class="cpu-pid" style="background:${p ? p.color : "#4f8cff"}">P${c.pid_ejecutando}</div>`;
  } else {
    box = `<div class="cpu-pid idle">CPU ociosa</div>`;
  }
  let info = `<div class="cpu-info"><b>${c.algoritmo_nombre}</b>`;
  if (c.quantum_restante !== null && c.quantum_restante !== undefined) {
    info += `<br>Quantum restante: ${c.quantum_restante}`;
  }
  info += `</div>`;
  $("cpu-actual").innerHTML = box + info;
}

function renderBitacora(snap) {
  $("bitacora").innerHTML = (snap.eventos || []).slice().reverse().map(e =>
    `<li class="ev-${e.tipo}"><span class="t mono">${e.tick}</span><span>${esc(e.texto)}</span></li>`).join("");
}

function render(snap) {
  renderTop(snap);
  renderCPU(snap);
  renderProcesos(snap);
  renderGantt(snap);
  renderMemoria(snap);
  renderIO(snap);
  renderMetricas(snap);
  renderBitacora(snap);
  syncControls(snap);
}

initControls();
initEditor();
iniciarStream(render);
