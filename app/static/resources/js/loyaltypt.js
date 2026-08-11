document.addEventListener('DOMContentLoaded', () => {
  const counter = document.getElementById('points-counter');
  if (!counter) return;
  const target = parseInt(counter.dataset.target) || 0;
  let current = 0;
  counter.textContent = '0';

  const duration = 2000; // 2 seconds
  const fps = 60;
  const totalFrames = duration / (1000 / fps);
  let frame = 0;
  const timer = setInterval(() => {
    frame++;
    const progress = frame / totalFrames;
    current = Math.round(target * progress);
    counter.textContent = current;

    if (frame >= totalFrames) {
      counter.textContent = target;
      clearInterval(timer);
    }
  }, 1000 / fps);
});
