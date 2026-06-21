// Dispositivos de E/S: proceso en servicio (barra de progreso) + cola.

export function renderIO(snap) {
  const cont = document.getElementById("io-dispositivos");
  cont.innerHTML = snap.io.dispositivos.map(d => {
    let serv = '<div class="serv" style="color:var(--txt2)">inactivo</div>';
    if (d.en_servicio) {
      const s = d.en_servicio;
      const pct = Math.round(s.progreso * 100);
      serv = `<div class="serv">⚙ <b style="color:${s.color}">P${s.pid}</b> — ${s.ticks_restantes}/${s.duracion_total} ticks
        <div class="barra-prog"><i style="width:${pct}%;background:${s.color}"></i></div></div>`;
    }
    const cola = d.cola.length
      ? d.cola.map(x => `<span class="chip" style="background:${x.color}">P${x.pid}</span>`).join("")
      : '<span style="color:var(--txt2);font-size:11px">cola vacía</span>';
    return `<div class="dispositivo">
      <div class="nom">${d.nombre}</div><div class="tipo">${d.tipo}</div>
      ${serv}<div class="cola-disp">${cola}</div></div>`;
  }).join("");
}
