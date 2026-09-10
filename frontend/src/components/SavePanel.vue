<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'
import { ui, game, setGameState, setSessionId, setUiView, togglePanel, clientId } from '../store'

const emit = defineEmits(['resume'])
const saves = ref([])
const msg = ref('')
const loading = ref(false)
const exporting = ref(null)  // 正在导出的 session_id，防双击重复下载

async function refresh() {
  try {
    const d = await api.saves(clientId())
    saves.value = d.saves || []
  } catch (e) { msg.value = e.message }
}

async function doSave() {
  if (!game.sessionId) return
  loading.value = true
  try {
    const d = await api.save(game.sessionId)
    msg.value = `已存档（回合 ${d.savepoint.turn}）`
    await refresh()
  } catch (e) { msg.value = e.message } finally { loading.value = false }
}

async function doResume(sid) {
  loading.value = true
  try {
    const d = await api.resume(sid)
    setGameState(d.state)
    togglePanel('showSave', false)
    emit('resume', { state: d.state, narrative: d.last_narrative, options: d.last_options, turns: d.turns, canUndo: d.can_undo })
  } catch (e) { msg.value = e.message } finally { loading.value = false }
}

async function doDelete(sid) {
  try {
    await api.del(sid)
    if (game.sessionId === sid) setSessionId(null)
    msg.value = '已删除'
    await refresh()
  } catch (e) { msg.value = e.message }
}

function goHome() {
  togglePanel('showSave', false)
  setUiView('home')
}

async function doExport(sid) {
  if (exporting.value) return  // 已有导出进行中，忽略重复点击
  exporting.value = sid
  try {
    const d = await api.export(sid)
    if (!d.content || !d.turns) {
      msg.value = '这段旅程还没有可导出的剧情'
      return
    }
    const blob = new Blob([d.content], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = d.filename || 'story.md'
    document.body.appendChild(a)
    a.click()
    a.remove()
    // 延迟释放对象 URL：click 同步释放会让 Firefox 中断下载
    setTimeout(() => URL.revokeObjectURL(url), 1000)
    msg.value = `已导出 ${d.title}（共 ${d.turns} 段剧情）`
  } catch (e) { msg.value = e.message } finally { exporting.value = null }
}

onMounted(refresh)
</script>

<template>
  <transition name="slide">
    <div v-if="ui.showSave" class="app-modal-backdrop" @click.self="togglePanel('showSave', false)">
      <div class="app-modal app-save-panel">
        <div class="app-sheet-header">
          <h3>存档与旅程</h3>
          <button @click="togglePanel('showSave', false)" class="app-icon-button" aria-label="关闭存档面板">×</button>
        </div>

        <div class="app-save-actions">
          <button @click="doSave" :disabled="loading || !game.sessionId"
            class="app-button app-button-primary flex-1 disabled:opacity-30">
            保存当前进度
          </button>
          <button @click="goHome"
            class="app-button app-button-ghost">
            返回主界面
          </button>
        </div>
        <p v-if="msg" class="app-save-message">{{ msg }}</p>

        <div class="app-save-list">
          <div v-for="s in saves" :key="s.session_id"
            class="app-save-entry">
            <div class="app-save-entry-head">
              <div>
                <span class="app-save-name">{{ s.name }}</span>
                <span class="app-save-turn">第 {{ s.turn }} 回合</span>
                <div class="app-save-meta">{{ s.place }} · {{ s.date }}</div>
              </div>
              <div class="app-save-entry-actions">
                <button @click="doResume(s.session_id)" class="app-button app-button-primary">继续</button>
                <button @click="doExport(s.session_id)" :disabled="exporting !== null" title="把这段旅程的剧情导出成 Markdown 小说" class="app-button app-button-secondary">{{ exporting === s.session_id ? '导出中…' : '导出故事' }}</button>
                <button @click="doDelete(s.session_id)" class="app-button app-button-ghost app-danger-action" aria-label="删除存档">删除</button>
              </div>
            </div>
          </div>
          <p v-if="!saves.length" class="app-empty-state">还没有存档。<br>当你保存旅程后，它会出现在这里。</p>
        </div>
      </div>
    </div>
  </transition>
</template>

<style>
.slide-enter-active, .slide-leave-active { transition: opacity 0.2s ease; }
.slide-enter-from, .slide-leave-to { opacity: 0; }
</style>
