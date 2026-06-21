// Diagrama de Gantt en <canvas>, dibujado desde los segmentos comprimidos.

export function renderGantt(snap) {
  const cv = document.getElementById("cv-gantt");
  const ctx = cv.getContext("2d");
  const segs = snap.gantt || [];
  const maxTick = Math.max(1, snap.tick || 1);

  const cell = Math.max(10, Math.min(30, 760 / maxTick));
  const margenX = 24;
  const w = Math.max(760, maxTick * cell + margenX + 16);
  const h = cv.height;
  cv.width = w;
  ctx.clearRect(0, 0, w, h);

  const top = 16, barH = 48;
  ctx.font = "12px Consolas, monospace";

  segs.forEach(s => {
    const x = margenX + s.inicio * cell;
    const ancho = (s.fin - s.inicio) * cell;
    if (s.pid === null) {
      ctx.fillStyle = "#2a3145";
    } else {
      ctx.fillStyle = s.color || "#4f8cff";
    }
    ctx.fillRect(x, top, ancho, barH);
    ctx.strokeStyle = "#0f1420";
    ctx.strokeRect(x, top, ancho, barH);
    if (s.pid !== null && ancho > 14) {
      ctx.fillStyle = "#0b1020";
      ctx.textAlign = "center";
      ctx.fillText("P" + s.pid, x + ancho / 2, top + barH / 2 + 4);
    }
  });

  // Eje de tiempo (etiquetas espaciadas si las celdas son angostas).
  ctx.fillStyle = "#9aa6c0";
  ctx.textAlign = "center";
  const paso = cell < 18 ? Math.ceil(18 / cell) : 1;
  for (let t = 0; t <= maxTick; t++) {
    if (t % paso === 0) {
      const x = margenX + t * cell;
      ctx.fillText(t, x, top + barH + 16);
      ctx.strokeStyle = "#252d40";
      ctx.beginPath(); ctx.moveTo(x, top); ctx.lineTo(x, top + barH); ctx.stroke();
    }
  }
}
