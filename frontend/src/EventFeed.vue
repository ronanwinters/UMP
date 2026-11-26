<script setup>
defineProps({ events: { type: Array, required: true } })
const when = iso => new Date(iso).toLocaleString()
</script>

<template>
  <div class="feed">
    <p v-if="!events.length" class="empty">
      No events yet. Post one to try it:<br>
      <code>curl -X POST localhost:8000/api/events -H 'content-type: application/json' -d '{"source":"bolt","instance":"jpmorgan","kind":"login","message":"jsmith logged in"}'</code>
    </p>
    <table v-else>
      <tr v-for="(e, i) in events" :key="i" :class="e.level">
        <td class="t">{{ when(e.received) }}</td>
        <td class="src">{{ e.source }}<span v-if="e.instance">/{{ e.instance }}</span></td>
        <td class="kind">{{ e.kind }}</td>
        <td>{{ e.message }}</td>
      </tr>
    </table>
  </div>
</template>

<style scoped>
.feed { background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: .4rem .9rem; }
.empty { color: var(--muted); font-size: .9rem; }
code { display: block; margin-top: .4rem; font-size: .75rem; white-space: pre-wrap; }
table { width: 100%; border-collapse: collapse; font-size: .85rem; }
td { padding: .4rem .5rem; border-top: 1px solid var(--line); vertical-align: top; }
tr:first-child td { border-top: 0; }
.t { color: var(--muted); white-space: nowrap; }
.src { font-family: Consolas, Menlo, monospace; white-space: nowrap; }
.kind { color: var(--muted); }
tr.warn td { background: #fbf0dc; } tr.error td { background: #f8eaea; }
</style>
