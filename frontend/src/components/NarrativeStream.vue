<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import MarkdownIt from 'markdown-it'
import { game } from '../store'
import { stripArtifacts, stripOptionsBlock } from '../md'

const md = new MarkdownIt({ breaks: true, linkify: false })

const scroller = ref(null)
const display = ref('')        // 流式期间的临时 raw 文本
const showStreaming = computed(() => game.streaming || !game.turnDone)
// 当前回合完成后的 markdown 渲染。用 computed 而非 watcher 填充：
// 开新世界时正文在进入 game 视图前就已写完，GameView 挂载时 watcher 不会触发，
// 会导致正文区空白、只剩选项——必须派生自当前状态，挂载即渲染。
const finalRendered = computed(() => {
  if (showStreaming.value) return ''
  return md.render(stripOptionsBlock(game.narrative))
})

// 距底部多少像素内视为"正在看底部"——只有在此范围内才跟随滚动。
// 玩家上翻阅读历史时绝不强制拉动，从根上消除"页面跳动"。
const PIN_THRESHOLD = 120
function pin() {
  const el = scroller.value
  if (!el) return
  if (el.scrollTop + el.clientHeight >= el.scrollHeight - PIN_THRESHOLD) {
    el.scrollTop = el.scrollHeight
  }
}

watch(() => game.narrative, async (v) => {
  display.value = stripArtifacts(stripOptionsBlock(v))
  await nextTick()
  pin()
})

// 流式 → 完成 切换时 DOM 高度变化，同样按需跟随滚动
watch(showStreaming, async () => {
  await nextTick()
  pin()
})

// 归档/后悔/出错后滚动位置可能变化，同样按需跟随
watch(() => [game.turns.length, game.error], async () => {
  await nextTick()
  pin()
})
</script>

<template>
  <main ref="scroller" class="narrative-scroller" aria-label="故事正文">
    <div class="narrative-column">
      <!-- 失败提示 -->
      <div v-if="game.error" class="narrative-error">
        {{ game.error }}
      </div>

      <!-- 过往回合：完整回放，文字不丢 -->
      <template v-for="(t, i) in game.turns" :key="i">
        <div v-html="t.html" class="prose-narrative narrative-copy"></div>
        <div v-if="t.choice" class="narrative-choice">
          你选择了 · {{ t.choice }}
        </div>
        <div v-if="t.event" class="narrative-annotation narrative-event">
          <span>事件</span>{{ t.event }}
        </div>
        <div v-if="t.notes && t.notes.length" class="narrative-annotation">
          <span>记录</span>{{ t.notes.join('；') }}
        </div>
      </template>

      <!-- 当前回合：同一位置持续渲染，生成 → 完成不重建 DOM -->
      <div v-if="game.lastChoice" class="narrative-choice">
        你选择了 · {{ game.lastChoice }}
      </div>
      <div v-if="showStreaming" class="whitespace-pre-wrap prose-narrative narrative-copy">
        <span>{{ display }}</span><span class="caret"></span>
      </div>
      <div v-else-if="finalRendered" v-html="finalRendered" class="prose-narrative narrative-copy"></div>
      <div v-else-if="game.turnDone && game.options.length" class="narrative-empty">
        （AI 未生成有效的叙述文本。请选择一个选项继续，系统将在下一回合重新生成叙述。）
      </div>
      <div v-else class="prose-narrative narrative-copy"></div>
      <div v-if="!showStreaming && game.event" class="narrative-annotation narrative-event">
        <span>事件</span>{{ game.event }}
      </div>
      <div v-if="!showStreaming && game.notes.length" class="narrative-annotation">
        <span>记录</span>{{ game.notes.join('；') }}
      </div>
    </div>
  </main>
</template>

<style>
.prose-narrative p { margin: 1.1em 0; }
.prose-narrative strong { color: var(--text-primary); font-weight: 600; }
.prose-narrative em { color: var(--text-secondary); }
</style>
