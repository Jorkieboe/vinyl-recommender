<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import DashboardTab from './components/DashboardTab.vue'
import DiscoveryTab from './components/DiscoveryTab.vue'
import AgentTab from './components/AgentTab.vue'
import AlbumSidePanel from './components/AlbumSidePanel.vue'

const message = ref('Waiting for bridge...')
const response = ref('')
const userId = ref('')
const syncStatus = ref('Idle')
const trackCount = ref(0)
const syncedTracks = ref([])
const userProfile = ref(null)
const currentTab = ref('dashboard')

// Album Analysis State
const activeAnalysis = ref(null)
const analysisResult = ref(null)
const discoveryResults = ref([])
const recommendedAlbums = ref([])
const selectedDiscoveryAlbum = ref(null)

// CLAP Analysis State
const activeClap = ref(null)
const clapResult = ref(null)

// Agent Lab State
const agentInput = ref('')
const agentResponse = ref(null)
const agentLoading = ref(false)

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

const callAgent = async () => {
  if (!agentInput.value) return
  agentLoading.value = true
  agentResponse.value = null
  if (window.pywebview && window.pywebview.api) {
    try {
      const res = await window.pywebview.api.call_agent(agentInput.value)
      if (res.status === 'success') {
        agentResponse.value = res.data
      } else {
        agentResponse.value = { message: "Error: " + res.message }
      }
    } catch (err) {
      console.error("Agent call failed", err)
      agentResponse.value = { message: "System failure." }
    } finally {
      agentLoading.value = false
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

const fetchRecommendedAlbums = async () => {
  if (window.pywebview && window.pywebview.api) {
    recommendedAlbums.value = await window.pywebview.api.get_recommended_albums()
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
    fetchRecommendedAlbums()
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

watch(selectedDiscoveryAlbum, (newalbum, oldalbum)=>{
  console.log(newalbum)
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
      <button
        @click="currentTab = 'agent'"
        :class="currentTab === 'agent' ? 'bg-indigo-600 text-white' : 'text-gray-400 hover:text-white'"
        class="px-6 py-2 rounded-xl font-bold transition text-sm"
      >
        Agent Search
      </button>
    </nav>

    <!-- Dashboard Tab Component -->
    <DashboardTab
      v-if="currentTab === 'dashboard'"
      v-model:userId="userId"
      v-model:showBrowser="showBrowser"
      v-model:manualSearchArtist="manualSearchArtist"
      v-model:manualSearchAlbum="manualSearchAlbum"
      :syncStatus="syncStatus"
      :trackCount="trackCount"
      :syncedTracks="syncedTracks"
      :userProfile="userProfile"
      :systemMessage="message"
      :systemResponse="response"
      :manualSearchResults="manualSearchResults"
      :searchLoading="searchLoading"
      :activeClap="activeClap"
      :clapResult="clapResult"
      :activeAnalysis="activeAnalysis"
      :analysisResult="analysisResult"
      @startSync="startSync"
      @triggerManualSearch="triggerManualSearch"
      @callEcho="callEcho"
      @analyzeAlbum="analyzeAlbum"
      @testClap="testClap"
    />

    <!-- Discovery Tab Component -->
    <DiscoveryTab
      v-else-if="currentTab === 'discovery'"
      :discoveryResults="discoveryResults"
      @startFlowDiscovery="startFlowDiscovery"
      @selectAlbum="selectedDiscoveryAlbum = $event"
    />

    <!-- Agent Tab Component -->
    <AgentTab
      v-else-if="currentTab === 'agent'"
      v-model:agentInput="agentInput"
      :agentResponse="agentResponse"
      :agentLoading="agentLoading"
      :recommendedAlbums="recommendedAlbums"
      @callAgent="callAgent"
      @selectAlbum="selectedDiscoveryAlbum = $event"
    />

    <!-- Shared Reusable Side Panel -->
    <AlbumSidePanel
      v-if="selectedDiscoveryAlbum"
      :album="selectedDiscoveryAlbum"
      @close="selectedDiscoveryAlbum = null"
    />

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