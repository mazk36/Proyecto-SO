// Cliente del API: POST de comandos + stream SSE (con fallback a polling).

export async function postJSON(url, body) {
  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body !== undefined ? JSON.stringify(body) : null,
  });
  if (!r.ok) {
    let detalle;
    try { detalle = (await r.json()).detail; } catch { detalle = await r.text(); }
    throw new Error(detalle || ("Error " + r.status));
  }
  try { return await r.json(); } catch { return {}; }
}

export async function getState() {
  const r = await fetch("/api/state");
  return r.json();
}

// Abre el stream SSE. Si falla (proxy/antivirus en Windows), cae a polling de
// /api/state hasta que el stream vuelva. El servidor conduce el reloj.
export function iniciarStream(onSnapshot) {
  let pollTimer = null;
  const poll = () => getState().then(onSnapshot).catch(() => {});
  const startPoll = () => { if (!pollTimer) { poll(); pollTimer = setInterval(poll, 800); } };
  const stopPoll = () => { if (pollTimer) { clearInterval(pollTimer); pollTimer = null; } };

  try {
    const es = new EventSource("/api/stream");
    es.onmessage = (e) => {
      stopPoll();
      try { onSnapshot(JSON.parse(e.data)); } catch (err) { /* keep-alive u otro */ }
    };
    es.onerror = () => { startPoll(); };   // EventSource reintenta solo; mientras, polling
  } catch (e) {
    startPoll();
  }
}
