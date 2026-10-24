/**
 * SISTEMA DE ASISTENCIA - LÓGICA DEL CLIENTE (KIOSKO / TOTEM)
 * Manejo de eventos de teclado, peticiones asíncronas y transiciones de estado.
 */

// Configuración de la API: usa ruta relativa en servidores (Vercel o local) y localhost si se abre como archivo local
const API_URL = (window.location.protocol === 'file:') 
  ? 'http://localhost:8000/api/asistencia' 
  : '/api/asistencia';

// Elementos del DOM
const attendanceForm = document.getElementById('attendanceForm');
const dniInput       = document.getElementById('dniInput');
const celularInput   = document.getElementById('celularInput');
const nacimientoInput = document.getElementById('nacimientoInput');
const submitBtn      = document.getElementById('submitBtn');
const inputView      = document.getElementById('inputView');
const successView    = document.getElementById('successView');
const loadingState   = document.getElementById('loadingState');
const errorState     = document.getElementById('errorState');
const errorMessage   = document.getElementById('errorMessage');
const errorDetail    = document.getElementById('errorDetail');
const successAttendeeName = document.getElementById('successAttendeeName');
const successTimestamp    = document.getElementById('successTimestamp');
const successCelular      = document.getElementById('successCelular');
const celularPill         = document.getElementById('celularPill');
const successNac          = document.getElementById('successNac');
const nacPill             = document.getElementById('nacPill');
const countdownBar        = document.getElementById('countdownBar');
const liveClock           = document.getElementById('liveClock');

let isSubmitting = false;
let resetTimeout = null;

// =============================================================================
// 1. Reloj en Vivo en la Cabecera
// =============================================================================
function updateClock() {
  const now = new Date();
  liveClock.textContent = now.toLocaleTimeString('es-PE', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true
  });
}
setInterval(updateClock, 1000);
updateClock();

// =============================================================================
// 2. Control de Foco y Validación de Entrada
// =============================================================================
function focusInput() {
  if (!isSubmitting && successView.classList.contains('hidden')) {
    dniInput.focus();
  }
}

// Auto-enfoque al cargar la página
window.addEventListener('DOMContentLoaded', () => {
  focusInput();
});

// Permitir únicamente dígitos numéricos en ambos inputs
dniInput.addEventListener('input', () => {
  dniInput.value = dniInput.value.replace(/\D/g, '');
  hideError();
});

celularInput.addEventListener('input', () => {
  celularInput.value = celularInput.value.replace(/\D/g, '');
  hideError();
});

// Envío a través del evento submit del formulario (cubre clics en el botón y Enter estándar)
if (attendanceForm) {
  attendanceForm.addEventListener('submit', (e) => {
    e.preventDefault();
    if (!isSubmitting) {
      handleAttendanceSubmit();
    }
  });
}

// DNI: Enter envía la asistencia directamente (o valida y ejecuta)
dniInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    if (!isSubmitting) {
      handleAttendanceSubmit();
    }
  }
});

// Celular: Enter envía la asistencia
celularInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    if (!isSubmitting) {
      handleAttendanceSubmit();
    }
  }
});

// Fecha de Nacimiento: Enter envía la asistencia y change limpia errores
if (nacimientoInput) {
  nacimientoInput.addEventListener('change', () => {
    hideError();
  });
  nacimientoInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (!isSubmitting) {
        handleAttendanceSubmit();
      }
    }
  });
}

// =============================================================================
// 3. Envío Asíncrono de la Asistencia
// =============================================================================
async function handleAttendanceSubmit() {
  const dni             = dniInput.value.trim();
  const celular         = celularInput.value.trim();
  const fechaNacimiento = nacimientoInput ? nacimientoInput.value.trim() : '';

  // Validar DNI
  if (!/^\d{8}$/.test(dni)) {
    showError('DNI Inválido', 'El número debe contener exactamente 8 dígitos numéricos.');
    playTone(150, 'sawtooth', 0.2);
    dniInput.select();
    dniInput.focus();
    return;
  }

  // Validar celular solo si fue ingresado
  if (celular && !/^9\d{8}$/.test(celular)) {
    showError('Celular Inválido', 'El celular debe tener 9 dígitos y empezar con 9.');
    playTone(150, 'sawtooth', 0.2);
    celularInput.select();
    celularInput.focus();
    return;
  }

  // Validar fecha de nacimiento solo si fue ingresada
  if (fechaNacimiento) {
    const selectedDate = new Date(fechaNacimiento + 'T00:00:00');
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    if (isNaN(selectedDate.getTime())) {
      showError('Fecha Inválida', 'La fecha de nacimiento no es válida.');
      playTone(150, 'sawtooth', 0.2);
      if (nacimientoInput) nacimientoInput.focus();
      return;
    }
    if (selectedDate > today) {
      showError('Fecha Inválida', 'La fecha de nacimiento no puede ser una fecha futura.');
      playTone(150, 'sawtooth', 0.2);
      if (nacimientoInput) nacimientoInput.focus();
      return;
    }
    if (selectedDate.getFullYear() < 1900) {
      showError('Fecha Inválida', 'El año de nacimiento debe ser mayor a 1900.');
      playTone(150, 'sawtooth', 0.2);
      if (nacimientoInput) nacimientoInput.focus();
      return;
    }
  }

  setLoading(true);
  hideError();

  // Construir body: incluir campos opcionales solo si fueron ingresados
  const body = { dni };
  if (celular) body.celular = celular;
  if (fechaNacimiento) body.fecha_nacimiento = fechaNacimiento;

  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(body)
    });

    const data = await response.json();

    if (!response.ok || !data.success) {
      const msg = data.message || 'No fue posible registrar la asistencia.';
      const detail = data.detail || 'Verifique el DNI e intente de nuevo.';
      throw new Error(JSON.stringify({ msg, detail }));
    }

    // Éxito: mostrar pantalla gigante durante 3 segundos
    showSuccess(data.data);
    playChime(); // Sonido sutil de éxito

  } catch (error) {
    let msg = 'Error de conexión';
    let detail = 'No se pudo conectar con el servidor (verifique el backend).';

    try {
      const parsed = JSON.parse(error.message);
      msg = parsed.msg;
      detail = parsed.detail;
    } catch (_) {
      if (error.message && error.message !== '[object Object]') {
        msg = error.message;
      }
    }

    showError(msg, detail);
    playTone(150, 'sawtooth', 0.25);
    setLoading(false);
    dniInput.select();
  }
}

// =============================================================================
// 4. Gestión de Estados Visuales
// =============================================================================

function setLoading(loading) {
  isSubmitting          = loading;
  dniInput.disabled     = loading;
  celularInput.disabled = loading;
  if (nacimientoInput) {
    nacimientoInput.disabled = loading;
  }
  if (submitBtn) {
    submitBtn.disabled  = loading;
  }

  if (loading) {
    loadingState.classList.remove('hidden');
  } else {
    loadingState.classList.add('hidden');
  }
}

function showError(title, detail) {
  errorMessage.textContent = title;
  errorDetail.textContent = detail;
  errorState.classList.remove('hidden');

  // Auto-ocultar error después de 4 segundos
  setTimeout(() => {
    hideError();
  }, 4000);
}

function hideError() {
  errorState.classList.add('hidden');
}

function showSuccess(attendeeData) {
  setLoading(false);

  successAttendeeName.textContent = attendeeData.nombre_completo || 'Asistente';
  successTimestamp.textContent    = attendeeData.fecha_hora || new Date().toLocaleTimeString();

  // Mostrar celular en pill solo si viene en la respuesta
  if (attendeeData.celular) {
    successCelular.textContent = attendeeData.celular;
    celularPill.classList.remove('hidden');
  } else {
    celularPill.classList.add('hidden');
  }

  // Mostrar fecha de nacimiento en pill solo si viene en la respuesta
  if (attendeeData.fecha_nacimiento && successNac && nacPill) {
    const parts = attendeeData.fecha_nacimiento.split('-');
    const formattedDate = (parts.length === 3) 
      ? `${parts[2]}/${parts[1]}/${parts[0]}` 
      : attendeeData.fecha_nacimiento;
    successNac.textContent = formattedDate;
    nacPill.classList.remove('hidden');
  } else if (nacPill) {
    nacPill.classList.add('hidden');
  }

  inputView.classList.add('hidden');
  successView.classList.remove('hidden');

  countdownBar.classList.remove('countdown-active');
  void countdownBar.offsetWidth;
  countdownBar.classList.add('countdown-active');

  if (resetTimeout) clearTimeout(resetTimeout);

  resetTimeout = setTimeout(() => {
    resetKiosk();
  }, 3000);
}

function resetKiosk() {
  dniInput.value        = '';
  celularInput.value    = '';
  if (nacimientoInput) {
    nacimientoInput.value = '';
    nacimientoInput.disabled = false;
  }
  dniInput.disabled     = false;
  celularInput.disabled = false;
  if (submitBtn) {
    submitBtn.disabled  = false;
  }
  isSubmitting = false;

  successView.classList.add('hidden');
  inputView.classList.remove('hidden');
  hideError();

  focusInput();
}

// =============================================================================
// 5. Retroalimentación Sonora con Web Audio API (Sin archivos externos)
// =============================================================================
let audioCtx = null;

function getAudioContext() {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  }
  if (audioCtx.state === 'suspended') {
    audioCtx.resume();
  }
  return audioCtx;
}

// Sonido positivo armónico para confirmación
function playChime() {
  try {
    const ctx = getAudioContext();
    const now = ctx.currentTime;
    
    // Tono 1 (E5 - 659.25Hz)
    const osc1 = ctx.createOscillator();
    const gain1 = ctx.createGain();
    osc1.frequency.setValueAtTime(659.25, now);
    gain1.gain.setValueAtTime(0.12, now);
    gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.5);
    osc1.connect(gain1);
    gain1.connect(ctx.destination);
    osc1.start(now);
    osc1.stop(now + 0.5);

    // Tono 2 (B5 - 987.77Hz)
    const osc2 = ctx.createOscillator();
    const gain2 = ctx.createGain();
    osc2.frequency.setValueAtTime(987.77, now + 0.12);
    gain2.gain.setValueAtTime(0.15, now + 0.12);
    gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.65);
    osc2.connect(gain2);
    gain2.connect(ctx.destination);
    osc2.start(now + 0.12);
    osc2.stop(now + 0.65);
  } catch (_) {
    // Si el navegador bloquea audio, no interfiere con el flujo visual
  }
}

// Tono para errores de validación
function playTone(freq, type, duration) {
  try {
    const ctx = getAudioContext();
    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, now);
    gain.gain.setValueAtTime(0.1, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + duration);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(now);
    osc.stop(now + duration);
  } catch (_) {}
}
