<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  ui, game, draft, worlds,
  setGameState, setStreaming, setTurnDone, setTurnCommitted,
  clearNarrative, setOptions, setNotes, setEvent,
  setLastChoice, setCanUndo, setError, setSessionId,
  setUiView, setBusy, setActivationOpen, togglePanel,
  appendNarrative, setTurns,
  clientId, getSubscriptionCode,
  refreshEntitlement, isGateError, selectWorld, loadWorlds,
} from './store'
import { postSse, api } from './api'
import { renderMd, stripOptionsBlock } from './md'
import HomeView from './views/HomeView.vue'
import GameView from './views/GameView.vue'
import CreationWizard from './components/CreationWizard.vue'
import GenericWizard from './components/GenericWizard.vue'
import CharacterCard from './components/CharacterCard.vue'
import ActivationPanel from './components/ActivationPanel.vue'
import SettingsPanel from './components/SettingsPanel.vue'

const archive = ref(null)
const showSettings = ref(false)  // 设置面板显示/隐藏

// 开局时选中的世界决定向导与加载文案；读档/续玩时以会话自带世界为准
const loadingText = computed(() => {
  if (!ui.busy) return ''
  const name = game.state?.meta?.world_name || worlds.selected?.name
  return `正在进入${name || '世界'}…`
})

function newGame(w) { selectWorld(w); setUiView('create') }
function onWizardComplete(a) { archive.value = a; setUiView('review') }
function onCardBack() { setUiView('create') }

async function onCardConfirm() {
  setBusy(true)
  setStreaming(true)
  setTurnDone(false)
  setTurnCommitted(false)
  clearNarrative()
  setOptions([])
  setNotes([])
  setEvent('')
  setLastChoice(null)
  setError('')
  setCanUndo(false)
  try {
    await postSse('/api/new-game', {
      world_id: worlds.selected?.id || 'douluo',
      archive: archive.value,
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
        setTurnCommitted(true)
      },
      onDone: () => { setUiView('game'); setBusy(false); setStreaming(false); setTurnDone(true) },
    })
  } catch (e) {
    setBusy(false)
    if (isGateError(e)) { setActivationOpen(true, e.message) }
    else alert(e.message)
  }
}

function onContinue(save) {
  if (save) {
    resumeGame(save.session_id)
    return
  }
  setUiView('game')
  togglePanel('showSave', true)
}

async function resumeGame(sessionId) {
  setBusy(true)
  setStreaming(true)
  setTurnDone(false)
  setTurnCommitted(false)
  clearNarrative()
  setOptions([])
  setNotes([])
  setEvent('')
  setLastChoice(null)
  setError('')
  setCanUndo(false)
  setSessionId(sessionId)
  try {
    const body = { client_id: clientId(), code: getSubscriptionCode() || null }
    const resp = await fetch('/api/resume', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...body, session_id: sessionId }),
    })
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}))
      throw new Error(err.detail || `请求失败 ${resp.status}`)
    }
    const d = await resp.json()
    setGameState(d.state)
    // 与 GameView.onResume(SavePanel 读档路径) 保持一致：后端 turns 末尾是“当前回合”，
    // 前段才是已归档回合。恢复当前回合叙述 + 选项，避免首页“继续冒险”读档后无选项可点。
    const bt = d.turns || []
    const cur = bt[bt.length - 1] || null
    setTurns(bt.slice(0, -1).map(t => ({
      narrative: t.narrative || '',
      options: t.options || [],
      notes: t.notes || [],
      event: t.event || '',
      choice: t.choice || null,
      html: renderMd(stripOptionsBlock(t.narrative || '')),
    })))
    if (cur && cur.narrative) appendNarrative(cur.narrative)
    setLastChoice(cur ? (cur.choice || null) : null)
    setOptions(d.last_options || [])
    setNotes(cur ? (cur.notes || []) : [])
    setEvent(cur ? (cur.event || '') : '')
    setCanUndo(!!d.can_undo)
    setError('')
    setTurnDone(true)
    setTurnCommitted(true)
    setStreaming(false)
    setUiView('game')
    setBusy(false)
  } catch (e) {
    setBusy(false)
    if (isGateError(e)) { setActivationOpen(true, e.message) }
    else alert(e.message)
  }
}

onMounted(async () => {
  try { await api.health() } catch { /* 后端未启动时提示 */ }
  refreshEntitlement()
  loadWorlds()
})
</script>

<template>
  <div class="h-full">
    <HomeView v-if="ui.view === 'home'" @new-game="newGame" @continue="onContinue" @open-settings="showSettings = true" />
    <GenericWizard v-else-if="ui.view === 'create' && worlds.selected && worlds.selected.id !== 'douluo'"
      :world="worlds.selected" @complete="onWizardComplete" />
    <CreationWizard v-else-if="ui.view === 'create'" @complete="onWizardComplete" />
    <CharacterCard v-else-if="ui.view === 'review'" :archive="archive" :world="worlds.selected"
      @confirm="onCardConfirm" @back="onCardBack" />
    <GameView v-else-if="ui.view === 'game'" />

    <ActivationPanel />

    <!-- 设置按钮（右上角浮动）：首页由底部导航接管，其余视图仍保留；顶部避开刘海安全区 -->
    <button v-if="ui.view !== 'home'" type="button" @click="showSettings = !showSettings" title="设置" aria-label="设置"
      style="top: calc(0.75rem + var(--safe-top))"
      class="fixed right-3 z-30 px-3 py-1.5 rounded-full border border-stone-700 bg-stone-900/80 text-sm text-stone-300 backdrop-blur transition hover:border-primary hover:text-primary">
      ⚙ 设置
    </button>
    <SettingsPanel v-if="showSettings" @close="showSettings = false" />

    <div v-if="ui.busy" class="fixed inset-0 z-50 bg-black/70 flex items-center justify-center text-stone-200">
      {{ loadingText }}
    </div>
  </div>
</template>
