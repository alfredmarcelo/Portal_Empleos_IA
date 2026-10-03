import React, { useState, useEffect, useRef } from "react";

// Importa automáticamente todos los fotogramas ordenados numéricamente
const frameModules = import.meta.glob(
  "../../assets/drawing_animation_frames/*.{jpg,jpeg,png,webp}",
  { eager: true, import: "default" }
);

const frameModules2 = import.meta.glob(
  "../../assets/drawing_animation_frames2/*.{jpg,jpeg,png,webp}",
  { eager: true, import: "default" }
);

export const ANIMATION_FRAMES_1 = Object.entries(frameModules)
  .sort(([a], [b]) => a.localeCompare(b, undefined, { numeric: true }))
  .map(([_, url]) => url);

export const ANIMATION_FRAMES_2 = Object.entries(frameModules2)
  .sort(([a], [b]) => a.localeCompare(b, undefined, { numeric: true }))
  .map(([_, url]) => url);

export const ANIMATION_SETS = [ANIMATION_FRAMES_1, ANIMATION_FRAMES_2].filter(
  (set) => set.length > 0
);

// Compatibilidad hacia atrás
export const ANIMATION_FRAMES = ANIMATION_FRAMES_1;

export default function FrameAnimation({
  isPlaying = true,
  fps = 30,
  pauseDuration = 1000,
  className = "Header-Image",
  sets = ANIMATION_SETS,
}) {
  const [isPaused, setIsPaused] = useState(false);
  const canvasRef = useRef(null);
  const imageCacheRef = useRef(new Map());

  // Referencias para la animación continua sin re-renderizar React en cada cuadro
  const isPlayingRef = useRef(isPlaying);
  const isPausedRef = useRef(false);
  const setIndexRef = useRef(0);
  const frameIndexRef = useRef(0);
  const pauseTimerRef = useRef(null);
  const rafIdRef = useRef(null);

  isPlayingRef.current = isPlaying;
  isPausedRef.current = isPaused;

  // Precarga y decodificación de todas las imágenes en GPU
  useEffect(() => {
    sets.forEach((setUrls) => {
      setUrls.forEach((url) => {
        if (!imageCacheRef.current.has(url)) {
          const img = new Image();
          img.src = url;
          if (typeof img.decode === "function") {
            img.decode().catch(() => {});
          }
          imageCacheRef.current.set(url, img);
        }
      });
    });
  }, [sets]);

  // Dibuja el fotograma de forma instantánea y sin parpadeos
  const drawFrame = (url) => {
    const canvas = canvasRef.current;
    if (!canvas || !url) return;
    const ctx = canvas.getContext("2d", { alpha: false });
    if (!ctx) return;

    let img = imageCacheRef.current.get(url);
    if (!img) {
      img = new Image();
      img.src = url;
      imageCacheRef.current.set(url, img);
    }

    const render = () => {
      if (img.naturalWidth > 0 && img.naturalHeight > 0) {
        if (canvas.width !== img.naturalWidth || canvas.height !== img.naturalHeight) {
          canvas.width = img.naturalWidth;
          canvas.height = img.naturalHeight;
        }
        ctx.drawImage(img, 0, 0);
      }
    };

    if (img.complete && img.naturalWidth > 0) {
      render();
    } else {
      img.onload = render;
    }
  };

  // Bucle de animación con requestAnimationFrame de alta precisión
  useEffect(() => {
    if (!isPlaying || sets.length === 0) {
      setIndexRef.current = 0;
      frameIndexRef.current = 0;
      setIsPaused(false);
      isPausedRef.current = false;
      if (pauseTimerRef.current) clearTimeout(pauseTimerRef.current);
      if (rafIdRef.current) cancelAnimationFrame(rafIdRef.current);
      return;
    }

    const targetFps = Math.max(1, Number(fps) || 30);
    const frameDuration = 1000 / targetFps;

    let lastTime = performance.now();
    let accumulator = 0;

    const startLoop = () => {
      const currentSet = sets[setIndexRef.current] || [];
      if (currentSet.length === 0) return;

      drawFrame(currentSet[frameIndexRef.current]);

      const loop = (now) => {
        if (!isPlayingRef.current) return;
        if (isPausedRef.current) return;

        const delta = now - lastTime;
        lastTime = now;
        accumulator += delta;

        const activeSet = sets[setIndexRef.current] || [];
        if (activeSet.length === 0) return;

        let frameChanged = false;
        while (accumulator >= frameDuration) {
          accumulator -= frameDuration;
          frameIndexRef.current += 1;
          frameChanged = true;

          // Si terminó el set actual
          if (frameIndexRef.current >= activeSet.length) {
            frameIndexRef.current = activeSet.length - 1;
            drawFrame(activeSet[frameIndexRef.current]);

            // Entra en la pausa entre loops
            setIsPaused(true);
            isPausedRef.current = true;

            pauseTimerRef.current = setTimeout(() => {
              if (!isPlayingRef.current) return;
              // Alterna al siguiente conjunto de fotogramas
              setIndexRef.current = (setIndexRef.current + 1) % sets.length;
              frameIndexRef.current = 0;
              setIsPaused(false);
              isPausedRef.current = false;
              lastTime = performance.now();
              accumulator = 0;
              startLoop();
            }, pauseDuration);

            return;
          }
        }

        if (frameChanged && frameIndexRef.current < activeSet.length) {
          drawFrame(activeSet[frameIndexRef.current]);
        }

        rafIdRef.current = requestAnimationFrame(loop);
      };

      rafIdRef.current = requestAnimationFrame(loop);
    };

    startLoop();

    return () => {
      if (pauseTimerRef.current) clearTimeout(pauseTimerRef.current);
      if (rafIdRef.current) cancelAnimationFrame(rafIdRef.current);
    };
  }, [isPlaying, fps, pauseDuration, sets]);

  if (sets.length === 0) return null;

  return (
    <canvas
      ref={canvasRef}
      role="img"
      aria-label="Animación fotogramas"
      className={className}
      style={{
        opacity: isPaused ? 0 : undefined,
        visibility: isPaused ? "hidden" : "visible",
      }}
    />
  );
}
