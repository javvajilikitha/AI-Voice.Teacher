/**
 * Animated Particle Background for AI Voice Teacher
 * Dark Navy-Blue Theme with glowing blue & cyan particles, subtle connecting lines,
 * and soft ambient glow effects.
 * 
 * Lightweight, vanilla JavaScript, zero dependencies.
 * Non-blocking: pointer-events are disabled so all clicks and scrolling work normally.
 */
(function () {
    "use strict";

    // 1. Ensure canvas exists and is placed behind all content
    let canvas = document.getElementById("bg-particles-canvas");
    if (!canvas) {
        canvas = document.createElement("canvas");
        canvas.id = "bg-particles-canvas";
        canvas.setAttribute("aria-hidden", "true");
        if (document.body) {
            document.body.insertBefore(canvas, document.body.firstChild);
        } else {
            document.addEventListener("DOMContentLoaded", function () {
                document.body.insertBefore(canvas, document.body.firstChild);
            });
        }
    }

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let width = 0;
    let height = 0;
    let dpr = 1;
    let animationFrameId = null;
    let isRunning = false;

    // 2. Responsive canvas sizing with high-DPI crispness
    function resize() {
        dpr = Math.min(window.devicePixelRatio || 1, 2);
        width = window.innerWidth;
        height = window.innerHeight;

        canvas.width = Math.floor(width * dpr);
        canvas.height = Math.floor(height * dpr);
        canvas.style.width = width + "px";
        canvas.style.height = height + "px";

        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    // 3. Ambient glow orbs in the background
    const ambientGlows = [
        { xRatio: 0.25, yRatio: 0.3, radius: 280, color: "rgba(14, 165, 233, 0.08)", vx: 0.05, vy: 0.03 },
        { xRatio: 0.75, yRatio: 0.65, radius: 340, color: "rgba(59, 130, 246, 0.07)", vx: -0.04, vy: -0.02 },
        { xRatio: 0.5, yRatio: 0.15, radius: 220, color: "rgba(34, 211, 238, 0.06)", vx: 0.03, vy: -0.04 }
    ];

    // 4. Color palette for glowing particles
    const particleColors = [
        { r: 56, g: 189, b: 248 },  // Electric Cyan (#38bdf8)
        { r: 96, g: 165, b: 250 },  // Sky Blue (#60a5fa)
        { r: 34, g: 211, b: 238 },  // Vibrant Aqua (#22d3ee)
        { r: 125, g: 211, b: 252 }, // Soft Ice Cyan (#7dd3fc)
        { r: 59, g: 130, b: 246 }   // Royal Blue (#3b82f6)
    ];

    // 5. Particle Generator
    let particles = [];
    const MAX_CONNECT_DIST = 125;
    const MAX_CONNECT_DIST_SQ = MAX_CONNECT_DIST * MAX_CONNECT_DIST;

    function initParticles() {
        // Density based on viewport size: minimum 45, max 95
        const count = Math.max(45, Math.min(95, Math.floor((width * height) / 16000)));
        particles = [];

        for (let i = 0; i < count; i++) {
            const color = particleColors[Math.floor(Math.random() * particleColors.length)];
            particles.push({
                x: Math.random() * width,
                y: Math.random() * height,
                vx: (Math.random() - 0.5) * 0.45,
                vy: (Math.random() - 0.5) * 0.45,
                baseRadius: Math.random() * 1.8 + 1.2,
                color: color,
                pulseSpeed: Math.random() * 0.025 + 0.015,
                pulseOffset: Math.random() * Math.PI * 2,
                alpha: Math.random() * 0.4 + 0.45
            });
        }
    }

    // 6. Passive cursor interaction (does not capture or block clicks)
    const mouse = {
        x: null,
        y: null,
        maxDist: 140
    };

    window.addEventListener("mousemove", function (e) {
        mouse.x = e.clientX;
        mouse.y = e.clientY;
    }, { passive: true });

    window.addEventListener("mouseleave", function () {
        mouse.x = null;
        mouse.y = null;
    }, { passive: true });

    // 7. Animation Draw Loop
    let lastTime = 0;

    function draw(currentTime) {
        if (!isRunning) return;

        animationFrameId = requestAnimationFrame(draw);

        // Limit update step if browser was throttled
        if (!lastTime) lastTime = currentTime;
        const delta = Math.min((currentTime - lastTime) / 1000, 0.1);
        lastTime = currentTime;

        // A. Draw Dark Navy-Blue Background Gradient
        const bgGrad = ctx.createRadialGradient(
            width * 0.5, height * 0.35, 60,
            width * 0.5, height * 0.5, Math.max(width, height) * 0.85
        );
        bgGrad.addColorStop(0, "#0b1f44"); // Soft deep navy glow at center
        bgGrad.addColorStop(0.45, "#07152f"); // Theme background
        bgGrad.addColorStop(1, "#030a18"); // Deep midnight navy edges

        ctx.fillStyle = bgGrad;
        ctx.fillRect(0, 0, width, height);

        // B. Render Ambient Floating Glow Orbs
        for (let i = 0; i < ambientGlows.length; i++) {
            const glow = ambientGlows[i];
            glow.xRatio += glow.vx * delta * 0.1;
            glow.yRatio += glow.vy * delta * 0.1;

            if (glow.xRatio < 0.1 || glow.xRatio > 0.9) glow.vx *= -1;
            if (glow.yRatio < 0.1 || glow.yRatio > 0.9) glow.vy *= -1;

            const gx = glow.xRatio * width;
            const gy = glow.yRatio * height;

            const orbGrad = ctx.createRadialGradient(gx, gy, 0, gx, gy, glow.radius);
            orbGrad.addColorStop(0, glow.color);
            orbGrad.addColorStop(1, "rgba(7, 21, 47, 0)");

            ctx.fillStyle = orbGrad;
            ctx.beginPath();
            ctx.arc(gx, gy, glow.radius, 0, Math.PI * 2);
            ctx.fill();
        }

        // C. Update and Draw Particles
        const now = currentTime * 0.001;

        for (let i = 0; i < particles.length; i++) {
            const p = particles[i];

            // Move
            p.x += p.vx;
            p.y += p.vy;

            // Wrap edges smoothly
            if (p.x < -10) p.x = width + 10;
            else if (p.x > width + 10) p.x = -10;

            if (p.y < -10) p.y = height + 10;
            else if (p.y > height + 10) p.y = -10;

            // Gentle mouse nudge
            if (mouse.x !== null && mouse.y !== null) {
                const dx = p.x - mouse.x;
                const dy = p.y - mouse.y;
                const distSq = dx * dx + dy * dy;
                if (distSq < mouse.maxDist * mouse.maxDist && distSq > 0) {
                    const dist = Math.sqrt(distSq);
                    const force = (1 - dist / mouse.maxDist) * 0.8;
                    p.x += (dx / dist) * force;
                    p.y += (dy / dist) * force;
                }
            }

            // Pulsing size and alpha
            const pulse = Math.sin(now * 2.5 + p.pulseOffset);
            const currentRadius = p.baseRadius + pulse * 0.4;
            const currentAlpha = Math.max(0.2, Math.min(0.95, p.alpha + pulse * 0.2));

            // Draw glowing particle with soft shadow
            ctx.save();
            ctx.beginPath();
            ctx.arc(p.x, p.y, Math.max(0.8, currentRadius), 0, Math.PI * 2);

            ctx.shadowBlur = 10;
            ctx.shadowColor = `rgba(${p.color.r}, ${p.color.g}, ${p.color.b}, ${currentAlpha})`;
            ctx.fillStyle = `rgba(${p.color.r}, ${p.color.g}, ${p.color.b}, ${currentAlpha})`;
            ctx.fill();
            ctx.restore();
        }

        // D. Draw Subtle Connecting Lines between nearby particles
        ctx.lineWidth = 0.75;
        for (let i = 0; i < particles.length; i++) {
            const p1 = particles[i];
            for (let j = i + 1; j < particles.length; j++) {
                const p2 = particles[j];
                const dx = p1.x - p2.x;
                const dy = p1.y - p2.y;
                const distSq = dx * dx + dy * dy;

                if (distSq < MAX_CONNECT_DIST_SQ) {
                    const dist = Math.sqrt(distSq);
                    const lineAlpha = (1 - dist / MAX_CONNECT_DIST) * 0.18;

                    ctx.strokeStyle = `rgba(56, 189, 248, ${lineAlpha})`;
                    ctx.beginPath();
                    ctx.moveTo(p1.x, p1.y);
                    ctx.lineTo(p2.x, p2.y);
                    ctx.stroke();
                }
            }

            // Also connect subtly to mouse if nearby
            if (mouse.x !== null && mouse.y !== null) {
                const mdx = p1.x - mouse.x;
                const mdy = p1.y - mouse.y;
                const mdistSq = mdx * mdx + mdy * mdy;

                if (mdistSq < mouse.maxDist * mouse.maxDist) {
                    const mdist = Math.sqrt(mdistSq);
                    const mAlpha = (1 - mdist / mouse.maxDist) * 0.28;
                    ctx.strokeStyle = `rgba(34, 211, 238, ${mAlpha})`;
                    ctx.beginPath();
                    ctx.moveTo(p1.x, p1.y);
                    ctx.lineTo(mouse.x, mouse.y);
                    ctx.stroke();
                }
            }
        }
    }

    // 8. Lifecycle Management
    function start() {
        if (!isRunning) {
            isRunning = true;
            lastTime = 0;
            animationFrameId = requestAnimationFrame(draw);
        }
    }

    function stop() {
        isRunning = false;
        if (animationFrameId) {
            cancelAnimationFrame(animationFrameId);
            animationFrameId = null;
        }
    }

    // Pause when tab is not visible to preserve battery & CPU
    document.addEventListener("visibilitychange", function () {
        if (document.hidden) {
            stop();
        } else {
            start();
        }
    });

    let resizeTimeout = null;
    window.addEventListener("resize", function () {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(function () {
            resize();
            initParticles();
        }, 150);
    });

    // Initialize
    resize();
    initParticles();
    start();
})();
