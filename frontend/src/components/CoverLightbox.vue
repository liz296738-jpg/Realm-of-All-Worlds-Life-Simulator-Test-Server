<script setup>
import { computed, nextTick, onUnmounted, ref, watch } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  src: { type: String, default: '' },
  title: { type: String, default: '' },
})
const emit = defineEmits(['close'])

const MIN_ZOOM = 1
const MAX_ZOOM = 4
const ZOOM_STEP = 0.25
const zoom = ref(MIN_ZOOM)
const x = ref(0)
const y = ref(0)
const dragging = ref(false)
const closeButton = ref(null)
let startPointerX = 0
let startPointerY = 0
let startX = 0
let startY = 0
let originalBodyOverflow = ''
let bodyLocked = false

const imageStyle = computed(() => ({
  transform: `translate3d(${x.value}px, ${y.value}px, 0) scale(${zoom.value})`,
}))

function reset() {
  zoom.value = MIN_ZOOM
  x.value = 0
  y.value = 0
  dragging.value = false
}

function zoomIn() { zoom.value = Math.min(MAX_ZOOM, zoom.value + ZOOM_STEP) }
function zoomOut() { zoom.value = Math.max(MIN_ZOOM, zoom.value - ZOOM_STEP) }
function close() { emit('close') }

function onPointerDown(event) {
  if (zoom.value <= MIN_ZOOM) return
  dragging.value = true
  startPointerX = event.clientX
  startPointerY = event.clientY
  startX = x.value
  startY = y.value
  event.currentTarget.setPointerCapture?.(event.pointerId)
}

function onPointerMove(event) {
  if (!dragging.value) return
  x.value = startX + event.clientX - startPointerX
  y.value = startY + event.clientY - startPointerY
}

function onPointerUp(event) {
  if (!dragging.value) return
  dragging.value = false
  event.currentTarget.releasePointerCapture?.(event.pointerId)
}

function onKeydown(event) {
  if (event.key === 'Escape') close()
  else if (event.key === '+' || event.key === '=') zoomIn()
  else if (event.key === '-') zoomOut()
  else if (event.key === '0') reset()
}

function lockBody() {
  originalBodyOverflow = document.body.style.overflow
  document.body.style.overflow = 'hidden'
  bodyLocked = true
}

function unlockBody() {
  if (!bodyLocked) return
  document.body.style.overflow = originalBodyOverflow
  bodyLocked = false
}

function activate() {
  reset()
  lockBody()
  window.addEventListener('keydown', onKeydown)
  window.addEventListener('resize', reset)
  nextTick(() => closeButton.value?.focus())
}

function deactivate() {
  reset()
  unlockBody()
  window.removeEventListener('keydown', onKeydown)
  window.removeEventListener('resize', reset)
}

watch(() => props.open, open => { if (open) activate(); else deactivate() })
watch(() => props.src, () => { if (props.open) reset() })
onUnmounted(deactivate)
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="cover-lightbox" role="dialog" aria-modal="true"
      :aria-label="`${title} 封面预览`" @click.self="close">
      <header class="cover-lightbox-header">
        <h2>{{ title }}</h2>
        <button ref="closeButton" type="button" class="app-icon-button cover-lightbox-close"
          aria-label="关闭封面预览" @click="close">×</button>
      </header>

      <div class="cover-lightbox-viewport" :class="{ 'is-dragging': dragging, 'is-zoomed': zoom > MIN_ZOOM }"
        @pointerdown="onPointerDown" @pointermove="onPointerMove" @pointerup="onPointerUp" @pointercancel="onPointerUp">
        <img :src="src" :alt="`${title} 世界封面`" class="cover-lightbox-image" :style="imageStyle" draggable="false" />
      </div>

      <div class="cover-lightbox-controls" aria-label="封面缩放控制">
        <button type="button" class="app-button app-button-ghost" :disabled="zoom === MIN_ZOOM" @click="zoomOut">−</button>
        <output>{{ Math.round(zoom * 100) }}%</output>
        <button type="button" class="app-button app-button-ghost" :disabled="zoom === MAX_ZOOM" @click="zoomIn">+</button>
        <button type="button" class="app-button app-button-secondary" @click="reset">还原</button>
      </div>
    </div>
  </Teleport>
</template>
