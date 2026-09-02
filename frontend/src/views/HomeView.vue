<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import {
  ui, worlds, loadWorlds, SITE_NAME,
  entitlement, refreshEntitlement, fmtDate, clientId, setActivationOpen,
} from '../store'

const emit = defineEmits(['newGame', 'continue'])
const sessions = ref([])

// ── 世界搜索 / 折叠 ─────────────────────────────
const searchQuery = ref('')
const isWorldsCollapsed = ref(false)
const filteredWorlds = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return worlds.builtin
  return worlds.builtin.filter(w =>
    (w.name || '').toLowerCase().includes(q) ||
    (w.desc || '').toLowerCase().includes(q)
  )
})

// ── 上传小说 → 建世界 ─────────────────────────────
const file = ref(null)
const apiKey = ref(localStorage.getItem('douluo_api_key') || '')
const buildPhase = ref('')      // '' | 'uploading' | 'error' | 'done'
const buildMsg = ref('')
const deleting = ref('')        // 正在删除的世界 id

const statusText = computed(() => {
  if (entitlement.loading) return '加载中…'
  if (entitlement.paid) return `已订阅 · 无限游玩（至 ${fmtDate(entitlement.paidUntil)}）`
  const left = Math.max(0, entitlement.trialLimit - entitlement.trialUsed)
  return `免费试玩中 · 剩余 ${left} 回合 · 1元/月无限玩`
})

async function buildWorld() {
  if (buildPhase.value === 'uploading') return
  if (!file.value) { buildMsg.value = '请先选择一本小说的 TXT 或 Word(.docx) 文件。'; return }
  const key = apiKey.value.trim()
  if (!key) { buildMsg.value = '建世界需要你自己的 DeepSeek API Key（站点不代付额度）。'; return }
  const fd = new FormData()
  fd.append('file', file.value)
  fd.append('api_key', key)
  fd.append('client_id', clientId())
  buildPhase.value = 'uploading'
  buildMsg.value = '正在解析小说并让 AI 搭建世界框架（约 30-90 秒）…'
  try {
    const w = await api.buildWorld(fd)
    await loadWorlds()
    buildPhase.value = 'done'
    buildMsg.value = `世界「${w.name}」创建成功！可在下方「我的世界」里进入。`
    file.value = null
  } catch (e) {
    buildPhase.value = 'error'
    buildMsg.value = e.message
  }
}

function onKeyInput(e) { localStorage.setItem('douluo_api_key', e.target.value.trim()) }

async function delWorld(w) {
  if (!confirm(`确定删除自建世界「${w.name}」吗？该世界的存档不会受影响，但世界本身不可恢复。`)) return
  deleting.value = w.id
  try {
    await api.deleteWorld({ world_id: w.id, client_id: clientId() })
    await loadWorlds()
  } catch (e) { alert(e.message) } finally { deleting.value = '' }
}

// 找出与指定世界关联的存档
function saveForWorld(worldId) {
  return sessions.value.find(s => s.world_id === worldId)
}

function continueSave(save) {
  emit('continue', save)
}

onMounted(async () => {
  refreshEntitlement()
  loadWorlds()
  try { const d = await api.saves(clientId()); sessions.value = d.saves || [] } catch {}
})
</script>

<template>
  <div class="h-full overflow-y-auto px-6 py-10">
    <div class="max-w-3xl mx-auto">
      <!-- 平台标题 -->
      <div class="text-center mb-8">
        <h1 class="text-3xl md:text-4xl font-bold text-amber-200 mb-3 tracking-wide">{{ SITE_NAME }}</h1>
        <p class="text-stone-400 text-sm md:text-base leading-relaxed">
          一个容纳众多模拟世界的文字 RPG 平台。选择你感兴趣的世界，从出生开始书写属于你的人生。
        </p>
      </div>

      <!-- 创作者已开发的世界 -->
      <section class="mb-10">
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-lg font-semibold text-stone-300 flex items-center gap-2">
            ✦ 创作者已开发的世界
          </h2>
          <div class="flex items-center">
            <input v-model="searchQuery" placeholder="搜索世界..." class="bg-stone-800 border border-stone-700 text-stone-200 text-xs rounded px-2 py-1 w-24 focus:w-32 transition-all mr-2" />
            <button @click="isWorldsCollapsed = !isWorldsCollapsed" class="text-xs text-stone-400 hover:text-amber-300 whitespace-nowrap">
              {{ isWorldsCollapsed ? '展开 ▼' : '收起 ▲' }}
            </button>
          </div>
        </div>
        <div v-if="worlds.builtin.length" v-show="!isWorldsCollapsed" class="grid gap-3 sm:grid-cols-2">
          <div v-for="w in filteredWorlds" :key="w.id"
            class="rounded-lg border border-amber-800/50 bg-stone-900/70 p-5 flex flex-col hover:border-primary transition">
            <div class="flex items-center justify-between mb-1">
              <h3 class="text-xl font-bold text-amber-200">{{ w.name }}</h3>
              <span class="text-[10px] px-2 py-0.5 rounded-full bg-amber-900/60 text-amber-300">创作者</span>
            </div>
            <p class="text-sm text-stone-400 flex-1 mb-4">{{ w.desc }}</p>
            <div class="space-y-2">
              <button v-if="saveForWorld(w.id)" @click="continueSave(saveForWorld(w.id))"
                class="w-full py-2.5 rounded-lg bg-emerald-700 text-white font-medium hover:bg-emerald-600 transition text-sm">
                ▶ 继续冒险（{{ saveForWorld(w.id).name }} · 第{{ saveForWorld(w.id).turn }}回合）
              </button>
              <button @click="emit('newGame', w)"
                class="w-full py-2.5 rounded-lg bg-primary text-stone-950 font-medium hover:opacity-80 transition">
                进入「{{ w.name }}」
              </button>
            </div>
          </div>
          <p v-if="searchQuery && !filteredWorlds.length" class="text-sm text-stone-500 sm:col-span-2">没有找到匹配「{{ searchQuery }}」的世界</p>
        </div>
        <p v-else class="text-sm text-stone-500">世界加载中…</p>
      </section>

      <!-- 我的世界 -->
      <section class="mb-10">
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-lg font-semibold text-stone-300">✦ 我的世界</h2>
          <span class="text-xs text-stone-500">仅你自己可见</span>
        </div>
        <div v-if="worlds.mine.length" class="grid gap-3 sm:grid-cols-2">
          <div v-for="w in worlds.mine" :key="w.id"
            class="rounded-lg border border-stone-700 bg-stone-900/70 p-5 flex flex-col hover:border-stone-500 transition">
            <div class="flex items-center justify-between mb-1">
              <h3 class="text-lg font-bold text-stone-200">{{ w.name }}</h3>
              <button @click="delWorld(w)" :disabled="deleting === w.id"
                class="text-xs text-stone-500 hover:text-red-400 transition disabled:opacity-30">删除</button>
            </div>
            <p class="text-sm text-stone-400 flex-1 mb-4">{{ w.desc || '由你上传小说生成的专属世界' }}</p>
            <div class="space-y-2">
              <button v-if="saveForWorld(w.id)" @click="continueSave(saveForWorld(w.id))"
                class="w-full py-2.5 rounded-lg bg-emerald-700 text-white font-medium hover:bg-emerald-600 transition text-sm">
                ▶ 继续冒险（{{ saveForWorld(w.id).name }} · 第{{ saveForWorld(w.id).turn }}回合）
              </button>
              <button @click="emit('newGame', w)"
                class="w-full py-2.5 rounded-lg border border-primary text-amber-200 hover:bg-amber-900/30 transition">
                进入「{{ w.name }}」
              </button>
            </div>
          </div>
        </div>
        <p v-else class="text-sm text-stone-500 mb-4">还没有自建世界——上传一本你喜欢的小说，AI 会帮你搭出它的世界框架。</p>

        <!-- 上传小说建世界 -->
        <div class="rounded-lg border border-dashed border-stone-600 bg-stone-900/40 p-5">
          <h3 class="font-medium text-stone-300 mb-2">📖 上传小说 → 创建专属世界</h3>
          <p class="text-xs text-stone-500 leading-relaxed mb-4">
            上传小说的 <b>TXT</b> 或 <b>Word(.docx)</b> 文件（≤30MB），AI 会抽样精读并生成一套
            可游玩的世界框架（规则书 + 资源属性 + 创建选项）。<br/>
            建世界会调用 <b>你自己的 DeepSeek API Key</b> 计费（约几分钱），站点不代付；原文章节不会留存。
          </p>
          <div class="space-y-3">
            <input type="file" accept=".txt,.md,.docx"
              @change="e => { file = e.target.files[0]; buildMsg = '' }"
              class="block w-full text-sm text-stone-300 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-stone-700 file:text-stone-200 file:hover:bg-stone-600 file:cursor-pointer" />
            <input v-model="apiKey" type="password" @input="onKeyInput" autocomplete="off" placeholder="你的 DeepSeek API Key（sk-...）"
              class="w-full bg-stone-900 border border-stone-700 rounded-lg p-2.5 font-mono text-sm" />
            <button @click="buildWorld" :disabled="buildPhase === 'uploading'"
              class="w-full py-2.5 rounded-lg bg-primary text-stone-950 font-medium hover:opacity-80 transition disabled:opacity-50">
              {{ buildPhase === 'uploading' ? '⏳ 正在生成世界框架…' : '✨ 生成世界框架' }}
            </button>
            <p v-if="buildMsg" :class="buildPhase === 'error' ? 'text-red-400' : 'text-emerald-400'"
              class="text-xs leading-relaxed">{{ buildMsg }}</p>
          </div>
        </div>
      </section>

      <!-- 继续游戏 -->
      <section v-if="sessions.length" class="mb-10">
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-lg font-semibold text-stone-300">✦ 继续游戏</h2>
          <button @click="emit('continue')"
            class="text-xs text-stone-400 hover:text-amber-300 transition">
            📂 全部存档
          </button>
        </div>
        <ul class="space-y-2">
          <li v-for="s in sessions" :key="s.session_id"
            class="flex items-center justify-between rounded-lg border border-stone-700 bg-stone-800/60 px-4 py-3 hover:border-amber-700/60 transition">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="text-stone-100 font-medium truncate">{{ s.name }}</span>
                <span class="text-xs text-amber-300/80 shrink-0">{{ s.level_field }} {{ s.level }}</span>
              </div>
              <div class="text-xs text-stone-400 mt-0.5 truncate">
                {{ s.world_name }} · {{ s.place }} · 第{{ s.turn }}回合 · {{ s.date }}
              </div>
            </div>
            <button @click="continueSave(s)"
              class="shrink-0 ml-3 px-3 py-1.5 rounded text-xs font-medium bg-primary text-stone-950 hover:opacity-80 transition">
              继续
            </button>
          </li>
        </ul>
      </section>

      <!-- 订阅 / 免费试玩状态 -->
      <div class="text-center mt-8">
        <button @click="setActivationOpen(true)"
          class="text-xs text-stone-400 hover:text-amber-300 transition">
          💳 订阅 / 激活码
        </button>
        <p class="text-[11px] text-stone-600 mt-1">{{ statusText }}</p>
      </div>
    </div>
  </div>
</template>
