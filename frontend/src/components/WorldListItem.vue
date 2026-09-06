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

// 整行是一个真 <button>：无存档 → 进入新游戏；有存档 → 继续该存档
function open() {
  if (props.save) emit('continue', props.save)
  else emit('enter')
}
</script>

<template>
  <div class="world-row-wrap">
    <!-- 主行按钮：键盘 Enter/Space 由原生 button 处理 -->
    <button type="button" class="world-row" @click="open">
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

      <span v-if="!mine" class="world-row-arrow" aria-hidden="true">›</span>
    </button>

    <!-- 删除：外层兄弟按钮，避免按钮套按钮（Enter 不会误触进入世界） -->
    <button v-if="mine" type="button" class="world-row-delete" :disabled="deleting"
      aria-label="删除世界" @click="emit('remove', world)">
      {{ deleting ? '删除中…' : '删除' }}
    </button>
  </div>
</template>
