// ============================================================
// app.js — Lógica Completa del Dashboard de Finanzas Personales
// Manejo de Sesión JWT, Fetch Seguro, KPIs, ML, Chart.js y CRUDs
// ============================================================

// ─────────────────────────────────────────
// CONFIGURACIÓN DINÁMICA DE LA URL DE LA API
// ─────────────────────────────────────────
// Si vas a desplegar el backend en Render / Railway, define su URL pública aquí:
const PRODUCTION_API_URL = 'https://aplicacion-finanzas.onrender.com';
const LOCAL_API_URL = 'http://127.0.0.1:8000';

function resolverApiUrl() {
    const hostname = (typeof window !== 'undefined' && window.location) ? window.location.hostname : '';
    const protocol = (typeof window !== 'undefined' && window.location) ? window.location.protocol : '';

    const esEntornoLocal = (
        protocol === 'file:' ||
        !hostname ||
        hostname === 'localhost' ||
        hostname === '127.0.0.1' ||
        hostname === '0.0.0.0'
    );

    if (esEntornoLocal) {
        return LOCAL_API_URL;
    }

    if (PRODUCTION_API_URL && PRODUCTION_API_URL.trim() !== '' && !PRODUCTION_API_URL.includes('tu-backend')) {
        return PRODUCTION_API_URL.trim().replace(/\/$/, '');
    }

    if (typeof window !== 'undefined' && window.location && window.location.origin && window.location.origin !== 'null') {
        return window.location.origin;
    }

    return LOCAL_API_URL;
}

const API_URL = resolverApiUrl();
const BASE_URL = `${API_URL.replace(/\/$/, '')}/api`;
const API_BASE_URL = BASE_URL; // Alias de compatibilidad global

// ─────────────────────────────────────────
// GESTIÓN DE AUTENTICACIÓN Y TOKENS (JWT)
// ─────────────────────────────────────────

const AUTH = {
    getAccessToken: () => localStorage.getItem('fp_access_token'),
    getRefreshToken: () => localStorage.getItem('fp_refresh_token'),
    getUser: () => {
        try {
            return JSON.parse(localStorage.getItem('fp_user_data')) || null;
        } catch (_) {
            return null;
        }
    },
    setSession: (accessToken, refreshToken, user) => {
        if (accessToken) localStorage.setItem('fp_access_token', accessToken);
        if (refreshToken) localStorage.setItem('fp_refresh_token', refreshToken);
        if (user) localStorage.setItem('fp_user_data', JSON.stringify(user));
        actualizarInfoUsuarioUI();
    },
    clearSession: () => {
        localStorage.removeItem('fp_access_token');
        localStorage.removeItem('fp_refresh_token');
        localStorage.removeItem('fp_user_data');
        actualizarInfoUsuarioUI();
    },
    isAuthenticated: () => !!localStorage.getItem('fp_access_token'),
};

/** Actualiza el widget del usuario en el sidebar */
function actualizarInfoUsuarioUI() {
    const user = AUTH.getUser();
    const nameEl = document.getElementById('user-display-name');
    const emailEl = document.getElementById('user-display-email');
    if (user && nameEl && emailEl) {
        nameEl.textContent = user.nombre || 'Usuario';
        emailEl.textContent = user.correo || 'Conectado';
    } else if (nameEl && emailEl) {
        nameEl.textContent = 'Sin Sesión';
        emailEl.textContent = 'Inicia sesión para ver tus datos';
    }
}

/** Control del Modal de Autenticación */
function mostrarModalAuth(tab = 'login') {
    const modal = document.getElementById('auth-modal');
    modal.style.display = 'flex';
    cambiarTabAuth(tab);
}

function ocultarModalAuth() {
    const modal = document.getElementById('auth-modal');
    modal.style.display = 'none';
}

function cambiarTabAuth(tab) {
    const tabLogin = document.getElementById('tab-login');
    const tabRegister = document.getElementById('tab-register');
    const formLogin = document.getElementById('form-login');
    const formRegister = document.getElementById('form-register');
    const titleEl = document.getElementById('auth-modal-title');
    const feedback = document.getElementById('auth-feedback');
    feedback.style.display = 'none';

    if (tab === 'login') {
        tabLogin.classList.add('active');
        tabRegister.classList.remove('active');
        formLogin.style.display = 'flex';
        formRegister.style.display = 'none';
        titleEl.textContent = 'Iniciar Sesión';
    } else {
        tabRegister.classList.add('active');
        tabLogin.classList.remove('active');
        formRegister.style.display = 'flex';
        formLogin.style.display = 'none';
        titleEl.textContent = 'Crear Cuenta';
    }
}

function autocompletarDemo() {
    const emailInput = document.getElementById('login-correo');
    const passInput = document.getElementById('login-password');
    const feedback = document.getElementById('auth-feedback');
    if (emailInput) emailInput.value = 'ana@example.com';
    if (passInput) passInput.value = 'Password123!';
    if (feedback) {
        feedback.style.display = 'none';
        feedback.textContent = '';
    }
}

function cerrarSesion() {
    if (confirm('¿Deseas cerrar tu sesión actual?')) {
        AUTH.clearSession();
        setEstadoAPI(false, 'Sesión finalizada');
        mostrarToast('Has cerrado sesión correctamente', 'info');
        mostrarModalAuth('login');
    }
}

// ─────────────────────────────────────────
// CLIENTE HTTP CON INTERCEPTOR DE TOKENS
// ─────────────────────────────────────────

let isRefreshing = false;

/**
 * Wrapper sobre fetch que inyecta el token Bearer JWT
 * y renueva automáticamente el token en caso de 401.
 */
async function apiFetch(endpoint, opciones = {}) {
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const apiPath = cleanEndpoint.startsWith('/api') ? cleanEndpoint : `/api${cleanEndpoint}`;
    const url = endpoint.startsWith('http') ? endpoint : `${API_URL.replace(/\/$/, '')}${apiPath}`;
    const token = AUTH.getAccessToken();

    const headers = {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        ...opciones.headers,
    };

    let response = await fetch(url, { ...opciones, headers });

    // Si el token expiró (401), intentar renovación con Refresh Token
    if (response.status === 401 && !opciones._retry && AUTH.getRefreshToken()) {
        if (!isRefreshing) {
            isRefreshing = true;
            try {
                const refreshResp = await fetch(`${API_URL.replace(/\/$/, '')}/api/auth/refresh`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ refresh_token: AUTH.getRefreshToken() }),
                });

                if (refreshResp.ok) {
                    const data = await refreshResp.json();
                    AUTH.setSession(data.access_token, data.refresh_token, data.usuario);
                    isRefreshing = false;
                    // Reintentar petición original
                    opciones._retry = true;
                    opciones.headers = {
                        ...opciones.headers,
                        'Authorization': `Bearer ${data.access_token}`,
                    };
                    return apiFetch(endpoint, opciones);
                } else {
                    // Refresh token inválido o expirado
                    AUTH.clearSession();
                    mostrarModalAuth('login');
                }
            } catch (e) {
                AUTH.clearSession();
                mostrarModalAuth('login');
            } finally {
                isRefreshing = false;
            }
        }
    }

    if (response.status === 401) {
        AUTH.clearSession();
        mostrarModalAuth('login');
        throw new Error('Sesión expirada. Por favor ingresa nuevamente.');
    }

    if (!response.ok) {
        let detalle = `Error ${response.status}: ${response.statusText}`;
        try {
            const errBody = await response.json();
            detalle = errBody.detalle || errBody.detail || errBody.error || detalle;
            if (Array.isArray(detalle)) detalle = detalle.join(', ');
        } catch (_) { }
        throw new Error(detalle);
    }

    return response.json();
}

// ─────────────────────────────────────────
// NOTIFICACIONES TOAST Y FEEDBACK
// ─────────────────────────────────────────

function mostrarToast(mensaje, tipo = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${tipo}`;
    const iconos = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
    toast.innerHTML = `<span>${iconos[tipo] || 'ℹ️'}</span><span>${mensaje}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(40px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function setEstadoAPI(conectado, textoCustom) {
    const badge = document.getElementById('api-status');
    const texto = document.getElementById('status-text');
    if (badge && texto) {
        badge.className = `status-badge ${conectado ? 'connected' : 'error'}`;
        texto.textContent = textoCustom || (conectado ? 'Conectado' : 'Sin conexión');
    }
}

function mostrarErrorGlobal(mensaje) {
    const banner = document.getElementById('error-banner');
    const msg = document.getElementById('error-banner-msg');
    if (banner && msg) {
        msg.textContent = mensaje;
        banner.style.display = 'flex';
    }
}

// ─────────────────────────────────────────
// FORMATO DE MONEDA
// ─────────────────────────────────────────

function formatearPesos(valor) {
    const num = parseFloat(valor) || 0;
    return new Intl.NumberFormat('es-CO', {
        style: 'currency',
        currency: 'COP',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
    }).format(num);
}

// ─────────────────────────────────────────
// NAVEGACIÓN SPA
// ─────────────────────────────────────────

function getSecciones() {
    return {
        'dashboard': document.getElementById('section-dashboard'),
        'movimientos': document.getElementById('section-movimientos'),
        'presupuestos-metas': document.getElementById('section-presupuestos-metas'),
        'analitica': document.getElementById('section-analitica'),
        'nuevo': document.getElementById('section-nuevo'),
    };
}

function toggleSidebar(abrir) {
    const sidebar = document.getElementById('sidebar') || document.querySelector('.sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    if (!sidebar) return;

    const estaAbierto = sidebar.classList.contains('open');
    const forzar = typeof abrir === 'boolean' ? abrir : !estaAbierto;

    if (forzar) {
        sidebar.classList.add('open');
        if (overlay) overlay.classList.add('active');
        document.body.classList.add('no-scroll');
    } else {
        sidebar.classList.remove('open');
        if (overlay) overlay.classList.remove('active');
        document.body.classList.remove('no-scroll');
    }
}

function navegarA(id) {
    const sec = getSecciones();
    Object.values(sec).forEach(s => s && s.classList.remove('active'));
    if (sec[id]) sec[id].classList.add('active');

    // Actualizar enlaces del sidebar lateral
    const links = document.querySelectorAll('.nav-link');
    links.forEach(link => link.classList.remove('active'));
    const linkActivo = document.getElementById(`nav-${id}`);
    if (linkActivo) linkActivo.classList.add('active');

    // Actualizar items de la barra inferior móvil
    const bnavItems = document.querySelectorAll('.bnav-item');
    bnavItems.forEach(bitem => {
        bitem.classList.remove('active');
        if (bitem.getAttribute('data-target') === id) {
            bitem.classList.add('active');
        }
    });

    const titulos = {
        'dashboard': ['Dashboard', 'Resumen financiero en tiempo real'],
        'movimientos': ['Historial de Movimientos', 'Consulta, filtra y gestiona ingresos y gastos'],
        'presupuestos-metas': ['Metas y Presupuestos', 'Planificación mensual y seguimiento de ahorro'],
        'analitica': ['Analítica Predictiva', 'Modelos Machine Learning e Inteligencia Financiera'],
        'nuevo': ['Registrar Movimiento', 'Agrega un nuevo ingreso o gasto a tu cuenta'],
    };

    if (titulos[id]) {
        const titleEl = document.getElementById('page-title');
        const subTitleEl = document.getElementById('page-subtitle');
        if (titleEl) titleEl.textContent = titulos[id][0];
        if (subTitleEl) subTitleEl.textContent = titulos[id][1];
    }

    // Cerrar sidebar en móviles tras seleccionar una opción
    toggleSidebar(false);

    // Desplazar al inicio suavemente
    window.scrollTo({ top: 0, behavior: 'smooth' });

    // Carga perezosa de secciones
    if (id === 'movimientos') cargarTablaMovimientos();
    if (id === 'presupuestos-metas') {
        cargarPresupuestos();
        cargarMetas();
        cargarCategorias();
    }
    if (id === 'analitica') cargarDetalleAnalitica();
}

// Event listeners para navegación lateral
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        const destino = link.id.replace('nav-', '');
        navegarA(destino);
    });
});

// Event listeners para barra inferior móvil
document.querySelectorAll('.bnav-item').forEach(bitem => {
    bitem.addEventListener('click', (e) => {
        e.preventDefault();
        const target = bitem.getAttribute('data-target');
        if (target) navegarA(target);
    });
});

// Botones de toggle para menú móvil
document.getElementById('btn-menu-toggle')?.addEventListener('click', () => toggleSidebar());
document.getElementById('btn-sidebar-close')?.addEventListener('click', () => toggleSidebar(false));
document.getElementById('sidebar-overlay')?.addEventListener('click', () => toggleSidebar(false));

// ─────────────────────────────────────────
// CARGA DE DATOS DEL DASHBOARD & KPIS
// ─────────────────────────────────────────

async function cargarResumen() {
    try {
        const data = await apiFetch('/resumen');
        const fIngresos = formatearPesos(data.total_ingresos);
        const fGastos = formatearPesos(data.total_gastos);
        const balance = data.balance;
        const fBalance = formatearPesos(balance);

        const elIngresos = document.getElementById('card-ingresos');
        const elGastos = document.getElementById('card-gastos');
        const elBalance = document.getElementById('card-balance');

        if (elIngresos) {
            elIngresos.textContent = fIngresos;
            elIngresos.title = fIngresos;
        }
        if (elGastos) {
            elGastos.textContent = fGastos;
            elGastos.title = fGastos;
        }
        if (elBalance) {
            elBalance.textContent = fBalance;
            elBalance.title = fBalance;
            elBalance.className = `kpi-value ${balance >= 0 ? 'text-income' : 'text-expense'}`;
        }

        const elAhorro = document.getElementById('card-tasa-ahorro');
        if (elAhorro) {
            elAhorro.textContent = data.porcentaje_ahorro > 0
                ? `🎯 Tasa de Ahorro: ${data.porcentaje_ahorro}%`
                : '💡 Sin ahorro neto acumulado';
        }

        setEstadoAPI(true, 'Conectado');
    } catch (err) {
        document.getElementById('card-ingresos').textContent = '$ 0';
        document.getElementById('card-gastos').textContent = '$ 0';
        document.getElementById('card-balance').textContent = '$ 0';
        setEstadoAPI(false);
    }
}

async function cargarPrediccion() {
    try {
        const data = await apiFetch('/analitica/prediccion');
        const fPred = formatearPesos(data.prediccion);
        const elPred = document.getElementById('card-prediccion');
        if (elPred) {
            elPred.textContent = fPred;
            elPred.title = fPred;
        }

        const badges = {
            alta: '🟢 Alta confianza',
            media: '🟡 Confianza media',
            baja: '🔴 Baja confianza',
        };
        const elConf = document.getElementById('prediccion-confianza');
        if (elConf) {
            elConf.textContent = badges[data.confianza] || data.confianza;
        }
    } catch (err) {
        document.getElementById('card-prediccion').textContent = 'No disponible';
    }
}

async function cargarAnomalias() {
    try {
        const data = await apiFetch('/analitica/anomalias?umbral_z=1.5');
        const alertBox = document.getElementById('alerta-anomalias');
        const lista = document.getElementById('lista-anomalias');

        if (data.anomalias && data.anomalias.length > 0) {
            alertBox.style.display = 'block';
            lista.innerHTML = data.anomalias.map(a => `
                <li>
                    📅 <strong>${a.fecha}</strong> — ${a.nombre_categoria}: 
                    <strong>${formatearPesos(a.monto)}</strong> 
                    (Promedio de la categoría: ${formatearPesos(a.promedio_categoria)} · Z-Score: ${a.z_score})
                </li>
            `).join('');
        } else {
            alertBox.style.display = 'none';
        }
    } catch (err) {
        console.warn('Error al verificar anomalías:', err);
    }
}

let listaCategoriasCache = [];

async function cargarCategorias() {
    try {
        const data = await apiFetch('/categorias');
        listaCategoriasCache = data;

        // Llenar select en formulario de registro de movimiento
        filtrarCategoriasPorTipo();

        // Llenar select en filtro de movimientos
        const selectFiltro = document.getElementById('filtro-categoria');
        if (selectFiltro) {
            selectFiltro.innerHTML = '<option value="">Todas las categorías</option>' +
                data.map(c => `<option value="${c.id_categoria}">${c.nombre} (${c.tipo})</option>`).join('');
        }

        // Llenar select en formulario de presupuestos (solo gastos)
        const selectPresupuesto = document.getElementById('presupuesto-categoria');
        if (selectPresupuesto) {
            const soloGastos = data.filter(c => c.tipo === 'gasto');
            selectPresupuesto.innerHTML = soloGastos.map(c => `<option value="${c.id_categoria}">${c.nombre}</option>`).join('');
        }

        return data;
    } catch (err) {
        return [];
    }
}

function filtrarCategoriasPorTipo() {
    const tipoSelect = document.getElementById('tipo');
    const catSelect = document.getElementById('categoria');
    if (!tipoSelect || !catSelect) return;

    const tipoSeleccionado = tipoSelect.value;
    const filtradas = listaCategoriasCache.filter(c => c.tipo === tipoSeleccionado);

    catSelect.innerHTML = '<option value="">Seleccionar categoría...</option>' +
        filtradas.map(c => `<option value="${c.id_categoria}">${c.nombre}</option>`).join('');
}

// ─────────────────────────────────────────
// TABLA DE MOVIMIENTOS Y PAGINACIÓN
// ─────────────────────────────────────────

let paginaActual = 1;
const limitePorPagina = 10;
let totalMovimientos = 0;

async function cargarTablaMovimientos() {
    const tbody = document.getElementById('tbody-movimientos');
    tbody.innerHTML = `<tr><td colspan="6" class="table-loading">⏳ Cargando movimientos...</td></tr>`;

    const tipo = document.getElementById('filtro-tipo').value;
    const cat = document.getElementById('filtro-categoria').value;
    const desde = document.getElementById('filtro-desde').value;
    const hasta = document.getElementById('filtro-hasta').value;
    const montoMin = document.getElementById('filtro-monto-min').value;
    const montoMax = document.getElementById('filtro-monto-max').value;

    const offset = (paginaActual - 1) * limitePorPagina;

    let endpoint = `/movimientos?paginado=true&limit=${limitePorPagina}&offset=${offset}`;
    if (tipo) endpoint += `&tipo=${encodeURIComponent(tipo)}`;
    if (cat) endpoint += `&id_categoria=${encodeURIComponent(cat)}`;
    if (desde) endpoint += `&desde=${encodeURIComponent(desde)}`;
    if (hasta) endpoint += `&hasta=${encodeURIComponent(hasta)}`;
    if (montoMin) endpoint += `&monto_min=${encodeURIComponent(montoMin)}`;
    if (montoMax) endpoint += `&monto_max=${encodeURIComponent(montoMax)}`;

    try {
        const data = await apiFetch(endpoint);
        const movimientos = data.items || [];
        totalMovimientos = data.total || 0;

        actualizarPaginadorUI();

        if (movimientos.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="table-loading">📭 No se encontraron movimientos con los filtros aplicados</td></tr>`;
            return;
        }

        tbody.innerHTML = movimientos.map(m => `
            <tr>
                <td>${m.fecha}</td>
                <td>${m.descripcion || '<em style="color:var(--txt-muted)">Sin descripción</em>'}</td>
                <td>${m.nombre_categoria || `Cat. #${m.id_categoria}`}</td>
                <td>
                    <span class="badge ${m.tipo === 'ingreso' ? 'badge-income' : 'badge-expense'}">
                        ${m.tipo === 'ingreso' ? '💵 Ingreso' : '💸 Gasto'}
                    </span>
                </td>
                <td class="${m.tipo === 'ingreso' ? 'text-income' : 'text-expense'}" style="font-weight:700">
                    ${formatearPesos(m.monto)}
                </td>
                <td>
                    <button class="btn-action" onclick="eliminarMovimiento(${m.id_movimiento})" title="Eliminar movimiento">
                        🗑️ Eliminar
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="6" class="table-loading" style="color:var(--clr-expense)">❌ Error al cargar: ${err.message}</td></tr>`;
    }
}

function actualizarPaginadorUI() {
    const totalPaginas = Math.ceil(totalMovimientos / limitePorPagina) || 1;
    const btnPrev = document.getElementById('btn-prev-page');
    const btnNext = document.getElementById('btn-next-page');
    const info = document.getElementById('pagination-info');
    const currentNum = document.getElementById('current-page-display');

    if (btnPrev) btnPrev.disabled = paginaActual <= 1;
    if (btnNext) btnNext.disabled = paginaActual >= totalPaginas;

    if (info) {
        const start = totalMovimientos === 0 ? 0 : (paginaActual - 1) * limitePorPagina + 1;
        const end = Math.min(paginaActual * limitePorPagina, totalMovimientos);
        info.textContent = `Mostrando ${start}-${end} de ${totalMovimientos} movimientos`;
    }
    if (currentNum) currentNum.textContent = `Página ${paginaActual} de ${totalPaginas}`;
}

document.getElementById('btn-prev-page')?.addEventListener('click', () => {
    if (paginaActual > 1) {
        paginaActual--;
        cargarTablaMovimientos();
    }
});

document.getElementById('btn-next-page')?.addEventListener('click', () => {
    const totalPaginas = Math.ceil(totalMovimientos / limitePorPagina);
    if (paginaActual < totalPaginas) {
        paginaActual++;
        cargarTablaMovimientos();
    }
});

document.getElementById('btn-filtrar')?.addEventListener('click', () => {
    paginaActual = 1;
    cargarTablaMovimientos();
});

document.getElementById('btn-limpiar-filtros')?.addEventListener('click', () => {
    document.getElementById('filtro-tipo').value = '';
    document.getElementById('filtro-categoria').value = '';
    document.getElementById('filtro-desde').value = '';
    document.getElementById('filtro-hasta').value = '';
    document.getElementById('filtro-monto-min').value = '';
    document.getElementById('filtro-monto-max').value = '';
    paginaActual = 1;
    cargarTablaMovimientos();
});

async function eliminarMovimiento(id) {
    if (!confirm(`¿Estás seguro de eliminar el movimiento #${id}? Esta acción no se puede deshacer.`)) return;

    try {
        await apiFetch(`/movimientos/${id}`, { method: 'DELETE' });
        mostrarToast('Movimiento eliminado correctamente', 'success');
        await Promise.all([cargarTablaMovimientos(), cargarResumen(), inicializarGraficos()]);
    } catch (err) {
        mostrarToast(`Error al eliminar: ${err.message}`, 'error');
    }
}

// ─────────────────────────────────────────
// PRESUPUESTOS Y METAS DE AHORRO
// ─────────────────────────────────────────

function toggleFormPresupuesto() {
    const card = document.getElementById('card-form-presupuesto');
    card.style.display = card.style.display === 'none' ? 'block' : 'none';
}

function toggleFormMeta() {
    const card = document.getElementById('card-form-meta');
    card.style.display = card.style.display === 'none' ? 'block' : 'none';
}

async function cargarPresupuestos() {
    const contenedor = document.getElementById('lista-presupuestos');
    try {
        const data = await apiFetch('/presupuestos/resumen');
        if (!data.items || data.items.length === 0) {
            contenedor.innerHTML = `<div class="empty-state">No tienes presupuestos configurados para este mes.<br>¡Crea uno con el botón superior!</div>`;
            return;
        }

        contenedor.innerHTML = data.items.map(p => {
            const fillClass = p.sobregirado ? 'progress-fill-danger' : (p.porcentaje_usado > 80 ? 'progress-fill-warning' : 'progress-fill-income');
            return `
                <div class="item-card">
                    <div class="item-card-header">
                        <span class="item-card-title">${p.nombre_categoria}</span>
                        <span class="badge ${p.sobregirado ? 'badge-warning' : 'badge-income'}">
                            ${p.sobregirado ? '🚨 Sobregirado' : `${p.porcentaje_usado}% usado`}
                        </span>
                    </div>
                    <div class="progress-bar-container">
                        <div class="progress-bar-fill ${fillClass}" style="width: ${Math.min(100, p.porcentaje_usado)}%"></div>
                    </div>
                    <div class="item-card-footer">
                        <span>Gastado: <strong>${formatearPesos(p.monto_gastado)}</strong></span>
                        <span>Límite: <strong>${formatearPesos(p.monto_limite)}</strong></span>
                    </div>
                </div>
            `;
        }).join('');
    } catch (err) {
        contenedor.innerHTML = `<div class="empty-state" style="color:var(--clr-expense)">Error al cargar presupuestos: ${err.message}</div>`;
    }
}

async function cargarMetas() {
    const contenedor = document.getElementById('lista-metas');
    try {
        const metas = await apiFetch('/metas');
        if (!metas || metas.length === 0) {
            contenedor.innerHTML = `<div class="empty-state">No tienes metas de ahorro activas.<br>¡Crea tu primera meta con el botón superior!</div>`;
            return;
        }

        contenedor.innerHTML = metas.map(m => `
            <div class="item-card">
                <div class="item-card-header">
                    <span class="item-card-title">🏆 ${m.nombre}</span>
                    <span class="badge ${m.completada ? 'badge-completed' : 'badge-income'}">
                        ${m.completada ? '🎉 Completada' : `${m.porcentaje_progreso}%`}
                    </span>
                </div>
                <div class="progress-bar-container">
                    <div class="progress-bar-fill progress-fill-primary" style="width: ${m.porcentaje_progreso}%"></div>
                </div>
                <div class="item-card-footer">
                    <span>Ahorrado: <strong>${formatearPesos(m.monto_actual)}</strong> de ${formatearPesos(m.monto_objetivo)}</span>
                    ${!m.completada ? `
                        <button type="button" class="btn btn-ghost btn-sm" onclick="abrirModalAbono(${m.id_meta}, '${m.nombre}')">
                            ➕ Abonar
                        </button>
                    ` : '<span>✅ Meta lograda</span>'}
                </div>
            </div>
        `).join('');
    } catch (err) {
        contenedor.innerHTML = `<div class="empty-state" style="color:var(--clr-expense)">Error al cargar metas: ${err.message}</div>`;
    }
}

// Modal de Abono a Meta
function abrirModalAbono(idMeta, nombreMeta) {
    document.getElementById('abono-meta-id').value = idMeta;
    document.getElementById('abono-meta-nombre').textContent = `Destino: ${nombreMeta}`;
    document.getElementById('abono-monto').value = '';
    document.getElementById('modal-abono').style.display = 'flex';
}

function cerrarModalAbono() {
    document.getElementById('modal-abono').style.display = 'none';
}

document.getElementById('form-abono')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const idMeta = document.getElementById('abono-meta-id').value;
    const monto = parseFloat(document.getElementById('abono-monto').value);

    if (!monto || monto <= 0) {
        mostrarToast('Ingresa un monto válido para abonar', 'warning');
        return;
    }

    try {
        await apiFetch(`/metas/${idMeta}/abonar`, {
            method: 'POST',
            body: JSON.stringify({ monto }),
        });
        cerrarModalAbono();
        mostrarToast('¡Abono registrado con éxito! 🎉', 'success');
        await cargarMetas();
    } catch (err) {
        mostrarToast(`Error al abonar: ${err.message}`, 'error');
    }
});

// Submit Formulario Presupuesto
document.getElementById('form-presupuesto')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const id_categoria = parseInt(document.getElementById('presupuesto-categoria').value);
    const monto_limite = parseFloat(document.getElementById('presupuesto-monto').value);
    const hoy = new Date();

    try {
        await apiFetch('/presupuestos', {
            method: 'POST',
            body: JSON.stringify({
                id_categoria,
                monto_limite,
                mes: hoy.getMonth() + 1,
                anio: hoy.getFullYear(),
            }),
        });
        mostrarToast('Presupuesto fijado correctamente', 'success');
        e.target.reset();
        toggleFormPresupuesto();
        await cargarPresupuestos();
    } catch (err) {
        mostrarToast(`Error: ${err.message}`, 'error');
    }
});

// Submit Formulario Meta
document.getElementById('form-meta')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const nombre = document.getElementById('meta-nombre').value;
    const monto_objetivo = parseFloat(document.getElementById('meta-objetivo').value);
    const fecha_limite = document.getElementById('meta-fecha').value || null;

    try {
        await apiFetch('/metas', {
            method: 'POST',
            body: JSON.stringify({
                nombre,
                monto_objetivo,
                fecha_limite,
            }),
        });
        mostrarToast('Meta de ahorro creada con éxito', 'success');
        e.target.reset();
        toggleFormMeta();
        await cargarMetas();
    } catch (err) {
        mostrarToast(`Error: ${err.message}`, 'error');
    }
});

// ─────────────────────────────────────────
// SECCIÓN ANALÍTICA & REENTRENAMIENTO ML
// ─────────────────────────────────────────

async function cargarDetalleAnalitica() {
    const elPrediccion = document.getElementById('ml-prediccion-detalle');
    const elAnomalias = document.getElementById('ml-anomalias-detalle');

    if (elPrediccion) elPrediccion.innerHTML = `<span class="skeleton-text">Calculando proyección...</span>`;
    if (elAnomalias) elAnomalias.innerHTML = `<span class="skeleton-text">Analizando patrones...</span>`;

    // Predicción
    try {
        const pred = await apiFetch('/analitica/prediccion');
        if (elPrediccion) {
            elPrediccion.innerHTML = `
                <p class="analytics-stat">${formatearPesos(pred.prediccion)}</p>
                <p style="margin-top:8px;font-size:0.84rem;color:var(--txt-secondary)">
                    <strong>Nivel de Confianza:</strong> ${pred.confianza.toUpperCase()} ${pred.modelo_cargado ? '⚡ (Modelo cargado desde joblib)' : ''}
                </p>
                <p style="margin-top:4px;font-size:0.8rem;color:var(--txt-muted)">${pred.razon}</p>
            `;
        }
    } catch (err) {
        if (elPrediccion) elPrediccion.innerHTML = `<p style="color:var(--clr-expense)">❌ ${err.message}</p>`;
    }

    // Anomalías
    try {
        const anom = await apiFetch('/analitica/anomalias?umbral_z=1.5');
        if (elAnomalias) {
            if (anom.total === 0) {
                elAnomalias.innerHTML = `<p style="color:var(--clr-income); font-weight:600">✅ No se detectaron gastos atípicos o anomalías en tu historial reciente.</p>`;
            } else {
                elAnomalias.innerHTML = `
                    <p style="color:#fbbf24;font-weight:700;margin-bottom:8px">
                        ⚠️ Se identificaron ${anom.total} gasto(s) extraordinario(s):
                    </p>
                    ${anom.anomalias.map(a => `
                        <p style="font-size:0.8rem;color:var(--txt-secondary);margin-bottom:4px">
                            • <strong>${a.fecha}</strong> (${a.nombre_categoria}): ${formatearPesos(a.monto)} (Z: ${a.z_score})
                        </p>
                    `).join('')}
                `;
            }
        }
    } catch (err) {
        if (elAnomalias) elAnomalias.innerHTML = `<p style="color:var(--clr-expense)">❌ ${err.message}</p>`;
    }
}

async function forzarReentrenamientoML() {
    const btn = document.getElementById('btn-reentrenar-ml');
    if (btn) {
        btn.textContent = '⏳ Entrenando Scikit-learn...';
        btn.disabled = true;
    }

    try {
        const res = await apiFetch('/analitica/entrenar', { method: 'POST' });
        mostrarToast(`Modelo reentrenado: ${res.mensaje}`, 'success');
        await Promise.all([cargarPrediccion(), cargarDetalleAnalitica()]);
    } catch (err) {
        mostrarToast(`Error al reentrenar: ${err.message}`, 'error');
    } finally {
        if (btn) {
            btn.textContent = '⚙️ Reentrenar Modelo (Joblib)';
            btn.disabled = false;
        }
    }
}

// ─────────────────────────────────────────
// GRÁFICOS (Chart.js)
// ─────────────────────────────────────────

if (typeof Chart !== 'undefined') {
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.borderColor = 'rgba(255,255,255,0.06)';
    Chart.defaults.font.family = "'Inter', sans-serif";
}

let chartDonut = null;
let chartLinea = null;

async function inicializarGraficos() {
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js no está disponible.');
        return;
    }
    let movimientos = [];
    try {
        const data = await apiFetch('/movimientos?limit=200');
        movimientos = Array.isArray(data) ? data : (data.items || []);
    } catch (_) { }

    await renderizarGraficoDonut(movimientos);
    await renderizarGraficoLinea(movimientos);
}

async function renderizarGraficoDonut(movimientos) {
    if (typeof Chart === 'undefined') return;
    const canvas = document.getElementById('chartCategorias');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const gastos = movimientos.filter(m => m.tipo === 'gasto');
    const agrupado = {};
    gastos.forEach(m => {
        const cat = m.nombre_categoria || `Cat #${m.id_categoria}`;
        agrupado[cat] = (agrupado[cat] || 0) + parseFloat(m.monto);
    });

    const labels = Object.keys(agrupado);
    const valores = Object.values(agrupado);
    const colores = ['#f43f5e', '#f97316', '#eab308', '#10b981', '#06b6d4', '#6366f1', '#a78bfa', '#ec4899', '#14b8a6'];

    if (chartDonut) chartDonut.destroy();
    chartDonut = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels.length ? labels : ['Sin datos de gastos'],
            datasets: [{
                data: valores.length ? valores : [1],
                backgroundColor: colores.slice(0, labels.length || 1),
                borderColor: '#1e293b',
                borderWidth: 3,
                hoverOffset: 8,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { padding: 14, boxWidth: 12, font: { size: 12 } },
                },
                tooltip: {
                    callbacks: {
                        label: (ctx) => ` ${new Intl.NumberFormat('es-CO').format(ctx.raw)} COP`,
                    },
                },
            },
        },
    });
}

async function renderizarGraficoLinea(movimientos) {
    if (typeof Chart === 'undefined') return;
    const canvas = document.getElementById('chartTendencia');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const meses = {};
    movimientos.forEach(m => {
        const mes = String(m.fecha).slice(0, 7);
        if (!meses[mes]) meses[mes] = { ingreso: 0, gasto: 0 };
        meses[mes][m.tipo] += parseFloat(m.monto);
    });

    const labels = Object.keys(meses).sort();
    const ingresos = labels.map(m => meses[m].ingreso);
    const gastos = labels.map(m => meses[m].gasto);

    const nombresLabels = labels.map(l => {
        const [yr, mo] = l.split('-');
        return new Date(parseInt(yr), parseInt(mo) - 1).toLocaleString('es-CO', { month: 'short', year: '2-digit' });
    });

    if (chartLinea) chartLinea.destroy();
    chartLinea = new Chart(ctx, {
        type: 'line',
        data: {
            labels: nombresLabels.length ? nombresLabels : ['Sin datos'],
            datasets: [
                {
                    label: 'Ingresos',
                    data: ingresos.length ? ingresos : [0],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    fill: true,
                    tension: 0.35,
                    pointBackgroundColor: '#10b981',
                    pointRadius: 4,
                },
                {
                    label: 'Gastos',
                    data: gastos.length ? gastos : [0],
                    borderColor: '#f43f5e',
                    backgroundColor: 'rgba(244, 63, 94, 0.08)',
                    fill: true,
                    tension: 0.35,
                    pointBackgroundColor: '#f43f5e',
                    pointRadius: 4,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { position: 'top', labels: { padding: 14, font: { size: 12 } } },
                tooltip: {
                    callbacks: {
                        label: (ctx) => ` ${ctx.dataset.label}: ${new Intl.NumberFormat('es-CO').format(ctx.raw)} COP`,
                    },
                },
            },
            scales: {
                x: { grid: { color: 'rgba(255,255,255,0.05)' } },
                y: {
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: {
                        callback: (val) => new Intl.NumberFormat('es-CO', { notation: 'compact' }).format(val),
                    },
                },
            },
        },
    });
}

// ─────────────────────────────────────────
// FORMULARIO REGISTRAR MOVIMIENTO
// ─────────────────────────────────────────

document.getElementById('fecha').valueAsDate = new Date();

document.getElementById('form-movimiento')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const btnGuardar = document.getElementById('btn-guardar');
    const btnText = btnGuardar.querySelector('.btn-text');
    const btnLoader = btnGuardar.querySelector('.btn-loader');

    btnGuardar.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline';

    const payload = {
        id_categoria: parseInt(document.getElementById('categoria').value),
        tipo: document.getElementById('tipo').value,
        monto: parseFloat(document.getElementById('monto').value),
        fecha: document.getElementById('fecha').value,
        descripcion: document.getElementById('descripcion').value || null,
    };

    if (!payload.id_categoria) {
        mostrarToast('Debes seleccionar una categoría válida', 'warning');
        btnGuardar.disabled = false;
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
        return;
    }

    try {
        await apiFetch('/movimientos', {
            method: 'POST',
            body: JSON.stringify(payload),
        });

        mostrarToast('Movimiento registrado correctamente ✨', 'success');
        e.target.reset();
        document.getElementById('fecha').valueAsDate = new Date();
        filtrarCategoriasPorTipo();

        // Refrescar vistas
        await Promise.all([cargarResumen(), cargarAnomalias(), inicializarGraficos()]);
    } catch (err) {
        mostrarToast(`Error al guardar: ${err.message}`, 'error');
    } finally {
        btnGuardar.disabled = false;
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
    }
});

// ─────────────────────────────────────────
// FORMULARIOS DE AUTENTICACIÓN
// ─────────────────────────────────────────

document.getElementById('form-login')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const correo = document.getElementById('login-correo')?.value?.trim() || '';
    const contrasena = document.getElementById('login-password')?.value || '';
    const btn = document.getElementById('btn-submit-login');
    const btnText = btn?.querySelector('.btn-text');
    const btnLoader = btn?.querySelector('.btn-loader');
    const feedback = document.getElementById('auth-feedback');

    if (feedback) {
        feedback.style.display = 'none';
        feedback.textContent = '';
    }

    if (!correo || !contrasena) {
        if (feedback) {
            feedback.textContent = '❌ Por favor ingresa tu correo y contraseña';
            feedback.className = 'form-feedback error';
            feedback.style.display = 'block';
        }
        return;
    }

    if (btn) btn.disabled = true;
    if (btnText) btnText.style.display = 'none';
    if (btnLoader) btnLoader.style.display = 'inline';

    try {
        const response = await fetch(`${API_URL.replace(/\/$/, '')}/api/auth/login-json`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ correo, contrasena }),
        });

        let res;
        try {
            res = await response.json();
        } catch (_) {
            res = {};
        }

        if (!response.ok) {
            throw new Error(res.detalle || res.detail || res.mensaje || 'Credenciales incorrectas o servidor no disponible');
        }

        AUTH.setSession(res.access_token, res.refresh_token, res.usuario);
        ocultarModalAuth();
        navegarA('dashboard');
        mostrarToast(`¡Bienvenido de nuevo, ${res.usuario?.nombre || 'Usuario'}! 👋`, 'success');

        // Cargar todo el dashboard
        await Promise.allSettled([
            cargarResumen(),
            cargarPrediccion(),
            cargarAnomalias(),
            cargarCategorias(),
            inicializarGraficos(),
        ]);
    } catch (err) {
        console.error('Error al iniciar sesión:', err);
        if (feedback) {
            feedback.textContent = `❌ ${err.message || 'Error de conexión con el backend'}`;
            feedback.className = 'form-feedback error';
            feedback.style.display = 'block';
        }
        mostrarToast(err.message || 'Error de autenticación', 'error');
    } finally {
        if (btn) btn.disabled = false;
        if (btnText) btnText.style.display = 'inline';
        if (btnLoader) btnLoader.style.display = 'none';
    }
});

document.getElementById('form-register')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const nombre = document.getElementById('reg-nombre')?.value?.trim() || '';
    const correo = document.getElementById('reg-correo')?.value?.trim() || '';
    const contrasena = document.getElementById('reg-password')?.value || '';
    const btn = document.getElementById('btn-submit-register');
    const btnText = btn?.querySelector('.btn-text');
    const btnLoader = btn?.querySelector('.btn-loader');
    const feedback = document.getElementById('auth-feedback');

    if (feedback) {
        feedback.style.display = 'none';
        feedback.textContent = '';
    }

    if (contrasena.length < 8) {
        mostrarToast('La contraseña debe tener mínimo 8 caracteres', 'warning');
        if (feedback) {
            feedback.textContent = '⚠️ La contraseña debe tener mínimo 8 caracteres';
            feedback.className = 'form-feedback warning';
            feedback.style.display = 'block';
        }
        return;
    }

    if (btn) btn.disabled = true;
    if (btnText) btnText.style.display = 'none';
    if (btnLoader) btnLoader.style.display = 'inline';

    try {
        const response = await fetch(`${API_URL.replace(/\/$/, '')}/api/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nombre, correo, contrasena }),
        });

        let res;
        try {
            res = await response.json();
        } catch (_) {
            res = {};
        }

        if (!response.ok) {
            throw new Error(res.detalle || res.detail || res.mensaje || 'Error al registrar');
        }

        AUTH.setSession(res.access_token, res.refresh_token, res.usuario);
        ocultarModalAuth();
        navegarA('dashboard');
        mostrarToast(`¡Cuenta creada con éxito! Bienvenido, ${nombre} ✨`, 'success');

        await Promise.allSettled([
            cargarResumen(),
            cargarPrediccion(),
            cargarAnomalias(),
            cargarCategorias(),
            inicializarGraficos(),
        ]);
    } catch (err) {
        console.error('Error en registro:', err);
        if (feedback) {
            feedback.textContent = `❌ ${err.message || 'Error al registrar'}`;
            feedback.className = 'form-feedback error';
            feedback.style.display = 'block';
        }
        mostrarToast(err.message || 'Error al registrar', 'error');
    } finally {
        if (btn) btn.disabled = false;
        if (btnText) btnText.style.display = 'inline';
        if (btnLoader) btnLoader.style.display = 'none';
    }
});

// ─────────────────────────────────────────
// BOTÓN ACTUALIZAR
// ─────────────────────────────────────────

document.getElementById('btn-refresh')?.addEventListener('click', async () => {
    const btn = document.getElementById('btn-refresh');
    if (btn) {
        btn.textContent = '⏳ Actualizando...';
        btn.disabled = true;
    }

    await Promise.allSettled([
        cargarResumen(),
        cargarPrediccion(),
        cargarAnomalias(),
        inicializarGraficos(),
    ]);

    if (btn) {
        btn.textContent = '🔄 Actualizar';
        btn.disabled = false;
    }
    mostrarToast('Datos actualizados en tiempo real', 'info');
});

// ─────────────────────────────────────────
// INICIALIZACIÓN
// ─────────────────────────────────────────

document.addEventListener('DOMContentLoaded', async () => {
    actualizarInfoUsuarioUI();

    if (!AUTH.isAuthenticated()) {
        mostrarModalAuth('login');
    } else {
        ocultarModalAuth();
        navegarA('dashboard');
        await Promise.allSettled([
            cargarResumen(),
            cargarPrediccion(),
            cargarAnomalias(),
            cargarCategorias(),
            inicializarGraficos(),
        ]);
    }
});