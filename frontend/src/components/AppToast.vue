<script setup>
import { computed } from 'vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },

  type: {
    type: String,
    default: 'success',
  },

  message: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['close'])

const icono = computed(() => {
  if (props.type === 'error') return '!'
  if (props.type === 'warning') return '!'
  return '✓'
})

const titulo = computed(() => {
  if (props.type === 'error') return 'No se pudo completar'
  if (props.type === 'warning') return 'Atención'
  return 'Operación completada'
})
</script>

<template>
  <Transition name="toast">
    <div
      v-if="show"
      class="toast"
      :class="type"
    >
      <div class="toast-icon">
        {{ icono }}
      </div>

      <div class="toast-content">
        <strong>{{ titulo }}</strong>
        <span>{{ message }}</span>
      </div>

      <button
        class="toast-close"
        aria-label="Cerrar notificación"
        @click="emit('close')"
      >
        ×
      </button>
    </div>
  </Transition>
</template>

<style scoped>
.toast {
  position: fixed;
  top: 24px;
  right: 24px;
  z-index: 3000;

  width: min(420px, calc(100vw - 48px));

  display: flex;
  align-items: flex-start;
  gap: 13px;

  padding: 16px;

  background: rgba(255, 255, 255, 0.97);
  backdrop-filter: blur(18px);

  border: 1px solid #e5e7eb;
  border-radius: 14px;

  box-shadow:
    0 20px 45px rgba(15, 23, 42, 0.12),
    0 4px 12px rgba(15, 23, 42, 0.06);
}

.toast.success {
  border-left: 4px solid #24845e;
}

.toast.error {
  border-left: 4px solid #dc4c4c;
}

.toast.warning {
  border-left: 4px solid #d69e2e;
}

.toast-icon {
  flex-shrink: 0;

  width: 34px;
  height: 34px;

  display: flex;
  align-items: center;
  justify-content: center;

  border-radius: 10px;

  font-weight: 800;
}

.success .toast-icon {
  background: #e6f6ee;
  color: #19704e;
}

.error .toast-icon {
  background: #feecec;
  color: #b63030;
}

.warning .toast-icon {
  background: #fff4d7;
  color: #946413;
}

.toast-content {
  flex: 1;

  display: flex;
  flex-direction: column;
  gap: 3px;
}

.toast-content strong {
  color: #16251f;
  font-size: 14px;
}

.toast-content span {
  color: #64706b;
  font-size: 13px;
  line-height: 1.45;
}

.toast-close {
  border: 0;
  background: transparent;

  color: #8a9490;
  cursor: pointer;

  font-size: 21px;
  line-height: 1;

  transition:
    color 0.2s ease,
    transform 0.2s ease;
}

.toast-close:hover {
  color: #26332e;
  transform: scale(1.12);
}

.toast-enter-active,
.toast-leave-active {
  transition:
    opacity 0.3s ease,
    transform 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(-12px) translateX(20px) scale(0.96);
}
</style>