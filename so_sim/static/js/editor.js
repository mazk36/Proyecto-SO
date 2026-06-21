// Editor de procesos / escenario: construye un escenario y lo carga vía
// POST /api/config/scenario. Precarga el escenario actual con GET /api/config/actual.
import { postJSON } from "./api.js";

const $ = (id) => document.getElementById(id);

function dispositivosActuales() {
  return $("ed-disp").value.split(",").map(s => s.trim()).filter(Boolean);
}

function filaAcceso(en_cpu = 0, vpn = 0) {
  const div = document.createElement("div");
  div.className = "ed-row ed-acc";
  div.innerHTML = `t-CPU <input class="acc-en num" type="number" min="0" value="${en_cpu}">
    página <input class="acc-vpn num" type="number" min="0" value="${vpn}">
    <button class="btn ed-mini ed-row-del" type="button">✕</button>`;
  return div;
}

function filaIO(en_cpu = 0, dispositivo = "", duracion = 2) {
  const opts = dispositivosActuales()
    .map(d => `<option ${d === dispositivo ? "selected" : ""}>${d}</option>`).join("");
  const div = document.createElement("div");
  div.className = "ed-row ed-io";
  div.innerHTML = `t-CPU <input class="io-en num" type="number" min="0" value="${en_cpu}">
    disp. <select class="io-disp">${opts}</select>
    dur. <input class="io-dur num" type="number" min="1" value="${duracion}">
    <button class="btn ed-mini ed-row-del" type="button">✕</button>`;
  return div;
}

function tarjetaProceso(p = {}) {
  const tam = Math.pow(2, parseInt($("ed-offset").value) || 12);
  const card = document.createElement("div");
  card.className = "ed-proc";
  card.innerHTML = `
    <div class="ed-fila">
      <label>PID <input class="ed-pid num" type="number" min="1" value="${p.pid ?? ""}"></label>
      <label>Nombre <input class="ed-nombre" type="text" value="${(p.nombre ?? "").replace(/"/g, "")}"></label>
      <label>Llegada <input class="ed-lleg num" type="number" min="0" value="${p.llegada ?? 0}"></label>
      <label>Ráfaga <input class="ed-raf num" type="number" min="1" value="${p.rafaga ?? 5}"></label>
      <label>Prioridad <input class="ed-prio num" type="number" min="0" value="${p.prioridad ?? 0}"></label>
      <label>Nivel <select class="ed-nivel">
        <option value="ALTA" ${p.nivel_mlq !== "BAJA" ? "selected" : ""}>ALTA</option>
        <option value="BAJA" ${p.nivel_mlq === "BAJA" ? "selected" : ""}>BAJA</option></select></label>
      <button class="btn peligro ed-proc-del" type="button">Eliminar</button>
    </div>
    <div class="ed-sub">
      <div class="ed-bloque">
        <div class="ed-bloque-cab">Accesos a memoria
          <button class="btn ed-mini ed-acc-add" type="button">＋ acceso</button></div>
        <div class="ed-acc-list"></div>
      </div>
      <div class="ed-bloque">
        <div class="ed-bloque-cab">Peticiones de E/S
          <button class="btn ed-mini ed-io-add" type="button">＋ E/S</button></div>
        <div class="ed-io-list"></div>
      </div>
    </div>`;
  const accList = card.querySelector(".ed-acc-list");
  (p.accesos || []).forEach(a => accList.appendChild(filaAcceso(a.en_cpu, Math.floor((a.va || 0) / tam))));
  const ioList = card.querySelector(".ed-io-list");
  (p.io || []).forEach(x => ioList.appendChild(filaIO(x.en_cpu, x.dispositivo, x.duracion)));
  return card;
}

function abrir(prefill) {
  $("ed-error").textContent = "";
  $("ed-scheduler").value = prefill.scheduler || "fcfs";
  $("ed-quantum").value = prefill.quantum || 3;
  $("ed-replacer").value = prefill.replacer || "fifo";
  $("ed-marcos").value = prefill.num_marcos || 4;
  $("ed-offset").value = prefill.offset_bits || 12;
  $("ed-disp").value = (prefill.dispositivos || []).map(d => d.nombre).join(", ") || "Disco, Impresora";

  const cont = $("ed-procesos");
  cont.innerHTML = "";
  (prefill.procesos || []).forEach(p => cont.appendChild(tarjetaProceso(p)));
  if (!cont.children.length) cont.appendChild(tarjetaProceso({ pid: 1, nombre: "P1" }));
  $("modal-editor").classList.remove("oculto");
}

function cerrar() { $("modal-editor").classList.add("oculto"); }

function repoblarIO() {
  const nombres = dispositivosActuales();
  document.querySelectorAll(".io-disp").forEach(sel => {
    const actual = sel.value;
    sel.innerHTML = nombres.map(d => `<option ${d === actual ? "selected" : ""}>${d}</option>`).join("");
  });
}

function recolectar() {
  const tam = Math.pow(2, parseInt($("ed-offset").value) || 12);
  const procesos = [...document.querySelectorAll(".ed-proc")].map(card => {
    const v = sel => card.querySelector(sel);
    const accesos = [...card.querySelectorAll(".ed-acc")].map(r => ({
      en_cpu: parseInt(r.querySelector(".acc-en").value) || 0,
      va: (parseInt(r.querySelector(".acc-vpn").value) || 0) * tam,
    }));
    const io = [...card.querySelectorAll(".ed-io")].map(r => ({
      en_cpu: parseInt(r.querySelector(".io-en").value) || 0,
      dispositivo: r.querySelector(".io-disp").value,
      duracion: parseInt(r.querySelector(".io-dur").value) || 1,
    }));
    const pid = parseInt(v(".ed-pid").value);
    return {
      pid,
      nombre: v(".ed-nombre").value || ("P" + pid),
      llegada: parseInt(v(".ed-lleg").value) || 0,
      rafaga: parseInt(v(".ed-raf").value) || 1,
      prioridad: parseInt(v(".ed-prio").value) || 0,
      nivel_mlq: v(".ed-nivel").value,
      accesos, io,
    };
  });
  return {
    scheduler: $("ed-scheduler").value,
    quantum: parseInt($("ed-quantum").value) || 3,
    replacer: $("ed-replacer").value,
    num_marcos: parseInt($("ed-marcos").value) || 1,
    offset_bits: parseInt($("ed-offset").value) || 12,
    costo_fault: 0,
    dispositivos: dispositivosActuales().map(n => ({ nombre: n, tipo: "disco" })),
    procesos,
  };
}

function validarCliente(esc) {
  if (!esc.procesos.length) return "Agrega al menos un proceso.";
  const pids = esc.procesos.map(p => p.pid);
  if (pids.some(x => !Number.isInteger(x) || x < 1)) return "Cada proceso necesita un PID entero ≥ 1.";
  if (new Set(pids).size !== pids.length) return "Hay PIDs repetidos.";
  if (!esc.dispositivos.length) return "Define al menos un dispositivo de E/S.";
  for (const p of esc.procesos) {
    if (p.rafaga < 1) return `P${p.pid}: la ráfaga debe ser ≥ 1.`;
    for (const x of p.io) {
      if (!esc.dispositivos.find(d => d.nombre === x.dispositivo))
        return `P${p.pid}: E/S en un dispositivo que no existe ("${x.dispositivo}").`;
      if (x.en_cpu >= p.rafaga) return `P${p.pid}: la E/S debe ocurrir antes de agotar la ráfaga.`;
    }
    for (const a of p.accesos) if (a.en_cpu >= p.rafaga)
      return `P${p.pid}: un acceso a memoria ocurre después de terminar la ráfaga.`;
  }
  return null;
}

async function cargar() {
  const esc = recolectar();
  const err = validarCliente(esc);
  if (err) { $("ed-error").textContent = err; return; }
  try {
    await postJSON("/api/config/scenario", esc);
    cerrar();
  } catch (e) {
    $("ed-error").textContent = "El servidor rechazó el escenario: " + e.message;
  }
}

export function initEditor() {
  $("btn-editor").onclick = async () => {
    let actual = {};
    try { actual = await (await fetch("/api/config/actual")).json(); } catch (e) { /* vacío */ }
    abrir(actual);
  };
  $("ed-cerrar").onclick = cerrar;
  $("ed-cancelar").onclick = cerrar;
  $("ed-cargar").onclick = cargar;
  $("ed-disp").addEventListener("change", repoblarIO);

  $("ed-add").onclick = () => {
    const pids = [...document.querySelectorAll(".ed-pid")].map(i => parseInt(i.value) || 0);
    const next = (pids.length ? Math.max(...pids) : 0) + 1;
    $("ed-procesos").appendChild(tarjetaProceso({ pid: next, nombre: "P" + next }));
  };

  // Delegación de eventos para los botones creados dinámicamente.
  $("ed-procesos").addEventListener("click", (e) => {
    const t = e.target;
    if (t.classList.contains("ed-proc-del")) t.closest(".ed-proc").remove();
    else if (t.classList.contains("ed-acc-add")) t.closest(".ed-proc").querySelector(".ed-acc-list").appendChild(filaAcceso());
    else if (t.classList.contains("ed-io-add")) t.closest(".ed-proc").querySelector(".ed-io-list").appendChild(filaIO());
    else if (t.classList.contains("ed-row-del")) t.closest(".ed-row").remove();
  });

  $("modal-editor").addEventListener("click", (e) => { if (e.target.id === "modal-editor") cerrar(); });
}
