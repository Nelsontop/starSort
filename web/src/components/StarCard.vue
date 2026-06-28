<script setup>
defineProps({
  star: Object,
})
</script>

<template>
  <a :href="star.html_url" target="_blank" class="star-card card-content">
    <div class="card-top">
      <span class="card-name">{{ star.full_name }}</span>
      <span v-if="star.override" class="override-pill">OVERRIDE</span>
    </div>
    <p class="card-desc">{{ star.description || 'No description' }}</p>
    <div class="card-meta">
      <span class="meta-item meta-lang" v-if="star.language">{{ star.language }}</span>
      <span class="meta-item meta-stars">⭐ {{ star.stargazers_count.toLocaleString() }}</span>
      <span class="meta-item meta-forks">🍴 {{ (star.forks_count || 0).toLocaleString() }}</span>
      <span class="meta-item meta-topic" v-for="topic in star.topics.slice(0, 4)" :key="topic">
        {{ topic }}
      </span>
    </div>
    <div class="card-footer" v-if="star.updated_at">
      <span class="meta-updated">Updated {{ new Date(star.updated_at).toLocaleDateString() }}</span>
    </div>
  </a>
</template>

<style scoped>
.star-card {
  display: flex;
  flex-direction: column;
  gap: var(--sp-sm);
  transition: background 0.15s ease;
}

.star-card:hover {
  background-color: var(--color-canvas-soft);
}

.card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--sp-sm);
}

.card-name {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 400;
  letter-spacing: -0.2px;
  color: var(--color-ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.override-pill {
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 1.1px;
  text-transform: uppercase;
  color: var(--color-accent-sunset);
  border: 1px solid var(--color-accent-sunset);
  border-radius: var(--radius-pill);
  padding: var(--sp-xxs) var(--sp-sm);
  flex-shrink: 0;
}

.card-desc {
  font-family: var(--font-body);
  font-size: 14px;
  line-height: 20px;
  color: var(--color-body);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-xs);
  margin-top: auto;
}

.meta-item {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 400;
  letter-spacing: 1.2px;
  color: var(--color-body-mid);
  padding: var(--sp-xxs) var(--sp-xs);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-sm);
  text-transform: uppercase;
}

.meta-lang {
  color: var(--color-accent-breeze);
  border-color: var(--color-accent-breeze);
}

.meta-stars {
  color: var(--color-accent-sunset-soft);
  border-color: var(--color-accent-sunset-soft);
}

.meta-forks {
  color: var(--color-accent-twilight);
  border-color: var(--color-accent-twilight);
}

.meta-topic {
  color: var(--color-body-mid);
  border-color: var(--color-hairline);
}

.card-footer {
  margin-top: var(--sp-xs);
}

.meta-updated {
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 1.1px;
  color: var(--color-mute);
}
</style>
