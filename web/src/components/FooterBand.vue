<script setup>
defineProps({
  lastUpdated: String,
})
</script>

<template>
  <footer class="footer">
    <div class="footer-inner">
      <span class="footer-mono eyebrow-mono">STAR SORT</span>
      <span class="footer-text">
        Last updated: {{ lastUpdated ? new Date(lastUpdated).toLocaleDateString() : '—' }}
      </span>
      <span class="footer-text">Powered by GitHub + Claude</span>
    </div>
  </footer>
</template>

<style scoped>
.footer {
  border-top: 1px solid var(--color-hairline);
  padding: var(--sp-3xl) var(--sp-xl);
  background: var(--color-canvas);
}

.footer-inner {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.footer-mono {
  color: var(--color-ink);
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 400;
  letter-spacing: 1.4px;
  text-transform: uppercase;
}

.footer-text {
  color: var(--color-body-mid);
  font-family: var(--font-body);
  font-size: 14px;
  line-height: 20px;
}

@media (max-width: 768px) {
  .footer-inner {
    flex-direction: column;
    gap: var(--sp-sm);
    text-align: center;
  }
}
</style>
