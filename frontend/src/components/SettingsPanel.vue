<script setup>
import { ref } from 'vue'
import { ui, updateThemeSettings, updateBackgroundImage } from '../store'

const emit = defineEmits(['close'])

const fileInput = ref(null)   // 隐藏的文件选择框
const bgBusy = ref(false)     // 图片压缩处理中
const bgError = ref('')       // 上传/压缩错误提示

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
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4"
    @click.self="emit('close')">
    <div class="w-full max-w-sm rounded-xl border border-stone-700 bg-stone-900/95 p-5 shadow-2xl backdrop-blur">
      <div class="mb-5 flex items-center justify-between">
        <h2 class="font-medium text-amber-200">外观设置</h2>
        <button type="button" @click="emit('close')"
          class="text-lg leading-none text-stone-500 transition hover:text-stone-300">✕</button>
      </div>

      <!-- 主题色 -->
      <div class="mb-5">
        <label for="theme-color" class="mb-2 block text-sm text-stone-300">主题色</label>
        <div class="flex items-center gap-3">
          <input id="theme-color" type="color" :value="ui.themeColor" @input="onColorInput"
            class="h-10 w-16 cursor-pointer rounded border border-stone-700 bg-stone-800 p-1" />
          <span class="font-mono text-xs text-stone-400">{{ ui.themeColor }}</span>
        </div>
      </div>

      <!-- 背景图 -->
      <div class="mb-5">
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
  </div>
</template>
