// One place for every call to the backend.
async function get(path) {
  const r = await fetch(path)
  if (!r.ok) throw new Error(`${path}: ${r.status}`)
  return r.json()
}
async function post(path, body) {
  const r = await fetch(path, { method: 'POST', headers: { 'content-type': 'application/json' }, body: body ? JSON.stringify(body) : undefined })
  if (!r.ok) throw new Error(`${path}: ${r.status}`)
  return r.json()
}

export const api = {
  health:  () => get('/api/health'),
  servers: () => get('/api/servers'),
  events:  (limit = 50) => get(`/api/events?limit=${limit}`),
  pollNow: () => post('/api/servers/poll'),
}
