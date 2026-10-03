/**
 * CollegeClue - Cinematic Roaming Universities & Constellation Intro Engine
 * Features:
 * - Fullscreen HTML5 canvas with roaming university typography
 * - Dynamic constellation plexus connecting lines with traveling energy pulses
 * - Interactive particle physics with cursor influence
 * - Live percentage loader & smooth dismissal
 */
(function() {
    'use strict';

    const UNIVERSITIES = [
        "IIT DELHI",
        "IISC BANGALORE",
        "DELHI UNIVERSITY",
        "BITS PILANI",
        "IIT BOMBAY",
        "MUMBAI UNIVERSITY",
        "ANNA UNIVERSITY",
        "IIT MADRAS",
        "JADAVPUR UNIVERSITY",
        "ALLIANCE UNIVERSITY",
        "SRCC DELHI",
        "ST. STEPHEN'S COLLEGE",
        "AIIMS NEW DELHI",
        "IIM AHMEDABAD",
        "BHU VARANASI",
        "SVR UNIVERSITY",
        "IIT KHARAGPUR",
        "CHRIST UNIVERSITY",
        "MANIPAL ACADEMY",
        "VELLORE INSTITUTE OF TECH"
    ];

    let animFrameId = null;
    let canvas = null;
    let ctx = null;
    let width = 0;
    let height = 0;
    let particles = [];
    let roamingTexts = [];
    let progressTimer = null;
    let autoCloseTimer = null;
    let progressVal = 0;
    let mouse = { x: null, y: null };

    function setupCanvas() {
        canvas = document.getElementById('ccRoamingCanvas');
        if (!canvas) return false;
        ctx = canvas.getContext('2d');
        resize();
        window.addEventListener('resize', resize);
        return true;
    }

    function resize() {
        if (!canvas) return;
        const dpr = Math.min(window.devicePixelRatio || 1, 2);
        width = window.innerWidth;
        height = window.innerHeight;
        canvas.width = width * dpr;
        canvas.height = height * dpr;
        canvas.style.width = width + 'px';
        canvas.style.height = height + 'px';
        ctx.scale(dpr, dpr);
    }

    function initElements() {
        particles = [];
        roamingTexts = [];

        // 1. Constellation Nodes
        const particleCount = Math.floor(Math.min(width, height) / 18);
        for (let i = 0; i < particleCount; i++) {
            particles.push({
                x: Math.random() * width,
                y: Math.random() * height,
                vx: (Math.random() - 0.5) * 0.9,
                vy: (Math.random() - 0.5) * 0.9,
                radius: Math.random() * 2 + 1.2,
                color: Math.random() > 0.4 ? '#3b82f6' : '#f59e0b'
            });
        }

        // 2. Roaming University Names
        const textCount = Math.min(UNIVERSITIES.length, Math.floor(width / 75));
        const shuffled = [...UNIVERSITIES].sort(() => 0.5 - Math.random());
        for (let i = 0; i < textCount; i++) {
            const size = Math.floor(Math.random() * 8) + 12; // 12px - 20px
            roamingTexts.push({
                text: shuffled[i],
                x: Math.random() * width,
                y: Math.random() * height,
                vx: (Math.random() - 0.5) * 0.75,
                vy: (Math.random() - 0.5) * 0.65,
                size: size,
                opacity: Math.random() * 0.28 + 0.18,
                color: Math.random() > 0.35 ? '#93c5fd' : '#fde68a'
            });
        }
    }

    function draw() {
        ctx.clearRect(0, 0, width, height);

        // A. Draw Connecting Constellation Lines
        const maxDist = 135;
        for (let i = 0; i < particles.length; i++) {
            const p1 = particles[i];

            // Update particle positions
            p1.x += p1.vx;
            p1.y += p1.vy;

            // Bounce off boundaries
            if (p1.x < 0 || p1.x > width) p1.vx *= -1;
            if (p1.y < 0 || p1.y > height) p1.vy *= -1;

            // Draw particle dot
            ctx.beginPath();
            ctx.arc(p1.x, p1.y, p1.radius, 0, Math.PI * 2);
            ctx.fillStyle = p1.color;
            ctx.shadowBlur = 8;
            ctx.shadowColor = p1.color;
            ctx.fill();
            ctx.shadowBlur = 0;

            // Connect nearby particles
            for (let j = i + 1; j < particles.length; j++) {
                const p2 = particles[j];
                const dx = p1.x - p2.x;
                const dy = p1.y - p2.y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < maxDist) {
                    const alpha = (1 - dist / maxDist) * 0.28;
                    ctx.beginPath();
                    ctx.moveTo(p1.x, p1.y);
                    ctx.lineTo(p2.x, p2.y);
                    ctx.strokeStyle = `rgba(59, 130, 246, ${alpha})`;
                    ctx.lineWidth = 0.9;
                    ctx.stroke();

                    // Dynamic light pulse traveling on lines
                    if (Math.random() < 0.003) {
                        const pulseX = p1.x + (p2.x - p1.x) * 0.5;
                        const pulseY = p1.y + (p2.y - p1.y) * 0.5;
                        ctx.beginPath();
                        ctx.arc(pulseX, pulseY, 2, 0, Math.PI * 2);
                        ctx.fillStyle = '#f59e0b';
                        ctx.shadowBlur = 10;
                        ctx.shadowColor = '#f59e0b';
                        ctx.fill();
                        ctx.shadowBlur = 0;
                    }
                }
            }

            // Mouse proximity line
            if (mouse.x !== null) {
                const mdx = p1.x - mouse.x;
                const mdy = p1.y - mouse.y;
                const mdist = Math.sqrt(mdx * mdx + mdy * mdy);
                if (mdist < 120) {
                    ctx.beginPath();
                    ctx.moveTo(p1.x, p1.y);
                    ctx.lineTo(mouse.x, mouse.y);
                    ctx.strokeStyle = `rgba(245, 158, 11, ${(1 - mdist / 120) * 0.35})`;
                    ctx.lineWidth = 1;
                    ctx.stroke();
                }
            }
        }

        // B. Draw Roaming Universities Typography
        ctx.font = '600 13px "Plus Jakarta Sans", system-ui, sans-serif';
        for (let i = 0; i < roamingTexts.length; i++) {
            const rt = roamingTexts[i];
            rt.x += rt.vx;
            rt.y += rt.vy;

            // Wrap around edges smoothly
            if (rt.x < -180) rt.x = width + 50;
            if (rt.x > width + 180) rt.x = -50;
            if (rt.y < -30) rt.y = height + 20;
            if (rt.y > height + 30) rt.y = -20;

            ctx.save();
            ctx.font = `700 ${rt.size}px "Plus Jakarta Sans", monospace`;
            ctx.fillStyle = rt.color;
            ctx.globalAlpha = rt.opacity;
            ctx.shadowBlur = 12;
            ctx.shadowColor = rt.color;
            ctx.fillText(rt.text, rt.x, rt.y);

            // Subtle connecting line from university to nearest particle
            if (particles.length > 0) {
                const nearest = particles[i % particles.length];
                const dx = rt.x - nearest.x;
                const dy = rt.y - nearest.y;
                const d = Math.sqrt(dx * dx + dy * dy);
                if (d < 160) {
                    ctx.beginPath();
                    ctx.moveTo(rt.x + 20, rt.y - 4);
                    ctx.lineTo(nearest.x, nearest.y);
                    ctx.strokeStyle = `rgba(245, 158, 11, ${(1 - d / 160) * 0.18})`;
                    ctx.lineWidth = 0.7;
                    ctx.stroke();
                }
            }

            ctx.restore();
        }

        animFrameId = requestAnimationFrame(draw);
    }

    function initController() {
        const overlay = document.getElementById('collegeClueIntroOverlay');
        if (!overlay) return;

        const percentEl = document.getElementById('ccIntroPercent');
        const progressBar = document.getElementById('ccIntroProgressBar');
        const enterBtn = document.getElementById('ccEnterPortalBtn');

        function closeOverlay() {
            if (progressTimer) clearInterval(progressTimer);
            if (autoCloseTimer) clearTimeout(autoCloseTimer);
            if (animFrameId) cancelAnimationFrame(animFrameId);

            overlay.classList.add('is-closing');
            setTimeout(() => {
                overlay.style.display = 'none';
                overlay.classList.remove('is-animating', 'is-closing');
                document.body.style.overflow = '';
            }, 380);
        }

        function playAnimation() {
            overlay.style.display = 'flex';
            overlay.classList.remove('is-closing');
            void overlay.offsetWidth;
            overlay.classList.add('is-animating');
            document.body.style.overflow = 'hidden';

            // Setup and start canvas loop
            if (setupCanvas()) {
                initElements();
                if (animFrameId) cancelAnimationFrame(animFrameId);
                draw();
            }

            // Progress loader ticker
            progressVal = 0;
            if (percentEl) percentEl.textContent = '0%';
            if (progressBar) progressBar.style.width = '0%';

            if (progressTimer) clearInterval(progressTimer);
            const durationMs = 3200;
            const intervalMs = 40;
            const step = 100 / (durationMs / intervalMs);

            progressTimer = setInterval(() => {
                progressVal = Math.min(100, progressVal + step);
                if (percentEl) percentEl.textContent = Math.floor(progressVal) + '%';
                if (progressBar) progressBar.style.width = progressVal + '%';

                if (progressVal >= 100) {
                    clearInterval(progressTimer);
                }
            }, intervalMs);

            // Auto-dismiss after 3.6s
            if (autoCloseTimer) clearTimeout(autoCloseTimer);
            autoCloseTimer = setTimeout(() => {
                closeOverlay();
            }, 3600);
        }

        // Global function for on-demand playback
        window.playCollegeClueLogoAnimation = playAnimation;

        // Skip buttons & click dismiss
        if (enterBtn) {
            enterBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                closeOverlay();
            });
        }

        overlay.addEventListener('click', () => {
            closeOverlay();
        });

        // Mousemove tracking on canvas
        overlay.addEventListener('mousemove', (e) => {
            mouse.x = e.clientX;
            mouse.y = e.clientY;
        });
        overlay.addEventListener('mouseleave', () => {
            mouse.x = null;
            mouse.y = null;
        });

        // Keyboard controls (Esc, Space, Enter)
        window.addEventListener('keydown', (e) => {
            if ((e.key === 'Escape' || e.key === ' ' || e.key === 'Enter') && overlay.style.display !== 'none') {
                closeOverlay();
            }
        });

        // Click navbar brand logo to replay
        document.querySelectorAll('.navbar-brand').forEach(brand => {
            brand.addEventListener('click', (e) => {
                if (window.location.pathname === '/' || window.location.pathname === '') {
                    e.preventDefault();
                    playAnimation();
                }
            });
        });

        // Trigger conditions:
        // 1. Just logged in / registered (server flagged)
        // 2. Query param ?animate=1
        // 3. First time opening the website in current browser session
        const serverTrigger = overlay.getAttribute('data-trigger-animation') === 'true';
        const queryTrigger = window.location.search.includes('animate');
        const sessionTrigger = !sessionStorage.getItem('cc_intro_seen_session');

        if (serverTrigger || queryTrigger || sessionTrigger) {
            sessionStorage.setItem('cc_intro_seen_session', 'true');
            playAnimation();
        } else {
            overlay.style.display = 'none';
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initController);
    } else {
        initController();
    }
})();
