(() => {
    'use strict';

    const API_BASE_URL = '';

    const elements = {
        screens: {
            carga: document.getElementById('pantalla-carga'),
            edicion: document.getElementById('pantalla-edicion'),
            exito: document.getElementById('pantalla-exito'),
        },
        dropZone: document.getElementById('drop-zone'),
        fileInput: document.getElementById('file-input'),
        fileInfo: document.getElementById('file-info'),
        fileName: document.getElementById('file-name'),
        removeFile: document.getElementById('remove-file'),
        loading: document.getElementById('loading'),
        errorMsg: document.getElementById('error-msg'),
        formEdicion: document.getElementById('form-edicion'),
        btnVolver: document.getElementById('btn-volver'),
        btnPublicar: document.getElementById('btn-publicar'),
        btnNuevaPublicacion: document.getElementById('btn-nueva-publicacion'),
        fields: {
            resumen_sesion: document.getElementById('resumen_sesion'),
            tarea: document.getElementById('tarea'),
            materiales: document.getElementById('materiales'),
            semaforo: document.getElementById('semaforo'),
            categoria: document.getElementById('categoria'),
        },
    };

    let archivoActual = null;

    function showScreen(name) {
        Object.values(elements.screens).forEach(screen => screen.classList.remove('active'));
        elements.screens[name].classList.add('active');
    }

    function showError(message) {
        elements.errorMsg.textContent = message;
        elements.errorMsg.classList.remove('hidden');
    }

    function hideError() {
        elements.errorMsg.classList.add('hidden');
    }

    function setLoading(isLoading) {
        if (isLoading) {
            elements.loading.classList.remove('hidden');
            elements.dropZone.style.pointerEvents = 'none';
            elements.dropZone.style.opacity = '0.6';
        } else {
            elements.loading.classList.add('hidden');
            elements.dropZone.style.pointerEvents = 'auto';
            elements.dropZone.style.opacity = '1';
        }
    }

    function updateFileInfo(filename) {
        elements.fileName.textContent = filename;
        elements.fileInfo.classList.remove('hidden');
    }

    function resetUpload() {
        archivoActual = null;
        elements.fileInput.value = '';
        elements.fileInfo.classList.add('hidden');
        hideError();
    }

    async function procesarArchivo(file) {
        if (!file) return;

        if (!file.name.endsWith('.docx')) {
            showError('Solo se aceptan archivos .docx');
            return;
        }

        archivoActual = file;
        updateFileInfo(file.name);
        hideError();
        setLoading(true);

        const formData = new FormData();
        formData.append('archivo', file);

        try {
            const response = await fetch(`${API_BASE_URL}/procesar-docx`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `Error ${response.status}: ${response.statusText}`);
            }

            const datos = await response.json();
            cargarFormulario(datos);
            showScreen('edicion');
        } catch (error) {
            console.error('Error procesando documento:', error);
            showError(error.message || 'Error al procesar el documento. Intenta nuevamente.');
        } finally {
            setLoading(false);
        }
    }

    function cargarFormulario(datos) {
        elements.fields.resumen_sesion.value = datos.resumen_sesion || '';
        elements.fields.tarea.value = datos.tarea || '';

        if (Array.isArray(datos.materiales)) {
            elements.fields.materiales.value = datos.materiales.join('\n');
        } else if (typeof datos.materiales === 'string') {
            elements.fields.materiales.value = datos.materiales;
        } else {
            elements.fields.materiales.value = '';
        }

        elements.fields.semaforo.value = datos.semaforo || 'amarillo';
        elements.fields.categoria.value = datos.categoria || 'cognitivo';
    }

    function obtenerDatosFormulario() {
        const materialesTexto = elements.fields.materiales.value.trim();
        const materiales = materialesTexto
            ? materialesTexto.split('\n').map(linea => linea.trim()).filter(linea => linea.length > 0)
            : [];

        return {
            resumen_sesion: elements.fields.resumen_sesion.value.trim(),
            tarea: elements.fields.tarea.value.trim(),
            materiales,
            semaforo: elements.fields.semaforo.value,
            categoria: elements.fields.categoria.value,
        };
    }

    async function publicarContenido(event) {
        event.preventDefault();

        const datos = obtenerDatosFormulario();

        if (!datos.resumen_sesion || !datos.tarea) {
            alert('Por favor completa al menos el resumen y la tarea.');
            return;
        }

        const token = localStorage.getItem('comucole_token');
        if (!token) {
            alert('Sesión expirada. Inicia sesión nuevamente.');
            window.location.href = '/';
            return;
        }

        const btnText = elements.btnPublicar.querySelector('.btn-text');
        const btnLoader = elements.btnPublicar.querySelector('.btn-loader');

        elements.btnPublicar.disabled = true;
        btnText.classList.add('hidden');
        btnLoader.classList.remove('hidden');

        try {
            await publicarEnAPI(datos, token);
            showScreen('exito');
        } catch (error) {
            console.error('Error publicando:', error);
            alert('Error al publicar. Por favor intenta nuevamente.');
        } finally {
            elements.btnPublicar.disabled = false;
            btnText.classList.remove('hidden');
            btnLoader.classList.add('hidden');
        }
    }

    async function publicarEnAPI(datos, token) {
        const tareaTexto = datos.tarea;
        const titulo = tareaTexto.length > 80 ? tareaTexto.substring(0, 77) + '...' : tareaTexto;

        const body = {
            title: titulo,
            description: datos.resumen_sesion,
            parent_code: '',
            file_url: '',
        };

        const response = await fetch(`${API_BASE_URL}/tasks`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify(body),
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Error ${response.status}: ${response.statusText}`);
        }
    }

    function nuevaPublicacion() {
        resetUpload();
        showScreen('carga');
    }

    function initEventListeners() {
        elements.dropZone.addEventListener('click', () => {
            elements.fileInput.click();
        });

        elements.fileInput.addEventListener('change', (event) => {
            const file = event.target.files[0];
            if (file) {
                procesarArchivo(file);
            }
        });

        elements.dropZone.addEventListener('dragover', (event) => {
            event.preventDefault();
            elements.dropZone.classList.add('drag-over');
        });

        elements.dropZone.addEventListener('dragleave', (event) => {
            event.preventDefault();
            elements.dropZone.classList.remove('drag-over');
        });

        elements.dropZone.addEventListener('drop', (event) => {
            event.preventDefault();
            elements.dropZone.classList.remove('drag-over');
            const file = event.dataTransfer.files[0];
            if (file) {
                procesarArchivo(file);
            }
        });

        elements.removeFile.addEventListener('click', (event) => {
            event.stopPropagation();
            resetUpload();
        });

        elements.formEdicion.addEventListener('submit', publicarContenido);

        elements.btnVolver.addEventListener('click', () => {
            showScreen('carga');
        });

        elements.btnNuevaPublicacion.addEventListener('click', nuevaPublicacion);

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
    }

    function init() {
        try {
            const token = localStorage.getItem('comucole_token');
            const rol = localStorage.getItem('comucole_rol');

            console.log('[docente] init token=', !!token, 'rol=', rol);

            if (!token || rol !== 'teacher') {
                console.warn('[docente] redirigiendo a login porque falta token o rol incorrecto');
                window.location.href = '/';
                return;
            }

            initEventListeners();
            showScreen('carga');
        } catch (error) {
            console.error('[docente] error en init', error);
            window.location.href = '/';
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
