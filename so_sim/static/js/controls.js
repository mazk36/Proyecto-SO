// Cablea la barra de control y las acciones del tablero con el API.
import { postJSON } from "./api.js";
import { abrirComparativa } from "./render_comparativa.js";
import { limpiarLog, exportarLog } from "./render_log.js";

const $ = (id) => document.getElementById(id);
let lastSnap = null;

function alertErr(e) {
  console.error(e);
  const b = $("estado-sim");
  if (b) { b.textContent = "ERROR"; b.title = e.message || e; }
}

function quantumVisible(algo) {
  $("wrap-quantum").style.display = (algo === "rr" || algo === "mlq") ? "flex" : "none";
}

function enviarScheduler() {
  const algo = $("sel-scheduler").value;
  const q = parseInt($("inp-quantum").value) || 3;
  quantumVisible(algo);
  postJSON("/api/config/scheduler", { algoritmo: algo, quantum: q }).catch(alertErr);
}

async function cargarPresets() {
  try {
    const lista = await (await fetch("/api/presets")).json();
    $("sel-preset").innerHTML = '<option value="">— elegir —</option>' +
      lista.map(p => `<option value="${p.nombre}" title="${p.descripcion}">${p.nombre}</option>`).join("");
  } catch (e) { /* sin presets */ }
}

function activarTab(cual) {
  document.querySelectorAll(".p-mem .tab").forEach(t =>
    t.classList.toggle("activa", t.dataset.tab === cual));
  $("tab-fisica").classList.toggle("oculto", cual !== "fisica");
  $("tab-paginacion").classList.toggle("oculto", cual !== "paginacion");
}

export function initControls() {
  $("btn-play").onclick = () => postJSON("/api/control/play").catch(alertErr);
  $("btn-pause").onclick = () => postJSON("/api/control/pause").catch(alertErr);
  $("btn-step").onclick = () => postJSON("/api/control/step").catch(alertErr);
  $("btn-reset").onclick = () => postJSON("/api/control/reset").catch(alertErr);

  const vel = $("vel");
  vel.oninput = () => { $("vel-label").textContent = vel.value + " ms"; };
  vel.onchange = () => postJSON("/api/control/speed", { velocidad_ms: parseInt(vel.value) }).catch(alertErr);

  $("sel-scheduler").onchange = enviarScheduler;
  $("inp-quantum").onchange = enviarScheduler;
  $("sel-estrategia").onchange = () =>
    postJSON("/api/config/estrategia", { algoritmo: $("sel-estrategia").value }).catch(alertErr);

  $("sel-preset").onchange = () => {
    const n = $("sel-preset").value;
    if (n === "demo20") { postJSON("/api/demo20").catch(alertErr); }
    else if (n) { postJSON("/api/presets/" + n).catch(alertErr); }
  };

  $("btn-demo").onclick = () => postJSON("/api/demo20").catch(alertErr);
  $("btn-generar").onclick = () => {
    const n = parseInt(prompt("¿Cuántos procesos aleatorios? (1-50)", "12"));
    if (n >= 1 && n <= 50) postJSON("/api/generar", { cantidad: n }).catch(alertErr);
  };
  $("btn-comparativa").onclick = () => abrirComparativa();

  // Bitacora
  $("btn-log-limpiar").onclick = () => limpiarLog(lastSnap);
  $("btn-log-export").onclick = () => exportarLog();

  // Pestañas de memoria
  document.querySelectorAll(".p-mem .tab").forEach(t =>
    t.addEventListener("click", () => activarTab(t.dataset.tab)));

  // Delegacion: botones de teclado (se re-renderizan)
  $("io-dispositivos").addEventListener("click", (e) => {
    if (e.target.closest(".btn-teclado-senal"))
      postJSON("/api/control/teclado/senal").catch(alertErr);
  });
  $("io-decision").addEventListener("click", (e) => {
    if (e.target.closest(".btn-teclado-cancelar"))
      postJSON("/api/control/teclado/resolver", { accion: "cancelar" }).catch(alertErr);
    else if (e.target.closest(".btn-teclado-continuar"))
      postJSON("/api/control/teclado/resolver", { accion: "continuar" }).catch(alertErr);
  });

  cargarPresets();
}

// Refleja el estado del servidor en los controles sin pisar lo que el usuario
// este manipulando en ese instante.
export function syncControls(snap) {
  lastSnap = snap;
  const sched = snap.cpu.algoritmo;
  if (document.activeElement !== $("sel-scheduler")) $("sel-scheduler").value = sched;
  if (document.activeElement !== $("sel-estrategia")) $("sel-estrategia").value = snap.memoria_fisica.estrategia;
  if (document.activeElement !== $("inp-quantum") && snap.cpu.quantum) $("inp-quantum").value = snap.cpu.quantum;
  if (document.activeElement !== $("vel")) {
    $("vel").value = snap.velocidad_ms;
    $("vel-label").textContent = snap.velocidad_ms + " ms";
  }
  quantumVisible(sched);
  // Botones deshabilitados segun estado
  $("btn-play").disabled = snap.corriendo || snap.terminado || !!snap.decision_teclado;
  $("btn-step").disabled = snap.terminado || !!snap.decision_teclado;
  $("btn-pause").disabled = !snap.corriendo;
  if (snap.decision_teclado) $("btn-play").title = "Resuelve la señal de teclado para continuar";
  else $("btn-play").title = "";
}
