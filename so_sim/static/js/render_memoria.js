// Marcos fisicos, contadores, ultimo acceso (VA->VPN+offset->PA) y tablas.
import { mapProc, nombrePid, hex } from "./state.js";

const $ = (id) => document.getElementById(id);

export function renderMemoria(snap) {
  const m = snap.memoria;
  const map = mapProc(snap);

  $("mem-alg").textContent = `· ${m.algoritmo_nombre} · página ${m.tam_pagina} B`;

  const ct = m.contadores;
  $("mem-contadores").innerHTML = `
    <div class="c aciertos"><b>${ct.aciertos}</b>Aciertos</div>
    <div class="c fallos"><b>${ct.fallos}</b>Fallos</div>
    <div class="c tasa"><b>${(ct.tasa_fallos * 100).toFixed(0)}%</b>Tasa fallos</div>`;

  const ev = m.ultimo_evento_va;
  const marcoFault = (ev && ev.resultado === "FAULT") ? ev.marco : null;

  $("marcos").innerHTML = m.marcos.map(f => {
    if (f.pid === null) {
      const ptr = (m.algoritmo === "reloj" && m.puntero_reloj === f.idx) ? '<span class="reloj-ptr">👆</span>' : "";
      return `<div class="marco libre"><span class="idx">#${f.idx}</span>libre${ptr}</div>`;
    }
    const vic = f.idx === marcoFault ? " victima" : "";
    const ptr = (m.algoritmo === "reloj" && m.puntero_reloj === f.idx) ? '<span class="reloj-ptr">👆</span>' : "";
    return `<div class="marco${vic}" style="background:${f.color}" title="${nombrePid(map, f.pid)}">
      <span class="idx">#${f.idx}</span>P${f.pid}<small>pág ${f.vpn}${f.ref ? " •" : ""}</small>${ptr}</div>`;
  }).join("");

  if (ev) {
    let txt = `<b>Último acceso</b> — P${ev.pid}: VA ${hex(ev.va)} → VPN ${ev.vpn} + offset ${hex(ev.offset)} `;
    if (ev.resultado === "HIT") {
      txt += `→ <b style="color:var(--ok)">ACIERTO</b> · marco ${ev.marco} → PA ${hex(ev.pa)}`;
    } else {
      txt += `→ <b style="color:var(--bad)">FALLO DE PÁGINA</b>`;
      if (ev.victima) txt += ` (reemplaza pág ${ev.victima.vpn} de P${ev.victima.pid})`;
      txt += ` · marco ${ev.marco} → PA ${hex(ev.pa)}`;
    }
    $("mem-ultimo").className = "mem-ultimo " + (ev.resultado === "HIT" ? "hit" : "fault");
    $("mem-ultimo").innerHTML = txt;
  } else {
    $("mem-ultimo").className = "mem-ultimo";
    $("mem-ultimo").innerHTML = '<span style="color:var(--txt2)">Sin accesos a memoria aún.</span>';
  }

  const tablas = m.tablas || {};
  const pids = Object.keys(tablas);
  $("mem-tablas").innerHTML = pids.length ? pids.map(pid => {
    const filas = tablas[pid].map(e =>
      `<tr><td>${e.vpn}</td><td>${e.presente ? "sí" : "no"}</td><td>${e.marco !== null ? e.marco : "—"}</td><td>${e.ref ? "1" : "0"}</td></tr>`).join("");
    const color = map[pid] ? map[pid].color : "#fff";
    return `<div class="tpag"><div class="cab" style="color:${color}">P${pid} — ${nombrePid(map, parseInt(pid))}</div>
      <table><tr><th>VPN</th><th>Pres.</th><th>Marco</th><th>Ref</th></tr>${filas}</table></div>`;
  }).join("") : '<span style="color:var(--txt2)">Sin tablas todavía.</span>';
}
