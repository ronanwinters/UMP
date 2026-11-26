<script setup>
defineProps({ server: { type: Object, required: true } })

const label = { ok: 'OK', warn: 'App stopped', error: 'Unreachable', not_reporting: 'Not reporting', pending: 'Checking…' }
</script>

<template>
  <article class="card">
    <div class="head">
      <span class="dot" :class="server.status.state"></span>
      <a :href="server.url" target="_blank" rel="noopener" class="name">{{ server.name }}</a>
      <span class="zone">{{ server.zone }}</span>
    </div>
    <div class="role">{{ server.role }}</div>
    <div class="state">{{ label[server.status.state] ?? server.status.state }}
      <span v-if="server.status.error" class="err"> · {{ server.status.error }}</span>
    </div>

    <template v-if="server.status.server">
      <dl>
        <dt>Memory</dt><dd>{{ server.status.server.memory_gb }} GB</dd>
        <dt>Cores</dt><dd>{{ server.status.server.cores }}</dd>
        <dt>Heap</dt><dd>{{ server.status.jvm?.heap_max_gb ?? '—' }} GB</dd>
        <dt>Java</dt><dd>{{ server.status.jvm?.java_version ?? '—' }}</dd>
      </dl>
      <ul class="instances" v-if="server.status.snapshots?.length">
        <li v-for="i in server.status.snapshots" :key="i.name">
          <span class="dot small" :class="i.deployed ? 'ok' : 'off'"></span>
          <a :href="server.url + i.url" target="_blank" rel="noopener">{{ i.name }}</a>
          <small v-if="i.calculator_threads">{{ i.calculator_threads }} threads</small>
        </li>
      </ul>
    </template>
  </article>
</template>

<style scoped>
.card { background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: .9rem 1rem; box-shadow: 0 4px 12px rgba(0,0,0,.04); }
.head { display: flex; align-items: center; gap: .5rem; }
.name { font-weight: 600; font-size: 1.05rem; color: var(--ink); text-decoration: none; }
.name:hover { color: var(--accent); }
.zone { margin-left: auto; font-size: .75rem; color: var(--muted); }
.role { color: var(--muted); font-size: .85rem; margin: .15rem 0 .4rem; }
.state { font-size: .85rem; }
.err { color: var(--err); }
.dot { width: 11px; height: 11px; border-radius: 50%; background: var(--off); flex: none; }
.dot.small { width: 8px; height: 8px; }
.dot.ok { background: var(--ok); } .dot.warn { background: var(--warn); } .dot.error { background: var(--err); }
dl { display: grid; grid-template-columns: auto 1fr; gap: .1rem .8rem; margin: .7rem 0 0; font-size: .8rem; }
dt { color: var(--muted); } dd { margin: 0; }
.instances { list-style: none; margin: .7rem 0 0; padding: .6rem 0 0; border-top: 1px solid var(--line); font-size: .85rem; }
.instances li { display: flex; align-items: center; gap: .5rem; padding: .15rem 0; }
.instances a { color: var(--accent); text-decoration: none; font-family: Consolas, Menlo, monospace; }
.instances small { color: var(--muted); margin-left: auto; }
</style>
