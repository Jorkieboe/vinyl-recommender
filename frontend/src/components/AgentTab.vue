<script setup>
import { computed } from 'vue'

const props = defineProps({
  agentInput: String,
  agentResponse: Object,
  agentLoading: Boolean,
  recommendedAlbums: Array
})

const emit = defineEmits(['update:agentInput', 'callAgent', 'selectAlbum'])

const localAgentInput = computed({
  get: () => props.agentInput,
  set: (val) => emit('update:agentInput', val)
})
</script>

<template>
  <div class="w-full max-w-6xl relative">
    <div class="mb-8">
      <h2 class="text-2xl font-bold">Agent Search</h2>
      <p class="text-gray-400 text-sm">Tell the AI what you're looking for and let it explore your taste profile.</p>
    </div>

    <div class="bg-gray-800 p-6 rounded-2xl shadow-xl border border-gray-700 mb-8">
      <div class="flex space-x-4">
        <input
          v-model="localAgentInput"
          @keyup.enter="$emit('callAgent')"
          placeholder="E.g., I want something energetic but similar to my favorite rock albums..."
          class="flex-1 bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-indigo-500 transition"
        />
        <button
          @click="$emit('callAgent')"
          :disabled="agentLoading"
          class="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-bold py-3 px-8 rounded-xl transition shadow-lg shadow-indigo-900/20"
        >
          {{ agentLoading ? 'Thinking...' : 'Search' }}
        </button>
      </div>

      <div v-if="agentResponse" class="mt-4 bg-gray-900/50 p-4 rounded-xl border border-gray-700">
        <span class="text-[10px] uppercase font-bold text-indigo-400 block mb-2 tracking-wider">Agent Response</span>
        <p class="text-sm text-gray-300 leading-relaxed whitespace-pre-line" v-if="agentResponse.message?.sonic_breakdown">
          {{ agentResponse.message.sonic_breakdown }}
        </p>
        <p class="text-sm text-gray-300 leading-relaxed whitespace-pre-line" v-else>
          {{ agentResponse.message }}
        </p>
      </div>
    </div>

    <div>
      <h3 class="text-xl font-bold mb-4 flex items-center">
        <span class="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
        Recommended by Agent
      </h3>
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        <div
          v-for="album in recommendedAlbums"
          :key="album.album_id"
          @click="$emit('selectAlbum', album)"
          class="bg-gray-800 rounded-2xl border border-gray-700 overflow-hidden cursor-pointer hover:border-green-500 transition-all group"
        >
          <div class="relative">
            <img :src="album.cover_url" class="w-full aspect-square object-cover" />
            <div class="absolute top-2 right-2 bg-gray-900/80 backdrop-blur px-2 py-1 rounded-lg border border-gray-700 text-xs font-black text-green-400">
              {{ album.confidence_score }}%
            </div>
          </div>
          <div class="p-4">
            <p class="font-bold text-sm truncate group-hover:text-green-400 transition">{{ album.title }}</p>
            <p class="text-[10px] text-gray-500 truncate uppercase tracking-tighter">{{ album.artist }}</p>
          </div>
        </div>
      </div>

      <div v-if="recommendedAlbums.length === 0" class="text-center py-20 bg-gray-800/50 rounded-3xl border border-dashed border-gray-700">
        <p class="text-gray-500">No agent recommendations yet. Send a query to get started!</p>
      </div>
    </div>
  </div>
</template>