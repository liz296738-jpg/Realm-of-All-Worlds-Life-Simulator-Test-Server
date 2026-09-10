<script setup>
import { computed } from 'vue'
import { draft, DEFAULT_WUHUN } from '../store'

const props = defineProps({
  archive: { type: Object, default: null },
  world: { type: Object, default: null },
})
const emit = defineEmits(['confirm', 'back'])

const TALENT_NOTE = {
  '凡人档': '先天 1-3 · 前期吃瘪，逆袭感最强',
  '普通魂师档': '先天 4-6 · 白灵藤品质上下',
  '天才档': '先天 7-9 · 顶级武魂级别',
  '怪物档': '先天 9-10 · 慎选，开局不超大陆顶级天才范围',
}

// 自建世界（非魂兽大陆）：档案来自 GenericWizard，用 world.creation_schema 的 label 展示
const isGeneric = computed(() => props.world && props.world.id !== 'douluo')

const card = computed(() => ({
  name: draft.name || '无名',
  gender: draft.gender,
  age: draft.age,
  identity: draft.identity + (draft.identityNote ? `（${draft.identityNote}）` : ''),
  wuhun: `${draft.wuhun || DEFAULT_WUHUN}（${draft.wuhunType}）`,
  innate: draft.innateSoulPower ?? '—',
  talent: draft.talentTier ? `${draft.talentTier} · ${TALENT_NOTE[draft.talentTier]}` : '未选',
  direction: draft.developmentDirection,
  origin: `${draft.origin} · ${draft.background || '平民'}`,
  family: draft.family || '—',
  secret: draft.secret || '无',
  traits: draft.traits || '—',
  personality: draft.personality || '—',
  desire: draft.desire,
  playDirection: draft.direction,
  binding: draft.timelineBinding,
  gold: draft.gold ?? '按出身',
  items: draft.specialItems || '无',
}))

// 通用世界档案展示：label 取自 creation_schema，空值跳过
const genericRows = computed(() => {
  const labels = {}
  for (const st of props.world?.creation_schema?.steps || []) {
    for (const f of st.fields || []) labels[f.key] = f.label || f.key
  }
  const ch = props.archive?.character || {}
  return Object.entries(ch)
    .filter(([, v]) => v !== undefined && v !== null && v !== '' && !(Array.isArray(v) && v.length === 0))
    .map(([k, v]) => ({
      label: labels[k] || k,
      value: Array.isArray(v) ? v.join('、') : String(v),
    }))
})
</script>

<template>
  <div class="app-flow max-w-xl mx-auto px-4 py-8">
    <div class="app-character-review p-6">
      <h2 class="text-center text-2xl font-bold text-stone-100 mb-1">你的角色</h2>
      <p class="text-center text-sm text-stone-500 mb-6">
        {{ isGeneric ? `确认后，你在「${world.name}」的旅程正式开始` : '确认后，你的魂兽大陆之行正式开始' }}
      </p>

      <!-- 通用世界（自建）：按 creation_schema 字段展示 -->
      <dl v-if="isGeneric" class="space-y-2 text-sm">
        <div v-for="row in genericRows" :key="row.label"
          class="app-character-row">
          <dt class="app-character-label">{{ row.label }}</dt>
          <dd class="app-character-value">{{ row.value }}</dd>
        </div>
      </dl>

      <!-- 魂兽大陆：专属档案卡 -->
      <dl v-else class="space-y-2 text-sm">
        <div class="app-character-row"><dt class="app-character-label">姓名</dt><dd class="app-character-value">{{ card.name }}（{{ card.gender }}，{{ card.age }}岁）</dd></div>
        <div class="app-character-row"><dt class="app-character-label">身份</dt><dd class="app-character-value">{{ card.identity }}</dd></div>
        <div class="app-character-row"><dt class="app-character-label">武魂</dt><dd class="app-character-value">{{ card.wuhun }}</dd></div>
        <div class="app-character-row"><dt class="app-character-label">天赋</dt><dd class="app-character-value">{{ card.talent }}，先天魂力 {{ card.innate }}</dd></div>
        <div class="app-character-row"><dt class="app-character-label">发展方向</dt><dd class="app-character-value">{{ card.direction }}</dd></div>
        <div class="app-character-row"><dt class="app-character-label">出身</dt><dd class="app-character-value">{{ card.origin }}</dd></div>
        <div class="app-character-row"><dt class="app-character-label">家庭</dt><dd class="app-character-value">{{ card.family }}</dd></div>
        <div class="app-character-row"><dt class="app-character-label">执念/秘密</dt><dd class="app-character-value">{{ card.secret }}</dd></div>
        <div class="app-character-row"><dt class="app-character-label">外貌</dt><dd class="app-character-value">{{ card.traits }}</dd></div>
        <div class="app-character-row"><dt class="app-character-label">性格</dt><dd class="app-character-value">{{ card.personality }}</dd></div>
        <div class="app-character-row"><dt class="app-character-label">变强渴望</dt><dd class="app-character-value">{{ card.desire }}/10</dd></div>
        <div class="app-character-row"><dt class="app-character-label">游玩方向</dt><dd class="app-character-value">{{ card.playDirection }}</dd></div>
        <div class="app-character-row"><dt class="app-character-label">时间线绑定</dt><dd class="app-character-value">{{ card.binding }}</dd></div>
        <div class="app-character-row"><dt class="app-character-label">初始财富</dt><dd class="app-character-value">{{ card.gold }} 金魂币</dd></div>
        <div class="app-character-row"><dt class="app-character-label">特殊物品</dt><dd class="app-character-value">{{ card.items }}</dd></div>
      </dl>
      <div class="mt-8 flex gap-3">
        <button @click="emit('back')" class="app-button app-button-secondary flex-1">返回修改</button>
        <button @click="emit('confirm')" class="app-button app-button-primary flex-1">开始人生</button>
      </div>
    </div>
  </div>
</template>
