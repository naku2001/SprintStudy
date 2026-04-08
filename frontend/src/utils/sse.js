/**
 * Consume a Server-Sent Events response stream.
 * Calls onEvent(eventName, parsedPayload) for each received event.
 */
export async function consumeSse(response, onEvent) {
  const reader = response.body.getReader();
  const dec = new TextDecoder('utf-8');
  let buf = '';

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });

    let idx;
    while ((idx = buf.indexOf('\n\n')) !== -1) {
      const raw = buf.slice(0, idx).trim();
      buf = buf.slice(idx + 2);
      if (!raw) continue;

      let evt = 'message';
      let data = '';
      for (const line of raw.split('\n')) {
        if (line.startsWith('event:')) evt = line.slice(6).trim();
        if (line.startsWith('data:'))  data += line.slice(5).trim();
      }
      if (!data) continue;

      let payload;
      try { payload = JSON.parse(data); } catch { payload = { text: data }; }
      onEvent(evt, payload);
    }
  }
}
