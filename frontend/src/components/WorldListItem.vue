<script setup>
import { computed } from 'vue'

const props = defineProps({
  world: { type: Object, required: true },
  save: { type: Object, default: null },
  cover: { type: String, default: null },
  mine: { type: Boolean, default: false },
  deleting: { type: Boolean, default: false },
})
const emit = defineEmits(['enter', 'continue', 'remove'])

const initial = computed(() => (props.world?.name || '界').charAt(0))

// 主行按钮：无存档 → 进入世界；有存档 → 继续该存档。
// “新开始 / 删除”作为独立兄弟按钮，与主动作不互斥。
function mainAction() {
  if (props.save) emit('continue', props.save)
  else emit('enter')
}
</script>

<template>
  <div class="world-row-wrap">
    <!-- 主行：整个内容区是一个真 <button>（键盘 Enter/Space 原生触发） -->
    <button type="button" class="world-row" @click="mainAction">
      <span class="world-row-thumb world-cover" aria-hidden="true">
        <img v-if="cover" :src="cover" alt="" loading="lazy" />
        <span v-else class="world-cover-placeholder">
          <span class="world-cover-initial">{{ initial }}</span>
        </span>
      </span>

      <span class="world-row-main">
        <span class="world-row-title">{{ world.name }}</span>
        <span class="world-row-desc">{{ world.desc || (mine ? '由你上传小说生成的专属世界' : '') }}</span>
        <span v-if="save" class="world-row-meta">第 {{ save.turn }} 回合 · {{ save.name }}</span>
      </span>

      <span class="world-row-trail" aria-hidden="true">
        <span v-if="save" class="world-row-continue-chip">继续 ›</span>
        <span v-else class="world-row-arrow">›</span>
      </span>
    </button>

    <!-- 次级动作：与主按钮同级，避免按钮套按钮；删除点击不会进入/继续 -->
    <div v-if="save || mine" class="world-row-actions">
      <button v-if="save" type="button" class="world-row-act" @click="emit('enter')">新开始</button>
      <button v-if="mine" type="button" class="world-row-delete" :disabled="deleting"
        aria-label="删除世界" @click="emit('remove', world)">
        {{ deleting ? '删除中…' : '删除' }}
      </button>
    </div>
  </div>
</template>
