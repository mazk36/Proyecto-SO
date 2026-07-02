// Metricas por proceso (espera/retorno/respuesta) + promedios + conteo de errores.

export function renderMetricas(snap) {
  const ps = snap.procesos;
  const pr = snap.metricas;

  const resumen = `<div class="metr-resumen">
    <div class="m"><b>${pr.terminados}/${pr.total}</b>terminados</div>
    <div class="m ok"><b>${pr.terminados_ok ?? 0}</b>OK</div>
    <div class="m err"><b>${pr.con_error ?? 0}</b>con error</div>
  </div>`;

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
    ? `<tr class="prom"><td>Promedio</td><td>${pr.espera}</td><td>${pr.retorno}</td>
       <td>${pr.respuesta !== null ? pr.respuesta : "—"}</td></tr>`
    : `<tr class="prom"><td colspan="4">Aún no termina ningún proceso…</td></tr>`;

  document.getElementById("tabla-metricas").innerHTML = resumen +
    `<table><tr><th>Proc</th><th>Espera</th><th>Retorno</th><th>Respuesta</th></tr>${filas}${prom}</table>`;
}
