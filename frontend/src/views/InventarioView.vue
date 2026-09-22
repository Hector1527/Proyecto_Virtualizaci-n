<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'

import AppToast from '../components/AppToast.vue'
import ConfirmModal from '../components/ConfirmModal.vue'

const productos = ref([])
const cargando = ref(true)

const mostrarFormulario = ref(false)
const editando = ref(false)
const productoEditandoId = ref(null)

const mostrarConfirmacion = ref(false)
const productoAEliminar = ref(null)
const eliminando = ref(false)

const toast = ref({
  show: false,
  type: 'success',
  message: '',
})

let toastTimer = null

const formulario = ref({
  sku: '',
  nombre: '',
  categoria: '',
  precio_q: '',
  stock: '',
})

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

function limpiarFormulario() {
  formulario.value = {
    sku: '',
    nombre: '',
    categoria: '',
    precio_q: '',
    stock: '',
  }

  editando.value = false
  productoEditandoId.value = null
}

function abrirFormularioNuevo() {
  limpiarFormulario()
  mostrarFormulario.value = true
}

function cancelarFormulario() {
  limpiarFormulario()
  mostrarFormulario.value = false
}

async function cargarProductos(mostrarMensaje = false) {
  try {
    cargando.value = true

    const response = await fetch('/api/inventario/productos')

    if (!response.ok) {
      throw new Error('No se pudo cargar el inventario.')
    }

    productos.value = await response.json()

    if (mostrarMensaje) {
      mostrarToast(
        'success',
        'La información del inventario se actualizó correctamente.',
      )
    }
  } catch (err) {
    console.error(err)

    mostrarToast(
      'error',
      err instanceof Error
        ? err.message
        : 'No se pudo conectar con el servicio de inventario.',
    )
  } finally {
    cargando.value = false
  }
}

async function guardarProducto() {
  try {
    if (
      !formulario.value.sku.trim() ||
      !formulario.value.nombre.trim() ||
      !formulario.value.categoria.trim() ||
      formulario.value.precio_q === '' ||
      formulario.value.stock === ''
    ) {
      mostrarToast(
        'warning',
        'Completa todos los campos antes de guardar el producto.',
      )

      return
    }

    if (Number(formulario.value.precio_q) < 0) {
      mostrarToast(
        'warning',
        'El precio del producto no puede ser negativo.',
      )

      return
    }

    if (Number(formulario.value.stock) < 0) {
      mostrarToast(
        'warning',
        'El stock del producto no puede ser negativo.',
      )

      return
    }

    let response

    if (editando.value) {
      response = await fetch(
        `/api/inventario/productos/${productoEditandoId.value}`,
        {
          method: 'PUT',

          headers: {
            'Content-Type': 'application/json',
          },

          body: JSON.stringify({
            nombre: formulario.value.nombre.trim(),
            categoria: formulario.value.categoria.trim(),
            precio_q: Number(formulario.value.precio_q),
            stock: Number(formulario.value.stock),
          }),
        },
      )
    } else {
      response = await fetch('/api/inventario/productos', {
        method: 'POST',

        headers: {
          'Content-Type': 'application/json',
        },

        body: JSON.stringify({
          sku: formulario.value.sku.trim(),
          nombre: formulario.value.nombre.trim(),
          categoria: formulario.value.categoria.trim(),
          precio_q: Number(formulario.value.precio_q),
          stock: Number(formulario.value.stock),
        }),
      })
    }

    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      if (response.status === 409) {
        throw new Error(
          'Ya existe un producto registrado con ese SKU.',
        )
      }

      if (response.status === 400) {
        throw new Error(
          data.error ||
            data.mensaje ||
            'Revisa los datos ingresados.',
        )
      }

      throw new Error(
        data.error ||
          data.mensaje ||
          'No se pudo guardar el producto.',
      )
    }

    const estabaEditando = editando.value

    cancelarFormulario()

    await cargarProductos()

    mostrarToast(
      'success',
      estabaEditando
        ? 'Producto actualizado correctamente.'
        : 'Producto creado correctamente.',
    )
  } catch (err) {
    console.error(err)

    mostrarToast(
      'error',
      err instanceof Error
        ? err.message
        : 'No se pudo guardar el producto.',
    )
  }
}

function editarProducto(producto) {
  formulario.value = {
    sku: producto.sku,
    nombre: producto.nombre,
    categoria: producto.categoria,
    precio_q: producto.precio_q,
    stock: producto.stock,
  }

  editando.value = true
  productoEditandoId.value = producto.id
  mostrarFormulario.value = true

  window.scrollTo({
    top: 0,
    behavior: 'smooth',
  })
}

function solicitarEliminar(producto) {
  productoAEliminar.value = producto
  mostrarConfirmacion.value = true
}

function cancelarEliminar() {
  if (eliminando.value) {
    return
  }

  mostrarConfirmacion.value = false
  productoAEliminar.value = null
}

async function confirmarEliminar() {
  if (!productoAEliminar.value) {
    return
  }

  try {
    eliminando.value = true

    const nombreProducto = productoAEliminar.value.nombre

    const response = await fetch(
      `/api/inventario/productos/${productoAEliminar.value.id}`,
      {
        method: 'DELETE',
      },
    )

    if (!response.ok) {
      throw new Error(
        'No se pudo eliminar el producto seleccionado.',
      )
    }

    mostrarConfirmacion.value = false
    productoAEliminar.value = null

    await cargarProductos()

    mostrarToast(
      'success',
      `${nombreProducto} fue eliminado correctamente del inventario.`,
    )
  } catch (err) {
    console.error(err)

    mostrarToast(
      'error',
      err instanceof Error
        ? err.message
        : 'No se pudo eliminar el producto.',
    )
  } finally {
    eliminando.value = false
  }
}

function formatoMoneda(valor) {
  return Number(valor || 0).toLocaleString('es-GT', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

onMounted(() => {
  cargarProductos()
})

onBeforeUnmount(() => {
  if (toastTimer) {
    clearTimeout(toastTimer)
  }
})
</script>

<template>
  <div class="inventory-page">
    <!-- NOTIFICACIONES -->
    <AppToast
      :show="toast.show"
      :type="toast.type"
      :message="toast.message"
      @close="cerrarToast"
    />

    <!-- ENCABEZADO -->
    <div class="page-header">
      <div>
        <div class="eyebrow">
          Gestión de productos
        </div>

        <h1>Inventario</h1>

        <p>
          Administra los productos y existencias de
          Distribuidora El Quetzal.
        </p>
      </div>

      <button
        class="primary-button new-product-button"
        @click="abrirFormularioNuevo"
      >
        <span class="button-plus">+</span>
        Nuevo producto
      </button>
    </div>

    <!-- FORMULARIO -->
    <Transition name="form-panel">
      <section
        v-if="mostrarFormulario"
        class="form-card"
      >
        <div class="form-header">
          <div>
            <div class="form-badge">
              {{ editando ? 'Edición' : 'Nuevo registro' }}
            </div>

            <h2>
              {{
                editando
                  ? 'Editar producto'
                  : 'Nuevo producto'
              }}
            </h2>

            <p>
              {{
                editando
                  ? 'Actualiza la información del producto seleccionado.'
                  : 'Completa los datos para agregar un producto al inventario.'
              }}
            </p>
          </div>

          <button
            class="close-button"
            aria-label="Cerrar formulario"
            @click="cancelarFormulario"
          >
            ×
          </button>
        </div>

        <form
          class="product-form"
          @submit.prevent="guardarProducto"
        >
          <div class="field">
            <label for="sku">
              SKU
            </label>

            <input
              id="sku"
              v-model="formulario.sku"
              type="text"
              placeholder="Ej. A1"
              :disabled="editando"
            />

            <small>
              Identificador único del producto
            </small>
          </div>

          <div class="field">
            <label for="nombre">
              Nombre
            </label>

            <input
              id="nombre"
              v-model="formulario.nombre"
              type="text"
              placeholder="Ej. Mouse Logitech"
            />

            <small>
              Nombre comercial
            </small>
          </div>

          <div class="field">
            <label for="categoria">
              Categoría
            </label>

            <input
              id="categoria"
              v-model="formulario.categoria"
              type="text"
              placeholder="Ej. Periféricos"
            />

            <small>
              Clasificación del producto
            </small>
          </div>

          <div class="field">
            <label for="precio">
              Precio (Q)
            </label>

            <input
              id="precio"
              v-model="formulario.precio_q"
              type="number"
              min="0"
              step="0.01"
              placeholder="0.00"
            />

            <small>
              Precio unitario
            </small>
          </div>

          <div class="field">
            <label for="stock">
              Stock
            </label>

            <input
              id="stock"
              v-model="formulario.stock"
              type="number"
              min="0"
              step="1"
              placeholder="0"
            />

            <small>
              Unidades disponibles
            </small>
          </div>

          <div class="form-actions">
            <button
              type="button"
              class="secondary-button"
              @click="cancelarFormulario"
            >
              Cancelar
            </button>

            <button
              type="submit"
              class="primary-button"
            >
              {{
                editando
                  ? 'Guardar cambios'
                  : 'Crear producto'
              }}
            </button>
          </div>
        </form>
      </section>
    </Transition>

    <!-- TABLA -->
    <section class="table-card">
      <div class="table-header">
        <div>
          <h2>Productos</h2>

          <p>
            {{ productos.length }}
            {{
              productos.length === 1
                ? 'producto registrado'
                : 'productos registrados'
            }}
          </p>
        </div>

        <button
          class="refresh-button"
          :disabled="cargando"
          @click="cargarProductos(true)"
        >
          <span
            class="refresh-icon"
            :class="{ spinning: cargando }"
          >
            ↻
          </span>

          Actualizar
        </button>
      </div>

      <!-- CARGANDO -->
      <div
        v-if="cargando"
        class="loading-state"
      >
        <div class="loader"></div>

        <strong>Cargando inventario</strong>

        <span>
          Estamos obteniendo la información más reciente.
        </span>
      </div>

      <!-- VACÍO -->
      <div
        v-else-if="productos.length === 0"
        class="empty-state"
      >
        <div class="empty-icon">
          ▦
        </div>

        <h3>
          El inventario está vacío
        </h3>

        <p>
          Agrega el primer producto para comenzar
          a administrar existencias.
        </p>

        <button
          class="primary-button"
          @click="abrirFormularioNuevo"
        >
          + Agregar producto
        </button>
      </div>

      <!-- PRODUCTOS -->
      <div
        v-else
        class="table-container"
      >
        <table>
          <thead>
            <tr>
              <th>SKU</th>
              <th>Producto</th>
              <th>Categoría</th>
              <th>Precio</th>
              <th>Stock</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>

          <tbody>
            <tr
              v-for="producto in productos"
              :key="producto.id"
            >
              <td>
                <span class="sku">
                  {{ producto.sku }}
                </span>
              </td>

              <td>
                <div class="product-name">
                  <div class="product-avatar">
                    {{ producto.nombre.charAt(0).toUpperCase() }}
                  </div>

                  <strong>
                    {{ producto.nombre }}
                  </strong>
                </div>
              </td>

              <td>
                <span class="category">
                  {{ producto.categoria }}
                </span>
              </td>

              <td>
                <strong class="price">
                  Q {{ formatoMoneda(producto.precio_q) }}
                </strong>
              </td>

              <td>
                <span
                  class="stock-badge"
                  :class="{
                    low: producto.stock <= 5,
                    empty: producto.stock === 0,
                  }"
                >
                  {{ producto.stock }}
                </span>
              </td>

              <td>
                <span
                  class="status-badge"
                  :class="{
                    normal: producto.stock > 5,
                    warning:
                      producto.stock > 0 &&
                      producto.stock <= 5,
                    danger: producto.stock === 0,
                  }"
                >
                  <span class="status-dot-small"></span>

                  {{
                    producto.stock === 0
                      ? 'Sin stock'
                      : producto.stock <= 5
                        ? 'Stock bajo'
                        : 'Disponible'
                  }}
                </span>
              </td>

              <td>
                <div class="actions">
                  <button
                    class="edit-button"
                    @click="editarProducto(producto)"
                  >
                    Editar
                  </button>

                  <button
                    class="delete-button"
                    @click="solicitarEliminar(producto)"
                  >
                    Eliminar
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- MODAL DE ELIMINACIÓN -->
    <ConfirmModal
      :show="mostrarConfirmacion"
      title="Eliminar producto"
      :message="
        productoAEliminar
          ? `¿Deseas eliminar '${productoAEliminar.nombre}' del inventario? Esta acción es permanente y no se puede deshacer.`
          : ''
      "
      :confirm-text="
        eliminando
          ? 'Eliminando...'
          : 'Eliminar producto'
      "
      danger
      @confirm="confirmarEliminar"
      @cancel="cancelarEliminar"
    />
  </div>
</template>

<style scoped>
.inventory-page {
  animation: contentIn 0.38s ease both;
}

/* ENCABEZADO */

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;

  gap: 24px;

  margin-bottom: 28px;
}

.eyebrow {
  margin-bottom: 6px;

  color: #34785c;

  font-size: 11px;
  font-weight: 750;

  text-transform: uppercase;
  letter-spacing: 1.05px;
}

.page-header h1 {
  margin: 0 0 7px;

  color: #17231e;

  font-size: 32px;
  line-height: 1.15;

  letter-spacing: -0.7px;
}

.page-header p {
  margin: 0;

  color: #6b7771;

  font-size: 15px;
}

.new-product-button {
  flex-shrink: 0;
}

.button-plus {
  margin-right: 5px;

  font-size: 18px;
  line-height: 0;
}

/* BOTONES */

.primary-button {
  border: none;

  padding: 11px 18px;

  border-radius: 10px;

  background:
    linear-gradient(
      135deg,
      #287457,
      #1f664c
    );

  color: white;

  cursor: pointer;

  font-size: 13px;
  font-weight: 700;

  box-shadow:
    0 6px 14px rgba(31, 102, 76, 0.16);

  transition:
    transform 0.18s ease,
    box-shadow 0.2s ease,
    background 0.2s ease;
}

.primary-button:hover {
  transform: translateY(-2px);

  box-shadow:
    0 10px 22px rgba(31, 102, 76, 0.23);
}

.primary-button:active {
  transform: translateY(1px) scale(0.98);
}

.secondary-button,
.refresh-button {
  border: 1px solid #dce3df;

  padding: 10px 16px;

  border-radius: 9px;

  background: #ffffff;

  color: #46524c;

  cursor: pointer;

  font-size: 13px;
  font-weight: 650;

  transition:
    transform 0.18s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    background 0.2s ease;
}

.secondary-button:hover,
.refresh-button:hover {
  transform: translateY(-1px);

  border-color: #bdcbc3;

  background: #fafcfb;

  box-shadow:
    0 5px 13px rgba(26, 50, 39, 0.06);
}

.refresh-button {
  display: flex;
  align-items: center;
  gap: 7px;
}

.refresh-button:disabled {
  opacity: 0.6;

  cursor: default;
  transform: none;
}

.refresh-icon {
  font-size: 16px;
}

/* FORMULARIO */

.form-card {
  position: relative;

  margin-bottom: 24px;
  padding: 26px;

  overflow: hidden;

  border: 1px solid #dfe7e2;
  border-radius: 16px;

  background:
    linear-gradient(
      135deg,
      rgba(245, 250, 247, 0.95),
      #ffffff 45%
    );

  box-shadow:
    0 8px 28px rgba(18, 61, 46, 0.06);
}

.form-card::before {
  content: '';

  position: absolute;
  top: 0;
  left: 0;

  width: 100%;
  height: 3px;

  background:
    linear-gradient(
      90deg,
      #286f54,
      #71ad91
    );
}

.form-header {
  display: flex;
  justify-content: space-between;
  gap: 20px;

  margin-bottom: 24px;
}

.form-badge {
  display: inline-flex;

  margin-bottom: 8px;
  padding: 5px 9px;

  border-radius: 999px;

  background: #e7f3ed;
  color: #246348;

  font-size: 10px;
  font-weight: 750;

  text-transform: uppercase;
  letter-spacing: 0.8px;
}

.form-header h2,
.table-header h2 {
  margin: 0 0 5px;

  color: #1a2922;

  font-size: 20px;
  letter-spacing: -0.25px;
}

.form-header p,
.table-header p {
  margin: 0;

  color: #74807a;

  font-size: 13px;
}

.close-button {
  width: 35px;
  height: 35px;

  flex-shrink: 0;

  border: none;
  border-radius: 9px;

  background: transparent;

  color: #78837e;

  cursor: pointer;

  font-size: 23px;

  transition:
    background 0.2s ease,
    color 0.2s ease,
    transform 0.2s ease;
}

.close-button:hover {
  background: #f0f3f1;
  color: #26362f;

  transform: rotate(4deg);
}

.product-form {
  display: grid;

  grid-template-columns:
    minmax(120px, 0.8fr)
    minmax(180px, 1.3fr)
    minmax(150px, 1fr)
    minmax(130px, 0.8fr)
    minmax(100px, 0.6fr);

  gap: 18px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.field label {
  color: #3b4a43;

  font-size: 12px;
  font-weight: 700;
}

.field small {
  color: #939c97;

  font-size: 10px;
}

.field input {
  width: 100%;

  padding: 11px 12px;

  border: 1px solid #d9e0dc;
  border-radius: 9px;

  background: rgba(255, 255, 255, 0.92);

  color: #1f2c26;

  font-size: 13px;

  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    background 0.2s ease;
}

.field input:hover {
  border-color: #c2cec8;
}

.field input:focus {
  outline: none;

  border-color: #559579;

  box-shadow:
    0 0 0 3px rgba(64, 137, 105, 0.11);

  background: #ffffff;
}

.field input:disabled {
  background: #f0f3f1;
  color: #7a8580;

  cursor: not-allowed;
}

.form-actions {
  grid-column: 1 / -1;

  display: flex;
  justify-content: flex-end;
  gap: 10px;

  margin-top: 5px;
}

/* TABLA */

.table-card {
  overflow: hidden;

  border: 1px solid #e1e7e4;
  border-radius: 16px;

  background: #ffffff;

  box-shadow:
    0 4px 18px rgba(19, 45, 33, 0.045);
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;

  padding: 21px 24px;

  border-bottom: 1px solid #e9edeb;
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

  color: #77817c;

  text-align: left;

  font-size: 10.5px;
  font-weight: 750;

  text-transform: uppercase;
  letter-spacing: 0.7px;
}

td {
  padding: 15px 20px;

  border-top: 1px solid #eff2f0;

  color: #334039;

  font-size: 13px;

  transition:
    background 0.2s ease;
}

tbody tr {
  transition:
    background 0.2s ease,
    transform 0.2s ease;
}

tbody tr:hover td {
  background: #fbfcfc;
}

.sku {
  display: inline-flex;

  padding: 5px 8px;

  border: 1px solid #e5e9e7;
  border-radius: 6px;

  background: #f4f6f5;

  color: #344139;

  font-family:
    "SFMono-Regular",
    Consolas,
    monospace;

  font-size: 11px;
  font-weight: 650;
}

.product-name {
  display: flex;
  align-items: center;
  gap: 10px;
}

.product-avatar {
  width: 32px;
  height: 32px;

  flex-shrink: 0;

  display: grid;
  place-items: center;

  border-radius: 9px;

  background:
    linear-gradient(
      135deg,
      #e8f3ed,
      #dcebe3
    );

  color: #27684e;

  font-size: 12px;
  font-weight: 800;
}

.product-name strong {
  color: #1d2b24;

  font-size: 13px;
}

.category {
  color: #64716a;
}

.price {
  color: #24322b;

  font-weight: 700;
}

/* STOCK */

.stock-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;

  min-width: 36px;

  padding: 5px 9px;

  border-radius: 999px;

  background: #e4f7eb;
  color: #267148;

  font-size: 12px;
  font-weight: 750;
}

.stock-badge.low {
  background: #fff3cf;
  color: #916410;
}

.stock-badge.empty {
  background: #fee8e8;
  color: #ac3434;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;

  padding: 5px 9px;

  border-radius: 999px;

  font-size: 10.5px;
  font-weight: 700;
}

.status-dot-small {
  width: 6px;
  height: 6px;

  border-radius: 50%;
}

.status-badge.normal {
  background: #edf8f2;
  color: #287251;
}

.status-badge.normal .status-dot-small {
  background: #45a475;
}

.status-badge.warning {
  background: #fff7df;
  color: #8c671d;
}

.status-badge.warning .status-dot-small {
  background: #d8a735;
}

.status-badge.danger {
  background: #feeeee;
  color: #a93a3a;
}

.status-badge.danger .status-dot-small {
  background: #d45151;
}

/* ACCIONES */

.actions {
  display: flex;
  gap: 7px;
}

.edit-button,
.delete-button {
  border: none;

  padding: 7px 11px;

  border-radius: 7px;

  cursor: pointer;

  font-size: 11px;
  font-weight: 700;

  transition:
    transform 0.18s ease,
    background 0.2s ease,
    box-shadow 0.2s ease;
}

.edit-button {
  background: #eaf4ef;
  color: #2b684e;
}

.edit-button:hover {
  background: #dcece4;

  transform: translateY(-1px);

  box-shadow:
    0 4px 10px rgba(41, 104, 78, 0.08);
}

.delete-button {
  background: #fceaea;
  color: #a43a3a;
}

.delete-button:hover {
  background: #f9dddd;

  transform: translateY(-1px);

  box-shadow:
    0 4px 10px rgba(164, 58, 58, 0.08);
}

.edit-button:active,
.delete-button:active {
  transform: translateY(1px) scale(0.98);
}

/* CARGA Y VACÍO */

.loading-state,
.empty-state {
  min-height: 280px;

  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;

  padding: 45px 20px;

  text-align: center;
}

.loading-state strong,
.empty-state h3 {
  margin: 12px 0 5px;

  color: #25332c;

  font-size: 15px;
}

.loading-state span,
.empty-state p {
  margin: 0 0 18px;

  color: #7b857f;

  font-size: 12px;
}

.empty-icon {
  width: 50px;
  height: 50px;

  display: grid;
  place-items: center;

  border-radius: 14px;

  background: #edf5f1;
  color: #367359;

  font-size: 25px;
}

.loader {
  width: 30px;
  height: 30px;

  border: 3px solid #e4ede8;
  border-top-color: #3d8265;
  border-radius: 50%;

  animation: spin 0.75s linear infinite;
}

/* TRANSICIONES */

.form-panel-enter-active,
.form-panel-leave-active {
  transition:
    opacity 0.28s ease,
    transform 0.34s cubic-bezier(0.16, 1, 0.3, 1),
    max-height 0.4s ease;
}

.form-panel-enter-from,
.form-panel-leave-to {
  opacity: 0;

  transform: translateY(-10px) scale(0.985);
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
  animation: spin 0.75s linear infinite;
}

/* RESPONSIVE */

@media (max-width: 1150px) {
  .product-form {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 720px) {
  .page-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .product-form {
    grid-template-columns: 1fr;
  }

  .new-product-button {
    width: 100%;
  }

  .table-header {
    align-items: flex-start;
    gap: 12px;
    flex-direction: column;
  }
}

@media (prefers-reduced-motion: reduce) {
  .inventory-page {
    animation: none;
  }
}
</style>