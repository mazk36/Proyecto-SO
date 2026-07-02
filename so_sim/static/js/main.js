// Punto de entrada: conecta el stream y re-renderiza TODO de forma idempotente
// a partir de cada snapshot (sin estado oculto en el cliente).
import { iniciarStream } from "./api.js";
import { initControls, syncControls } from "./controls.js";
import { initEditor } from "./editor.js";
import { initComparativa } from "./render_comparativa.js";
import { renderCPU } from "./render_cpu.js";
import { renderProcesos } from "./render_procesos.js";
import { renderGantt } from "./render_gantt.js";
import { renderMemoria } from "./render_memoria.js";
import { renderIO } from "./render_io.js";
import { renderMetricas } from "./render_metricas.js";
import { renderLog } from "./render_log.js";

const $ = (id) => document.getElementById(id);

function renderTop(snap) {
  $("tick-actual").textContent = snap.tick;
  const b = $("estado-sim");
  if (snap.terminado) { b.className = "badge terminado"; b.textContent = "TERMINADO"; }
  else if (snap.corriendo) { b.className = "badge corriendo"; b.textContent = "EN EJECUCIÓN"; }
  else { b.className = "badge pausado"; b.textContent = "PAUSADO"; }
}

function render(snap) {
  renderTop(snap);
  renderCPU(snap);
  renderProcesos(snap);
  renderMemoria(snap);
  renderIO(snap);
  renderMetricas(snap);
  renderLog(snap);
  renderGantt(snap);
  syncControls(snap);
}

initControls();
initEditor();
initComparativa();
iniciarStream(render);
