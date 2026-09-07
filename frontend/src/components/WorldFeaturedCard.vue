<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  world: { type: Object, required: true },
  save: { type: Object, default: null },
  cover: { type: String, default: null },
})
const emit = defineEmits(['enter', 'continue'])

const initial = computed(() => (props.world?.name || '界').charAt(0))
const coverFailed = ref(false)
watch(() => props.cover, () => { coverFailed.value = false })
</script>

<template>
  <article class="world-featured">
    <div class="world-cover world-cover--featured">
      <img v-if="cover && !coverFailed" :src="cover" :alt="world.name" loading="eager"
        fetchpriority="high" @error="coverFailed = true" />
      <div v-else class="world-cover-placeholder" aria-hidden="true">
        <span class="world-cover-initial">{{ initial }}</span>
        <span class="world-cover-name">{{ world.name }}</span>
      </div>
    </div>

    <div class="world-featured-body">
      <span class="app-chip">创作者世界</span>
      <h2 class="world-featured-title">{{ world.name }}</h2>
      <p class="world-featured-desc">{{ world.desc }}</p>

      <div class="world-featured-actions">
        <button v-if="save" type="button" class="app-button app-button-primary" @click="emit('continue', save)">
          继续冒险
        </button>
        <button v-else type="button" class="app-button app-button-primary" @click="emit('enter')">
          进入世界
        </button>
        <button v-if="save" type="button" class="app-button app-button-ghost" @click="emit('enter')">
          重新开始
        </button>
      </div>

      <p v-if="save" class="world-featured-save-meta">
        第 {{ save.turn }} 回合 · {{ save.name }}
      </p>
    </div>
  </article>
</template>
