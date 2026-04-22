<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const message = ref('Waiting for bridge...')
const response = ref('')
const userId = ref('2529')
const syncStatus = ref('Idle')
const trackCount = ref(0)
const syncedTracks = ref([])

// Album Analysis State
const activeAnalysis = ref(null)
const analysisResult = ref(null)

// CLAP Analysis State
const activeClap = ref(null)
const clapResult = ref(null)

let pollInterval = null
let analysisInterval = null
let clapInterval = null

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
      if (trackCount.value > 0 && syncedTracks.value.length === 0) {
        fetchSyncedTracks()
      }
    } catch (err) {
      console.error("Status check failed", err)
    }
  }
}

const fetchSyncedTracks = async () => {
  if (window.pywebview && window.pywebview.api) {
    syncedTracks.value = await window.pywebview.api.get_synced_tracks()
  }
}

const analyzeAlbum = async (trackId) => {
  if (window.pywebview && window.pywebview.api) {
    // Reset CLAP state
    if (clapInterval) clearInterval(clapInterval)
    activeClap.value = null
    clapResult.value = null

    activeAnalysis.value = { status: 'Analyzing...', id: trackId }
    analysisResult.value = null
    try {
      const res = await window.pywebview.api.analyze_album_for_track(trackId)
      if (res.status === 'success') {
        analysisResult.value = res.data
        activeAnalysis.value = null
      } else {
        startAnalysisPolling(res.album_id)
      }
    } catch (err) {
      activeAnalysis.value = { status: 'Error' }
      console.error(err)
    }
  }
}

const startAnalysisPolling = (albumId) => {
  if (analysisInterval) clearInterval(analysisInterval)
  analysisInterval = setInterval(async () => {
    const res = await window.pywebview.api.get_album_analysis(albumId)
    if (res.status === 'success') {
      analysisResult.value = res.data
      activeAnalysis.value = null
      clearInterval(analysisInterval)
    }
  }, 2000)
}

const testClap = async (trackId) => {
  if (window.pywebview && window.pywebview.api) {
    // Reset Album state
    if (analysisInterval) clearInterval(analysisInterval)
    activeAnalysis.value = null
    analysisResult.value = null

    activeClap.value = { status: 'Running CLAP Models...', id: trackId }
    clapResult.value = null
    try {
      const res = await window.pywebview.api.test_clap_on_track(trackId)
      if (res.status === 'success') {
        clapResult.value = res.data
        activeClap.value = null
      } else {
        startClapPolling(trackId)
      }
    } catch (err) {
      activeClap.value = { status: 'Error' }
      console.error(err)
    }
  }
}

const startClapPolling = (trackId) => {
  if (clapInterval) clearInterval(clapInterval)
  clapInterval = setInterval(async () => {
    const res = await window.pywebview.api.get_clap_result(trackId)
    if (res.status === 'success') {
      clapResult.value = res.data
      activeClap.value = null
      clearInterval(clapInterval)
    }
  }, 2000)
}

const startPolling = () => {
  if (pollInterval) clearInterval(pollInterval)
  pollInterval = setInterval(() => {
    updateStatus()
    fetchSyncedTracks()
  }, 2000)
}

onMounted(() => {
  const interval = setInterval(() => {
    if (window.pywebview && window.pywebview.api) {
      message.value = 'Bridge Connected'
      updateStatus()
      fetchSyncedTracks()
      clearInterval(interval)
    }
  }, 100)
  setTimeout(() => clearInterval(interval), 5000)
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
  if (analysisInterval) clearInterval(analysisInterval)
  if (clapInterval) clearInterval(clapInterval)
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

    <main class="w-full max-w-6xl grid grid-cols-1 lg:grid-cols-3 gap-8">

      <!-- Left Column: Controls & Stats -->
      <div class="lg:col-span-1 space-y-8">
        <section class="bg-gray-800 p-6 rounded-2xl shadow-xl border border-gray-700">
          <h2 class="text-lg font-bold mb-4 flex items-center">
            <span class="w-2 h-2 bg-purple-500 rounded-full mr-3"></span>
            Sync Profile
          </h2>
          <div class="mb-4">
            <label class="block text-xs uppercase text-gray-500 font-bold mb-2">Deezer User ID</label>
            <input
              v-model="userId"
              type="text"
              class="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-2 text-indigo-300 focus:outline-none focus:border-indigo-500 transition"
            />
          </div>
          <button
            @click="startSync"
            class="w-full bg-purple-600 hover:bg-purple-500 text-white font-bold py-2 rounded-xl transition duration-300 mb-4"
          >
            Sync Loved Tracks
          </button>
          <div class="grid grid-cols-2 gap-4">
            <div class="bg-gray-900/50 p-3 rounded-xl border border-gray-700 text-center">
              <span class="text-gray-500 block text-[10px] uppercase">Status</span>
              <span class="text-purple-400 text-sm font-bold">{{ syncStatus }}</span>
            </div>
            <div class="bg-gray-900/50 p-3 rounded-xl border border-gray-700 text-center">
              <span class="text-gray-500 block text-[10px] uppercase">Tracks</span>
              <span class="text-green-400 text-sm font-bold">{{ trackCount }}</span>
            </div>
          </div>
        </section>

        <section class="bg-gray-800 p-6 rounded-2xl shadow-xl border border-gray-700">
          <h2 class="text-lg font-bold mb-4 flex items-center">
            <span class="w-2 h-2 bg-indigo-500 rounded-full mr-3"></span>
            System
          </h2>
          <div class="flex items-center justify-between mb-4">
            <div
              class="px-3 py-1 rounded-full text-[10px] font-bold uppercase"
              :class="message === 'Bridge Connected' ? 'bg-green-900/30 text-green-400' : 'bg-yellow-900/30 text-yellow-400'"
            >
              {{ message }}
            </div>
            <button @click="callEcho" class="text-xs text-indigo-400 hover:underline">Test Bridge</button>
          </div>
          <div v-if="response" class="bg-gray-900/50 p-3 rounded-xl border border-gray-700 font-mono text-[10px] text-indigo-300 break-all">
            {{ response }}
          </div>
        </section>
      </div>

      <!-- Center Column: Loved Tracks Dashboard -->
      <div class="lg:col-span-1">
        <section class="bg-gray-800 rounded-2xl shadow-xl border border-gray-700 overflow-hidden flex flex-col h-[600px]">
          <div class="p-6 border-b border-gray-700">
            <h2 class="text-lg font-bold">Your Loved Tracks</h2>
            <p class="text-xs text-gray-400">Click to evaluate full album suitability.</p>
          </div>
          <div class="flex-1 overflow-y-auto p-4 space-y-2">
            <div v-for="track in syncedTracks" :key="track.id"
                 class="group bg-gray-900/40 hover:bg-gray-700 p-3 rounded-xl border border-gray-700/50 transition cursor-pointer flex items-center"
                 @click="analyzeAlbum(track.id)">
              <img :src="track.cover" class="w-10 h-10 rounded-lg mr-3 shadow-lg group-hover:scale-105 transition" v-if="track.cover" />
              <div class="flex-1 min-w-0">
                <p class="font-bold text-sm truncate group-hover:text-indigo-400 transition">{{ track.title }}</p>
                <p class="text-[10px] text-gray-500 truncate">{{ track.artist }} • {{ track.album }}</p>
              </div>

              <!-- CLAP AI Tagging Test Button -->
              <button @click.stop="testClap(track.id)" title="AI Audio Tagging Test" class="ml-2 bg-pink-600/20 group-hover:bg-pink-600 text-pink-400 group-hover:text-white p-2 rounded-lg transition">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </button>

              <button class="ml-2 bg-indigo-600/20 group-hover:bg-indigo-600 text-indigo-400 group-hover:text-white p-2 rounded-lg transition" title="Evaluate Full Album">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>
            <div v-if="syncedTracks.length === 0" class="text-center py-12 text-gray-500 italic text-sm">
              No tracks synced yet.
            </div>
          </div>
        </section>
      </div>

      <!-- Right Column: Analysis Verdict & CLAP -->
      <div class="lg:col-span-1">
        <section class="bg-gray-800 p-6 rounded-2xl shadow-xl border border-gray-700 min-h-[600px] flex flex-col overflow-y-auto">

          <!-- CLAP Loading State -->
          <div v-if="activeClap" class="flex-1 flex flex-col items-center justify-center space-y-4">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-pink-500"></div>
            <p class="text-pink-400 font-bold animate-pulse">{{ activeClap.status }}</p>
            <p class="text-[10px] text-gray-500 max-w-[200px] text-center">First run will download the model to your device (this may take a few minutes).</p>
          </div>

          <!-- CLAP Result View -->
          <div v-else-if="clapResult" class="space-y-6">
            <div class="text-center mb-6">
                <h2 class="text-xl font-bold mt-4 text-pink-400 flex items-center justify-center">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  CLAP Audio Analysis
                </h2>
                <p class="text-xs text-gray-400 mt-2">Natural language semantic tag probabilities</p>
            </div>
            <div v-for="(probs, layerName) in clapResult" :key="layerName" class="bg-gray-900/50 p-4 rounded-xl border border-gray-700">
                <h4 class="text-[10px] uppercase font-bold text-gray-500 mb-3 tracking-widest">{{ layerName }}</h4>
                <div class="space-y-3">
                    <div v-for="(prob, label) in probs" :key="label" class="flex items-center">
                        <div class="w-32 truncate text-[11px] text-gray-300 pr-3" :title="label">{{ label }}</div>
                        <div class="flex-1 bg-gray-800 rounded-full h-1.5 overflow-hidden">
                            <div class="bg-pink-500 h-1.5 rounded-full transition-all duration-1000" :style="{ width: (prob * 100) + '%' }"></div>
                        </div>
                        <div class="w-10 text-right text-[10px] text-gray-500 font-mono">{{ Math.round(prob * 100) }}%</div>
                    </div>
                </div>
            </div>
          </div>

          <!-- Album Analysis Loading State -->
          <div v-else-if="activeAnalysis" class="flex-1 flex flex-col items-center justify-center space-y-4">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500"></div>
            <p class="text-indigo-400 font-bold animate-pulse">{{ activeAnalysis.status }}</p>
            <p class="text-[10px] text-gray-500 max-w-[200px] text-center">Analyzing every track on the album for sonic compatibility...</p>
          </div>

          <!-- Album Analysis Verdict View -->
          <div v-else-if="analysisResult" class="space-y-6">
            <h2 class="text-lg font-bold mb-2 flex items-center">
              <span class="w-2 h-2 bg-indigo-500 rounded-full mr-3"></span>
              The Verdict
            </h2>
            <div class="text-center">
              <div class="relative inline-block mb-4">
                <img :src="analysisResult.cover_url" class="w-48 h-48 rounded-2xl shadow-2xl mx-auto border-4 border-gray-700" v-if="analysisResult.cover_url" />
                <div class="absolute -bottom-4 -right-4 inline-flex items-center justify-center p-4 rounded-full border-4 bg-gray-800 shadow-xl"
                     :class="analysisResult.confidence_score > 70 ? 'border-green-500' : 'border-yellow-500'">
                  <span class="text-2xl font-black">{{ analysisResult.confidence_score }}%</span>
                </div>
              </div>
              <h3 class="text-xl font-bold mt-4">{{ analysisResult.title }}</h3>
              <p class="text-sm text-gray-400">{{ analysisResult.artist }}</p>
            </div>

            <div class="bg-gray-900/50 p-4 rounded-xl border border-gray-700">
              <h4 class="text-[10px] uppercase font-bold text-gray-500 mb-2 tracking-widest">Sonic Breakdown</h4>
              <p class="text-sm italic leading-relaxed text-gray-300">"{{ analysisResult.analysis_json.sonic_breakdown }}"</p>
            </div>

            <div v-if="analysisResult.analysis_json.filler_tracks?.length" class="space-y-2">
              <h4 class="text-[10px] uppercase font-bold text-red-400 tracking-widest">Risk Factor: Possible Skips</h4>
              <div class="flex flex-wrap gap-2">
                <span v-for="track in analysisResult.analysis_json.filler_tracks" :key="track"
                      class="px-2 py-1 bg-red-900/20 text-red-400 text-[10px] rounded border border-red-900/50">
                  {{ track }}
                </span>
              </div>
            </div>

            <div v-if="analysisResult.analysis_json.acquisition_links?.length" class="space-y-3 pt-4 border-t border-gray-700">
              <h4 class="text-[10px] uppercase font-bold text-green-400 tracking-widest">Where to Buy</h4>
              <div v-for="link in analysisResult.analysis_json.acquisition_links" :key="link.url"
                   class="bg-gray-900/80 p-3 rounded-xl border border-gray-700 flex items-center justify-between">
                <div>
                  <p class="font-bold text-sm">{{ link.site }}</p>
                  <p class="text-xs text-green-400">{{ link.price }} • {{ link.status }}</p>
                </div>
                <a :href="link.url" target="_blank"
                   class="bg-indigo-600 hover:bg-indigo-500 text-xs font-bold px-3 py-1 rounded-lg transition">
                  Buy
                </a>
              </div>
            </div>
            <div v-else-if="analysisResult.confidence_score > 65" class="text-xs text-gray-500 italic text-center">
              No physical copies found at supported retailers.
            </div>
          </div>

          <!-- Empty View -->
          <div v-else class="flex-1 flex flex-col items-center justify-center text-gray-600 text-center px-4">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 mb-4 opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
            </svg>
            <p>Select a track from the dashboard to run deep-audio tagging or album audits.</p>
          </div>
        </section>
      </div>
    </main>

    <footer class="mt-12 text-gray-600 text-[10px] uppercase tracking-[0.2em] font-medium">
      Vinyl Recommender Alpha • Deep Analysis Layer Active
    </footer>
  </div>
</template>

<style>
body {
  margin: 0;
  font-family: 'Inter', ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  background-color: #111827;
  overflow-x: hidden;
}

::-webkit-scrollbar {
  width: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: #374151;
  border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover {
  background: #4b5563;
}
</style>