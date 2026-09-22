<script setup>
defineProps({
  show: {
    type: Boolean,
    default: false,
  },

  title: {
    type: String,
    default: 'Confirmar acción',
  },

  message: {
    type: String,
    default: '',
  },

  confirmText: {
    type: String,
    default: 'Confirmar',
  },

  danger: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['confirm', 'cancel'])
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="show"
        class="modal-backdrop"
        @click.self="emit('cancel')"
      >
        <div class="modal-card">
          <div
            class="modal-icon"
            :class="{ danger }"
          >
            {{ danger ? '!' : '?' }}
          </div>

          <h2>{{ title }}</h2>

          <p>
            {{ message }}
          </p>

          <div class="modal-actions">
            <button
              class="button secondary"
              @click="emit('cancel')"
            >
              Cancelar
            </button>

            <button
              class="button"
              :class="danger ? 'danger-button' : 'primary'"
              @click="emit('confirm')"
            >
              {{ confirmText }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 2500;

  display: grid;
  place-items: center;

  padding: 24px;

  background: rgba(12, 22, 18, 0.48);
  backdrop-filter: blur(7px);
}

.modal-card {
  width: min(430px, 100%);

  padding: 30px;

  background: #ffffff;

  border: 1px solid rgba(255, 255, 255, 0.7);
  border-radius: 20px;

  text-align: center;

  box-shadow:
    0 30px 70px rgba(9, 20, 15, 0.22),
    0 5px 20px rgba(9, 20, 15, 0.08);
}

.modal-icon {
  width: 54px;
  height: 54px;

  margin: 0 auto 18px;

  display: grid;
  place-items: center;

  border-radius: 16px;

  background: #e8f4ee;
  color: #216f52;

  font-size: 25px;
  font-weight: 800;
}

.modal-icon.danger {
  background: #feecec;
  color: #c23c3c;
}

.modal-card h2 {
  margin: 0 0 9px;

  color: #182620;

  font-size: 21px;
}

.modal-card p {
  margin: 0 auto;

  max-width: 340px;

  color: #66716c;

  font-size: 14px;
  line-height: 1.6;
}

.modal-actions {
  display: flex;
  justify-content: center;
  gap: 11px;

  margin-top: 26px;
}

.button {
  min-width: 110px;

  border: none;
  border-radius: 10px;

  padding: 11px 18px;

  cursor: pointer;

  font-weight: 650;

  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease,
    background 0.18s ease;
}

.button:hover {
  transform: translateY(-1px);
}

.button:active {
  transform: translateY(1px) scale(0.98);
}

.secondary {
  border: 1px solid #dce1df;
  background: #ffffff;
  color: #4a5651;
}

.secondary:hover {
  background: #f5f7f6;
}

.primary {
  background: #236d51;
  color: #ffffff;

  box-shadow: 0 7px 16px rgba(35, 109, 81, 0.2);
}

.danger-button {
  background: #c74343;
  color: #ffffff;

  box-shadow: 0 7px 16px rgba(199, 67, 67, 0.2);
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.25s ease;
}

.modal-enter-active .modal-card,
.modal-leave-active .modal-card {
  transition:
    transform 0.32s cubic-bezier(0.16, 1, 0.3, 1),
    opacity 0.25s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-card,
.modal-leave-to .modal-card {
  opacity: 0;
  transform: translateY(18px) scale(0.94);
}
</style>