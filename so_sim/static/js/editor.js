// Editor de procesos / escenario: construye un escenario completo (memoria fisica,
// paginacion, dispatcher, procesos) y lo carga via POST /api/config/scenario.
// Validacion inline por campo antes de enviar (sin alert()).
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

function filaIO(en_cpu = 0, dispositivo = "", duracion = 3) {
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
    <div class="ed-fila">
      <label>Ejecutable (KB) <input class="ed-tejec num" type="number" min="1" value="${p.tam_ejecutable ?? 128}"></label>
      <label>Datos (KB) <input class="ed-tdatos num" type="number" min="0" value="${p.tam_datos ?? 64}"></label>
      <label>Dinámica (KB) <input class="ed-tdin num" type="number" min="0" value="${p.tam_dinamica ?? 32}"></label>
      <label>Interrupciones <select class="ed-modo">
        <option value="declarativo" ${p.modo_interrupciones !== "aleatorio" ? "selected" : ""}>declarativo</option>
        <option value="aleatorio" ${p.modo_interrupciones === "aleatorio" ? "selected" : ""}>aleatorio</option></select></label>
    </div>
    <div class="ed-sub">
      <div class="ed-bloque">
        <div class="ed-bloque-cab">Accesos a memoria (paginación)
          <button class="btn ed-mini ed-acc-add" type="button">＋</button></div>
        <div class="ed-acc-list"></div>
      </div>
      <div class="ed-bloque">
        <div class="ed-bloque-cab">Peticiones de E/S (modo declarativo)
          <button class="btn ed-mini ed-io-add" type="button">＋</button></div>
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
  $("ed-costocc").value = prefill.costo_cambio ?? 0;
  $("ed-error-rate").value = ((prefill.tasa_error ?? 0) * 100).toFixed(1);
  $("ed-ram").value = prefill.ram_total || 16384;
  $("ed-ramso").value = prefill.ram_so ?? 2048;
  $("ed-bloque").value = prefill.tam_bloque || 256;
  $("ed-estrategia").value = prefill.estrategia_mem || "first_fit";
  $("ed-pag").checked = prefill.paginacion_activa !== false;
  $("ed-marcos").value = prefill.num_marcos || 4;
  $("ed-offset").value = prefill.offset_bits || 12;
  $("ed-replacer").value = prefill.replacer || "fifo";
  $("ed-disp").value = (prefill.dispositivos || []).map(d => d.nombre).join(", ")
    || "Teclado, Disco, Impresora, Mouse, Red";

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
      tam_ejecutable: parseInt(v(".ed-tejec").value) || 1,
      tam_datos: parseInt(v(".ed-tdatos").value) || 0,
      tam_dinamica: parseInt(v(".ed-tdin").value) || 0,
      modo_interrupciones: v(".ed-modo").value,
      accesos, io,
    };
  });
  return {
    scheduler: $("ed-scheduler").value,
    quantum: parseInt($("ed-quantum").value) || 3,
    costo_cambio: parseInt($("ed-costocc").value) || 0,
    tasa_error: (parseFloat($("ed-error-rate").value) || 0) / 100,
    ram_total: parseInt($("ed-ram").value) || 16384,
    ram_so: parseInt($("ed-ramso").value) || 0,
    tam_bloque: parseInt($("ed-bloque").value) || 256,
    estrategia_mem: $("ed-estrategia").value,
    paginacion_activa: $("ed-pag").checked,
    num_marcos: parseInt($("ed-marcos").value) || 1,
    offset_bits: parseInt($("ed-offset").value) || 12,
    replacer: $("ed-replacer").value,
    dispositivos: dispositivosActuales().map(n => ({ nombre: n, tipo: n.toLowerCase() })),
    procesos,
  };
}

function esPot2(n) { return n > 0 && (n & (n - 1)) === 0; }

function validarCliente(esc) {
  if (!esc.procesos.length) return "Agrega al menos un proceso.";
  if (!esc.dispositivos.length) return "Define al menos un dispositivo de E/S.";
  if (!esPot2(esc.tam_bloque) || esc.tam_bloque < 32 || esc.tam_bloque > 2048)
    return "El tamaño de bloque debe ser potencia de 2 entre 32 y 2048 KB.";
  if (esc.ram_so >= esc.ram_total) return "La RAM del SO debe ser menor que la RAM total.";
  const disponible = esc.ram_total - esc.ram_so;
  const pids = esc.procesos.map(p => p.pid);
  if (pids.some(x => !Number.isInteger(x) || x < 1)) return "Cada proceso necesita un PID entero ≥ 1.";
  if (new Set(pids).size !== pids.length) return "Hay PIDs repetidos.";
  for (const p of esc.procesos) {
    if (p.rafaga < 1) return `P${p.pid}: la ráfaga debe ser ≥ 1.`;
    const tam = p.tam_ejecutable + p.tam_datos + p.tam_dinamica;
    if (tam > disponible) return `P${p.pid}: necesita ${tam} KB pero solo hay ${disponible} KB para procesos.`;
    for (const x of p.io) {
      if (!esc.dispositivos.find(d => d.nombre === x.dispositivo))
        return `P${p.pid}: E/S en un dispositivo inexistente ("${x.dispositivo}").`;
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

  $("ed-procesos").addEventListener("click", (e) => {
    const t = e.target;
    if (t.classList.contains("ed-proc-del")) t.closest(".ed-proc").remove();
    else if (t.classList.contains("ed-acc-add")) t.closest(".ed-proc").querySelector(".ed-acc-list").appendChild(filaAcceso());
    else if (t.classList.contains("ed-io-add")) t.closest(".ed-proc").querySelector(".ed-io-list").appendChild(filaIO());
    else if (t.classList.contains("ed-row-del")) t.closest(".ed-row").remove();
  });

  $("modal-editor").addEventListener("click", (e) => { if (e.target.id === "modal-editor") cerrar(); });
}
