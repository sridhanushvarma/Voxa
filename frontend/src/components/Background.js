import React, { useEffect, useRef } from 'react';
import { useSettings } from '../contexts/SettingsContext';
import './Background.css';

/**
 * Layered ambient background:
 *  - parallax grid that drifts toward the cursor
 *  - canvas particle constellation
 *  - CRT scanline + vignette overlays
 * All layers respect the animations / scanlines settings.
 */
export default function Background() {
  const { settings } = useSettings();
  const canvasRef = useRef(null);
  const gridRef = useRef(null);
  const rafRef = useRef(0);

  // Parallax grid
  useEffect(() => {
    if (!settings.animations) return;
    const onMove = (e) => {
      const x = (e.clientX / window.innerWidth - 0.5) * 24;
      const y = (e.clientY / window.innerHeight - 0.5) * 24;
      if (gridRef.current) {
        gridRef.current.style.transform = `translate3d(${x}px, ${y}px, 0)`;
      }
    };
    window.addEventListener('mousemove', onMove);
    return () => window.removeEventListener('mousemove', onMove);
  }, [settings.animations]);

  // Particle constellation
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let w, h, particles;

    const accent = () =>
      getComputedStyle(document.documentElement)
        .getPropertyValue('--accent')
        .trim() || '#00d9ff';

    const resize = () => {
      w = canvas.width = window.innerWidth;
      h = canvas.height = window.innerHeight;
      const count = Math.min(90, Math.floor((w * h) / 22000));
      particles = Array.from({ length: count }, () => ({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.35,
        vy: (Math.random() - 0.5) * 0.35,
        r: Math.random() * 1.6 + 0.4,
      }));
    };
    resize();
    window.addEventListener('resize', resize);

    const draw = () => {
      const color = accent();
      ctx.clearRect(0, 0, w, h);
      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0 || p.x > w) p.vx *= -1;
        if (p.y < 0 || p.y > h) p.vy *= -1;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.globalAlpha = 0.5;
        ctx.fill();
        for (let j = i + 1; j < particles.length; j++) {
          const q = particles[j];
          const dx = p.x - q.x;
          const dy = p.y - q.y;
          const dist = dx * dx + dy * dy;
          if (dist < 14000) {
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(q.x, q.y);
            ctx.strokeStyle = color;
            ctx.globalAlpha = 0.12 * (1 - dist / 14000);
            ctx.lineWidth = 1;
            ctx.stroke();
          }
        }
      }
      ctx.globalAlpha = 1;
      rafRef.current = requestAnimationFrame(draw);
    };

    if (settings.animations) {
      draw();
    } else {
      ctx.clearRect(0, 0, w, h);
    }

    return () => {
      cancelAnimationFrame(rafRef.current);
      window.removeEventListener('resize', resize);
    };
  }, [settings.animations]);

  return (
    <div className="bg-root" aria-hidden="true">
      <div ref={gridRef} className="bg-grid" />
      <div className="bg-aurora" />
      <canvas ref={canvasRef} className="bg-canvas" />
      {settings.scanlines && <div className="bg-scanlines" />}
      <div className="bg-vignette" />
    </div>
  );
}
