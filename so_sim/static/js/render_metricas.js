// Tabla de metricas por proceso (espera/retorno/respuesta) + promedios.

export function renderMetricas(snap) {
  const ps = snap.procesos;
  const pr = snap.metricas;

  const filas = ps.map(p => {
    const m = p.metricas;
    return `<tr>
      <td><span class="dotpid" style="background:${p.color}"></span>P${p.pid}</td>
      <td>${m.espera}</td>
      <td>${m.retorno !== null ? m.retorno : "—"}</td>
      <td>${m.respuesta !== null ? m.respuesta : "—"}</td>
    </tr>`;
  }).join("");

  const prom = (pr.retorno !== null)
    ? `<tr class="prom"><td>Promedio (${pr.terminados}/${pr.total})</td>
       <td>${pr.espera}</td><td>${pr.retorno}</td><td>${pr.respuesta !== null ? pr.respuesta : "—"}</td></tr>`
    : `<tr class="prom"><td colspan="4">Aún no termina ningún proceso…</td></tr>`;

  document.getElementById("tabla-metricas").innerHTML =
    `<table><tr><th>Proc</th><th>Espera</th><th>Retorno</th><th>Respuesta</th></tr>${filas}${prom}</table>`;
}
