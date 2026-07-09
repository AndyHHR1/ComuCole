(() => {
    'use strict';

    const ROL_DOCENTE = 'docente';
    const ROL_PADRE = 'padre';

    const elements = {
        btnDocente: document.getElementById('btn-docente'),
        btnPadre: document.getElementById('btn-padre'),
    };

    function setRol(rol) {
        localStorage.setItem('comucole_rol', rol);
    }

    function getRol() {
        return localStorage.getItem('comucole_rol');
    }

    function redirigir(rol) {
        setRol(rol);
        if (rol === ROL_DOCENTE) {
            window.location.href = '/index.html';
        } else if (rol === ROL_PADRE) {
            window.location.href = '/padre.html';
        }
    }

    function init() {
        const rol = getRol();
        if (rol === ROL_DOCENTE) {
            window.location.href = '/index.html';
            return;
        }
        if (rol === ROL_PADRE) {
            window.location.href = '/padre.html';
            return;
        }

        elements.btnDocente.addEventListener('click', () => redirigir(ROL_DOCENTE));
        elements.btnPadre.addEventListener('click', () => redirigir(ROL_PADRE));
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
