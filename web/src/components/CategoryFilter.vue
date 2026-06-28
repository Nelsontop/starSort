<script setup>
defineProps({
  categories: Array,
  selected: String,
})

defineEmits(['select'])

function tintColor(tint) {
  const map = {
    olive: '#8e8a25', sage: '#b3bd95', salmon: '#d77a7a', peach: '#e6915d',
    lime: '#c0d4a7', sky: '#9ab6c8', steel: '#a5b8c0', periwinkle: '#8c9ae0',
  }
  return map[tint] || 'var(--color-hairline)'
}
</script>

<template>
  <section class="category-filter">
    <span class="filter-eyebrow eyebrow-mono">Categories</span>
    <div class="pill-row">
      <button
        class="filter-pill"
        :class="{ active: selected === null }"
        @click="$emit('select', null)"
      >ALL</button>
      <button
        v-for="cat in categories"
        :key="cat.id"
        class="filter-pill"
        :class="{ active: selected === cat.id }"
        :style="{ borderColor: selected === cat.id ? tintColor(cat.tint) : undefined }"
        @click="$emit('select', cat.id)"
      >
        <span class="pill-dot" :style="{ backgroundColor: tintColor(cat.tint) }"></span>
        {{ cat.name }}
        <span class="pill-count">{{ cat.count }}</span>
      </button>
    </div>
  </section>
</template>

<style scoped>
.category-filter {
  margin-bottom: var(--sp-xl);
}

.filter-eyebrow {
  color: var(--color-ink);
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 400;
  letter-spacing: 1.4px;
  text-transform: uppercase;
  display: block;
  margin-bottom: var(--sp-md);
}

.pill-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-sm);
}

.filter-pill {
  display: flex;
  align-items: center;
  gap: var(--sp-xs);
  background: transparent;
  color: var(--color-body-mid);
  border: 1px solid var(--color-hairline);
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 400;
  padding: var(--sp-sm) var(--sp-lg);
  border-radius: var(--radius-pill);
  cursor: pointer;
}

.filter-pill:hover {
  background: var(--color-canvas-soft);
}

.filter-pill.active {
  background: var(--color-primary);
  color: var(--color-on-primary);
  border-color: var(--color-primary);
}

.pill-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.pill-count {
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 1.2px;
  opacity: 0.7;
}
</style>
