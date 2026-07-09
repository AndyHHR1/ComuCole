(() => {
    'use strict';

    const API_BASE = '';
    const ROL_DOCENTE = 'teacher';
    const ROL_PADRE = 'parent';

    let selectedRole = null;
    let isRegisterMode = false;

    const elements = {
        screenRol: document.getElementById('screen-rol'),
        screenAuth: document.getElementById('screen-auth'),
        btnDocente: document.getElementById('btn-docente'),
        btnPadre: document.getElementById('btn-padre'),
        btnVolver: document.getElementById('btn-volver'),
        btnLogin: document.getElementById('btn-login'),
        btnRegister: document.getElementById('btn-register'),
        btnToggleMode: document.getElementById('btn-toggle-mode'),
        formAuth: document.getElementById('form-auth'),
        authHint: document.getElementById('auth-hint'),
        authCode: document.getElementById('auth-code'),
        authPassword: document.getElementById('auth-password'),
        authNombre: document.getElementById('auth-nombre'),
        groupNombre: document.getElementById('group-nombre'),
        authError: document.getElementById('auth-error'),
    };

    function showScreen(name) {
        elements.screenRol.classList.toggle('active', name === 'rol');
        elements.screenAuth.classList.toggle('active', name === 'auth');
    }

    function setError(msg) {
        elements.authError.textContent = msg;
        elements.authError.classList.remove('hidden');
    }

    function clearError() {
        elements.authError.textContent = '';
        elements.authError.classList.add('hidden');
    }

    function setMode(register) {
        isRegisterMode = register;
        elements.btnLogin.classList.toggle('hidden', register);
        elements.btnRegister.classList.toggle('hidden', !register);
        elements.groupNombre.classList.toggle('hidden', !register);
        elements.authHint.textContent = register ? 'Completa tus datos para registrarte' : 'Inicia sesión con tu código';
        elements.btnToggleMode.textContent = register ? '¿Ya tienes cuenta? Inicia sesión' : '¿No tienes cuenta? Regístrate';
    }

    function redirect(role) {
        const destino = role === ROL_DOCENTE ? '/docente.html' : '/padre.html';
        window.location.href = destino;
    }

    async function handleSubmit(e) {
        e.preventDefault();
        clearError();

        const code = elements.authCode.value.trim();
        const password = elements.authPassword.value.trim();
        const nombre = elements.authNombre.value.trim();

        if (!code || !password) {
            setError('Completa código y contraseña');
            return;
        }

        const endpoint = isRegisterMode ? '/register' : '/login';
        const body = {
            code,
            password,
        };

        if (isRegisterMode) {
            if (!nombre) {
                setError('Ingresa tu nombre completo');
                return;
            }
            body.full_name = nombre;
            body.role = selectedRole;
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
                redirect(data.role);
                return;
            } else if (isRegisterMode) {
                setMode(false);
                elements.authPassword.value = '';
                elements.authNombre.value = '';
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

        elements.btnVolver.addEventListener('click', () => {
            clearError();
            elements.authCode.value = '';
            elements.authPassword.value = '';
            elements.authNombre.value = '';
            showScreen('rol');
        });

        elements.btnToggleMode.addEventListener('click', () => {
            clearError();
            elements.authCode.value = '';
            elements.authPassword.value = '';
            elements.authNombre.value = '';
            setMode(!isRegisterMode);
        });

        elements.btnLogin.addEventListener('click', (e) => {
            e.preventDefault();
            elements.formAuth.dispatchEvent(new Event('submit'));
        });

        elements.btnRegister.addEventListener('click', (e) => {
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
