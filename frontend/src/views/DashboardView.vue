<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

import AppToast from '../components/AppToast.vue'

const cargando = ref(true)
const actualizando = ref(false)

const dashboard = ref({
  total_productos: 0,
  valor_total_inventario_q: 0,
  pedidos_hoy: 0,
  confirmados_hoy: 0,
  rechazados_hoy: 0,
  alerta_stock_bajo: [],
})

const ultimaActualizacion = ref(null)

const toast = ref({
  show: false,
  type: 'success',
  message: '',
})

let toastTimer = null

function mostrarToast(type, message) {
  if (toastTimer) {
    clearTimeout(toastTimer)
  }

  toast.value = {
    show: true,
    type,
    message,
  }

  toastTimer = setTimeout(() => {
    cerrarToast()
  }, 4200)
}

function cerrarToast() {
  toast.value.show = false
}

function normalizarListaStockBajo(valor) {
  if (Array.isArray(valor)) {
    return valor
  }

  if (valor && typeof valor === 'object') {
    if (Array.isArray(valor.items)) {
      return valor.items
    }

    if (Array.isArray(valor.productos)) {
      return valor.productos
    }

    return Object.values(valor).filter((item) => typeof item === 'object')
  }

  return []
}

async function cargarDashboard(mostrarMensaje = false) {
  try {
    if (!cargando.value) {
      actualizando.value = true
    }

    const response = await fetch('/api/reportes/dashboard')

    if (!response.ok) {
      throw new Error('No se pudo cargar la información del dashboard.')
    }

    const data = await response.json()

    dashboard.value = {
      total_productos: Number(data.total_productos ?? 0),
      valor_total_inventario_q: Number(data.valor_total_inventario_q ?? 0),
      pedidos_hoy: Number(data.pedidos_hoy ?? 0),
      confirmados_hoy: Number(data.confirmados_hoy ?? 0),
      rechazados_hoy: Number(data.rechazados_hoy ?? 0),
      alerta_stock_bajo: normalizarListaStockBajo(data.alerta_stock_bajo),
    }

    ultimaActualizacion.value = new Date()

    if (mostrarMensaje) {
      mostrarToast(
        'success',
        'El dashboard se actualizó correctamente.',
      )
    }
  } catch (err) {
    console.error(err)

    mostrarToast(
      'error',
      err instanceof Error
        ? err.message
        : 'No se pudo obtener la información del dashboard.',
    )
  } finally {
    cargando.value = false
    actualizando.value = false
  }
}

const stockBajoCount = computed(
  () => dashboard.value.alerta_stock_bajo.length,
)

const productosStockBajo = computed(() =>
  dashboard.value.alerta_stock_bajo.slice(0, 5),
)

const tasaConfirmacion = computed(() => {
  if (dashboard.value.pedidos_hoy === 0) {
    return 0
  }

  return Math.round(
    (dashboard.value.confirmados_hoy / dashboard.value.pedidos_hoy) * 100,
  )
})

const estadoGeneral = computed(() => {
  if (dashboard.value.rechazados_hoy > 0) {
    return {
      label: 'Con atención',
      className: 'warning',
      text: 'Se detectaron pedidos rechazados hoy. Revisa el módulo de pedidos.',
    }
  }

  if (stockBajoCount.value > 0) {
    return {
      label: 'Operativo',
      className: 'warning',
      text: 'El sistema funciona correctamente, pero hay productos con existencias bajas.',
    }
  }

  return {
    label: 'Estable',
    className: 'success',
    text: 'Todos los indicadores principales se encuentran en buen estado.',
  }
})

function formatoMoneda(valor) {
  return Number(valor || 0).toLocaleString('es-GT', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

function formatoFecha(fecha) {
  if (!fecha) {
    return 'Sin registros'
  }

  return new Intl.DateTimeFormat('es-GT', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(fecha)
}

function obtenerNombreProducto(item) {
  return item.nombre || item.producto || item.sku || 'Producto'
}

function obtenerSkuProducto(item) {
  return item.sku || item.codigo || '---'
}

function obtenerStockProducto(item) {
  return Number(item.stock ?? item.existencias ?? item.cantidad ?? 0)
}

onMounted(() => {
  cargarDashboard()
})

onBeforeUnmount(() => {
  if (toastTimer) {
    clearTimeout(toastTimer)
  }
})
</script>

<template>
  <div class="dashboard-page">
    <AppToast
      :show="toast.show"
      :type="toast.type"
      :message="toast.message"
      @close="cerrarToast"
    />

    <!-- Encabezado -->
    <section class="hero-card">
      <div class="hero-content">
        <div class="hero-text">
          <div class="hero-eyebrow">
            Panel ejecutivo
          </div>

          <h1>Dashboard</h1>

          <p>
            Visualiza el estado general del inventario y los pedidos de
            Distribuidora El Quetzal en tiempo real.
          </p>

          <div class="hero-meta">
            <div
              class="status-pill"
              :class="estadoGeneral.className"
            >
              <span class="status-dot"></span>
              {{ estadoGeneral.label }}
            </div>

            <div class="last-update">
              Última actualización:
              <strong>{{ formatoFecha(ultimaActualizacion) }}</strong>
            </div>
          </div>
        </div>

        <button
          class="refresh-button"
          :disabled="actualizando"
          @click="cargarDashboard(true)"
        >
          <span
            class="refresh-icon"
            :class="{ spinning: actualizando }"
          >
            ↻
          </span>
          {{ actualizando ? 'Actualizando...' : 'Actualizar' }}
        </button>
      </div>

      <div class="hero-summary">
        {{ estadoGeneral.text }}
      </div>
    </section>

    <!-- KPIs -->
    <section
      v-if="!cargando"
      class="kpi-grid"
    >
      <article class="kpi-card">
        <div class="kpi-icon products">
          📦
        </div>

        <div class="kpi-info">
          <span>Total de productos</span>
          <strong>{{ dashboard.total_productos }}</strong>
          <small>Productos activos en inventario</small>
        </div>
      </article>

      <article class="kpi-card">
        <div class="kpi-icon money">
          Q
        </div>

        <div class="kpi-info">
          <span>Valor del inventario</span>
          <strong>Q {{ formatoMoneda(dashboard.valor_total_inventario_q) }}</strong>
          <small>Valor total disponible</small>
        </div>
      </article>

      <article class="kpi-card">
        <div class="kpi-icon orders">
          🧾
        </div>

        <div class="kpi-info">
          <span>Pedidos del día</span>
          <strong>{{ dashboard.pedidos_hoy }}</strong>
          <small>Solicitudes registradas hoy</small>
        </div>
      </article>

      <article class="kpi-card">
        <div class="kpi-icon warning">
          ⚠
        </div>

        <div class="kpi-info">
          <span>Stock bajo</span>
          <strong>{{ stockBajoCount }}</strong>
          <small>Productos por debajo del nivel recomendado</small>
        </div>
      </article>

      <article class="kpi-card">
        <div class="kpi-icon success">
          ✓
        </div>

        <div class="kpi-info">
          <span>Confirmados hoy</span>
          <strong>{{ dashboard.confirmados_hoy }}</strong>
          <small>Tasa de confirmación: {{ tasaConfirmacion }}%</small>
        </div>
      </article>

      <article class="kpi-card">
        <div class="kpi-icon danger">
          ✕
        </div>

        <div class="kpi-info">
          <span>Rechazados hoy</span>
          <strong>{{ dashboard.rechazados_hoy }}</strong>
          <small>Pedidos no aprobados hoy</small>
        </div>
      </article>
    </section>

    <!-- Loader -->
    <section
      v-if="cargando"
      class="loading-card"
    >
      <div class="loader"></div>
      <h3>Cargando dashboard</h3>
      <p>Estamos preparando los indicadores del sistema.</p>
    </section>

    <!-- Contenido -->
    <section
      v-else
      class="content-grid"
    >
      <article class="panel-card large">
        <div class="panel-header">
          <div>
            <div class="section-tag">
              Resumen
            </div>
            <h2>Estado del sistema</h2>
            <p>
              Indicadores generales del comportamiento operativo del sistema.
            </p>
          </div>
        </div>

        <div class="highlights-grid">
          <div class="highlight-box">
            <span class="highlight-label">Inventario monitoreado</span>
            <strong>{{ dashboard.total_productos }}</strong>
            <small>Productos incluidos en control actual</small>
          </div>

          <div class="highlight-box">
            <span class="highlight-label">Pedidos atendidos</span>
            <strong>{{ dashboard.confirmados_hoy }}</strong>
            <small>Pedidos confirmados durante el día</small>
          </div>

          <div class="highlight-box">
            <span class="highlight-label">Pedidos con incidencia</span>
            <strong>{{ dashboard.rechazados_hoy }}</strong>
            <small>Pedidos rechazados o no completados</small>
          </div>
        </div>

        <div class="insight-banner">
          <div class="insight-icon">
            ✦
          </div>

          <div>
            <strong>Lectura rápida:</strong>
            <p>
              Hay <strong>{{ stockBajoCount }}</strong> producto(s) con stock bajo,
              <strong>{{ dashboard.confirmados_hoy }}</strong> pedido(s) confirmados hoy y un
              valor de inventario actual de
              <strong>Q {{ formatoMoneda(dashboard.valor_total_inventario_q) }}</strong>.
            </p>
          </div>
        </div>
      </article>

      <article class="panel-card">
        <div class="panel-header">
          <div>
            <div class="section-tag">
              Alertas
            </div>
            <h2>Productos con stock bajo</h2>
            <p>
              Productos que requieren seguimiento o reabastecimiento.
            </p>
          </div>
        </div>

        <div
          v-if="productosStockBajo.length === 0"
          class="empty-mini-state"
        >
          <div class="empty-mini-icon">
            ✓
          </div>

          <strong>Sin alertas de stock</strong>
          <span>Todos los productos tienen existencias adecuadas.</span>
        </div>

        <div
          v-else
          class="low-stock-list"
        >
          <div
            v-for="(producto, index) in productosStockBajo"
            :key="`${obtenerSkuProducto(producto)}-${index}`"
            class="low-stock-item"
          >
            <div class="low-stock-main">
              <div class="low-stock-avatar">
                {{ obtenerNombreProducto(producto).charAt(0).toUpperCase() }}
              </div>

              <div>
                <strong>{{ obtenerNombreProducto(producto) }}</strong>
                <span>SKU: {{ obtenerSkuProducto(producto) }}</span>
              </div>
            </div>

            <div class="low-stock-right">
              <span class="stock-chip low">
                {{ obtenerStockProducto(producto) }}
              </span>
            </div>
          </div>
        </div>
      </article>

      <article class="panel-card">
        <div class="panel-header">
          <div>
            <div class="section-tag">
              Rendimiento
            </div>
            <h2>Indicadores del día</h2>
            <p>
              Resumen breve de la actividad diaria.
            </p>
          </div>
        </div>

        <div class="stats-list">
          <div class="stats-row">
            <span>Pedidos del día</span>
            <strong>{{ dashboard.pedidos_hoy }}</strong>
          </div>

          <div class="stats-row">
            <span>Confirmados</span>
            <strong class="text-success">{{ dashboard.confirmados_hoy }}</strong>
          </div>

          <div class="stats-row">
            <span>Rechazados</span>
            <strong class="text-danger">{{ dashboard.rechazados_hoy }}</strong>
          </div>

          <div class="stats-row">
            <span>Tasa de confirmación</span>
            <strong>{{ tasaConfirmacion }}%</strong>
          </div>
        </div>
      </article>
    </section>
  </div>
</template>

<style scoped>
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 24px;

  animation: pageEnter 0.35s ease;
}

/* HERO */

.hero-card {
  padding: 28px;

  border: 1px solid #e1e7e3;
  border-radius: 20px;

  background:
    linear-gradient(
      135deg,
      #f8fbf9 0%,
      #ffffff 48%,
      #f5faf7 100%
    );

  box-shadow:
    0 10px 30px rgba(19, 52, 39, 0.05);
}

.hero-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
}

.hero-text h1 {
  margin: 0 0 8px;

  color: #17241e;

  font-size: 36px;
  line-height: 1.1;

  letter-spacing: -0.8px;
}

.hero-text p {
  max-width: 760px;
  margin: 0;

  color: #66746d;

  font-size: 15px;
  line-height: 1.6;
}

.hero-eyebrow {
  margin-bottom: 8px;

  color: #2f775a;

  font-size: 11px;
  font-weight: 800;

  text-transform: uppercase;
  letter-spacing: 1px;
}

.hero-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;

  margin-top: 18px;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;

  padding: 8px 12px;

  border-radius: 999px;

  font-size: 12px;
  font-weight: 700;
}

.status-pill.success {
  background: #eaf7ef;
  color: #216645;
}

.status-pill.warning {
  background: #fff5db;
  color: #8a6517;
}

.status-dot {
  width: 8px;
  height: 8px;

  border-radius: 50%;
  background: currentColor;
}

.last-update {
  color: #72807a;
  font-size: 12px;
}

.last-update strong {
  color: #415049;
}

.hero-summary {
  margin-top: 18px;
  padding: 14px 16px;

  border: 1px solid #e6ece8;
  border-radius: 14px;

  background: rgba(255, 255, 255, 0.72);

  color: #506059;
  font-size: 14px;
  line-height: 1.6;
}

.refresh-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;

  border: none;
  padding: 12px 18px;

  border-radius: 12px;

  background:
    linear-gradient(
      135deg,
      #2a7559,
      #1f654c
    );

  color: white;

  cursor: pointer;

  font-size: 13px;
  font-weight: 700;

  box-shadow:
    0 8px 18px rgba(31, 101, 76, 0.18);

  transition:
    transform 0.18s ease,
    box-shadow 0.22s ease,
    opacity 0.2s ease;
}

.refresh-button:hover {
  transform: translateY(-2px);

  box-shadow:
    0 12px 24px rgba(31, 101, 76, 0.24);
}

.refresh-button:active {
  transform: translateY(1px) scale(0.98);
}

.refresh-button:disabled {
  opacity: 0.7;
  cursor: default;
  transform: none;
}

.refresh-icon {
  font-size: 16px;
}

.spinning {
  animation: spin 0.9s linear infinite;
}

/* KPI GRID */

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.kpi-card {
  display: flex;
  align-items: center;
  gap: 16px;

  padding: 20px;

  border: 1px solid #e5ebe7;
  border-radius: 18px;

  background: #ffffff;

  box-shadow:
    0 8px 24px rgba(18, 45, 34, 0.04);

  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease,
    border-color 0.2s ease;
}

.kpi-card:hover {
  transform: translateY(-4px);

  border-color: #d6e3dc;

  box-shadow:
    0 14px 30px rgba(18, 45, 34, 0.08);
}

.kpi-icon {
  width: 54px;
  height: 54px;

  flex-shrink: 0;

  display: grid;
  place-items: center;

  border-radius: 16px;

  font-size: 22px;
  font-weight: 800;
}

.kpi-icon.products {
  background: #edf6ef;
}

.kpi-icon.money {
  background: #edf8f2;
  color: #1f6e49;
}

.kpi-icon.orders {
  background: #f2f1fb;
}

.kpi-icon.warning {
  background: #fff5db;
}

.kpi-icon.success {
  background: #eaf8ef;
  color: #1f6f49;
}

.kpi-icon.danger {
  background: #fdeaea;
  color: #b24040;
}

.kpi-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.kpi-info span {
  color: #73807a;
  font-size: 12px;
  font-weight: 600;
}

.kpi-info strong {
  color: #1b2822;
  font-size: 28px;
  line-height: 1.1;
}

.kpi-info small {
  color: #94a09a;
  font-size: 11px;
}

/* CONTENT */

.content-grid {
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: 18px;
}

.panel-card {
  padding: 22px;

  border: 1px solid #e5ebe7;
  border-radius: 18px;

  background: #ffffff;

  box-shadow:
    0 8px 24px rgba(18, 45, 34, 0.04);
}

.panel-card.large {
  grid-column: span 1;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;

  margin-bottom: 18px;
}

.section-tag {
  display: inline-flex;

  margin-bottom: 7px;
  padding: 5px 9px;

  border-radius: 999px;

  background: #edf6f1;
  color: #2b6b50;

  font-size: 10px;
  font-weight: 800;

  text-transform: uppercase;
  letter-spacing: 0.8px;
}

.panel-header h2 {
  margin: 0 0 6px;

  color: #1d2b24;
  font-size: 22px;
}

.panel-header p {
  margin: 0;

  color: #73807a;
  font-size: 13px;
}

/* Highlights */

.highlights-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;

  margin-bottom: 18px;
}

.highlight-box {
  padding: 16px;

  border: 1px solid #eef2f0;
  border-radius: 14px;

  background: #fafcfb;
}

.highlight-label {
  display: block;
  margin-bottom: 8px;

  color: #71807a;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.7px;
}

.highlight-box strong {
  display: block;

  color: #1f2d26;
  font-size: 24px;
}

.highlight-box small {
  color: #8a9690;
  font-size: 12px;
}

.insight-banner {
  display: flex;
  align-items: flex-start;
  gap: 14px;

  padding: 16px;

  border-radius: 16px;

  background:
    linear-gradient(
      135deg,
      #f5faf7,
      #ffffff
    );

  border: 1px solid #e5ede8;
}

.insight-icon {
  width: 42px;
  height: 42px;

  flex-shrink: 0;

  display: grid;
  place-items: center;

  border-radius: 12px;

  background: #e8f5ee;
  color: #2c6d52;

  font-size: 20px;
}

.insight-banner strong {
  color: #213029;
}

.insight-banner p {
  margin: 5px 0 0;

  color: #5d6a64;
  font-size: 14px;
  line-height: 1.6;
}

/* Low stock list */

.low-stock-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.low-stock-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;

  padding: 14px;

  border: 1px solid #edf1ef;
  border-radius: 14px;

  background: #fafcfb;

  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease;
}

.low-stock-item:hover {
  transform: translateY(-2px);

  box-shadow:
    0 8px 16px rgba(18, 45, 34, 0.05);
}

.low-stock-main {
  display: flex;
  align-items: center;
  gap: 12px;
}

.low-stock-avatar {
  width: 40px;
  height: 40px;

  display: grid;
  place-items: center;

  border-radius: 12px;

  background: #edf5f0;
  color: #2b6a4f;

  font-weight: 800;
}

.low-stock-main strong {
  display: block;

  color: #24312b;
  font-size: 14px;
}

.low-stock-main span {
  color: #7a8781;
  font-size: 12px;
}

.stock-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;

  min-width: 38px;

  padding: 7px 10px;

  border-radius: 999px;

  font-size: 12px;
  font-weight: 800;
}

.stock-chip.low {
  background: #fff2d0;
  color: #906314;
}

/* Stats */

.stats-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stats-row {
  display: flex;
  justify-content: space-between;
  align-items: center;

  padding: 14px 0;

  border-bottom: 1px solid #eef2f0;
}

.stats-row:last-child {
  border-bottom: none;
}

.stats-row span {
  color: #6f7c76;
  font-size: 14px;
}

.stats-row strong {
  color: #1f2c25;
  font-size: 18px;
}

.text-success {
  color: #207048 !important;
}

.text-danger {
  color: #b54242 !important;
}

/* Loading and empty states */

.loading-card {
  min-height: 280px;

  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;

  padding: 36px;

  border: 1px solid #e4ebe7;
  border-radius: 18px;

  background: #ffffff;

  text-align: center;
}

.loading-card h3 {
  margin: 16px 0 6px;

  color: #1f2d26;
  font-size: 18px;
}

.loading-card p {
  margin: 0;

  color: #7a8781;
  font-size: 13px;
}

.loader {
  width: 34px;
  height: 34px;

  border: 3px solid #e6efea;
  border-top-color: #3d8265;
  border-radius: 50%;

  animation: spin 0.85s linear infinite;
}

.empty-mini-state {
  min-height: 220px;

  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;

  text-align: center;
}

.empty-mini-icon {
  width: 54px;
  height: 54px;

  display: grid;
  place-items: center;

  margin-bottom: 12px;

  border-radius: 16px;

  background: #ebf7ef;
  color: #28704a;

  font-size: 24px;
  font-weight: 800;
}

.empty-mini-state strong {
  color: #24312b;
  font-size: 15px;
}

.empty-mini-state span {
  margin-top: 5px;

  color: #7e8a84;
  font-size: 13px;
}

/* Animations */

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes pageEnter {
  from {
    opacity: 0;
    transform: translateY(8px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Responsive */

@media (max-width: 1180px) {
  .kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 860px) {
  .hero-content {
    flex-direction: column;
    align-items: stretch;
  }

  .highlights-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .kpi-grid {
    grid-template-columns: 1fr;
  }

  .hero-card,
  .panel-card {
    padding: 18px;
  }

  .hero-text h1 {
    font-size: 30px;
  }
}
</style>