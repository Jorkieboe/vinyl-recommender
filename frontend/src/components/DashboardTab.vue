<script setup>
import { computed } from 'vue'

const props = defineProps({
  userId: String,
  syncStatus: String,
  trackCount: Number,
  syncedTracks: Array,
  userProfile: Object,
  systemMessage: String,
  systemResponse: String,
  showBrowser: Boolean,
  manualSearchArtist: String,
  manualSearchAlbum: String,
  manualSearchResults: Array,
  searchLoading: Boolean,
  activeClap: Object,
  clapResult: Object,
  activeAnalysis: Object,
  analysisResult: Object
})

const emit = defineEmits([
  'update:userId',
  'update:showBrowser',
  'update:manualSearchArtist',
  'update:manualSearchAlbum',
  'startSync',
  'triggerManualSearch',
  'callEcho',
  'analyzeAlbum',
  'testClap'
])

const localUserId = computed({
  get: () => props.userId,
  set: (val) => emit('update:userId', val)
})

const localShowBrowser = computed({
  get: () => props.showBrowser,
  set: (val) => emit('update:showBrowser', val)
})

const localManualSearchArtist = computed({
  get: () => props.manualSearchArtist,
  set: (val) => emit('update:manualSearchArtist', val)
})

const localManualSearchAlbum = computed({
  get: () => props.manualSearchAlbum,
  set: (val) => emit('update:manualSearchAlbum', val)
})
</script>

<template>
  <div class="w-full max-w-6xl grid grid-cols-1 lg:grid-cols-3 gap-8">
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
            v-model="localUserId"
            type="text"
            class="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-2 text-indigo-300 focus:outline-none focus:border-indigo-500 transition"
          />
        </div>
        <button
          @click="$emit('startSync')"
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
              <input type="checkbox" v-model="localShowBrowser" class="sr-only" />
              <div class="w-8 h-4 bg-gray-900 rounded-full border border-gray-700 shadow-inner"></div>
              <div class="dot absolute w-2 h-2 bg-gray-500 rounded-full left-1 top-1 transition-all duration-300" :class="localShowBrowser ? 'translate-x-4 bg-orange-500' : ''"></div>
            </div>
          </label>
        </div>

        <p class="text-[10px] text-gray-400 mb-4 uppercase font-bold tracking-wider">Test Search Logic Independently</p>
        <div class="space-y-3 mb-4">
          <input
            v-model="localManualSearchArtist"
            placeholder="Artist Name"
            class="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-2 text-xs text-orange-200 focus:outline-none focus:border-orange-500 transition"
          />
          <input
            v-model="localManualSearchAlbum"
            placeholder="Album Title"
            class="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-2 text-xs text-orange-200 focus:outline-none focus:border-orange-500 transition"
          />
        </div>
        <button
          @click="$emit('triggerManualSearch')"
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
            :class="systemMessage === 'Bridge Connected' ? 'bg-green-900/30 text-green-400' : 'bg-yellow-900/30 text-yellow-400'"
          >
            {{ systemMessage }}
          </div>
          <button @click="$emit('callEcho')" class="text-xs text-indigo-400 hover:underline">Test Bridge</button>
        </div>
        <div v-if="systemResponse" class="bg-gray-900/50 p-3 rounded-xl border border-gray-700 font-mono text-[10px] text-indigo-300 break-all">
          {{ systemResponse }}
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
               @click="$emit('analyzeAlbum', album.sample_track_id)">
            <img :src="album.cover" class="w-10 h-10 rounded-lg mr-3 shadow-lg group-hover:scale-105 transition" v-if="album.cover" />
            <div class="flex-1 min-w-0">
              <p class="font-bold text-sm truncate group-hover:text-indigo-400 transition">{{ album.title }}</p>
              <p class="text-[10px] text-gray-500 truncate">{{ album.artist }}</p>
            </div>

            <!-- CLAP AI Tagging Test Button -->
            <button @click.stop="$emit('testClap', album.sample_track_id)" title="Analyze Sonic Profile" class="ml-2 bg-pink-600/20 group-hover:bg-pink-600 text-pink-400 group-hover:text-white p-2 rounded-lg transition">
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

    <!-- Right Column: Results Section -->
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

          <!-- Render Acquisition Links -->
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
  </div>
</template>