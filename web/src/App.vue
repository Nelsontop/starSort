<script setup>
import { ref, computed, onMounted } from 'vue'
import NavBar from './components/NavBar.vue'
import CategoryFilter from './components/CategoryFilter.vue'
import ContentArea from './components/ContentArea.vue'
import FooterBand from './components/FooterBand.vue'

const data = ref({ categories: [], stars: [], last_updated: '' })
const searchQuery = ref('')
const selectedCategory = ref(null)
const selectedLanguage = ref(null)

onMounted(async () => {
  const res = await fetch('/stars.json')
  data.value = await res.json()
})

const languages = computed(() => {
  const langs = new Set(data.value.stars.map(s => s.language).filter(Boolean))
  return [...langs].sort()
})

const filteredStars = computed(() => {
  let stars = data.value.stars
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    stars = stars.filter(s =>
      s.full_name.toLowerCase().includes(q) ||
      s.description.toLowerCase().includes(q)
    )
  }
  if (selectedCategory.value) {
    stars = stars.filter(s => s.categories.includes(selectedCategory.value))
  }
  if (selectedLanguage.value) {
    stars = stars.filter(s => s.language === selectedLanguage.value)
  }
  return stars
})

const filteredCategories = computed(() => {
  return data.value.categories.map(c => ({
    ...c,
    stars: filteredStars.value.filter(s => s.categories.includes(c.id))
  })).filter(c => c.stars.length > 0 || !selectedCategory.value)
})

function selectCategory(id) {
  selectedCategory.value = selectedCategory.value === id ? null : id
}

function clearFilters() {
  searchQuery.value = ''
  selectedCategory.value = null
  selectedLanguage.value = null
}
</script>

<template>
  <div class="app">
    <NavBar
      :search-query="searchQuery"
      :selected-language="selectedLanguage"
      :languages="languages"
      :total-count="filteredStars.length"
      @update:search-query="searchQuery = $event"
      @update:selected-language="selectedLanguage = $event"
      @clear="clearFilters"
    />
    <div class="app-body">
      <CategoryFilter
        :categories="data.categories"
        :selected="selectedCategory"
        @select="selectCategory"
      />
      <ContentArea :categories="filteredCategories" :stars="filteredStars" />
    </div>
    <FooterBand :last-updated="data.last_updated" />
  </div>
</template>

<style scoped>
.app {
  background-color: var(--color-canvas);
  min-height: 100vh;
  color: var(--color-ink);
}

.app-body {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--sp-xl);
}

@media (max-width: 768px) {
  .app-body {
    padding: var(--sp-lg);
  }
}
</style>
