// Bitacora con badges de color por tipo, ultimos eventos resaltados y utilidades
// de Limpiar (cliente) y Exportar .txt.
import { esc } from "./state.js";

const BADGE = {
  interrupcion_io: ["be-io", "E/S"], bloqueo_io: ["be-io", "E/S"],
  fin_quantum: ["be-reloj", "Reloj"], apropiacion: ["be-reloj", "Reloj"],
  abort_error: ["be-abort", "Abort"], terminacion: ["be-otro", "Fin"],
  cambio_contexto: ["be-ctx", "Contexto"],
  teclado_senal: ["be-teclado", "Teclado"], teclado_cancela: ["be-teclado", "Teclado"],
  teclado_continua: ["be-teclado", "Teclado"],
  page_fault: ["be-otro", "Pág.Fault"], page_hit: ["be-otro", "Pág.Hit"],
  admision: ["be-otro", "Admisión"], despacho: ["be-otro", "Despacho"],
  carga_memoria: ["be-otro", "Mem"], libera_memoria: ["be-otro", "Mem"],
};

let minTick = 0;          // eventos con tick < minTick quedan "limpiados" (cliente)
let ultimos = [];         // ultimos eventos mostrados (para exportar)

export function limpiarLog(snap) { minTick = (snap ? snap.tick : 0) + 1; render([]); }
export function resetLog() { minTick = 0; }

export function exportarLog() {
  const txt = ultimos.map(e => `[Tick ${String(e.tick).padStart(3, "0")}] [${e.tipo}] ${e.texto}`).join("\n");
  const blob = new Blob([txt || "(sin eventos)"], { type: "text/plain;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "bitacora_so.txt";
  a.click();
  URL.revokeObjectURL(a.href);
}

function render(eventos) {
  const items = eventos.slice().reverse();
  document.getElementById("bitacora").innerHTML = items.map((e, i) => {
    const [cls, etq] = BADGE[e.tipo] || ["be-otro", e.tipo];
    const reciente = i < 3 ? " reciente" : "";
    return `<li class="${reciente}">
      <span class="t mono">${e.tick}</span>
      <span class="badge-ev ${cls}">${etq}</span>
      <span>${esc(e.texto)}</span></li>`;
  }).join("");
}

export function renderLog(snap) {
  ultimos = (snap.eventos || []).filter(e => e.tick >= minTick);
  render(ultimos);
}
