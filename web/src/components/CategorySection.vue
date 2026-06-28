<script setup>
import StarCard from './StarCard.vue'

defineProps({
  category: Object,
})
</script>

<template>
  <section class="category-section" v-if="category.stars?.length">
    <div class="section-header">
      <span class="section-eyebrow eyebrow-mono">{{ category.name }}</span>
      <span class="section-count">{{ category.stars.length }} projects</span>
    </div>
    <div class="card-grid">
      <StarCard
        v-for="star in category.stars"
        :key="star.full_name"
        :star="star"
      />
    </div>
  </section>
</template>

<style scoped>
.category-section {
  margin-bottom: var(--sp-3xl);
}

.section-header {
  display: flex;
  align-items: baseline;
  gap: var(--sp-md);
  margin-bottom: var(--sp-lg);
}

.section-eyebrow {
  color: var(--color-ink);
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 400;
  letter-spacing: 1.4px;
  text-transform: uppercase;
}

.section-count {
  color: var(--color-body-mid);
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 1.2px;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: var(--sp-lg);
}

@media (max-width: 480px) {
  .card-grid {
    grid-template-columns: 1fr;
  }
}
</style>
