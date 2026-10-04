// Actualización de reloj en tiempo real
function updateClock() {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    document.getElementById('clock').textContent = `${hours}:${minutes}`;

    const options = { weekday: 'long', day: 'numeric', month: 'long' };
    const dateStr = now.toLocaleDateString('es-ES', options);
    document.getElementById('date').textContent = dateStr;
}
setInterval(updateClock, 1000);
updateClock();

// Integración con la API de LightDM
let targetUser = 'patini';

function showMessage(text, isError = false) {
    const area = document.getElementById('message-area');
    area.textContent = text;
    area.className = isError ? 'msg-error' : 'msg-info';
}

// Callback de fin de autenticación (conectado vía señal en initLightDM)
function authenticationComplete() {
    if (window.lightdm && lightdm.is_authenticated) {
        showMessage("¡Sesión iniciada!", false);
        startSession();
    } else {
        showMessage("Contraseña incorrecta", true);
        const card = document.getElementById('login-card');
        card.style.animation = 'none';
        void card.offsetWidth; // Trigger reflow
        card.style.animation = 'shake 0.4s ease-in-out';

        const input = document.getElementById('password-input');
        input.value = '';
        input.focus();

        // Reiniciar el ciclo de autenticación (las señales ya están conectadas)
        if (window.lightdm) lightdm.authenticate(targetUser);
    }
}

function initLightDM() {
    if (window.lightdm) {
        if (lightdm.users && lightdm.users.length > 0) {
            targetUser = lightdm.users[0].username;
            document.getElementById('user-name').textContent = lightdm.users[0].display_name || targetUser;
            if (lightdm.users[0].image) {
                document.getElementById('user-avatar').src = lightdm.users[0].image;
            }
        }

        // web-greeter v4: señales estilo Qt con .connect()
        // (los callbacks globales window.* del greeter antiguo ya no se despachan)
        lightdm.authentication_complete.connect(authenticationComplete);
        lightdm.show_message.connect((text, type) => {
            showMessage(text, String(type || '').toLowerCase().includes('error'));
        });
        lightdm.show_prompt.connect(() => {
            const input = document.getElementById('password-input');
            if (input) input.focus();
        });

        // Iniciar la autenticación para el usuario
        if (typeof lightdm.cancel_authentication === 'function') {
            lightdm.cancel_authentication();
        }
        lightdm.authenticate(targetUser);
    } else {
        console.log("Modo de vista previa: LightDM API no detectada en navegador.");
    }
}

function submitPassword() {
    const input = document.getElementById('password-input');
    const password = input.value;

    if (!password) {
        showMessage("Introduce tu contraseña", true);
        return;
    }

    showMessage("Autenticando...", false);

    if (window.lightdm) {
        if (lightdm.is_authenticated) {
            startSession();
        } else {
            lightdm.respond(password);
        }
    } else {
        // Simulación en vista previa
        setTimeout(() => {
            showMessage("¡Bienvenido Patini!", false);
        }, 600);
    }
}

function startSession() {
    if (window.lightdm) {
        let sessionKey = 'cinnamon';
        if (lightdm.default_session) {
            sessionKey = (typeof lightdm.default_session === 'object') ? (lightdm.default_session.key || 'cinnamon') : lightdm.default_session;
        } else if (lightdm.sessions && lightdm.sessions.length > 0) {
            sessionKey = (typeof lightdm.sessions[0] === 'object') ? (lightdm.sessions[0].key || 'cinnamon') : lightdm.sessions[0];
        }

        // Validar contra las sesiones realmente instaladas
        // (v4 puede devolver "default", que no existe como .desktop)
        const valid = (lightdm.sessions || []).map(s => (typeof s === 'object' ? s.key : s));
        if (!valid.includes(sessionKey)) {
            sessionKey = valid.includes('cinnamon') ? 'cinnamon' : (valid[0] || sessionKey);
        }

        console.log("Iniciando sesión con clave:", sessionKey);
        lightdm.start_session(sessionKey);
    }
}

function handlePower(action) {
    if (window.lightdm) {
        if (action === 'shutdown') lightdm.shutdown();
        else if (action === 'restart') lightdm.restart();
        else if (action === 'suspend') lightdm.suspend();
    } else {
        console.log(`Acción de energía: ${action}`);
        showMessage(`Acción de energía: ${action}`, false);
    }
}

window.addEventListener('DOMContentLoaded', initLightDM);
