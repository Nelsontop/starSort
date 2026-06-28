<script setup>
defineProps({
  searchQuery: String,
  selectedLanguage: String,
  languages: Array,
  totalCount: Number,
})

defineEmits(['update:search-query', 'update:selected-language', 'clear'])
</script>

<template>
  <nav class="nav-bar">
    <div class="nav-left">
      <span class="nav-eyebrow eyebrow-mono">STAR SORT</span>
      <h1 class="nav-title">My GitHub Stars</h1>
      <span class="nav-count">{{ totalCount }} projects</span>
    </div>
    <div class="nav-controls">
      <input
        type="text"
        class="search-input"
        placeholder="Search..."
        :value="searchQuery"
        @input="$emit('update:search-query', $event.target.value)"
      />
      <select
        class="lang-select"
        :value="selectedLanguage || ''"
        @change="$emit('update:selected-language', $event.target.value || null)"
      >
        <option value="">All Languages</option>
        <option v-for="lang in languages" :key="lang" :value="lang">{{ lang }}</option>
      </select>
      <button class="btn-pill btn-outline" @click="$emit('clear')">CLEAR</button>
    </div>
  </nav>
</template>

<style scoped>
.nav-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--sp-md) var(--sp-xl);
  background-color: var(--color-canvas);
  border-bottom: 1px solid var(--color-hairline);
  position: sticky;
  top: 0;
  z-index: 10;
}

.nav-left {
  display: flex;
  align-items: baseline;
  gap: var(--sp-md);
}

.nav-eyebrow {
  color: var(--color-ink);
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 400;
  letter-spacing: 1.4px;
  text-transform: uppercase;
}

.nav-title {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 400;
  letter-spacing: -0.3px;
}

.nav-count {
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 1.2px;
  text-transform: uppercase;
  color: var(--color-body-mid);
}

.nav-controls {
  display: flex;
  gap: var(--sp-sm);
  align-items: center;
}

.search-input {
  width: 200px;
}

.lang-select {
  min-width: 140px;
}

.btn-outline {
  background: transparent;
  color: var(--color-ink);
  border: 1px solid var(--color-hairline);
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 400;
  padding: var(--sp-sm) var(--sp-lg);
  border-radius: var(--radius-pill);
  cursor: pointer;
}

.btn-outline:hover {
  background: var(--color-canvas-soft);
}

@media (max-width: 768px) {
  .nav-bar {
    flex-direction: column;
    gap: var(--sp-md);
  }
  .nav-controls {
    flex-wrap: wrap;
  }
  .search-input {
    width: 100%;
  }
}
</style>
