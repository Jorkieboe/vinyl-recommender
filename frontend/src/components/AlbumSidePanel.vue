<script setup>
defineProps({
  album: {
    type: Object,
    required: true
  }
})

defineEmits(['close'])

// watch(props.album, (newalbum, oldalbum)=>{
//   console.log(newalbum)
// })
</script>

<template>
  <div class="fixed inset-y-0 right-0 w-[400px] bg-gray-900 border-l border-gray-700 shadow-2xl z-50 transform transition-transform p-8 overflow-y-auto">
    <button @click="$emit('close')" class="absolute top-6 left-6 text-gray-500 hover:text-white">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>

    <div class="mt-8 space-y-6">
      <img :src="album.cover_url" class="w-full rounded-2xl shadow-xl" v-if="album.cover_url" />

      <div>
        <h3 class="text-2xl font-bold">{{ album.title }}</h3>
        <p class="text-indigo-400 font-medium">{{ album.artist }}</p>
      </div>

      <div class="flex items-center space-x-4">
        <div class="bg-gray-800 p-4 rounded-2xl flex-1 text-center border border-gray-700">
          <span class="block text-[10px] uppercase text-gray-500 font-bold mb-1">Match Score</span>
          <span class="text-3xl font-black">{{ album.confidence_score }}%</span>
        </div>
      </div>

      <div class="bg-gray-800 p-6 rounded-2xl border border-gray-700">
        <h4 class="text-[10px] uppercase font-bold text-indigo-400 mb-3 tracking-widest">Sonic Breakdown</h4>
        <p class="text-sm italic leading-relaxed text-gray-300" :class="{ 'mb-4': album.analysis_json?.filler_tracks?.length }">
          "{{ album.analysis_json?.sonic_breakdown || 'No detailed analysis provided.' }}"
        </p>

        <div v-if="album.analysis_json?.filler_tracks?.length" class="space-y-2 pt-3 border-t border-gray-700/50">
          <h5 class="text-[10px] uppercase font-bold text-red-400 tracking-widest">
            Risk Factor: Possible Skips
          </h5>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="track in album.analysis_json.filler_tracks"
              :key="track"
              class="px-2 py-1 bg-red-900/20 text-red-400 text-[10px] rounded border border-red-900/50"
            >
              {{ track }}
            </span>
          </div>
        </div>
      </div>

      <div v-if="album.analysis_json?.acquisition_links?.length" class="space-y-3">
         <h4 class="text-[10px] uppercase font-bold text-green-400 tracking-widest">Purchase Links</h4>
         <div v-for="link in album.analysis_json.acquisition_links" :key="link.link" class="bg-gray-800 p-3 rounded-xl border border-gray-700 text-xs">
            <div class="flex justify-between mb-1">
              <span class="font-bold text-green-400">{{ link.store }}</span>
              <span class="font-mono">{{ link.price }}</span>
            </div>
            <a :href="link.link" target="_blank" class="text-indigo-400 hover:underline truncate block">{{ link.link }}</a>
         </div>
      </div>
    </div>
  </div>
</template>