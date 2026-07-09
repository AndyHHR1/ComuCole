(() => {
    'use strict';

    const API_BASE = '';
    const ROL_DOCENTE = 'teacher';
    const ROL_PADRE = 'parent';

    let selectedRole = null;
    let isRegisterMode = false;

    const $ = (id) => document.getElementById(id);

    const elements = {
        screenRol: $('screen-rol'),
        screenAuth: $('screen-auth'),
        btnDocente: $('btn-docente'),
        btnPadre: $('btn-padre'),
        btnVolver: $('btn-volver'),
        btnLogin: $('btn-login'),
        btnRegister: $('btn-register'),
        btnToggleMode: $('btn-toggle-mode'),
        formAuth: $('form-auth'),
        authHint: $('auth-hint'),
        authCode: $('auth-code'),
        authPassword: $('auth-password'),
        authNombre: $('auth-nombre'),
        groupNombre: $('group-nombre'),
        authAño: $('auth-año'),
        authSeccion: $('auth-seccion'),
        authColorAula: $('auth-color-aula'),
        groupAño: $('group-año'),
        groupSeccion: $('group-seccion'),
        groupColorAula: $('group-color-aula'),
        authError: $('auth-error'),
    };

    function showScreen(name) {
        elements.screenRol?.classList.toggle('active', name === 'rol');
        elements.screenAuth?.classList.toggle('active', name === 'auth');
    }

    function setError(msg) {
        if (elements.authError) {
            elements.authError.textContent = msg;
            elements.authError.classList.remove('hidden');
        }
    }

    function clearError() {
        if (elements.authError) {
            elements.authError.textContent = '';
            elements.authError.classList.add('hidden');
        }
    }

    function setMode(register) {
        isRegisterMode = register;
        elements.btnLogin?.classList.toggle('hidden', register);
        elements.btnRegister?.classList.toggle('hidden', !register);
        elements.groupNombre?.classList.toggle('hidden', !register);
        if (selectedRole === ROL_PADRE) {
            elements.groupAño?.classList.toggle('hidden', !register);
            elements.groupSeccion?.classList.toggle('hidden', !register);
            elements.groupColorAula?.classList.toggle('hidden', !register);
        } else {
            elements.groupAño?.classList.add('hidden');
            elements.groupSeccion?.classList.add('hidden');
            elements.groupColorAula?.classList.add('hidden');
        }
        if (elements.authHint) {
            elements.authHint.textContent = register ? 'Completa tus datos para registrarte' : 'Inicia sesión con tu código';
        }
        if (elements.btnToggleMode) {
            elements.btnToggleMode.textContent = register ? '¿Ya tienes cuenta? Inicia sesión' : '¿No tienes cuenta? Regístrate';
        }
    }

    function redirect(role) {
        const destino = role === ROL_DOCENTE ? '/docente.html' : '/padre.html';
        window.location.href = destino;
    }

    async function handleSubmit(e) {
        e.preventDefault();
        clearError();

        const code = elements.authCode?.value?.trim() || '';
        const password = elements.authPassword?.value?.trim() || '';
        const nombre = elements.authNombre?.value?.trim() || '';
        const año = elements.authAño?.value || '';
        const seccion = elements.authSeccion?.value || '';
        const colorAula = elements.authColorAula?.value || '';

        if (!code || !password) {
            setError('Completa código y contraseña');
            return;
        }

        const endpoint = isRegisterMode ? '/register' : '/login';
        const body = {
            code,
            password,
            role: selectedRole,
        };

        if (isRegisterMode) {
            if (!nombre) {
                setError('Ingresa tu nombre completo');
                return;
            }
            body.full_name = nombre;

            if (selectedRole === ROL_PADRE) {
                body.año = año;
                body.seccion = seccion;
                body.color_aula = colorAula;
            }
        }

        try {
            const res = await fetch(API_BASE + endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });

            const data = await res.json();
            if (!res.ok) {
                setError(data.detail || 'Error en la solicitud');
                return;
            }

            if (!isRegisterMode && data.access_token) {
                localStorage.setItem('comucole_token', data.access_token);
                localStorage.setItem('comucole_role', data.role);
                localStorage.setItem('comucole_full_name', data.full_name || '');
                localStorage.setItem('comucole_code', code);
                if (data.año) localStorage.setItem('comucole_año', data.año);
                if (data.seccion) localStorage.setItem('comucole_seccion', data.seccion);
                if (data.color_aula) localStorage.setItem('comucole_color_aula', data.color_aula);
                redirect(data.role);
                return;
            } else if (isRegisterMode) {
                setMode(false);
                if (elements.authPassword) elements.authPassword.value = '';
                if (elements.authNombre) elements.authNombre.value = '';
                if (elements.authAño) elements.authAño.value = '';
                if (elements.authSeccion) elements.authSeccion.value = '';
                if (elements.authColorAula) elements.authColorAula.value = '';
                setError('');
                setError('Registrado. Ahora inicia sesión.');
                return;
            }

            redirect(selectedRole);
        } catch (err) {
            console.error('[login] error', err);
            setError('Error de conexión');
        }
    }

    function init() {
        if (!elements.btnDocente || !elements.btnPadre || !elements.formAuth) {
            console.error('[login] faltan elementos criticos en el DOM');
            return;
        }

        elements.btnDocente.addEventListener('click', () => {
            selectedRole = ROL_DOCENTE;
            setMode(false);
            showScreen('auth');
        });

        elements.btnPadre.addEventListener('click', () => {
            selectedRole = ROL_PADRE;
            setMode(false);
            showScreen('auth');
        });

        elements.btnVolver?.addEventListener('click', () => {
            clearError();
            if (elements.authCode) elements.authCode.value = '';
            if (elements.authPassword) elements.authPassword.value = '';
            if (elements.authNombre) elements.authNombre.value = '';
            if (elements.authAño) elements.authAño.value = '';
            if (elements.authSeccion) elements.authSeccion.value = '';
            if (elements.authColorAula) elements.authColorAula.value = '';
            showScreen('rol');
        });

        elements.btnToggleMode?.addEventListener('click', () => {
            clearError();
            if (elements.authCode) elements.authCode.value = '';
            if (elements.authPassword) elements.authPassword.value = '';
            if (elements.authNombre) elements.authNombre.value = '';
            if (elements.authAño) elements.authAño.value = '';
            if (elements.authSeccion) elements.authSeccion.value = '';
            if (elements.authColorAula) elements.authColorAula.value = '';
            setMode(!isRegisterMode);
        });

        elements.btnLogin?.addEventListener('click', (e) => {
            e.preventDefault();
            elements.formAuth.dispatchEvent(new Event('submit'));
        });

        elements.btnRegister?.addEventListener('click', (e) => {
            e.preventDefault();
            elements.formAuth.dispatchEvent(new Event('submit'));
        });

        elements.formAuth.addEventListener('submit', handleSubmit);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
