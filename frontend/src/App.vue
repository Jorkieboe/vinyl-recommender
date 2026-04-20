<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const message = ref('Waiting for bridge...')
const response = ref('')
const userId = ref('2529')
const syncStatus = ref('Idle')
const trackCount = ref(0)
let pollInterval = null

const callEcho = async () => {
  if (window.pywebview && window.pywebview.api) {
    try {
      response.value = await window.pywebview.api.echo('Hello from Vue!')
    } catch (err) {
      response.value = `Error: ${err}`
    }
  } else {
    response.value = 'Bridge not available'
  }
}

const startSync = async () => {
  if (window.pywebview && window.pywebview.api) {
    syncStatus.value = 'Starting...'
    try {
      const res = await window.pywebview.api.start_initial_sync(userId.value)
      syncStatus.value = 'Syncing...'
      console.log(res.message)
      startPolling()
    } catch (err) {
      syncStatus.value = 'Error'
      console.error(err)
    }
  }
}

const updateStatus = async () => {
  if (window.pywebview && window.pywebview.api) {
    try {
      const res = await window.pywebview.api.get_sync_status()
      trackCount.value = res.count
    } catch (err) {
      console.error("Status check failed", err)
    }
  }
}

const startPolling = () => {
  if (pollInterval) clearInterval(pollInterval)
  pollInterval = setInterval(updateStatus, 1000)
}

onMounted(() => {
  const interval = setInterval(() => {
    if (window.pywebview && window.pywebview.api) {
      message.value = 'Bridge Connected'
      updateStatus() // Initial count check
      clearInterval(interval)
    }
  }, 100)
  setTimeout(() => clearInterval(interval), 5000)
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})
</script>

<template>
  <div class="min-h-screen bg-gray-900 text-white flex flex-col items-center p-8">
    <header class="mb-12 text-center">
      <h1 class="text-5xl font-extrabold mb-2 text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-500">
        Vinyl Recommender
      </h1>
      <p class="text-gray-400 italic">Ensure your next purchase is skip-free.</p>
    </header>

    <main class="grid grid-cols-1 md:grid-cols-2 gap-8 w-full max-w-4xl">
      <!-- Section 1: Bridge Test -->
      <section class="bg-gray-800 p-8 rounded-2xl shadow-2xl border border-gray-700 flex flex-col">
        <h2 class="text-xl font-bold mb-6 flex items-center">
          <span class="w-2 h-2 bg-indigo-500 rounded-full mr-3"></span>
          System Bridge
        </h2>

        <div class="flex items-center justify-center mb-6">
          <div
            class="px-4 py-1 rounded-full text-xs font-bold uppercase tracking-wider"
            :class="message === 'Bridge Connected' ? 'bg-green-900/30 text-green-400 border border-green-500/50' : 'bg-yellow-900/30 text-yellow-400 border border-yellow-500/50'"
          >
            {{ message }}
          </div>
        </div>

        <button
          @click="callEcho"
          class="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-3 px-6 rounded-xl transition duration-300 transform hover:scale-[1.02] active:scale-[0.98] mb-6 shadow-lg shadow-indigo-500/20"
        >
          Test Bridge (Echo)
        </button>

        <div v-if="response" class="bg-gray-900/50 p-4 rounded-xl border border-gray-700 font-mono text-sm text-indigo-300 break-all mt-auto">
          <span class="text-gray-500 block mb-1 font-sans text-xs uppercase">Response:</span>
          {{ response }}
        </div>
      </section>

      <!-- Section 2: Deezer Sync Test -->
      <section class="bg-gray-800 p-8 rounded-2xl shadow-2xl border border-gray-700 flex flex-col">
        <h2 class="text-xl font-bold mb-6 flex items-center">
          <span class="w-2 h-2 bg-purple-500 rounded-full mr-3"></span>
          Taste Profile Sync
        </h2>

        <div class="mb-6">
          <label class="block text-xs uppercase text-gray-500 font-bold mb-2">Deezer User ID</label>
          <input
            v-model="userId"
            type="text"
            class="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-indigo-300 focus:outline-none focus:border-indigo-500 transition"
            placeholder="Enter ID (e.g. 2529)"
          />
        </div>

        <button
          @click="startSync"
          class="w-full bg-purple-600 hover:bg-purple-500 text-white font-bold py-3 px-6 rounded-xl transition duration-300 transform hover:scale-[1.02] active:scale-[0.98] mb-6 shadow-lg shadow-purple-500/20"
        >
          Sync Loved Tracks
        </button>

        <div class="grid grid-cols-2 gap-4 mt-auto">
          <div class="bg-gray-900/50 p-4 rounded-xl border border-gray-700 text-center">
            <span class="text-gray-500 block text-xs uppercase mb-1">Status</span>
            <span class="text-purple-400 font-bold">{{ syncStatus }}</span>
          </div>
          <div class="bg-gray-900/50 p-4 rounded-xl border border-gray-700 text-center">
            <span class="text-gray-500 block text-xs uppercase mb-1">Analyzed</span>
            <span class="text-green-400 font-bold font-mono">{{ trackCount }}</span>
          </div>
        </div>
      </section>
    </main>

    <footer class="mt-12 text-gray-600 text-xs uppercase tracking-widest">
      Alpha v0.0.1
    </footer>
  </div>
</template>

<style>
body {
  margin: 0;
  font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif;
  background-color: #111827;
}
</style>