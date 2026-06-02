<script setup>
defineProps({
  discoveryResults: {
    type: Array,
    required: true
  }
})

defineEmits(['startFlowDiscovery', 'selectAlbum'])
</script>

<template>
  <div class="w-full max-w-6xl relative">
    <div class="flex justify-between items-center mb-8">
      <div>
        <h2 class="text-2xl font-bold">Sonic Discovery</h2>
        <p class="text-gray-400 text-sm">Albums found in your Flow with >60% compatibility.</p>
      </div>
      <button
        @click="$emit('startFlowDiscovery')"
        class="bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-3 px-8 rounded-2xl transition shadow-lg shadow-indigo-900/20"
      >
        Discover New Flow
      </button>
    </div>

    <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
      <div
        v-for="album in discoveryResults"
        :key="album.album_id"
        @click="$emit('selectAlbum', album)"
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
  </div>
</template>