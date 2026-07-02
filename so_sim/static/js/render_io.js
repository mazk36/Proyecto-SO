// Dispositivos de E/S (5): proceso en servicio + cola + destello en interrupcion.
// El Teclado tiene un boton de "Señal" y, si hay decision pendiente, un banner
// con Cancelar / Continuar. Los botones se manejan por delegacion en controls.js.
import { esc } from "./state.js";

const ICONO = { teclado: "⌨️", disco: "💽", impresora: "🖨️", mouse: "🖱️", red: "🌐" };

export function renderIO(snap) {
  // Dispositivos cuya E/S se completó en este tick (para el destello).
  const recien = new Set();
  (snap.eventos || []).forEach(e => {
    if (e.tick === snap.tick && e.tipo === "interrupcion_io") {
      snap.io.dispositivos.forEach(d => { if (e.texto.includes(d.nombre)) recien.add(d.nombre); });
    }
  });

  const cont = document.getElementById("io-dispositivos");
  cont.innerHTML = snap.io.dispositivos.map(d => {
    const ic = ICONO[d.tipo] || "🔌";
    let serv = '<div class="serv" style="color:var(--txt2)">inactivo</div>';
    if (d.en_servicio) {
      const s = d.en_servicio;
      const pct = Math.round(s.progreso * 100);
      serv = `<div class="serv">⚙ <b style="color:${s.color}">P${s.pid}</b> ${s.ticks_restantes}/${s.duracion_total}
        <div class="barra-prog"><i style="width:${pct}%;background:${s.color}"></i></div></div>`;
    }
    const cola = d.cola.length
      ? d.cola.map(x => `<span class="chip" style="background:${x.color}">P${x.pid}</span>`).join("")
      : '<span style="color:var(--txt2);font-size:10px">cola vacía</span>';
    const btn = d.tipo === "teclado"
      ? `<button class="btn ed-mini btn-teclado-senal" title="Disparar interrupción de teclado">⌨️ Señal</button>`
      : "";
    return `<div class="dispositivo${recien.has(d.nombre) ? " destello" : ""}">
      <div class="nom">${ic} ${esc(d.nombre)} ${btn}</div>
      <div class="tipo">${d.tipo}</div>
      ${serv}<div class="cola-disp">${cola}</div></div>`;
  }).join("");

  const banner = document.getElementById("io-decision");
  const dec = snap.decision_teclado;
  if (dec) {
    banner.classList.remove("oculto");
    banner.innerHTML = `<b>⌨️ Interrupción de teclado</b> sobre P${dec.pid} (${esc(dec.nombre)}):
      el usuario debe decidir.
      <div class="acc">
        <button class="btn peligro btn-teclado-cancelar">Cancelar proceso</button>
        <button class="btn primario btn-teclado-continuar">Continuar</button>
      </div>`;
  } else {
    banner.classList.add("oculto");
    banner.innerHTML = "";
  }
}
