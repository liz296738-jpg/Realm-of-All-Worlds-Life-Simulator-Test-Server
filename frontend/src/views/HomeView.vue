<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import {
  worlds, loadWorlds, SITE_NAME,
  refreshEntitlement, clientId,
} from '../store'
import WorldFeaturedCard from '../components/WorldFeaturedCard.vue'
import WorldListItem from '../components/WorldListItem.vue'
import CoverLightbox from '../components/CoverLightbox.vue'

const emit = defineEmits(['newGame', 'continue', 'open-settings'])
const sessions = ref([])
const previewCover = ref(null)

// ── 世界封面映射（预留）：未来填入真实图片路径，无需改组件结构 ──
const WORLD_COVERS = {
  douluo: '/world-covers/douluo.webp',
  gebi: '/world-covers/gebi.webp',
  shanhe: '/world-covers/shanhe.webp',
  shengluolan: '/world-covers/shengluolan.webp',
  shuguang: '/world-covers/shuguang.webp',
  taishangfuli: '/world-covers/taishangfuli.webp',
  wanwusheng: '/world-covers/wanwusheng.webp',
  yongzhou: '/world-covers/yongzhou.webp',
  zhenshi: '/world-covers/zhenshi.webp',
  zhujie: '/world-covers/zhujie.webp',
}
function worldCover(w) {
  return (w && WORLD_COVERS[w.id]) || null
}

function openCover(world) {
  const src = worldCover(world)
  if (!src) return
  previewCover.value = { src, title: world.name }
}

function closeCover() {
  previewCover.value = null
}

// ── 分段控件：创作者世界 / 我的世界 ──
const activeWorldTab = ref('featured')  // 'featured' | 'mine'
const showWorldBuilder = ref(false)

// ── 世界搜索 ──
const searchQuery = ref('')
const filteredWorlds = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return worlds.builtin
  return worlds.builtin.filter(w =>
    (w.name || '').toLowerCase().includes(q) ||
    (w.desc || '').toLowerCase().includes(q)
  )
})
const featuredWorld = computed(() => filteredWorlds.value[0] || null)
const restWorlds = computed(() => filteredWorlds.value.slice(1))

// ── 快捷存档：取 sessions 首项作为首页快捷入口（后端目前无可靠更新时间字段，
//    故不伪称“最近/上次”，仅作“继续冒险”快捷位） ──
const quickSave = computed(() => sessions.value[0] || null)

// ── 上传小说 → 建世界 ──
const file = ref(null)
const fileName = ref('')
const apiKey = ref(localStorage.getItem('douluo_api_key') || '')
const buildPhase = ref('')      // '' | 'uploading' | 'error' | 'done'
const buildMsg = ref('')
const deleting = ref('')        // 正在删除的世界 id
const fileInput = ref(null)

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
    buildMsg.value = `世界「${w.name}」创建成功！可在「我的世界」里进入。`
    file.value = null
    fileName.value = ''
  } catch (e) {
    buildPhase.value = 'error'
    buildMsg.value = e.message
  }
}

function onKeyInput(e) { localStorage.setItem('douluo_api_key', e.target.value.trim()) }

function onFileChange(e) {
  file.value = e.target.files[0]
  fileName.value = file.value ? file.value.name : ''
  buildMsg.value = ''
}

function pickFile() {
  if (buildPhase.value === 'uploading') return
  fileInput.value?.click()
}

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

function enterWorld(w) {
  emit('newGame', w)
}

onMounted(async () => {
  refreshEntitlement()
  loadWorlds()
  try { const d = await api.saves(clientId()); sessions.value = d.saves || [] } catch {}
})
</script>

<template>
  <div class="h-full">
    <!-- 滚动内容区 -->
    <div class="h-full overflow-y-auto">
      <div class="max-w-2xl mx-auto px-5"
        style="padding-bottom: calc(96px + var(--safe-bottom));">

        <!-- 品牌 Hero -->
        <header class="home-hero">
          <h1 class="home-hero-title">{{ SITE_NAME }}<span class="home-hero-dot">。</span></h1>
          <p class="home-hero-subtitle">穿行不同世界，书写属于你的另一种人生。</p>
        </header>

        <!-- 分段控件：互斥切换用 aria-pressed（不做 ARIA tabs，避免承诺整套 tabpanel/方向键契约） -->
        <div class="home-segmented" role="group" aria-label="世界类型">
          <button type="button" :aria-pressed="activeWorldTab === 'featured'"
            @click="activeWorldTab = 'featured'">创作者世界</button>
          <button type="button" :aria-pressed="activeWorldTab === 'mine'"
            @click="activeWorldTab = 'mine'">我的世界</button>
        </div>

        <!-- ── 创作者世界 ── -->
        <section v-if="activeWorldTab === 'featured'" class="space-y-4">
          <input v-model="searchQuery" type="search" class="app-input" placeholder="搜索世界…" aria-label="搜索世界" />

          <!-- 加载中 / 真正为空（后端不可达）两态分开，避免“加载中…”永久占位 -->
          <p v-if="worlds.loading && !worlds.builtin.length" class="home-empty">世界加载中…</p>
          <p v-else-if="!worlds.builtin.length" class="home-empty">
            世界暂不可用——请确认后端服务已启动。
            <button type="button" class="home-retry" @click="loadWorlds">重新加载</button>
          </p>
          <template v-else-if="featuredWorld">
            <WorldFeaturedCard :world="featuredWorld" :save="saveForWorld(featuredWorld.id)"
              :cover="worldCover(featuredWorld)" @enter="enterWorld(featuredWorld)" @continue="continueSave"
              @preview="openCover(featuredWorld)" />

            <div v-if="restWorlds.length" class="space-y-2">
              <WorldListItem v-for="w in restWorlds" :key="w.id" :world="w"
                :save="saveForWorld(w.id)" :cover="worldCover(w)"
                @enter="enterWorld(w)" @continue="continueSave" @preview="openCover(w)" />
            </div>
          </template>
          <p v-else class="home-empty">没有找到匹配「{{ searchQuery }}」的世界。</p>
        </section>

        <!-- ── 我的世界 ── -->
        <section v-else class="space-y-4">
          <!-- 建世界入口（折叠） -->
          <button type="button" class="home-builder-cta" @click="showWorldBuilder = !showWorldBuilder"
            :aria-expanded="showWorldBuilder">
            <span aria-hidden="true">{{ showWorldBuilder ? '－' : '＋' }}</span>
            <span>{{ showWorldBuilder ? '收起创建面板' : '上传小说，创建专属世界' }}</span>
          </button>

          <!-- 建世界上传表单 -->
          <div v-if="showWorldBuilder" class="app-panel p-4 space-y-3">
            <p class="text-xs leading-relaxed app-muted">
              上传小说的 <b>TXT</b>、<b>Markdown(.md)</b> 或 <b>Word(.docx)</b> 文件（≤30MB），AI 会抽样精读并生成一套可游玩的世界框架（规则书 + 资源属性 + 创建选项）。建世界会调用 <b>你自己的 DeepSeek API Key</b> 计费（约几分钱），站点不代付；原文章节不会留存。
            </p>
            <input ref="fileInput" type="file" accept=".txt,.md,.docx" class="hidden" @change="onFileChange" />
            <button type="button" class="app-button app-button-secondary w-full" @click="pickFile"
              :disabled="buildPhase === 'uploading'">
              {{ fileName ? '已选：' + fileName : '选择小说文件' }}
            </button>
            <input v-model="apiKey" type="password" @input="onKeyInput" autocomplete="off"
              placeholder="你的 DeepSeek API Key（sk-...）" class="app-input" />
            <button type="button" class="app-button app-button-primary w-full" @click="buildWorld"
              :disabled="buildPhase === 'uploading'">
              {{ buildPhase === 'uploading' ? '⏳ 正在生成世界框架…' : '✨ 生成世界框架' }}
            </button>
            <p v-if="buildMsg" :style="{ color: buildPhase === 'error' ? 'var(--danger)' : 'var(--success)' }"
              class="text-xs leading-relaxed">{{ buildMsg }}</p>
          </div>

          <!-- 我的世界列表 -->
          <template v-if="worlds.mine.length">
            <WorldListItem v-for="w in worlds.mine" :key="w.id" :world="w" mine
              :save="saveForWorld(w.id)" :cover="worldCover(w)" :deleting="deleting === w.id"
              @enter="enterWorld(w)" @continue="continueSave" @remove="delWorld" @preview="openCover(w)" />
          </template>
          <p v-else-if="!showWorldBuilder" class="home-empty">
            还没有自建世界——上传一本你喜欢的小说，AI 会帮你搭出它的世界框架。
          </p>
        </section>

        <!-- ── 继续冒险（首页快捷存档入口） ── -->
        <section v-if="quickSave" class="mt-8">
          <div class="flex items-center justify-between mb-3">
            <h2 class="app-section-title">继续冒险</h2>
            <button type="button" class="text-xs app-muted hover:text-primary transition"
              @click="emit('continue')">全部存档 ›</button>
          </div>
          <button type="button" class="home-recent-save" @click="continueSave(quickSave)">
            <div class="home-recent-save-main">
              <p class="world-row-title">{{ quickSave.name }}</p>
              <p class="text-xs app-muted mt-0.5 truncate">
                {{ quickSave.world_name }} · {{ quickSave.place }} · 第{{ quickSave.turn }}回合 · {{ quickSave.date }}
              </p>
            </div>
            <span class="home-recent-save-arrow" aria-hidden="true">继续 ›</span>
          </button>
        </section>
      </div>
    </div>

    <!-- 底部导航 -->
    <nav class="home-bottom-nav" aria-label="主导航">
      <button type="button" class="home-bottom-nav-item" aria-current="page" aria-label="首页">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M3 10.5 12 3l9 7.5" /><path d="M5 9.5V21h14V9.5" /></svg>
        <span>首页</span>
      </button>
      <button type="button" class="home-bottom-nav-item" @click="emit('continue')" aria-label="存档">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3h9l3 3v15H6z" /><path d="M9 3v6h6V3" /></svg>
        <span>存档</span>
      </button>
      <button type="button" class="home-bottom-nav-item" @click="emit('open-settings')" aria-label="设置">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3" /><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M19.1 4.9 17 7M7 17l-2.1 2.1" /></svg>
        <span>设置</span>
      </button>
    </nav>

    <CoverLightbox :open="!!previewCover" :src="previewCover?.src || ''" :title="previewCover?.title || ''"
      @close="closeCover" />
  </div>
</template>
