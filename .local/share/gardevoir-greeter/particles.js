const canvas = document.getElementById('particles-canvas');
const ctx = canvas.getContext('2d');

let width, height;
let particles = [];
let mouse = { x: null, y: null, radius: 140 };

function resize() {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
}

window.addEventListener('resize', resize);
window.addEventListener('mousemove', (e) => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
});

window.addEventListener('mouseleave', () => {
    mouse.x = null;
    mouse.y = null;
});

class Particle {
    constructor() {
        this.reset();
    }

    reset() {
        this.x = Math.random() * width;
        this.y = Math.random() * height;
        this.size = Math.random() * 2.2 + 0.7;
        this.baseSize = this.size;
        this.speedX = (Math.random() - 0.5) * 0.55;
        this.speedY = -Math.random() * 0.7 - 0.15; // Suave deriva ascendente
        this.alpha = Math.random() * 0.52 + 0.2;
        this.isShiny = Math.random() > 0.86; // Destellos rosas poco frecuentes
        this.pulse = Math.random() * Math.PI * 2;
        this.pulseSpeed = Math.random() * 0.03 + 0.01;
    }

    update() {
        this.x += this.speedX;
        this.y += this.speedY;
        this.pulse += this.pulseSpeed;

        // Rebote o reaparición suave
        if (this.y < -10) this.y = height + 10;
        if (this.x < -10) this.x = width + 10;
        if (this.x > width + 10) this.x = -10;

        // Interacción con el ratón
        if (mouse.x !== null && mouse.y !== null) {
            const dx = mouse.x - this.x;
            const dy = mouse.y - this.y;
            const dist = Math.sqrt(dx * dx + dy * dy);

            if (dist < mouse.radius) {
                const force = (mouse.radius - dist) / mouse.radius;
                const angle = Math.atan2(dy, dx);
                this.x -= Math.cos(angle) * force * 3;
                this.y -= Math.sin(angle) * force * 3;
            }
        }
    }

    draw() {
        ctx.save();
        const currentAlpha = Math.max(0.1, this.alpha + Math.sin(this.pulse) * 0.25);
        ctx.globalAlpha = currentAlpha;

        if (this.isShiny) {
            // Destello Shiny (Estrella de 4 puntas dorada / rosa)
            ctx.fillStyle = '#ff4370';
            ctx.shadowBlur = 10;
            ctx.shadowColor = '#ff4370';
            this.drawStar(this.x, this.y, this.size * 2, this.size * 0.8);
        } else {
            // Orbe de Energía Psíquica (Cian / Turquesa)
            ctx.fillStyle = '#2ba1df';
            ctx.shadowBlur = 8;
            ctx.shadowColor = '#38bdf8';
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();
        }

        ctx.restore();
    }

    drawStar(cx, cy, outerRadius, innerRadius) {
        let rot = Math.PI / 2 * 3;
        let x = cx;
        let y = cy;
        const step = Math.PI / 4;

        ctx.beginPath();
        ctx.moveTo(cx, cy - outerRadius);
        for (let i = 0; i < 4; i++) {
            x = cx + Math.cos(rot) * outerRadius;
            y = cy + Math.sin(rot) * outerRadius;
            ctx.lineTo(x, y);
            rot += step;

            x = cx + Math.cos(rot) * innerRadius;
            y = cy + Math.sin(rot) * innerRadius;
            ctx.lineTo(x, y);
            rot += step;
        }
        ctx.lineTo(cx, cy - outerRadius);
        ctx.closePath();
        ctx.fill();
    }
}

function initParticles() {
    resize();
    particles = [];
    const count = Math.min(70, Math.floor((width * height) / 22000));
    for (let i = 0; i < count; i++) {
        particles.push(new Particle());
    }
}

function connectParticles() {
    const maxDist = 125;
    for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
            const dx = particles[i].x - particles[j].x;
            const dy = particles[i].y - particles[j].y;
            const dist = Math.sqrt(dx * dx + dy * dy);

            if (dist < maxDist) {
                const alpha = (1 - dist / maxDist) * 0.16;
                ctx.strokeStyle = `rgba(43, 161, 223, ${alpha})`;
                ctx.lineWidth = 0.8;
                ctx.beginPath();
                ctx.moveTo(particles[i].x, particles[i].y);
                ctx.lineTo(particles[j].x, particles[j].y);
                ctx.stroke();
            }
        }
    }
}

function animate() {
    ctx.clearRect(0, 0, width, height);

    for (let i = 0; i < particles.length; i++) {
        particles[i].update();
        particles[i].draw();
    }

    connectParticles();
    requestAnimationFrame(animate);
}

initParticles();
animate();
