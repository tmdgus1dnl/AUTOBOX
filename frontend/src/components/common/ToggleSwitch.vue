<script setup>
const model = defineModel({ type: Boolean, default: false })
</script>

<template>
  <div class="toggle-switch" :class="{ active: model }" @click="model = !model">
    <div class="toggle-thumb"></div>
  </div>
</template>

<style scoped>
.toggle-switch {
  width: 50px;
  height: 28px;
  background: var(--overlay-dark);
  border-radius: 14px;
  padding: 3px;
  transition: all 0.2s;
  cursor: pointer;
}

.toggle-switch.active {
  background: var(--color-primary);
}

.toggle-thumb {
  width: 22px;
  height: 22px;
  background: white;
  border-radius: 50%;
  transition: transform 0.2s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.toggle-switch.active .toggle-thumb {
  transform: translateX(22px);
}
</style>
