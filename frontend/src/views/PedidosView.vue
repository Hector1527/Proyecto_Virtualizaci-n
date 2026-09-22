<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

import AppToast from '../components/AppToast.vue'

const productos = ref([])
const pedidos = ref([])
const cargando = ref(true)
const procesando = ref(false)

const carne = ref('1143323')
const productoSeleccionado = ref('')
const cantidad = ref(1)

const carrito = ref([])

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
  }, 4500)
}

function cerrarToast() {
  toast.value.show = false
}

const productoActual = computed(() =>
  productos.value.find(
    (producto) => producto.sku === productoSeleccionado.value,
  ),
)

const totalPedido = computed(() =>
  carrito.value.reduce(
    (total, item) =>
      total + Number(item.precio_q) * Number(item.cantidad),
    0,
  ),
)

const totalItems = computed(() =>
  carrito.value.reduce(
    (total, item) => total + Number(item.cantidad),
    0,
  ),
)

const pedidosConfirmados = computed(
  () =>
    pedidos.value.filter(
      (pedido) => pedido.estado === 'confirmado',
    ).length,
)

const pedidosRechazados = computed(
  () =>
    pedidos.value.filter(
      (pedido) => pedido.estado === 'rechazado',
    ).length,
)

async function cargarProductos() {
  const response = await fetch('/api/inventario/productos')

  if (!response.ok) {
    throw new Error('No se pudo cargar el inventario.')
  }

  productos.value = await response.json()

  if (
    productos.value.length > 0 &&
    !productoSeleccionado.value
  ) {
    productoSeleccionado.value = productos.value[0].sku
  }
}

async function cargarPedidos() {
  const response = await fetch('/api/pedidos')

  if (!response.ok) {
    throw new Error('No se pudo cargar el historial de pedidos.')
  }

  pedidos.value = await response.json()
}

async function cargarDatos(mostrarMensaje = false) {
  try {
    cargando.value = true

    await Promise.all([
      cargarProductos(),
      cargarPedidos(),
    ])

    if (mostrarMensaje) {
      mostrarToast(
        'success',
        'La información de pedidos se actualizó correctamente.',
      )
    }
  } catch (err) {
    console.error(err)

    mostrarToast(
      'error',
      err instanceof Error
        ? err.message
        : 'No se pudo cargar la información de pedidos.',
    )
  } finally {
    cargando.value = false
  }
}

function agregarProducto() {
  if (!productoActual.value) {
    mostrarToast(
      'warning',
      'Selecciona un producto antes de agregarlo al pedido.',
    )

    return
  }

  if (Number(cantidad.value) <= 0) {
    mostrarToast(
      'warning',
      'La cantidad debe ser mayor que cero.',
    )

    return
  }

  const existente = carrito.value.find(
    (item) => item.sku === productoActual.value.sku,
  )

  if (existente) {
    existente.cantidad += Number(cantidad.value)
  } else {
    carrito.value.push({
      sku: productoActual.value.sku,
      nombre: productoActual.value.nombre,
      precio_q: Number(productoActual.value.precio_q),
      stock: Number(productoActual.value.stock),
      cantidad: Number(cantidad.value),
    })
  }

  cantidad.value = 1

  mostrarToast(
    'success',
    `${productoActual.value.nombre} fue agregado al pedido.`,
  )
}

function eliminarDelCarrito(sku) {
  const producto = carrito.value.find(
    (item) => item.sku === sku,
  )

  carrito.value = carrito.value.filter(
    (item) => item.sku !== sku,
  )

  if (producto) {
    mostrarToast(
      'success',
      `${producto.nombre} fue retirado del pedido.`,
    )
  }
}

function limpiarPedido() {
  carrito.value = []
  cantidad.value = 1

  mostrarToast(
    'success',
    'El pedido fue limpiado.',
  )
}

function obtenerInsuficientes(data) {
  if (!data || typeof data !== 'object') {
    return []
  }

  if (Array.isArray(data.insuficientes)) {
    return data.insuficientes
  }

  if (
    data.motivo &&
    typeof data.motivo === 'object' &&
    Array.isArray(data.motivo.insuficientes)
  ) {
    return data.motivo.insuficientes
  }

  return []
}

function obtenerMensajeError(data) {
  if (!data) {
    return 'No se pudo procesar el pedido.'
  }

  if (typeof data === 'string') {
    return data
  }

  if (typeof data.error === 'string') {
    return data.error
  }

  if (typeof data.mensaje === 'string') {
    return data.mensaje
  }

  if (typeof data.motivo === 'string') {
    return data.motivo
  }

  return 'No se pudo procesar el pedido.'
}

async function confirmarPedido() {
  try {
    if (!carne.value.trim()) {
      mostrarToast(
        'warning',
        'Ingresa el carné del integrante.',
      )

      return
    }

    if (carrito.value.length === 0) {
      mostrarToast(
        'warning',
        'Agrega al menos un producto al pedido.',
      )

      return
    }

    procesando.value = true

    const response = await fetch('/api/pedidos', {
      method: 'POST',

      headers: {
        'Content-Type': 'application/json',
      },

      body: JSON.stringify({
        carne: carne.value.trim(),

        items: carrito.value.map((item) => ({
          sku: item.sku,
          cantidad: Number(item.cantidad),
        })),
      }),
    })

    const data = await response.json().catch(() => ({}))

    if (response.status === 409) {
      const insuficientes = obtenerInsuficientes(data)

      if (insuficientes.length > 0) {
        const detalle = insuficientes
          .map((item) => {
            const sku = item.sku || 'Producto'
            const disponible =
              item.disponible ?? item.stock ?? '?'
            const solicitado =
              item.solicitado ?? item.cantidad ?? '?'

            return `${sku}: disponible ${disponible}, solicitado ${solicitado}`
          })
          .join(' | ')

        mostrarToast(
          'error',
          `Pedido rechazado por stock insuficiente. ${detalle}`,
        )
      } else {
        mostrarToast(
          'error',
          'Pedido rechazado por stock insuficiente.',
        )
      }

      await Promise.all([
        cargarProductos(),
        cargarPedidos(),
      ])

      return
    }

    if (!response.ok) {
      throw new Error(obtenerMensajeError(data))
    }

    limpiarPedido()

    await Promise.all([
      cargarProductos(),
      cargarPedidos(),
    ])

    mostrarToast(
      'success',
      'Pedido confirmado correctamente y stock actualizado.',
    )
  } catch (err) {
    console.error(err)

    mostrarToast(
      'error',
      err instanceof Error
        ? err.message
        : 'No se pudo procesar el pedido.',
    )
  } finally {
    procesando.value = false
  }
}

function formatoMoneda(valor) {
  return Number(valor || 0).toLocaleString('es-GT', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

function formatoFecha(fecha) {
  if (!fecha) {
    return '-'
  }

  const valor = new Date(fecha)

  if (Number.isNaN(valor.getTime())) {
    return fecha
  }

  return new Intl.DateTimeFormat('es-GT', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(valor)
}

onMounted(() => {
  cargarDatos()
})

onBeforeUnmount(() => {
  if (toastTimer) {
    clearTimeout(toastTimer)
  }
})
</script>

<template>
  <div class="orders-page">
    <AppToast
      :show="toast.show"
      :type="toast.type"
      :message="toast.message"
      @close="cerrarToast"
    />

    <!-- HERO -->
    <section class="hero-card">
      <div>
        <div class="eyebrow">
          Gestión de pedidos
        </div>

        <h1>Pedidos</h1>

        <p>
          Crea solicitudes, valida existencias y consulta el historial
          de pedidos de Distribuidora El Quetzal.
        </p>
      </div>

      <button
        class="refresh-button"
        :disabled="cargando"
        @click="cargarDatos(true)"
      >
        <span
          class="refresh-icon"
          :class="{ spinning: cargando }"
        >
          ↻
        </span>

        {{ cargando ? 'Actualizando...' : 'Actualizar' }}
      </button>
    </section>

    <!-- MÉTRICAS -->
    <section class="metrics-grid">
      <article class="metric-card">
        <div class="metric-icon neutral">
          ▤
        </div>

        <div>
          <span>Pedidos registrados</span>
          <strong>{{ pedidos.length }}</strong>
        </div>
      </article>

      <article class="metric-card">
        <div class="metric-icon success">
          ✓
        </div>

        <div>
          <span>Confirmados</span>
          <strong>{{ pedidosConfirmados }}</strong>
        </div>
      </article>

      <article class="metric-card">
        <div class="metric-icon danger">
          ✕
        </div>

        <div>
          <span>Rechazados</span>
          <strong>{{ pedidosRechazados }}</strong>
        </div>
      </article>

      <article class="metric-card">
        <div class="metric-icon cart">
          #
        </div>

        <div>
          <span>Items actuales</span>
          <strong>{{ totalItems }}</strong>
        </div>
      </article>
    </section>

    <!-- CONTENIDO -->
    <section class="orders-layout">
      <!-- NUEVO PEDIDO -->
      <article class="panel-card order-builder">
        <div class="panel-header">
          <div>
            <div class="section-tag">
              Nueva solicitud
            </div>

            <h2>Crear pedido</h2>

            <p>
              Selecciona productos y cantidades para preparar una nueva solicitud.
            </p>
          </div>

          <div
            v-if="carrito.length > 0"
            class="item-count"
          >
            {{ totalItems }}
            {{ totalItems === 1 ? 'unidad' : 'unidades' }}
          </div>
        </div>

        <div class="field">
          <label for="carne">
            Carné del integrante
          </label>

          <input
            id="carne"
            v-model="carne"
            type="text"
            placeholder="Ej. 1143323"
          />

          <small>
            Este dato queda asociado al pedido generado.
          </small>
        </div>

        <div class="product-selector">
          <div class="field product-field">
            <label for="producto">
              Producto
            </label>

            <select
              id="producto"
              v-model="productoSeleccionado"
              :disabled="productos.length === 0"
            >
              <option
                v-for="producto in productos"
                :key="producto.id"
                :value="producto.sku"
              >
                {{ producto.sku }} · {{ producto.nombre }}
                · Stock: {{ producto.stock }}
              </option>
            </select>
          </div>

          <div class="field quantity-field">
            <label for="cantidad">
              Cantidad
            </label>

            <input
              id="cantidad"
              v-model.number="cantidad"
              type="number"
              min="1"
            />
          </div>

          <button
            class="add-button"
            :disabled="productos.length === 0"
            @click="agregarProducto"
          >
            + Agregar
          </button>
        </div>

        <TransitionGroup
          v-if="carrito.length > 0"
          name="item-list"
          tag="div"
          class="cart-list"
        >
          <div
            v-for="item in carrito"
            :key="item.sku"
            class="cart-item"
          >
            <div class="cart-product">
              <div class="product-avatar">
                {{ item.nombre.charAt(0).toUpperCase() }}
              </div>

              <div>
                <strong>{{ item.nombre }}</strong>

                <span>
                  {{ item.sku }} · Stock disponible: {{ item.stock }}
                </span>
              </div>
            </div>

            <div class="cart-details">
              <div class="quantity-summary">
                <span>
                  {{ item.cantidad }} ×
                  Q {{ formatoMoneda(item.precio_q) }}
                </span>

                <strong>
                  Q
                  {{
                    formatoMoneda(
                      Number(item.cantidad) *
                        Number(item.precio_q),
                    )
                  }}
                </strong>
              </div>

              <button
                class="remove-button"
                title="Quitar del pedido"
                @click="eliminarDelCarrito(item.sku)"
              >
                ×
              </button>
            </div>
          </div>
        </TransitionGroup>

        <div
          v-else
          class="empty-cart"
        >
          <div class="empty-cart-icon">
            ▤
          </div>

          <strong>No hay productos agregados</strong>

          <span>
            Selecciona un producto y presiona Agregar para comenzar.
          </span>
        </div>

        <div class="order-summary">
          <div>
            <span>Total estimado</span>
            <small>
              {{ totalItems }}
              {{ totalItems === 1 ? 'unidad agregada' : 'unidades agregadas' }}
            </small>
          </div>

          <strong>
            Q {{ formatoMoneda(totalPedido) }}
          </strong>
        </div>

        <div class="order-actions">
          <button
            class="secondary-button"
            :disabled="carrito.length === 0"
            @click="limpiarPedido"
          >
            Limpiar
          </button>

          <button
            class="primary-button"
            :disabled="procesando || carrito.length === 0"
            @click="confirmarPedido"
          >
            {{
              procesando
                ? 'Procesando...'
                : 'Confirmar pedido'
            }}
          </button>
        </div>
      </article>

      <!-- INVENTARIO DISPONIBLE -->
      <article class="panel-card inventory-panel">
        <div class="panel-header">
          <div>
            <div class="section-tag">
              Inventario
            </div>

            <h2>Disponibilidad</h2>

            <p>
              Existencias actuales disponibles para pedidos.
            </p>
          </div>
        </div>

        <div
          v-if="cargando"
          class="mini-loading"
        >
          <div class="loader"></div>
          <span>Cargando existencias...</span>
        </div>

        <div
          v-else-if="productos.length === 0"
          class="empty-mini-state"
        >
          <div class="empty-mini-icon">
            ▦
          </div>

          <strong>Sin productos</strong>

          <span>
            No hay productos disponibles para realizar pedidos.
          </span>
        </div>

        <div
          v-else
          class="inventory-list"
        >
          <div
            v-for="producto in productos"
            :key="producto.id"
            class="inventory-item"
          >
            <div class="inventory-product">
              <div class="inventory-avatar">
                {{ producto.nombre.charAt(0).toUpperCase() }}
              </div>

              <div>
                <strong>{{ producto.nombre }}</strong>

                <span>
                  {{ producto.sku }}
                </span>
              </div>
            </div>

            <div
              class="stock-chip"
              :class="{
                low: producto.stock <= 5,
                empty: producto.stock === 0,
              }"
            >
              {{ producto.stock }}
            </div>
          </div>
        </div>
      </article>
    </section>

    <!-- HISTORIAL -->
    <section class="history-card">
      <div class="history-header">
        <div>
          <div class="section-tag">
            Historial
          </div>

          <h2>Pedidos registrados</h2>

          <p>
            Consulta el estado y resultado de las solicitudes procesadas.
          </p>
        </div>

        <div class="history-count">
          {{ pedidos.length }}
          {{ pedidos.length === 1 ? 'pedido' : 'pedidos' }}
        </div>
      </div>

      <div
        v-if="pedidos.length === 0"
        class="history-empty"
      >
        <div class="empty-mini-icon">
          ▤
        </div>

        <strong>No hay pedidos registrados</strong>

        <span>
          Los pedidos procesados aparecerán aquí.
        </span>
      </div>

      <div
        v-else
        class="table-container"
      >
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Carné</th>
              <th>Estado</th>
              <th>Total</th>
              <th>Fecha</th>
            </tr>
          </thead>

          <tbody>
            <tr
              v-for="pedido in pedidos"
              :key="pedido.id"
            >
              <td>
                <span class="order-id">
                  #{{ pedido.id }}
                </span>
              </td>

              <td>
                <strong class="carne">
                  {{ pedido.carne }}
                </strong>
              </td>

              <td>
                <span
                  class="status-badge"
                  :class="{
                    confirmed:
                      pedido.estado === 'confirmado',
                    rejected:
                      pedido.estado === 'rechazado',
                  }"
                >
                  <span class="status-dot-small"></span>

                  {{ pedido.estado }}
                </span>
              </td>

              <td>
                <strong class="total-value">
                  Q {{ formatoMoneda(pedido.total_q) }}
                </strong>
              </td>

              <td>
                <span class="date-value">
                  {{ formatoFecha(pedido.creado_en) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<style scoped>
.orders-page {
  display: flex;
  flex-direction: column;
  gap: 22px;

  animation: contentIn 0.38s ease both;
}

/* HERO */

.hero-card {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 24px;

  padding: 27px;

  border: 1px solid #e1e8e4;
  border-radius: 19px;

  background:
    linear-gradient(
      135deg,
      #f8fbf9,
      #ffffff 55%,
      #f3f9f6
    );

  box-shadow:
    0 9px 28px rgba(19, 50, 38, 0.05);
}

.eyebrow {
  margin-bottom: 7px;

  color: #357a5d;

  font-size: 11px;
  font-weight: 800;

  text-transform: uppercase;
  letter-spacing: 1px;
}

.hero-card h1 {
  margin: 0 0 7px;

  color: #18251f;

  font-size: 34px;

  letter-spacing: -0.7px;
}

.hero-card p {
  max-width: 720px;

  margin: 0;

  color: #6d7973;

  font-size: 14px;
  line-height: 1.6;
}

/* MÉTRICAS */

.metrics-grid {
  display: grid;

  grid-template-columns:
    repeat(4, minmax(0, 1fr));

  gap: 16px;
}

.metric-card {
  display: flex;
  align-items: center;
  gap: 14px;

  padding: 17px;

  border: 1px solid #e5ebe7;
  border-radius: 15px;

  background: #ffffff;

  box-shadow:
    0 6px 18px rgba(18, 45, 34, 0.035);

  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

.metric-card:hover {
  transform: translateY(-3px);

  box-shadow:
    0 11px 24px rgba(18, 45, 34, 0.07);
}

.metric-icon {
  width: 44px;
  height: 44px;

  flex-shrink: 0;

  display: grid;
  place-items: center;

  border-radius: 13px;

  font-size: 17px;
  font-weight: 800;
}

.metric-icon.neutral {
  background: #eef4f1;
  color: #386552;
}

.metric-icon.success {
  background: #e9f7ee;
  color: #237148;
}

.metric-icon.danger {
  background: #fceaea;
  color: #b34141;
}

.metric-icon.cart {
  background: #f1effb;
  color: #6458a4;
}

.metric-card span {
  display: block;

  color: #76827c;

  font-size: 11px;
  font-weight: 650;
}

.metric-card strong {
  display: block;

  margin-top: 2px;

  color: #1c2923;

  font-size: 23px;
}

/* LAYOUT */

.orders-layout {
  display: grid;

  grid-template-columns:
    minmax(0, 1.65fr)
    minmax(300px, 0.75fr);

  gap: 18px;

  align-items: start;
}

.panel-card,
.history-card {
  border: 1px solid #e3e9e6;
  border-radius: 17px;

  background: #ffffff;

  box-shadow:
    0 7px 24px rgba(18, 45, 34, 0.04);
}

.panel-card {
  padding: 24px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;

  margin-bottom: 22px;
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

.panel-header h2,
.history-header h2 {
  margin: 0 0 5px;

  color: #1c2a23;

  font-size: 21px;
}

.panel-header p,
.history-header p {
  margin: 0;

  color: #77837d;

  font-size: 12.5px;
  line-height: 1.5;
}

.item-count,
.history-count {
  flex-shrink: 0;

  padding: 7px 10px;

  border-radius: 999px;

  background: #f1f6f3;
  color: #4d6358;

  font-size: 11px;
  font-weight: 700;
}

/* FIELDS */

.field {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.field label {
  color: #3d4c45;

  font-size: 12px;
  font-weight: 700;
}

.field small {
  color: #919b96;

  font-size: 10.5px;
}

.field input,
.field select {
  width: 100%;

  padding: 11px 12px;

  border: 1px solid #d9e0dc;
  border-radius: 9px;

  background: #ffffff;

  color: #202d27;

  font-size: 13px;

  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.field input:focus,
.field select:focus {
  outline: none;

  border-color: #559579;

  box-shadow:
    0 0 0 3px rgba(64, 137, 105, 0.11);
}

.product-selector {
  display: grid;

  grid-template-columns:
    minmax(0, 1fr)
    105px
    auto;

  gap: 12px;

  align-items: end;

  margin-top: 18px;
}

.add-button {
  height: 40px;

  border: none;
  border-radius: 9px;

  padding: 0 17px;

  background:
    linear-gradient(
      135deg,
      #2a7559,
      #21684f
    );

  color: white;

  cursor: pointer;

  font-size: 12px;
  font-weight: 700;

  box-shadow:
    0 6px 13px rgba(33, 104, 79, 0.14);

  transition:
    transform 0.18s ease,
    box-shadow 0.2s ease;
}

.add-button:hover {
  transform: translateY(-1px);

  box-shadow:
    0 9px 18px rgba(33, 104, 79, 0.2);
}

.add-button:active {
  transform: translateY(1px) scale(0.98);
}

.add-button:disabled {
  opacity: 0.55;

  cursor: not-allowed;

  transform: none;
}

/* CART */

.cart-list {
  display: flex;
  flex-direction: column;

  margin-top: 22px;

  border-top: 1px solid #eef2ef;
}

.cart-item {
  display: flex;
  justify-content: space-between;
  align-items: center;

  gap: 18px;

  padding: 15px 0;

  border-bottom: 1px solid #eef2ef;
}

.cart-product {
  display: flex;
  align-items: center;
  gap: 11px;
}

.product-avatar {
  width: 36px;
  height: 36px;

  flex-shrink: 0;

  display: grid;
  place-items: center;

  border-radius: 10px;

  background:
    linear-gradient(
      135deg,
      #e8f3ed,
      #dceae2
    );

  color: #28694f;

  font-size: 12px;
  font-weight: 800;
}

.cart-product strong {
  display: block;

  color: #1e2c25;

  font-size: 13px;
}

.cart-product span {
  color: #818c86;

  font-size: 11px;
}

.cart-details {
  display: flex;
  align-items: center;
  gap: 13px;
}

.quantity-summary {
  text-align: right;
}

.quantity-summary span {
  display: block;

  color: #7b8781;

  font-size: 11px;
}

.quantity-summary strong {
  display: block;

  margin-top: 2px;

  color: #1d2a24;

  font-size: 14px;
}

.remove-button {
  width: 30px;
  height: 30px;

  border: none;
  border-radius: 8px;

  background: #fceaea;
  color: #aa3d3d;

  cursor: pointer;

  font-size: 16px;

  transition:
    transform 0.18s ease,
    background 0.2s ease;
}

.remove-button:hover {
  transform: scale(1.06);

  background: #f8dddd;
}

.empty-cart {
  min-height: 195px;

  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;

  padding: 30px;

  text-align: center;
}

.empty-cart-icon,
.empty-mini-icon {
  width: 47px;
  height: 47px;

  display: grid;
  place-items: center;

  margin-bottom: 10px;

  border-radius: 13px;

  background: #edf5f1;
  color: #356f58;

  font-size: 20px;
}

.empty-cart strong,
.empty-mini-state strong {
  color: #28352f;

  font-size: 14px;
}

.empty-cart span,
.empty-mini-state span {
  margin-top: 4px;

  color: #818d87;

  font-size: 11.5px;
}

/* SUMMARY */

.order-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;

  margin-top: 20px;
  padding: 17px 0;

  border-top: 1px solid #e9eeeb;
}

.order-summary span {
  display: block;

  color: #37463f;

  font-size: 13px;
  font-weight: 700;
}

.order-summary small {
  display: block;

  margin-top: 3px;

  color: #8a958f;

  font-size: 10px;
}

.order-summary > strong {
  color: #17241e;

  font-size: 24px;
}

.order-actions {
  display: flex;
  justify-content: flex-end;
  gap: 9px;
}

.primary-button,
.secondary-button,
.refresh-button {
  border-radius: 9px;

  cursor: pointer;

  font-size: 12px;
  font-weight: 700;

  transition:
    transform 0.18s ease,
    box-shadow 0.2s ease,
    border-color 0.2s ease;
}

.primary-button {
  border: none;

  padding: 11px 17px;

  background:
    linear-gradient(
      135deg,
      #287457,
      #1f664c
    );

  color: white;

  box-shadow:
    0 6px 14px rgba(31, 102, 76, 0.16);
}

.secondary-button,
.refresh-button {
  border: 1px solid #dce3df;

  padding: 10px 15px;

  background: #ffffff;

  color: #46524c;
}

.primary-button:hover,
.refresh-button:hover,
.secondary-button:hover {
  transform: translateY(-1px);
}

.primary-button:disabled,
.secondary-button:disabled {
  opacity: 0.55;

  cursor: not-allowed;

  transform: none;
}

.refresh-button {
  display: flex;
  align-items: center;
  gap: 7px;
}

.refresh-icon {
  font-size: 15px;
}

/* INVENTORY */

.inventory-list {
  display: flex;
  flex-direction: column;
}

.inventory-item {
  display: flex;
  justify-content: space-between;
  align-items: center;

  padding: 13px 0;

  border-bottom: 1px solid #edf1ef;
}

.inventory-product {
  display: flex;
  align-items: center;
  gap: 10px;
}

.inventory-avatar {
  width: 35px;
  height: 35px;

  display: grid;
  place-items: center;

  border-radius: 10px;

  background: #edf5f1;
  color: #316b53;

  font-weight: 800;
}

.inventory-product strong {
  display: block;

  color: #24312b;

  font-size: 13px;
}

.inventory-product span {
  color: #818c87;

  font-size: 11px;
}

.stock-chip {
  min-width: 36px;

  padding: 5px 9px;

  border-radius: 999px;

  background: #e6f6ec;
  color: #277049;

  text-align: center;

  font-size: 11px;
  font-weight: 800;
}

.stock-chip.low {
  background: #fff3cf;
  color: #8e6418;
}

.stock-chip.empty {
  background: #feeaea;
  color: #ab3939;
}

/* HISTORY */

.history-card {
  overflow: hidden;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 15px;

  padding: 22px 24px;

  border-bottom: 1px solid #e8ecea;
}

.history-empty,
.empty-mini-state,
.mini-loading {
  min-height: 210px;

  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;

  text-align: center;
}

.table-container {
  overflow-x: auto;
}

table {
  width: 100%;

  border-collapse: collapse;
}

thead {
  background:
    linear-gradient(
      180deg,
      #fafcfb,
      #f7f9f8
    );
}

th {
  padding: 13px 20px;

  color: #78837e;

  text-align: left;

  font-size: 10px;
  font-weight: 800;

  text-transform: uppercase;
  letter-spacing: 0.7px;
}

td {
  padding: 15px 20px;

  border-top: 1px solid #eef2ef;

  color: #36433d;

  font-size: 12px;
}

tbody tr {
  transition: background 0.2s ease;
}

tbody tr:hover {
  background: #fbfcfc;
}

.order-id {
  display: inline-flex;

  padding: 5px 8px;

  border-radius: 6px;

  background: #f2f5f3;

  color: #44524a;

  font-family: monospace;

  font-weight: 700;
}

.carne,
.total-value {
  color: #25322c;
}

.date-value {
  color: #707c76;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;

  padding: 5px 9px;

  border-radius: 999px;

  text-transform: capitalize;

  font-size: 10.5px;
  font-weight: 750;
}

.status-dot-small {
  width: 6px;
  height: 6px;

  border-radius: 50%;
}

.status-badge.confirmed {
  background: #e8f7ed;
  color: #24704a;
}

.status-badge.confirmed .status-dot-small {
  background: #45a675;
}

.status-badge.rejected {
  background: #fceaea;
  color: #ac3e3e;
}

.status-badge.rejected .status-dot-small {
  background: #d25050;
}

/* LOADING */

.loader {
  width: 29px;
  height: 29px;

  margin-bottom: 10px;

  border: 3px solid #e4ede8;
  border-top-color: #3d8265;
  border-radius: 50%;

  animation: spin 0.8s linear infinite;
}

.mini-loading span {
  color: #7c8882;

  font-size: 11px;
}

/* TRANSITIONS */

.item-list-enter-active,
.item-list-leave-active {
  transition:
    opacity 0.25s ease,
    transform 0.28s ease;
}

.item-list-enter-from {
  opacity: 0;
  transform: translateY(-7px);
}

.item-list-leave-to {
  opacity: 0;
  transform: translateX(10px);
}

@keyframes contentIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.spinning {
  animation: spin 0.8s linear infinite;
}

/* RESPONSIVE */

@media (max-width: 1150px) {
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .orders-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 700px) {
  .hero-card {
    align-items: flex-start;
    flex-direction: column;
  }

  .metrics-grid {
    grid-template-columns: 1fr;
  }

  .product-selector {
    grid-template-columns: 1fr;
  }

  .cart-item {
    align-items: flex-start;
    flex-direction: column;
  }

  .cart-details {
    width: 100%;

    justify-content: space-between;
  }

  .history-header {
    flex-direction: column;
  }
}
</style>