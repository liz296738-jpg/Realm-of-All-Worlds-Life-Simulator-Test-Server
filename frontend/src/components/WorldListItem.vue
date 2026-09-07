<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  world: { type: Object, required: true },
  save: { type: Object, default: null },
  cover: { type: String, default: null },
  mine: { type: Boolean, default: false },
  deleting: { type: Boolean, default: false },
})
const emit = defineEmits(['enter', 'continue', 'remove', 'preview'])

const initial = computed(() => (props.world?.name || '世').charAt(0))
const coverFailed = ref(false)
watch(() => props.cover, () => { coverFailed.value = false })

function mainAction() {
  if (props.save) emit('continue', props.save)
  else emit('enter')
}
</script>

<template>
  <div class="world-row-wrap">
    <div class="world-row">
      <button v-if="cover && !coverFailed" type="button" class="world-row-thumb world-cover world-cover-preview-button"
        :aria-label="`查看 ${world.name} 世界封面`" @click="emit('preview')">
        <img :src="cover" alt="" loading="lazy" decoding="async" @error="coverFailed = true" />
      </button>
      <span v-else class="world-row-thumb world-cover" aria-hidden="true">
        <span class="world-cover-placeholder">
          <span class="world-cover-initial">{{ initial }}</span>
        </span>
      </span>

      <button type="button" class="world-row-main-action" @click="mainAction"
        :aria-label="save ? `继续 ${world.name}` : `进入 ${world.name}`">
        <span class="world-row-main">
          <span class="world-row-title">{{ world.name }}</span>
          <span class="world-row-desc">{{ world.desc || (mine ? '由你上传小说生成的专属世界' : '') }}</span>
          <span v-if="save" class="world-row-meta">第 {{ save.turn }} 回合 · {{ save.name }}</span>
        </span>

        <span class="world-row-trail" aria-hidden="true">
          <span v-if="save" class="world-row-continue-chip">继续 →</span>
          <span v-else class="world-row-arrow">→</span>
        </span>
      </button>
    </div>

    <div v-if="save || mine" class="world-row-actions">
      <button v-if="save" type="button" class="world-row-act" @click="emit('enter')">新开始</button>
      <button v-if="mine" type="button" class="world-row-delete" :disabled="deleting"
        aria-label="删除世界" @click="emit('remove', world)">
        {{ deleting ? '删除中…' : '删除' }}
      </button>
    </div>
  </div>
</template>
