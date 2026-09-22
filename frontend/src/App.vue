<script setup>
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <div class="app">
    <aside class="sidebar">
      <div class="brand">
        <h2>El Quetzal</h2>
        <span>Distribuidora</span>
      </div>

      <nav>
        <RouterLink to="/">Dashboard</RouterLink>
        <RouterLink to="/inventario">Inventario</RouterLink>
        <RouterLink to="/pedidos">Pedidos</RouterLink>
      </nav>
    </aside>

    <main class="content">
      <header class="topbar">
        <div>
          <strong>Sistema de gestión</strong>
          <span>Inventario y pedidos</span>
        </div>
      </header>

      <section class="page">
        <RouterView />
      </section>
    </main>
  </div>
</template>

<style>
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family:
    Inter, Arial, sans-serif;
  background: #f4f6f8;
  color: #1f2937;
}

.app {
  min-height: 100vh;
  display: flex;
}

.sidebar {
  width: 240px;
  min-height: 100vh;
  background: #12372a;
  color: white;
  padding: 28px 20px;
}

.brand {
  margin-bottom: 40px;
}

.brand h2 {
  margin: 0;
  font-size: 25px;
}

.brand span {
  color: #b7d4c4;
  font-size: 13px;
}

nav {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

nav a {
  color: #dce8e1;
  text-decoration: none;
  padding: 12px 15px;
  border-radius: 8px;
}

nav a:hover {
  background: #1d503d;
}

nav a.router-link-exact-active {
  background: #2f7659;
  color: white;
  font-weight: bold;
}

.content {
  flex: 1;
}

.topbar {
  height: 72px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
  padding: 15px 30px;
  display: flex;
  align-items: center;
}

.topbar div {
  display: flex;
  flex-direction: column;
}

.topbar span {
  color: #6b7280;
  font-size: 13px;
  margin-top: 3px;
}

.page {
  padding: 30px;
}
</style>