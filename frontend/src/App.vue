<script setup>
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div>
        <div class="brand">
          <div class="brand-symbol">
            Q
          </div>

          <div class="brand-text">
            <h2>El Quetzal</h2>
            <span>Distribuidora</span>
          </div>
        </div>

        <div class="menu-label">
          MENÚ PRINCIPAL
        </div>

        <nav>
          <RouterLink to="/">
            <span class="nav-icon">⌂</span>

            <span>Dashboard</span>
          </RouterLink>

          <RouterLink to="/inventario">
            <span class="nav-icon">▦</span>

            <span>Inventario</span>
          </RouterLink>

          <RouterLink to="/pedidos">
            <span class="nav-icon">▤</span>

            <span>Pedidos</span>
          </RouterLink>
        </nav>
      </div>

      <div class="sidebar-footer">
        <div class="system-status">
          <span class="status-dot"></span>

          <div>
            <strong>Sistema activo</strong>
            <span>Servicios disponibles</span>
          </div>
        </div>
      </div>
    </aside>

    <main class="content">
      <header class="topbar">
        <div>
          <strong>Sistema de gestión</strong>

          <span>
            Inventario y pedidos
          </span>
        </div>

        <div class="topbar-right">
          <div class="environment-badge">
            <span></span>
            Operativo
          </div>
        </div>
      </header>

      <section class="page">
        <RouterView v-slot="{ Component }">
          <Transition
            name="page"
            mode="out-in"
          >
            <component :is="Component" />
          </Transition>
        </RouterView>
      </section>
    </main>
  </div>
</template>

<style>
:root {
  --green-950: #0c3024;
  --green-900: #123d2e;
  --green-800: #18513d;
  --green-700: #216a4f;
  --green-600: #2d7f61;

  --green-100: #e5f2ec;
  --green-50: #f1f8f5;

  --surface: #ffffff;
  --background: #f5f7f6;

  --border: #e4e9e6;

  --text: #17231e;
  --muted: #6b7771;

  --shadow-sm:
    0 1px 2px rgba(15, 35, 26, 0.04),
    0 4px 12px rgba(15, 35, 26, 0.04);

  --shadow-md:
    0 8px 26px rgba(15, 35, 26, 0.08);

  --shadow-lg:
    0 20px 50px rgba(15, 35, 26, 0.12);
}

* {
  box-sizing: border-box;
}

html {
  background: var(--background);
}

body {
  margin: 0;

  min-width: 320px;
  min-height: 100vh;

  font-family:
    Inter,
    -apple-system,
    BlinkMacSystemFont,
    "Segoe UI",
    sans-serif;

  background:
    radial-gradient(
      circle at 90% 0%,
      rgba(45, 127, 97, 0.055),
      transparent 28%
    ),
    var(--background);

  color: var(--text);

  -webkit-font-smoothing: antialiased;
}

button,
input,
select {
  font: inherit;
}

button {
  -webkit-tap-highlight-color: transparent;
}

/* APP */

.app-shell {
  min-height: 100vh;
  display: flex;
}

/* SIDEBAR */

.sidebar {
  position: fixed;
  inset: 0 auto 0 0;

  z-index: 100;

  width: 254px;
  min-height: 100vh;

  display: flex;
  flex-direction: column;
  justify-content: space-between;

  padding: 27px 18px 22px;

  background:
    linear-gradient(
      180deg,
      #123c2e 0%,
      #0d3025 100%
    );

  color: #ffffff;

  box-shadow: 8px 0 28px rgba(14, 41, 31, 0.07);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;

  padding: 0 10px;
  margin-bottom: 42px;
}

.brand-symbol {
  width: 42px;
  height: 42px;

  display: grid;
  place-items: center;

  border: 1px solid rgba(255, 255, 255, 0.15);

  border-radius: 13px;

  background:
    linear-gradient(
      135deg,
      rgba(255,255,255,0.16),
      rgba(255,255,255,0.05)
    );

  font-size: 21px;
  font-weight: 800;

  box-shadow:
    inset 0 1px rgba(255,255,255,0.11),
    0 7px 16px rgba(0,0,0,0.08);
}

.brand-text h2 {
  margin: 0;

  font-size: 21px;
  letter-spacing: -0.4px;
}

.brand-text span {
  display: block;

  margin-top: 2px;

  color: #aad0bd;

  font-size: 12px;
}

.menu-label {
  padding: 0 12px;
  margin-bottom: 9px;

  color: rgba(205, 231, 218, 0.58);

  font-size: 10px;
  font-weight: 700;

  letter-spacing: 1.3px;
}

nav {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

nav a {
  position: relative;

  display: flex;
  align-items: center;
  gap: 12px;

  min-height: 48px;

  padding: 0 14px;

  border-radius: 11px;

  color: #d9e8e0;

  text-decoration: none;

  font-size: 14px;
  font-weight: 500;

  transition:
    background 0.22s ease,
    color 0.22s ease,
    transform 0.2s ease,
    box-shadow 0.22s ease;
}

nav a::before {
  content: '';

  position: absolute;
  left: 0;

  width: 3px;
  height: 0;

  border-radius: 4px;

  background: #97d2b6;

  transition: height 0.22s ease;
}

nav a:hover {
  background: rgba(255, 255, 255, 0.07);
  color: #ffffff;

  transform: translateX(2px);
}

nav a.router-link-exact-active {
  background:
    linear-gradient(
      135deg,
      rgba(111, 175, 144, 0.43),
      rgba(111, 175, 144, 0.25)
    );

  color: #ffffff;

  font-weight: 650;

  box-shadow:
    inset 0 1px rgba(255,255,255,0.08),
    0 7px 18px rgba(3, 20, 13, 0.07);
}

nav a.router-link-exact-active::before {
  height: 24px;
}

.nav-icon {
  width: 21px;

  text-align: center;

  font-size: 18px;
  line-height: 1;
}

.sidebar-footer {
  padding: 0 5px;
}

.system-status {
  display: flex;
  align-items: center;
  gap: 10px;

  padding: 12px;

  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;

  background: rgba(255,255,255,0.035);
}

.status-dot {
  width: 9px;
  height: 9px;

  flex-shrink: 0;

  border-radius: 50%;

  background: #6bd69a;

  box-shadow:
    0 0 0 4px rgba(107, 214, 154, 0.12);

  animation: statusPulse 2.6s infinite;
}

.system-status strong,
.system-status span {
  display: block;
}

.system-status strong {
  color: #e8f3ed;

  font-size: 11px;
}

.system-status div > span {
  margin-top: 2px;

  color: #8eb6a3;

  font-size: 10px;
}

/* CONTENT */

.content {
  flex: 1;

  min-width: 0;

  margin-left: 254px;
}

/* TOPBAR */

.topbar {
  position: sticky;
  top: 0;

  z-index: 80;

  height: 76px;

  display: flex;
  align-items: center;
  justify-content: space-between;

  padding: 0 34px;

  border-bottom: 1px solid rgba(224, 231, 227, 0.85);

  background: rgba(255, 255, 255, 0.89);

  backdrop-filter: blur(18px);
}

.topbar > div:first-child {
  display: flex;
  flex-direction: column;
}

.topbar strong {
  color: #1c2c25;

  font-size: 14px;
}

.topbar > div:first-child span {
  margin-top: 3px;

  color: var(--muted);

  font-size: 12px;
}

.environment-badge {
  display: flex;
  align-items: center;
  gap: 7px;

  padding: 7px 11px;

  border: 1px solid #dfe8e3;
  border-radius: 999px;

  background: #f7faf8;

  color: #53615b;

  font-size: 11px;
  font-weight: 650;
}

.environment-badge span {
  width: 7px;
  height: 7px;

  border-radius: 50%;

  background: #39a571;
}

/* PAGE */

.page {
  width: min(1500px, 100%);

  margin: 0 auto;

  padding: 34px;
}

/* GLOBAL BUTTON POLISH */

.primary-button,
.refresh-button,
.secondary-button,
.add-button,
.edit-button,
.delete-button {
  transition:
    transform 0.18s ease,
    box-shadow 0.2s ease,
    background 0.2s ease,
    border-color 0.2s ease,
    color 0.2s ease;
}

.primary-button:hover,
.add-button:hover {
  transform: translateY(-2px);

  box-shadow:
    0 8px 18px rgba(31, 107, 79, 0.2);
}

.refresh-button:hover,
.secondary-button:hover {
  transform: translateY(-1px);

  border-color: #bfcac4;

  box-shadow: var(--shadow-sm);
}

.edit-button:hover,
.delete-button:hover {
  transform: translateY(-1px);
}

.primary-button:active,
.refresh-button:active,
.secondary-button:active,
.add-button:active,
.edit-button:active,
.delete-button:active {
  transform: translateY(1px) scale(0.98);
}

/* GLOBAL CARDS */

.card,
.table-card,
.form-card,
.information,
.history-card {
  box-shadow: var(--shadow-sm);

  transition:
    transform 0.25s ease,
    box-shadow 0.25s ease,
    border-color 0.25s ease;
}

.card:hover,
.information:hover {
  border-color: #d9e2dd;

  box-shadow: var(--shadow-md);
}

/* INPUT POLISH */

input,
select {
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    background 0.2s ease;
}

input:focus,
select:focus {
  outline: none !important;

  border-color: #4f9577 !important;

  box-shadow:
    0 0 0 3px rgba(79, 149, 119, 0.12) !important;
}

/* ROUTE TRANSITIONS */

.page-enter-active {
  transition:
    opacity 0.28s ease,
    transform 0.34s cubic-bezier(0.16, 1, 0.3, 1);
}

.page-leave-active {
  transition:
    opacity 0.15s ease,
    transform 0.15s ease;
}

.page-enter-from {
  opacity: 0;
  transform: translateY(9px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-3px);
}

/* ANIMATION */

@keyframes statusPulse {
  0%,
  100% {
    box-shadow:
      0 0 0 4px rgba(107, 214, 154, 0.12);
  }

  50% {
    box-shadow:
      0 0 0 7px rgba(107, 214, 154, 0.04);
  }
}

@media (max-width: 800px) {
  .sidebar {
    width: 210px;
  }

  .content {
    margin-left: 210px;
  }

  .page {
    padding: 24px;
  }

  .topbar {
    padding: 0 24px;
  }
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    scroll-behavior: auto !important;
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
</style>