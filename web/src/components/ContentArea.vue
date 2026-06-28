<script setup>
import CategorySection from './CategorySection.vue'

defineProps({
  categories: Array,
})
</script>

<template>
  <div class="content-area">
    <CategorySection
      v-for="cat in categories"
      :key="cat.id"
      :category="cat"
    />
    <div v-if="!categories.length" class="empty-state">
      <div class="empty-card">
        <p class="empty-text">No projects match your filters.</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.content-area {
  min-height: 40vh;
}

.empty-state {
  display: flex;
  justify-content: center;
  padding: var(--sp-4xl) var(--sp-xl);
}

.empty-card {
  background-color: var(--color-canvas-soft);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-sm);
  padding: var(--sp-3xl);
  text-align: center;
}

.empty-text {
  color: var(--color-body-mid);
  font-size: 16px;
  font-family: var(--font-body);
}
</style>
