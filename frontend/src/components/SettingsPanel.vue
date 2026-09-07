<script setup>
import { ref, computed } from 'vue'
import { api } from '../api'
import { ui, draft, updateThemeSettings, updateBackgroundImage, setFreedom, clientId, loadWorlds, entitlement, fmtDate, setActivationOpen } from '../store'

const emit = defineEmits(['close'])

const fileInput = ref(null)   // 隐藏的文件选择框
const bgBusy = ref(false)     // 图片压缩处理中
const bgError = ref('')       // 上传/压缩错误提示

// 四个可折叠分组：默认都收起
const themeOpen = ref(false)    // 「主题」分组
const freedomOpen = ref(false)  // 「文字数量」分组
const dataOpen = ref(false)     // 「数据管理」分组
const subOpen = ref(false)      // 「订阅」分组

// 自由度（文字数量）五档：200 ~ 2000 字
const FREEDOM_TIERS = [
  { value: 1, label: '精炼', chars: 200, note: '短小精悍，快节奏推进' },
  { value: 2, label: '简洁', chars: 500, note: '适度展开，节奏较快' },
  { value: 3, label: '标准', chars: 1000, note: '剧情适中 · 默认' },
  { value: 4, label: '详尽', chars: 1500, note: '细节丰富，沉浸感强' },
  { value: 5, label: '极尽', chars: 2000, note: '事无巨细，最长生成' },
]

// 调色盘：只改主题色，字号维持当前值
function onColorInput(e) {
  updateThemeSettings(e.target.value, ui.baseFontSize)
}

// 滑块：只改字号，主题色维持当前值
function onSizeInput(e) {
  updateThemeSettings(ui.themeColor, Number(e.target.value))
}

// 读取并压缩图片为背景图 data URL：等比限宽 1920px、JPEG 质量 0.8，控制体积
async function fileToBgDataUrl(file) {
  const raw = await new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = () => reject(new Error('读取图片失败'))
    reader.readAsDataURL(file)
  })
  const img = await new Promise((resolve, reject) => {
    const image = new Image()
    image.onload = () => resolve(image)
    image.onerror = () => reject(new Error('图片解码失败'))
    image.src = raw
  })
  const MAX_W = 1920
  const scale = Math.min(1, MAX_W / (img.naturalWidth || 1))
  const w = Math.max(1, Math.round(img.naturalWidth * scale))
  const h = Math.max(1, Math.round(img.naturalHeight * scale))
  const canvas = document.createElement('canvas')
  canvas.width = w
  canvas.height = h
  const ctx = canvas.getContext('2d')
  ctx.drawImage(img, 0, 0, w, h)
  return canvas.toDataURL('image/jpeg', 0.8)
}

async function onFileChange(e) {
  const file = e.target.files && e.target.files[0]
  e.target.value = ''          // 允许重复选择同一文件
  if (!file) return
  if (!file.type.startsWith('image/')) {
    bgError.value = '请选择图片文件'
    return
  }
  bgError.value = ''
  bgBusy.value = true
  try {
    const dataUrl = await fileToBgDataUrl(file)
    updateBackgroundImage(dataUrl)
  } catch (err) {
    bgError.value = err.message || '处理图片失败'
  } finally {
    bgBusy.value = false
  }
}

function clearBgImage() {
  bgError.value = ''
  updateBackgroundImage('')
}

// ── 数据管理：导出 / 导入 / 刷新 ─────────────────────────
const exporting = ref(false)
const dataMsg = ref('')
const dataMsgType = ref('ok')  // 'ok' | 'err'

async function exportData() {
  if (exporting.value) return
  exporting.value = true
  dataMsg.value = ''
  try {
    const blob = await api.exportAll({ client_id: clientId() })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const ts = new Date().toISOString().slice(0, 10).replace(/-/g, '')
    a.download = `万界人生模拟器-备份-${ts}.json`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
    dataMsg.value = '导出成功，请妥善保存文件'
    dataMsgType.value = 'ok'
  } catch (e) {
    dataMsg.value = '导出失败：' + e.message
    dataMsgType.value = 'err'
  } finally { exporting.value = false }
}

async function importData(e) {
  const f = e.target.files?.[0]
  if (!f) return
  dataMsg.value = '正在导入…'
  dataMsgType.value = 'ok'
  try {
    const fd = new FormData()
    fd.append('file', f)
    fd.append('client_id', clientId())
    const r = await api.importAll(fd)
    const parts = []
    if (r.worlds_imported) parts.push(`${r.worlds_imported} 个世界`)
    if (r.saves_imported) parts.push(`${r.saves_imported} 个存档`)
    const skipped = (r.worlds_skipped || 0) + (r.saves_skipped || 0)
    let msg = parts.length ? `已恢复 ${parts.join('、')}` : '没有新数据可导入'
    if (skipped) msg += `，${skipped} 项已存在已跳过`
    dataMsg.value = msg
    dataMsgType.value = 'ok'
    await loadWorlds()
  } catch (e) {
    dataMsg.value = '导入失败：' + e.message
    dataMsgType.value = 'err'
  }
  e.target.value = ''
}

function refreshPage() {
  window.location.reload()
}

// ── 订阅状态文本 ─────────────────────────
const statusText = computed(() => {
  if (entitlement.loading) return '加载中…'
  if (entitlement.paid) return `已订阅 · 无限游玩（至 ${fmtDate(entitlement.paidUntil)}）`
  const left = Math.max(0, entitlement.trialLimit - entitlement.trialUsed)
  return `免费试玩中 · 剩余 ${left} 回合 · 1元/月无限玩`
})

// 打开订阅/激活码面板：先关设置面板，避免两层 z-50 弹窗重叠
function openActivation() {
  setActivationOpen(true)
  emit('close')
}
</script>

<template>
  <div class="app-modal-backdrop"
    @click.self="emit('close')">
    <div class="app-modal app-settings-panel">
      <div class="app-sheet-header">
        <h2>设置</h2>
        <button type="button" @click="emit('close')"
          class="app-icon-button" aria-label="关闭设置">
          ×
        </button>
      </div>

      <!-- 主题分组（可折叠） -->
      <section class="app-settings-section">
        <button type="button" @click="themeOpen = !themeOpen"
          class="flex w-full items-center justify-between rounded-md px-2 py-1.5 text-sm text-stone-200 transition hover:bg-stone-800 hover:text-amber-200">
          <span class="font-medium">主题</span>
          <span class="text-xs text-stone-500">{{ themeOpen ? '▾' : '▸' }}</span>
        </button>
        <div v-if="themeOpen" class="mt-3 space-y-5 px-2">
          <!-- 主题色 -->
          <div>
            <label for="theme-color" class="mb-2 block text-sm text-stone-300">主题色</label>
            <div class="flex items-center gap-3">
              <input id="theme-color" type="color" :value="ui.themeColor" @input="onColorInput"
                class="h-10 w-16 cursor-pointer rounded border border-stone-700 bg-stone-800 p-1" />
              <span class="font-mono text-xs text-stone-400">{{ ui.themeColor }}</span>
            </div>
          </div>

          <!-- 背景图 -->
          <div>
            <label class="mb-2 block text-sm text-stone-300">背景图</label>
            <div class="flex items-center gap-3">
              <button type="button" :disabled="bgBusy" @click="fileInput.click()"
                class="px-3 py-1.5 rounded border border-stone-700 text-sm text-stone-300 transition hover:border-primary hover:text-primary disabled:opacity-50">
                {{ bgBusy ? '处理中…' : (ui.bgImage ? '更换图片' : '上传图片') }}
              </button>
              <button v-if="ui.bgImage" type="button" @click="clearBgImage"
                class="px-3 py-1.5 rounded border border-stone-700 text-sm text-stone-400 transition hover:border-red-500/50 hover:text-red-400">
                清除
              </button>
              <input ref="fileInput" type="file" accept="image/*" class="hidden" @change="onFileChange" />
            </div>
            <p class="mt-2 text-[11px] leading-relaxed text-stone-500">
              支持常见图片格式；上传后自动等比压缩以节省空间，并叠加暗色遮罩保证文字可读。
            </p>
            <p v-if="bgError" class="mt-1 text-[11px] text-red-400">{{ bgError }}</p>
            <div v-if="ui.bgImage" class="mt-2 overflow-hidden rounded border border-stone-700">
              <img :src="ui.bgImage" alt="背景预览" class="h-20 w-full object-cover" />
            </div>
          </div>

          <!-- 字体大小 -->
          <div>
            <label for="font-size" class="mb-2 block text-sm text-stone-300">
              字体大小 <span class="font-mono text-amber-400">{{ ui.baseFontSize }}px</span>
            </label>
            <input id="font-size" type="range" min="12" max="24" step="1" :value="ui.baseFontSize" @input="onSizeInput"
              class="w-full accent-primary" />
            <div class="mt-1 flex justify-between text-[11px] text-stone-500">
              <span>小 · 12</span>
              <span>大 · 24</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 文字数量分组（可折叠） -->
      <section class="app-settings-section">
        <button type="button" @click="freedomOpen = !freedomOpen"
          class="flex w-full items-center justify-between rounded-md px-2 py-1.5 text-sm text-stone-200 transition hover:bg-stone-800 hover:text-amber-200">
          <span class="font-medium">文字数量</span>
          <span class="text-xs text-stone-500">{{ freedomOpen ? '▾' : '▸' }}</span>
        </button>
        <div v-if="freedomOpen" class="mt-3 px-2">
          <div class="space-y-1.5">
            <button v-for="t in FREEDOM_TIERS" :key="t.value" type="button" @click="setFreedom(t.value)"
              class="w-full flex items-center justify-between gap-2 px-3 py-2 rounded text-sm transition"
              :class="draft.freedom === t.value
                ? 'border border-primary bg-amber-900/50 text-amber-100'
                : 'border border-stone-700 text-stone-300 hover:bg-stone-800'">
              <span class="font-medium">{{ t.label }} <span class="text-xs text-stone-500">· {{ t.chars }}字</span></span>
              <span class="text-xs text-stone-500 text-right shrink-0">{{ t.note }}</span>
            </button>
          </div>
          <p class="mt-2 text-[11px] leading-relaxed text-stone-500">
            决定每次选择后 AI 生成的剧情文字多少：档位越高文字越长、细节越丰富，生成耗时也相应增加。
          </p>
        </div>
      </section>

      <!-- 数据管理分组（可折叠） -->
      <section class="app-settings-section">
        <button type="button" @click="dataOpen = !dataOpen"
          class="flex w-full items-center justify-between rounded-md px-2 py-1.5 text-sm text-stone-200 transition hover:bg-stone-800 hover:text-amber-200">
          <span class="font-medium">数据管理</span>
          <span class="text-xs text-stone-500">{{ dataOpen ? '▾' : '▸' }}</span>
        </button>
        <div v-if="dataOpen" class="mt-3 px-2">
          <div class="space-y-2">
            <button type="button" @click="exportData" :disabled="exporting"
              class="w-full px-3 py-2 rounded border border-stone-700 text-sm text-stone-300 transition hover:border-primary hover:text-primary disabled:opacity-50">
              {{ exporting ? '⏳ 导出中…' : '📥 导出数据' }}
            </button>
            <label class="block w-full px-3 py-2 rounded border border-stone-700 text-sm text-stone-300 text-center transition hover:border-primary hover:text-primary cursor-pointer">
              📤 导入数据
              <input type="file" accept=".json" @change="importData" class="hidden" />
            </label>
            <button type="button" @click="refreshPage"
              class="w-full px-3 py-2 rounded border border-stone-700 text-sm text-stone-300 transition hover:border-primary hover:text-primary">
              🔄 刷新页面
            </button>
          </div>
          <p v-if="dataMsg" :class="[
            'mt-2 px-3 py-2 rounded border text-[11px] leading-relaxed',
            dataMsgType === 'err'
              ? 'bg-red-900/40 border-red-800 text-red-200'
              : 'bg-emerald-900/40 border-emerald-800 text-emerald-100'
          ]">{{ dataMsg }}</p>
          <p class="mt-2 text-[11px] leading-relaxed text-stone-500">
            导出为 JSON 备份文件；浏览器清缓存或换设备后，可通过导入恢复世界与存档。
          </p>
        </div>
      </section>

      <!-- 订阅分组（可折叠） -->
      <section class="app-settings-section">
        <button type="button" @click="subOpen = !subOpen"
          class="flex w-full items-center justify-between rounded-md px-2 py-1.5 text-sm text-stone-200 transition hover:bg-stone-800 hover:text-amber-200">
          <span class="font-medium">订阅</span>
          <span class="text-xs text-stone-500">{{ subOpen ? '▾' : '▸' }}</span>
        </button>
        <div v-if="subOpen" class="mt-3 px-2">
          <button type="button" @click="openActivation"
            class="w-full px-3 py-2 rounded border border-stone-700 text-sm text-stone-300 transition hover:border-primary hover:text-primary">
            💳 订阅 / 激活码
          </button>
          <p class="mt-2 text-[11px] leading-relaxed text-stone-500">{{ statusText }}</p>
        </div>
      </section>
    </div>
  </div>
</template>
