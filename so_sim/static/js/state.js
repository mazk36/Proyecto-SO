// Helpers compartidos por los renderizadores. Los colores vienen del backend
// (cada proceso trae su color HSL estable), aqui solo se consultan por pid.

export function mapProc(snap) {
  const m = {};
  (snap.procesos || []).forEach(p => { m[p.pid] = p; });
  return m;
}

export function colorPid(map, pid) {
  return map[pid] ? map[pid].color : "#4a546b";
}

export function nombrePid(map, pid) {
  return map[pid] ? map[pid].nombre : ("P" + pid);
}

export function chip(map, pid) {
  return `<span class="chip" style="background:${colorPid(map, pid)}" title="${esc(nombrePid(map, pid))}">P${pid}</span>`;
}

export function esc(s) {
  return String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

export function hex(v) {
  return "0x" + (v >>> 0).toString(16).toUpperCase();
}
