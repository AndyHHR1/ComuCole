(() => {
    'use strict';

    const CONFIG = {
        categories: {
            cognitivo: {
                className: 'categoria-cognitivo',
                emojis: ['🧠', '📘'],
            },
            manual: {
                className: 'categoria-manual',
                emojis: ['🎨', '✂️'],
            },
            psicomotriz: {
                className: 'categoria-psicomotriz',
                emojis: ['🏃', '⚽'],
            },
        },
        semaforos: {
            rojo: {
                className: 'semaforo-rojo',
                emoji: '🔴',
                texto: 'Es para ya',
            },
            amarillo: {
                className: 'semaforo-amarillo',
                emoji: '🟡',
                texto: 'Tienes tiempo',
            },
            verde: {
                className: 'semaforo-verde',
                emoji: '🟢',
                texto: 'Vas bien de tiempo',
            },
        },
    };

    const API_BASE_URL = '';

    const elements = {
        screens: {
            carga: document.getElementById('vista-carga'),
            contenido: document.getElementById('vista-contenido'),
            ranking: document.getElementById('vista-ranking'),
        },
        tabs: {
            clase: document.getElementById('tab-clase'),
            ranking: document.getElementById('tab-ranking'),
        },
        cardClase: document.getElementById('card-clase'),
        categoriaEmojis: document.getElementById('categoria-emojis'),
        semaforoBadge: document.getElementById('semaforo-badge'),
        resumenSesion: document.getElementById('resumen_sesion'),
        tarea: document.getElementById('tarea'),
        materialesAlerta: document.getElementById('materiales-alerta'),
        materialesLista: document.getElementById('materiales-lista'),
        btnRevisada: document.getElementById('btn-revisada'),
        btnCumplida: document.getElementById('btn-cumplida'),
        puntosValor: document.getElementById('puntos-valor'),
        rankingLoading: document.getElementById('ranking-loading'),
        rankingEmpty: document.getElementById('ranking-empty'),
        rankingContent: document.getElementById('ranking-content'),
        rankingBody: document.getElementById('ranking-body'),
    };

    let misPuntos = 0;
    let revisadaMarcada = false;
    let cumplidaMarcada = false;

    function showScreen(name) {
        Object.values(elements.screens).forEach(screen => screen.classList.remove('active'));
        if (elements.screens[name]) {
            elements.screens[name].classList.add('active');
        }
    }

    function showTab(tabName) {
        Object.values(elements.tabs).forEach(tab => tab.classList.remove('active'));
        elements.tabs[tabName].classList.add('active');

        if (tabName === 'clase') {
            showScreen('contenido');
        } else if (tabName === 'ranking') {
            showScreen('ranking');
            cargarRanking();
        }
    }

    function limpiarClasesPrevias() {
        Object.values(CONFIG.categories).forEach(cat => {
            elements.cardClase.classList.remove(cat.className);
        });
        Object.values(CONFIG.semaforos).forEach(sem => {
            elements.semaforoBadge.classList.remove(sem.className);
        });
    }

    function renderizarClase(datos) {
        limpiarClasesPrevias();

        const categoria = datos.categoria || 'cognitivo';
        const semaforo = datos.semaforo || 'amarillo';
        const categoriaConfig = CONFIG.categories[categoria] || CONFIG.categories.cognitivo;
        const semaforoConfig = CONFIG.semaforos[semaforo] || CONFIG.semaforos.amarillo;

        elements.cardClase.classList.add(categoriaConfig.className);
        elements.categoriaEmojis.textContent = categoriaConfig.emojis.join(' ');

        elements.semaforoBadge.classList.add(semaforoConfig.className);
        elements.semaforoBadge.innerHTML = `${semaforoConfig.emoji} ${semaforoConfig.texto}`;

        elements.resumenSesion.textContent = datos.resumen_sesion || 'Sin resumen disponible.';
        elements.tarea.textContent = datos.tarea || 'Sin tarea asignada.';

        const materiales = Array.isArray(datos.materiales) ? datos.materiales : [];
        if (materiales.length > 0) {
            elements.materialesLista.innerHTML = materiales
                .map(material => `<li>${escapeHtml(material)}</li>`)
                .join('');
            elements.materialesAlerta.classList.remove('hidden');
        } else {
            elements.materialesAlerta.classList.add('hidden');
        }

        resetBotones();
        showTab('clase');
    }

    function resetBotones() {
        revisadaMarcada = false;
        cumplidaMarcada = false;
        elements.btnRevisada.disabled = false;
        elements.btnCumplida.disabled = false;
        elements.btnRevisada.classList.remove('marcado');
        elements.btnCumplida.classList.remove('marcado');
    }

    function actualizarPuntos(nuevosPuntos) {
        misPuntos = nuevosPuntos;
        elements.puntosValor.textContent = misPuntos;
    }

    async function marcarRevisada() {
        if (revisadaMarcada) return;

        const token = localStorage.getItem('comucole_token');
        if (!token) {
            alert('Sesión expirada. Inicia sesión nuevamente.');
            window.location.href = '/';
            return;
        }

        elements.btnRevisada.disabled = true;

        try {
            const response = await fetch(`${API_BASE_URL}/marcar-revisada`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!response.ok) {
                throw new Error(`Error ${response.status}`);
            }

            const data = await response.json();
            revisadaMarcada = true;
            elements.btnRevisada.classList.add('marcado');
            actualizarPuntos(data.puntos);
        } catch (error) {
            console.error('Error marcando revisada:', error);
            elements.btnRevisada.disabled = false;
            alert('No se pudo registrar la acción. Intenta nuevamente.');
        }
    }

    async function marcarCumplida() {
        if (cumplidaMarcada) return;

        const token = localStorage.getItem('comucole_token');
        if (!token) {
            alert('Sesión expirada. Inicia sesión nuevamente.');
            window.location.href = '/';
            return;
        }

        elements.btnCumplida.disabled = true;

        try {
            const response = await fetch(`${API_BASE_URL}/marcar-cumplida`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!response.ok) {
                throw new Error(`Error ${response.status}`);
            }

            const data = await response.json();
            cumplidaMarcada = true;
            elements.btnCumplida.classList.add('marcado');
            actualizarPuntos(data.puntos);
        } catch (error) {
            console.error('Error marcando cumplida:', error);
            elements.btnCumplida.disabled = false;
            alert('No se pudo registrar la acción. Intenta nuevamente.');
        }
    }

    async function cargarRanking() {
        const token = localStorage.getItem('comucole_token');
        if (!token) {
            window.location.href = '/';
            return;
        }

        elements.rankingLoading.classList.remove('hidden');
        elements.rankingEmpty.classList.add('hidden');
        elements.rankingContent.classList.add('hidden');

        try {
            const response = await fetch(`${API_BASE_URL}/ranking`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!response.ok) {
                throw new Error(`Error ${response.status}`);
            }

            const data = await response.json();
            renderizarRanking(data.ranking || []);
        } catch (error) {
            console.error('Error cargando ranking:', error);
            elements.rankingLoading.classList.add('hidden');
            elements.rankingEmpty.classList.remove('hidden');
        }
    }

    function renderizarRanking(ranking) {
        elements.rankingLoading.classList.add('hidden');

        if (!ranking.length) {
            elements.rankingEmpty.classList.remove('hidden');
            elements.rankingContent.classList.add('hidden');
            return;
        }

        elements.rankingEmpty.classList.add('hidden');
        elements.rankingContent.classList.remove('hidden');

        const miCode = localStorage.getItem('comucole_code');

        elements.rankingBody.innerHTML = ranking.map((entry, index) => {
            const esYo = miCode && entry.id === miCode;
            const rowClass = esYo ? 'class="row-yo"' : '';
            const nombre = esYo ? 'Tú' : anonimizarId(entry.id);
            const puntosClass = esYo ? 'class="ranking-puntos"' : '';

            return `
                <tr ${rowClass}>
                    <td>${entry.puesto}</td>
                    <td><span class="ranking-anonimo">${escapeHtml(nombre)}</span></td>
                    <td class="text-right"><span ${puntosClass}>${entry.puntos}</span></td>
                </tr>
            `;
        }).join('');
    }

    function anonimizarId(id) {
        if (!id || id.length < 8) return id;
        return id.substring(0, 4) + '...' + id.substring(id.length - 4);
    }

    function escapeHtml(texto) {
        const div = document.createElement('div');
        div.textContent = texto;
        return div.innerHTML;
    }

    async function cargarDatosDeDemo() {
        const token = localStorage.getItem('comucole_token');
        if (!token) {
            setTimeout(() => {
                window.location.href = '/';
            }, 1000);
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/me/tasks`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!response.ok) {
                if (response.status === 401) {
                    localStorage.removeItem('comucole_token');
                    localStorage.removeItem('comucole_rol');
                    localStorage.removeItem('comucole_code');
                    localStorage.removeItem('comucole_full_name');
                    window.location.href = '/';
                    return;
                }
                throw new Error(`Error ${response.status}`);
            }

            const data = await response.json();
            const tasks = data.tasks || [];

            if (tasks.length === 0) {
                showScreen('carga');
                return;
            }

            const ultimaTarea = tasks[tasks.length - 1];
            renderizarClase({
                resumen_sesion: ultimaTarea.description || '',
                tarea: ultimaTarea.title || '',
                materiales: [],
                semaforo: 'amarillo',
                categoria: 'cognitivo',
            });
        } catch (error) {
            console.error('Error cargando tareas:', error);
            showScreen('carga');
        }
    }

    function init() {
        const token = localStorage.getItem('comucole_token');
        const rol = localStorage.getItem('comucole_rol');

        if (!token || rol !== 'parent') {
            setTimeout(() => {
                window.location.href = '/';
            }, 1000);
            return;
        }

        showScreen('carga');

        elements.tabs.clase.addEventListener('click', () => showTab('clase'));
        elements.tabs.ranking.addEventListener('click', () => showTab('ranking'));

        elements.btnRevisada.addEventListener('click', marcarRevisada);
        elements.btnCumplida.addEventListener('click', marcarCumplida);

        const btnCerrarSesion = document.getElementById('btn-cerrar-sesion');
        if (btnCerrarSesion) {
            btnCerrarSesion.addEventListener('click', () => {
                localStorage.removeItem('comucole_token');
                localStorage.removeItem('comucole_rol');
                localStorage.removeItem('comucole_code');
                localStorage.removeItem('comucole_full_name');
                window.location.href = '/';
            });
        }

        setTimeout(() => {
            cargarDatosDeDemo();
        }, 600);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
