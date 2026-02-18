<script setup>
defineProps({
  label: String,
  description: String,
  readonly: {
    type: Boolean,
    default: false
  }
})

defineEmits(['click'])
</script>

<template>
  <div 
    class="setting-item" 
    :class="{ readonly }"
    @click="!readonly && $emit('click')"
  >
    <div class="setting-info">
      <div class="setting-icon">
        <slot name="icon" />
      </div>
      <div class="setting-text">
        <span class="setting-label">{{ label }}</span>
        <span class="setting-value">
          <slot name="value">{{ description }}</slot>
        </span>
      </div>
    </div>
    <div class="setting-action">
      <slot name="action" />
    </div>
  </div>
</template>

<style scoped>
.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  cursor: pointer;
  transition: background 0.15s;
}

.setting-item:not(:last-child) {
  border-bottom: 1px solid var(--glass-border);
}

.setting-item:hover:not(.readonly) {
  background: var(--overlay-lighter);
}

.setting-item.readonly {
  cursor: default;
}

.setting-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.setting-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: var(--overlay-lighter);
  border-radius: 10px;
  color: var(--text-secondary);
}

.setting-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.setting-label {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.setting-value {
  font-size: 13px;
  color: var(--text-muted);
}
</style>
