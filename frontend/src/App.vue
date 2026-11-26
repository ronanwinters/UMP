<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { api } from './api'
import ServerCard from './ServerCard.vue'
import EventFeed from './EventFeed.vue'

const servers = ref([])
const events = ref([])
const error = ref('')
const lastRefresh = ref(null)

async function refresh() {
  try {
    ;[servers.value, events.value] = await Promise.all([api.servers(), api.events()])
    lastRefresh.value = new Date()
    error.value = ''
  } catch (e) {
    error.value = e.message
  }
}
async function pollNow() { await api.pollNow(); await refresh() }

let timer
onMounted(() => { refresh(); timer = setInterval(refresh, 30000) })
onUnmounted(() => clearInterval(timer))
</script>

<template>
  <main class="wrap">
    <header>
      <div>
        <h1>PROMS Maintenance Panel</h1>
        <p class="sub">All servers and instances · hello-world build</p>
        <div class="line"></div>
      </div>
      <div class="actions">
        <button @click="pollNow">Refresh now</button>
        <small v-if="lastRefresh">updated {{ lastRefresh.toLocaleTimeString() }}</small>
      </div>
    </header>

    <p v-if="error" class="error">Backend unreachable: {{ error }}</p>

    <section>
      <h2>Servers</h2>
      <div class="grid">
        <ServerCard v-for="s in servers" :key="s.name" :server="s" />
      </div>
    </section>

    <section>
      <h2>Activity</h2>
      <EventFeed :events="events" />
    </section>
  </main>
</template>

<style scoped>
.wrap { max-width: 1100px; margin: 0 auto; padding: 2rem 1rem; }
header { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; flex-wrap: wrap; }
h1 { font-size: 1.6rem; margin: 0; }
.sub { color: var(--muted); margin: .2rem 0 0; }
.line { width: 60px; height: 3px; background: var(--accent); border-radius: 2px; margin: .8rem 0; }
.actions { display: flex; flex-direction: column; align-items: flex-end; gap: .3rem; }
.actions small { color: var(--muted); }
button { background: var(--accent); color: #fff; border: 0; border-radius: 6px; padding: .5rem .9rem; cursor: pointer; font: inherit; }
h2 { font-size: .8rem; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); margin: 1.6rem 0 .6rem; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: .8rem; }
.error { background: #f8eaea; border-left: 4px solid var(--accent); padding: .8rem; border-radius: 6px; }
</style>
