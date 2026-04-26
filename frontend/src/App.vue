<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'

const message = ref('Waiting for bridge...')
const response = ref('')
const userId = ref('')
const syncStatus = ref('Idle')
const trackCount = ref(0)
const syncedTracks = ref([])
const userProfile = ref(null)
const currentTab = ref('dashboard') // 'dashboard' or 'discovery'

// Album Analysis State
const activeAnalysis = ref(null)
const analysisResult = ref(null)
const discoveryResults = ref([])
const selectedDiscoveryAlbum = ref(null)

// CLAP Analysis State
const activeClap = ref(null)
const clapResult = ref(null)

// Manual Search Lab State
const manualSearchArtist = ref('')
const manualSearchAlbum = ref('')
const manualSearchResults = ref([])
const searchLoading = ref(false)
const showBrowser = ref(false)

let pollInterval = null
let analysisInterval = null
let clapInterval = null

// Watch showBrowser to update Python bridge
watch(showBrowser, (newVal) => {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.set_headless_mode(newVal)
  }
})

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
  let pollCount = 0
  analysisInterval = setInterval(async () => {
    pollCount++
    const res = await window.pywebview.api.get_album_analysis(albumId)

    if (res.status === 'success') {
      // Force a fresh object reference to ensure Vue detects deep changes
      analysisResult.value = { ...res.data }
      activeAnalysis.value = null

      const isComplete = res.data.analysis_json.is_complete

      // Stop polling if the backend explicitly marked the process as complete
      // or if we've exceeded the safety timeout (60 seconds / 30 polls)
      if (isComplete || pollCount >= 30) {
        console.log("Analysis cycle finished.")
        clearInterval(analysisInterval)
      } else {
        console.log(`Polling for marketplace links... (${pollCount}/30)`)
      }
    }
  }, 2000)
}

const triggerManualSearch = async () => {
  if (!manualSearchArtist.value || !manualSearchAlbum.value) return
  searchLoading.value = true
  manualSearchResults.value = []
  if (window.pywebview && window.pywebview.api) {
    try {
      const res = await window.pywebview.api.manual_marketplace_search(manualSearchArtist.value, manualSearchAlbum.value)
      manualSearchResults.value = res
    } catch (err) {
      console.error("Manual search failed", err)
    } finally {
      searchLoading.value = false
    }
  }
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

const fetchUserProfile = async () => {
  if (window.pywebview && window.pywebview.api) {
    const res = await window.pywebview.api.get_user_profile()
    if (res.status === 'success') {
      userProfile.value = res.data
    }
  }
}

const fetchDiscoveryResults = async () => {
  if (window.pywebview && window.pywebview.api) {
    discoveryResults.value = await window.pywebview.api.get_discovery_results()
  }
}

const startFlowDiscovery = async () => {
  if (window.pywebview && window.pywebview.api) {
    await window.pywebview.api.start_flow_discovery(userId.value)
  }
}

const startPolling = () => {
  if (pollInterval) clearInterval(pollInterval)
  pollInterval = setInterval(() => {
    updateStatus()
    fetchSyncedTracks()
    fetchUserProfile()
    fetchDiscoveryResults()
  }, 2000)
}

onMounted(() => {
  const interval = setInterval(async () => {
    if (window.pywebview && window.pywebview.api) {
      message.value = 'Bridge Connected'
      const defUser = await window.pywebview.api.get_default_user()
      if (defUser) userId.value = defUser

      // Start the regular update loop immediately on connect
      startPolling()

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

    <nav class="flex space-x-4 mb-8 bg-gray-800 p-2 rounded-2xl border border-gray-700">
      <button
        @click="currentTab = 'dashboard'"
        :class="currentTab === 'dashboard' ? 'bg-indigo-600 text-white' : 'text-gray-400 hover:text-white'"
        class="px-6 py-2 rounded-xl font-bold transition text-sm"
      >
        My Dashboard
      </button>
      <button
        @click="currentTab = 'discovery'"
        :class="currentTab === 'discovery' ? 'bg-indigo-600 text-white' : 'text-gray-400 hover:text-white'"
        class="px-6 py-2 rounded-xl font-bold transition text-sm"
      >
        Flow Discovery
      </button>
    </nav>

    <main v-if="currentTab === 'dashboard'" class="w-full max-w-6xl grid grid-cols-1 lg:grid-cols-3 gap-8">

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

        <!-- Marketplace Test Section -->
        <section class="bg-gray-800 p-6 rounded-2xl shadow-xl border border-gray-700">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-lg font-bold flex items-center">
              <span class="w-2 h-2 bg-orange-500 rounded-full mr-3"></span>
              Marketplace Lab
            </h2>
            <label class="flex items-center cursor-pointer group">
              <span class="text-[9px] uppercase font-bold text-gray-500 mr-2 group-hover:text-orange-400 transition">Show Browser</span>
              <div class="relative">
                <input type="checkbox" v-model="showBrowser" class="sr-only" />
                <div class="w-8 h-4 bg-gray-900 rounded-full border border-gray-700 shadow-inner"></div>
                <div class="dot absolute w-2 h-2 bg-gray-500 rounded-full left-1 top-1 transition-all duration-300" :class="showBrowser ? 'translate-x-4 bg-orange-500' : ''"></div>
              </div>
            </label>
          </div>

          <p class="text-[10px] text-gray-400 mb-4 uppercase font-bold tracking-wider">Test Search Logic Independently</p>
          <div class="space-y-3 mb-4">
            <input
              v-model="manualSearchArtist"
              placeholder="Artist Name"
              class="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-2 text-xs text-orange-200 focus:outline-none focus:border-orange-500 transition"
            />
            <input
              v-model="manualSearchAlbum"
              placeholder="Album Title"
              class="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-2 text-xs text-orange-200 focus:outline-none focus:border-orange-500 transition"
            />
          </div>
          <button
            @click="triggerManualSearch"
            :disabled="searchLoading"
            class="w-full bg-orange-600 hover:bg-orange-500 disabled:opacity-50 text-white font-bold py-2 rounded-xl transition duration-300 text-sm"
          >
            {{ searchLoading ? 'Searching Google...' : 'Search Dutch Shops' }}
          </button>

          <div v-if="manualSearchResults.length" class="mt-4 space-y-2 max-h-[300px] overflow-y-auto">
            <div v-for="item in manualSearchResults" :key="item.link" class="bg-gray-900/50 p-3 rounded-xl border border-gray-700 text-[10px]">
              <div class="flex justify-between items-start mb-1">
                <span class="font-bold text-orange-400 uppercase tracking-tighter">{{ item.store }}</span>
                <span class="text-green-400 font-mono">{{ item.price }}</span>
              </div>
              <p class="text-gray-300 mb-2 font-medium">{{ item.product }}</p>
              <a :href="item.link" target="_blank" class="text-indigo-400 hover:underline block truncate">{{ item.link }}</a>
            </div>
          </div>
        </section>

        <section v-if="userProfile && Object.keys(userProfile).length > 0" class="bg-gray-800 p-6 rounded-2xl shadow-xl border border-gray-700">
          <h2 class="text-lg font-bold mb-4 flex items-center">
            <span class="w-2 h-2 bg-pink-500 rounded-full mr-3"></span>
            Sonic DNA Profile
          </h2>
          <div class="space-y-4">
            <div v-for="(labels, layer) in userProfile" :key="layer" class="bg-gray-900/50 p-3 rounded-xl border border-gray-700">
              <span class="text-[10px] uppercase font-bold text-gray-500 block mb-2">{{ layer.split(':')[1]?.trim() || layer }}</span>
              <div class="flex flex-col gap-1">
                <div v-for="(label, idx) in labels" :key="label" class="flex items-center text-[11px]">
                  <span class="text-pink-400 font-mono w-4">{{ idx + 1 }}.</span>
                  <span class="text-gray-300 truncate">{{ label }}</span>
                </div>
              </div>
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

      <!-- Center Column: Loved Albums Dashboard -->
      <div class="lg:col-span-1">
        <section class="bg-gray-800 rounded-2xl shadow-xl border border-gray-700 overflow-hidden flex flex-col h-[600px]">
          <div class="p-6 border-b border-gray-700">
            <h2 class="text-lg font-bold">Your Loved Albums</h2>
            <p class="text-xs text-gray-400">Qualified albums (3+ songs) from your favorites.</p>
          </div>
          <div class="flex-1 overflow-y-auto p-4 space-y-2">
            <div v-for="album in syncedTracks" :key="album.album_id"
                 class="group bg-gray-900/40 hover:bg-gray-700 p-3 rounded-xl border border-gray-700/50 transition cursor-pointer flex items-center"
                 @click="analyzeAlbum(album.sample_track_id)">
              <img :src="album.cover" class="w-10 h-10 rounded-lg mr-3 shadow-lg group-hover:scale-105 transition" v-if="album.cover" />
              <div class="flex-1 min-w-0">
                <p class="font-bold text-sm truncate group-hover:text-indigo-400 transition">{{ album.title }}</p>
                <p class="text-[10px] text-gray-500 truncate">{{ album.artist }}</p>
              </div>

              <!-- CLAP AI Tagging Test Button (Uses sample track) -->
              <button @click.stop="testClap(album.sample_track_id)" title="Analyze Sonic Profile" class="ml-2 bg-pink-600/20 group-hover:bg-pink-600 text-pink-400 group-hover:text-white p-2 rounded-lg transition">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </button>

              <button class="ml-2 bg-indigo-600/20 group-hover:bg-indigo-600 text-indigo-400 group-hover:text-white p-2 rounded-lg transition" title="Audit Full Album Compatibility">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>
            <div v-if="syncedTracks.length === 0" class="text-center py-12 text-gray-500 italic text-sm px-4">
              Sync loved tracks to find eligible albums. Singles and EPs (&lt;3 songs) are used for DNA only.
            </div>
          </div>
        </section>
      </div>

      <div class="lg:col-span-1">
    <section class="bg-gray-800 p-6 rounded-2xl shadow-xl border border-gray-700 min-h-[600px] flex flex-col overflow-y-auto">

      <!-- CLAP Loading State -->
      <div v-if="activeClap" class="flex-1 flex flex-col items-center justify-center space-y-4">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-pink-500"></div>
        <p class="text-pink-400 font-bold animate-pulse">{{ activeClap.status }}</p>
        <p class="text-[10px] text-gray-500 max-w-[200px] text-center">
          First run will download the model to your device (this may take a few minutes).
        </p>
      </div>

      <!-- CLAP Result -->
      <div v-else-if="clapResult" class="space-y-4">

        <div class="text-center mb-4">
          <h2 class="text-xl font-bold mt-4 text-pink-400 flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            Sonic Signature
          </h2>
          <p class="text-[10px] text-gray-500 uppercase tracking-widest mt-1">Top Track Traits</p>
        </div>

        <div
          v-for="(pairs, layerName) in clapResult"
          :key="layerName"
          class="bg-gray-900/50 p-4 rounded-xl border border-gray-700"
        >
          <h4 class="text-[9px] uppercase font-black text-gray-500 mb-3 tracking-[0.2em]">
            {{ layerName.split(':')[1]?.trim() || layerName }}
          </h4>

          <div class="space-y-3">
            <div v-for="([label, prob], idx) in pairs" :key="label">

              <div class="flex items-center justify-between mb-1">
                <div class="flex items-center">
                  <span class="text-[9px] font-mono mr-2" :class="idx === 0 ? 'text-pink-400' : 'text-gray-600'">
                    #{{ idx + 1 }}
                  </span>
                  <span class="text-[11px] text-gray-300 font-medium truncate max-w-[150px]" :title="label">
                    {{ label }}
                  </span>
                </div>
                <span class="text-[10px] font-mono text-gray-500">
                  {{ Math.round(prob * 100) }}%
                </span>
              </div>

              <div class="w-full bg-gray-800 h-1 rounded-full overflow-hidden">
                <div
                  class="bg-pink-500 h-full rounded-full transition-all duration-1000"
                  :style="{ width: (prob * 100) + '%', opacity: 1 - (idx * 0.25) }"
                ></div>
              </div>

            </div>
          </div>
        </div>

      </div>

      <!-- Album Analysis Loading State -->
      <div v-else-if="activeAnalysis" class="flex-1 flex flex-col items-center justify-center space-y-4">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500"></div>
        <p class="text-indigo-400 font-bold animate-pulse">{{ activeAnalysis.status }}</p>
        <p class="text-[10px] text-gray-500 max-w-[200px] text-center">
          Analyzing every track on the album for sonic compatibility...
        </p>
      </div>

      <!-- Album Analysis Verdict View -->
      <div
        v-else-if="analysisResult"
        class="space-y-6"
        :key="analysisResult.album_id + '_' + analysisResult.analysis_json.is_complete + '_' + (analysisResult.analysis_json.acquisition_links?.length || 0)"
      >

        <h2 class="text-lg font-bold mb-2 flex items-center">
          <span class="w-2 h-2 bg-indigo-500 rounded-full mr-3"></span>
          The Verdict
        </h2>

        <div class="text-center">
          <div class="relative inline-block mb-4">
            <img
              :src="analysisResult.cover_url"
              class="w-48 h-48 rounded-2xl shadow-2xl mx-auto border-4 border-gray-700"
              v-if="analysisResult.cover_url"
            />

            <div
              class="absolute -bottom-4 -right-4 inline-flex items-center justify-center p-4 rounded-full border-4 bg-gray-800 shadow-xl"
              :class="analysisResult.confidence_score > 70 ? 'border-green-500' : 'border-yellow-500'"
            >
              <span class="text-2xl font-black">{{ analysisResult.confidence_score }}%</span>
            </div>
          </div>

          <h3 class="text-xl font-bold mt-4">{{ analysisResult.title }}</h3>
          <p class="text-sm text-gray-400">{{ analysisResult.artist }}</p>
        </div>

        <div class="bg-gray-900/50 p-4 rounded-xl border border-gray-700">
          <h4 class="text-[10px] uppercase font-bold text-gray-500 mb-2 tracking-widest">
            Sonic Breakdown
          </h4>
          <p class="text-sm italic leading-relaxed text-gray-300">
            "{{ analysisResult.analysis_json.sonic_breakdown }}"
          </p>
        </div>

        <div v-if="analysisResult.analysis_json.filler_tracks?.length" class="space-y-2">
          <h4 class="text-[10px] uppercase font-bold text-red-400 tracking-widest">
            Risk Factor: Possible Skips
          </h4>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="track in analysisResult.analysis_json.filler_tracks"
              :key="track"
              class="px-2 py-1 bg-red-900/20 text-red-400 text-[10px] rounded border border-red-900/50"
            >
              {{ track }}
            </span>
          </div>
        </div>

        <!-- Render Acquisition Links in Verdict -->
        <div v-if="analysisResult.confidence_score > 60" class="space-y-3">
          <h4 class="text-[10px] uppercase font-bold text-green-400 tracking-widest flex justify-between items-center">
            Marketplace Matches
            <span v-if="!analysisResult.analysis_json.is_complete" class="animate-pulse text-orange-400 normal-case font-medium">Searching Dutch shops...</span>
          </h4>

          <div v-if="analysisResult.analysis_json.acquisition_links?.length" class="space-y-2">
            <div v-for="link in analysisResult.analysis_json.acquisition_links" :key="link.link" class="bg-gray-900/50 p-3 rounded-xl border border-gray-700 text-[10px]">
              <div class="flex justify-between items-start mb-1">
                <span class="font-bold text-green-400 uppercase">{{ link.store }}</span>
                <span class="font-mono">{{ link.price }}</span>
              </div>
              <p class="text-gray-400 truncate mb-1">{{ link.product }}</p>
              <a :href="link.link" target="_blank" class="text-indigo-400 hover:underline truncate block">{{ link.link }}</a>
            </div>
          </div>

          <!-- Empty State: Show only when search is finished and list is empty -->
          <div v-else-if="analysisResult.analysis_json.is_complete" class="bg-gray-900/50 p-6 rounded-xl border border-dashed border-gray-700 text-center">
            <p class="text-[10px] text-gray-500 uppercase font-bold tracking-wider mb-1">No direct matches found</p>
            <p class="text-[9px] text-gray-600 italic">This record might be out of stock at tracked retailers.</p>
          </div>
        </div>

      </div>

      <!-- Empty View -->
      <div v-else class="flex-1 flex flex-col items-center justify-center text-gray-600 text-center px-4">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 mb-4 opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
        </svg>
        <p>Select a track from the dashboard to run deep-audio tagging or album audits.</p>
      </div>

    </section>
  </div>
    </main>

    <main v-else class="w-full max-w-6xl relative">
      <div class="flex justify-between items-center mb-8">
        <div>
          <h2 class="text-2xl font-bold">Sonic Discovery</h2>
          <p class="text-gray-400 text-sm">Albums found in your Flow with >60% compatibility.</p>
        </div>
        <button
          @click="startFlowDiscovery"
          class="bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-3 px-8 rounded-2xl transition shadow-lg shadow-indigo-900/20"
        >
          Discover New Flow
        </button>
      </div>

      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        <div
          v-for="album in discoveryResults"
          :key="album.album_id"
          @click="selectedDiscoveryAlbum = album"
          class="bg-gray-800 rounded-2xl border border-gray-700 overflow-hidden cursor-pointer hover:border-indigo-500 transition-all group"
        >
          <div class="relative">
            <img :src="album.cover_url" class="w-full aspect-square object-cover" />
            <div class="absolute top-2 right-2 bg-gray-900/80 backdrop-blur px-2 py-1 rounded-lg border border-gray-700 text-xs font-black text-indigo-400">
              {{ album.confidence_score }}%
            </div>
          </div>
          <div class="p-4">
            <p class="font-bold text-sm truncate group-hover:text-indigo-400 transition">{{ album.title }}</p>
            <p class="text-[10px] text-gray-500 truncate uppercase tracking-tighter">{{ album.artist }}</p>
          </div>
        </div>
      </div>

      <div v-if="discoveryResults.length === 0" class="text-center py-32 bg-gray-800/50 rounded-3xl border border-dashed border-gray-700">
        <p class="text-gray-500">No high-match albums found yet. Click "Discover New Flow" to start scanning.</p>
      </div>

      <!-- Side Panel -->
      <div
        v-if="selectedDiscoveryAlbum"
        class="fixed inset-y-0 right-0 w-[400px] bg-gray-900 border-l border-gray-700 shadow-2xl z-50 transform transition-transform p-8 overflow-y-auto"
      >
        <button @click="selectedDiscoveryAlbum = null" class="absolute top-6 left-6 text-gray-500 hover:text-white">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <div class="mt-8 space-y-6">
          <img :src="selectedDiscoveryAlbum.cover_url" class="w-full rounded-2xl shadow-xl" />

          <div>
            <h3 class="text-2xl font-bold">{{ selectedDiscoveryAlbum.title }}</h3>
            <p class="text-indigo-400 font-medium">{{ selectedDiscoveryAlbum.artist }}</p>
          </div>

          <div class="flex items-center space-x-4">
            <div class="bg-gray-800 p-4 rounded-2xl flex-1 text-center border border-gray-700">
              <span class="block text-[10px] uppercase text-gray-500 font-bold mb-1">Match Score</span>
              <span class="text-3xl font-black">{{ selectedDiscoveryAlbum.confidence_score }}%</span>
            </div>
          </div>

          <div class="bg-gray-800 p-6 rounded-2xl border border-gray-700">
            <h4 class="text-[10px] uppercase font-bold text-indigo-400 mb-3 tracking-widest">Sonic Breakdown</h4>
            <p class="text-sm italic leading-relaxed text-gray-300">
              "{{ selectedDiscoveryAlbum.analysis_json.sonic_breakdown }}"
            </p>
          </div>

          <div v-if="selectedDiscoveryAlbum.analysis_json.acquisition_links?.length" class="space-y-3">
             <h4 class="text-[10px] uppercase font-bold text-green-400 tracking-widest">Purchase Links</h4>
             <div v-for="link in selectedDiscoveryAlbum.analysis_json.acquisition_links" :key="link.link" class="bg-gray-800 p-3 rounded-xl border border-gray-700 text-xs">
                <div class="flex justify-between mb-1">
                  <span class="font-bold text-green-400">{{ link.store }}</span>
                  <span class="font-mono">{{ link.price }}</span>
                </div>
                <a :href="link.link" target="_blank" class="text-indigo-400 hover:underline truncate block">{{ link.link }}</a>
             </div>
          </div>
        </div>
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