// Cablea la barra de control con el API.
import { postJSON } from "./api.js";

const $ = (id) => document.getElementById(id);

function alertErr(e) {
  console.error(e);
  const b = $("estado-sim");
  if (b) { b.textContent = "ERROR"; b.title = e.message || e; }
}

function actualizarQuantumVisible(algo) {
  $("wrap-quantum").style.display = (algo === "rr" || algo === "mlq") ? "flex" : "none";
}

function enviarScheduler() {
  const algo = $("sel-scheduler").value;
  const q = parseInt($("inp-quantum").value) || 3;
  actualizarQuantumVisible(algo);
  postJSON("/api/config/scheduler", { algoritmo: algo, quantum: q }).catch(alertErr);
}

async function cargarPresets() {
  try {
    const lista = await (await fetch("/api/presets")).json();
    $("sel-preset").innerHTML =
      lista.map(p => `<option value="${p.nombre}" title="${p.descripcion}">${p.nombre}</option>`).join("");
  } catch (e) { /* sin presets */ }
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
  $("sel-replacer").onchange = () =>
    postJSON("/api/config/replacer", { algoritmo: $("sel-replacer").value }).catch(alertErr);

  $("sel-preset").onchange = () => {
    const n = $("sel-preset").value;
    if (n) postJSON("/api/presets/" + n).catch(alertErr);
  };
  cargarPresets();
}

// Refleja el estado del servidor en los controles, sin pisar lo que el usuario
// este manipulando en ese instante.
export function syncControls(snap) {
  const sched = snap.cpu.algoritmo;
  if (document.activeElement !== $("sel-scheduler")) $("sel-scheduler").value = sched;
  if (document.activeElement !== $("sel-replacer")) $("sel-replacer").value = snap.memoria.algoritmo;
  if (document.activeElement !== $("inp-quantum") && snap.cpu.quantum) $("inp-quantum").value = snap.cpu.quantum;
  if (document.activeElement !== $("vel")) {
    $("vel").value = snap.velocidad_ms;
    $("vel-label").textContent = snap.velocidad_ms + " ms";
  }
  actualizarQuantumVisible(sched);
}
