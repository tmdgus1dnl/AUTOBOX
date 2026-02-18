<script setup>
import { ref } from 'vue'

const props = defineProps({
  title: String,
  icon: String
})

const url = defineModel('url', { type: String, default: '' })
const path = defineModel('path', { type: String, default: '' })
const ip = defineModel('ip', { type: String, default: '' })
const port = defineModel('port', { type: String, default: '' })
const topic = defineModel('topic', { type: String, default: '' })

const isConnected = ref(false)
const isTesting = ref(false)

const emit = defineEmits(['test'])

const handleTest = () => {
  emit('test')
}
</script>

<template>
  <section class="settings-section">
    <h2 class="section-title">
      <slot name="icon" />
      {{ title }}
    </h2>
    <div class="settings-card">
      <slot />
    </div>
  </section>
</template>

<style scoped>
.settings-section {
  margin-bottom: 28px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0 0 12px 4px;
}

.settings-card {
  background: var(--glass-panel);
  backdrop-filter: blur(var(--blur-amount));
  border: 1px solid var(--glass-border);
  border-radius: 16px;
  overflow: hidden;
}
</style>
