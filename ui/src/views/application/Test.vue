<script setup>
// 测试数据
const testValue = "likedValues_test"
</script>

<template>
  <div class="test-container">
    <div class="glass-panel">
      {{ testValue }}
    </div>
  </div>
</template>

<style scoped>
.test-container {
  padding: 30px;
  min-height: calc(100vh - 70px);
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
}

.glass-panel {
  background: rgba(15, 15, 15, 0.6);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  padding: 40px;
  color: #10b981;
  font-size: 24px;
  font-weight: 600;
  letter-spacing: 2px;
}
</style>