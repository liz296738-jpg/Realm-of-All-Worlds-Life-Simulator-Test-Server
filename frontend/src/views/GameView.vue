<script setup>
import { computed } from 'vue'
import {
  game, ui, draft,
  commitTurn, clientId, getSubscriptionCode, isGateError, worldName,
  setGameState, setStreaming, setTurnDone, setTurnCommitted,
  clearNarrative, appendNarrative, setOptions, setNotes, setEvent,
  setLastChoice, setCanUndo, setError, setTurns,
  setActivationOpen, togglePanel,
} from '../store'
import { postSse, api } from '../api'
import { renderMd, stripOptionsBlock } from '../md'
import NarrativeStream from '../components/NarrativeStream.vue'
import OptionsBar from '../components/OptionsBar.vue'
import StatusPanel from '../components/StatusPanel.vue'
import SavePanel from '../components/SavePanel.vue'
import CharacterPanel from '../components/CharacterPanel.vue'

const contextItems = computed(() => {
  const state = game.state || {}
  const items = []
  const age = state.character?.age
  if (age !== undefined && age !== null && age !== '') items.push(`年龄 ${age}`)
  const turn = state.meta?.turn
  if (turn !== undefined && turn !== null && turn !== '') items.push(`第 ${turn} 回合`)
  if (state.location?.season) items.push(state.location.season)
  return items.slice(0, 3)
})

const emit = defineEmits(['open-settings'])

function openPanel(name) {
  const nextOpen = !ui[name]
  togglePanel('showStatus', name === 'showStatus' && nextOpen)
  togglePanel('showCharacter', name === 'showCharacter' && nextOpen)
  togglePanel('showSave', name === 'showSave' && nextOpen)
}

// 后端返回的 turns 不含渲染后的 html，此处补齐（剥掉 AI 自带的选项块，与当前回合显示一致）
function hydrateTurns(turns) {
  return (turns || []).map(t => ({ ...t, html: renderMd(stripOptionsBlock(t.narrative)) }))
}

// 后端 turns 末尾是"当前回合"，前段才是已归档的过往回合（resume/undo 恢复显示用）
function splitTurns(bt) {
  const archived = hydrateTurns(bt.slice(0, -1))
  const cur = bt[bt.length - 1] || null
  return { archived, cur }
}

/** 覆盖当前回合叙述（先清空再追加，等效于直接赋值：仅组件只读后禁止直接 game.narrative = 必须走 action）。 */
function setNarrative(text) {
  clearNarrative()
  if (text) appendNarrative(text)
}

function submit(action) {
  if (game.streaming || !game.sessionId) return
  // 在【新回合开始前】归档上一回合：叙述不丢，且当前回合 DOM 全程不重建（防页面跳动）。
  // 只有后端确认过落账（turnCommitted）的回合才归档——失败/中断的残篇不归档，避免前后端回合列表分叉。
  if (game.turnCommitted && game.narrative.trim()) {
    commitTurn({ narrative: game.narrative, options: game.options, notes: game.notes, event: game.event, choice: game.lastChoice })
  }
  setLastChoice(action)
  setStreaming(true)
  setTurnDone(false)
  setTurnCommitted(false) // 等后端 delta 确认后才可归档
  clearNarrative()
  setOptions([])
  setNotes([])   // 清除上一回合残留，防止失败后带着旧 event/notes 归档
  setEvent('')
  setError('')

  postSse('/api/act', {
    session_id: game.sessionId, action,
    api_key: draft.apiKey?.trim() || null,
    freedom: draft.freedom,
    client_id: clientId(),
    code: getSubscriptionCode() || null,
  }, {
    onText: (t) => { appendNarrative(t) },
    onDelta: (d) => {
      setGameState(d.state)
      setOptions(d.options || [])
      setNotes(d.notes || [])
      setEvent(d.event || '')
      setCanUndo(!!d.can_undo)
      setTurnCommitted(true) // 后端已把本回合写入 turns/历史
    },
    onDone: () => { setStreaming(false); setTurnDone(true) },
  }).catch((e) => {
    setStreaming(false)
    setTurnDone(true)
    setError(e.message)
    if (isGateError(e)) setActivationOpen(true, e.message)
    else alert(e.message)
  })
}

// "后悔"：退回上一回合，状态/选项/叙述全部还原（后端不调 AI，即时返回）。
// 复用 streaming 锁防止双击并发（否则两个在途 undo 各弹一层，一次点击退回两回合）。
async function undo() {
  if (game.streaming || !game.sessionId || !game.canUndo) return
  setStreaming(true)
  setTurnDone(false)
  try {
    const d = await api.undo(game.sessionId)
    const { archived, cur } = splitTurns(d.turns)
    setGameState(d.state)
    setTurns(archived)
    setNarrative(cur ? cur.narrative : '')
    setLastChoice(cur ? (cur.choice || null) : null)
    setOptions(d.options || [])
    setNotes(cur ? (cur.notes || []) : [])
    setEvent(cur ? (cur.event || '') : '')
    setCanUndo(!!d.can_undo)
    setError('')
    setTurnCommitted(true) // 恢复出的当前回合是完整已落账回合，可再次提交
  } catch (e) {
    setError(e.message)
    alert(e.message)
  } finally {
    setStreaming(false)
    setTurnDone(true)
  }
}

function onResume(payload) {
  const { archived, cur } = splitTurns(payload.turns)
  setGameState(payload.state)
  setTurns(archived)
  setNarrative(cur ? cur.narrative : '')
  setLastChoice(cur ? (cur.choice || null) : null)
  setOptions(payload.options || [])
  setNotes(cur ? (cur.notes || []) : [])
  setEvent(cur ? (cur.event || '') : '')
  setCanUndo(!!payload.canUndo)
  setError('')
  setTurnCommitted(true) // 恢复出的当前回合是完整回合
  setTurnDone(true)
  setStreaming(false)
}
</script>

<template>
  <div class="game-shell">
    <header class="game-header">
      <button type="button" class="app-icon-button" title="存档 / 读档" aria-label="存档 / 读档"
        :aria-pressed="ui.showSave" @click="openPanel('showSave')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M5 3h12l3 3v15H5z"/><path d="M8 3v6h8V3M8 21v-7h8v7"/></svg>
      </button>
      <div class="game-header-title">
        <h1>{{ worldName(game.state) }}</h1>
        <p v-if="game.state?.location?.place">{{ game.state.location.place }}</p>
      </div>
      <nav class="game-header-tools" aria-label="游戏工具">
        <button type="button" class="app-icon-button" title="状态" aria-label="状态" :aria-pressed="ui.showStatus"
          :class="{ 'game-tool-active': ui.showStatus }" @click="openPanel('showStatus')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M4 19V9m5 10V5m6 14v-8m5 8V3"/></svg>
        </button>
        <button type="button" class="app-icon-button" title="角色" aria-label="角色" :aria-pressed="ui.showCharacter"
          :class="{ 'game-tool-active': ui.showCharacter }" @click="openPanel('showCharacter')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><circle cx="12" cy="8" r="3"/><path d="M5 21c.7-4 3-6 7-6s6.3 2 7 6"/></svg>
        </button>
        <button type="button" class="app-icon-button" title="设置" aria-label="设置" @click="emit('open-settings')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .34 1.88l.06.06-2.12 2.12-.06-.06a1.7 1.7 0 0 0-1.88-.34 1.7 1.7 0 0 0-1.03 1.55V20.3h-3v-.09A1.7 1.7 0 0 0 10.68 18.66a1.7 1.7 0 0 0-1.88.34l-.06.06-2.12-2.12.06-.06A1.7 1.7 0 0 0 7.02 15 1.7 1.7 0 0 0 5.47 14H5.4v-3h.07A1.7 1.7 0 0 0 7.02 10a1.7 1.7 0 0 0-.34-1.88l-.06-.06 2.12-2.12.06.06A1.7 1.7 0 0 0 10.68 6.34 1.7 1.7 0 0 0 11.7 4.8V4.7h3v.1a1.7 1.7 0 0 0 1.03 1.54A1.7 1.7 0 0 0 17.61 6l.06-.06 2.12 2.12-.06.06A1.7 1.7 0 0 0 19.4 10 1.7 1.7 0 0 0 20.94 11H21v3h-.06A1.7 1.7 0 0 0 19.4 15Z"/></svg>
        </button>
      </nav>
    </header>

    <div v-if="contextItems.length" class="game-context" aria-label="当前进度">
      <span v-for="item in contextItems" :key="item">{{ item }}</span>
    </div>

    <!-- 叙事流 -->
    <NarrativeStream />

    <!-- 选项与输入 -->
    <OptionsBar @choose="submit" @undo="undo" />

    <!-- 折叠状态栏 + 角色设定 + 存档面板 -->
    <StatusPanel />
    <CharacterPanel />
    <SavePanel @resume="onResume" />
  </div>
</template>
