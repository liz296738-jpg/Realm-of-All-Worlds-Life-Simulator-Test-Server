<script setup>
import { ref, watch } from 'vue'
import { game } from '../store'

const emit = defineEmits(['choose', 'undo'])
const freeInput = ref('')
const open = ref(false)  // 选项栏是否展开

// 新回合开始（提交行动/流式生成）时自动收回选项栏，避免旧选项一直占位
watch(() => game.streaming, (v) => { if (v) open.value = false })

// 新选项抵达（包括读档恢复）时默认展开，避免玩家还要多点一次才能行动。
watch(() => [game.turnDone, game.options.length], ([done, count]) => {
  if (done && count) open.value = true
}, { immediate: true })

function onFreeSubmit() {
  if (!game.turnDone) return
  const text = freeInput.value.trim()
  if (!text) return
  emit('choose', text)
  freeInput.value = ''
}
</script>

<template>
  <section class="game-action-area" aria-label="行动选择">
    <div class="game-action-inner">
      <div v-if="game.options.length && game.turnDone" class="choice-heading">
        <p>接下来，你准备怎么做？</p>
        <button type="button" @click="open = !open" :aria-expanded="open">{{ open ? '收起选择' : '展开选择' }}</button>
      </div>

      <div v-if="open && game.options.length && game.turnDone" class="choice-list">
        <button v-for="opt in game.options" :key="opt.label" type="button" @click="emit('choose', opt.label)"
          class="choice-row" :class="{ 'choice-row-recommended': opt.recommended }">
          <span class="choice-label">{{ opt.label }}</span>
          <span class="choice-text">{{ opt.text }}</span>
          <span v-if="opt.recommended" class="choice-recommended">推荐</span>
        </button>
        <button v-if="game.canUndo" @click="emit('undo')" type="button" class="choice-undo"
          title="撤销上一次选择，回到上一回合的选项">
          撤销上一次选择
        </button>
      </div>

      <form @submit.prevent="onFreeSubmit" class="game-free-input">
        <input v-model="freeInput" :placeholder="game.turnDone ? '你准备怎么做？' : '世界正在书写…'"
          :disabled="!game.turnDone" class="app-input" />
        <button type="submit" :disabled="!game.turnDone || !freeInput.trim()" class="game-send-button" aria-label="提交行动">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M12 19V5m-5 5 5-5 5 5"/></svg>
        </button>
      </form>
    </div>
  </section>
</template>
