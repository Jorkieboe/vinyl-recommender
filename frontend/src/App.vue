<script setup>
import { ref, onMounted } from 'vue'

const message = ref('Waiting for bridge...')
const response = ref('')

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

onMounted(() => {
  // Check periodically if pywebview is ready
  const interval = setInterval(() => {
    if (window.pywebview && window.pywebview.api) {
      message.value = 'Bridge Connected'
      clearInterval(interval)
    }
  }, 100)

  // Clear interval after 5 seconds to avoid infinite loop if bridge fails
  setTimeout(() => clearInterval(interval), 5000)
})
</script>

<template>
  <div class="min-h-screen bg-gray-900 text-white flex flex-col items-center justify-center p-4">
    <header class="mb-12 text-center">
      <h1 class="text-5xl font-extrabold mb-2 text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-500">
        Vinyl Recommender
      </h1>
      <p class="text-gray-400 italic">Ensure your next purchase is skip-free.</p>
    </header>

    <div class="bg-gray-800 p-8 rounded-2xl shadow-2xl w-full max-w-md border border-gray-700">
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

      <div v-if="response" class="bg-gray-900/50 p-4 rounded-xl border border-gray-700 font-mono text-sm text-indigo-300 break-all">
        <span class="text-gray-500 block mb-1 font-sans text-xs uppercase">Response:</span>
        {{ response }}
      </div>
    </div>

    <footer class="mt-12 text-gray-600 text-xs uppercase tracking-widest">
      Alpha v0.0.1
    </footer>
  </div>
</template>

<style>
body {
  margin: 0;
  font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif;
}
</style>