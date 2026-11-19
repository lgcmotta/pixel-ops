import { monitoring, modeAt, countdown, withFallback, prReference, battleHeading } from './model.mjs';

const canvas = document.querySelector('#screen');
const ctx = canvas.getContext('2d');
const params = new URLSearchParams(location.search);
const inCam = params.get('kraken') === '1';
const demo = !inCam && ['thermal', 'meeting', 'battle'].includes(params.get('demo')) ? params.get('demo') : null;
const colors = { background: '#10192b', panel: '#25354c', ink: '#d8e0ed', muted: '#8fa6bd', blue: '#78beff', green: '#64c5b2', warm: '#e5bd73' };
let state = null;
let temperatures = { cpu: null, gpu: null, liquid: null };
let sensorAt = -Infinity;
let battleImage = null;
let lastFrame = null;
let lastRender = 0;
let sensorUpdates = 0;
const demoStarted = Date.now();

// Preserve the dimensions and targetFps CAM already injected into its v1 object.
window.nzxt ??= {};
window.nzxt.v1 ??= {};
window.nzxt.v1.onMonitoringDataUpdate = data => {
  temperatures = monitoring(data);
  sensorAt = performance.now();
  sensorUpdates += 1;
  try {
    localStorage.setItem('pixelops.kraken.cam', JSON.stringify({ readings: temperatures, updated_at: Date.now(), updates: sensorUpdates, gpus: (data?.gpus ?? []).map(gpu => ({ name: gpu.name, temperature: sensorValue(gpu.temperature) })) }));
  } catch { /* The LCD remains usable when browser storage is unavailable. */ }
};
function sensorValue(value) { return typeof value === 'number' && Number.isFinite(value) ? value : null; }
if (!inCam) {
  document.body.classList.add('config');
  document.querySelector('#setup').hidden = false;
  setInterval(() => {
    try {
      const status = JSON.parse(localStorage.getItem('pixelops.kraken.cam') ?? 'null');
      if (!status) return;
      const age = Math.max(0, Math.floor((Date.now() - status.updated_at) / 1000));
      document.querySelector('#sensors').textContent = `CAM: ${status.updates} updates, last ${age}s ago. GPUs: ${status.gpus.map(gpu => `${gpu.name}: ${gpu.temperature ?? 'unavailable'}°C`).join('; ')}`;
    } catch { /* Diagnostics must not interrupt rendering. */ }
  }, 1000);
}

function text(value, x, y, size = 24, color = colors.ink, align = 'center') {
  ctx.fillStyle = color;
  ctx.font = `${size}px PixelOps, monospace`;
  ctx.textAlign = align;
  ctx.textBaseline = 'middle';
  ctx.fillText(value, x, y);
}

function fit(value, size, width) {
  ctx.font = `${size}px PixelOps, monospace`;
  let result = String(value);
  if (ctx.measureText(result).width <= width) return result;
  while (result && ctx.measureText(result + '...').width > width) result = result.slice(0, -1);
  return result + '...';
}

function lines(value, y, size, width, maxLines = 3) {
  const words = String(value).split(/\s+/);
  const rows = [];
  let line = '';
  ctx.font = `${size}px PixelOps, monospace`;
  for (const word of words) {
    if (line && ctx.measureText(`${line} ${word}`).width > width) {
      rows.push(line);
      line = word;
    } else line = line ? `${line} ${word}` : word;
  }
  if (line) rows.push(line);
  rows.slice(0, maxLines).forEach((row, index) => {
    const final = index === maxLines - 1 && rows.length > maxLines ? row + '...' : row;
    text(fit(final, size, width), 320, y + index * (size + 12), size);
  });
}

function ball(x, y, radius = 22, bob = 0) {
  ctx.save(); ctx.translate(x, y + bob);
  ctx.fillStyle = colors.warm;
  ctx.beginPath(); ctx.arc(0, 0, radius, Math.PI, 0); ctx.fill();
  ctx.fillStyle = colors.ink;
  ctx.beginPath(); ctx.arc(0, 0, radius, 0, Math.PI); ctx.fill();
  ctx.strokeStyle = colors.background; ctx.lineWidth = 5;
  ctx.beginPath(); ctx.moveTo(-radius, 0); ctx.lineTo(radius, 0); ctx.stroke();
  ctx.fillStyle = colors.background; ctx.beginPath(); ctx.arc(0, 0, 9, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = colors.ink; ctx.beginPath(); ctx.arc(0, 0, 4, 0, Math.PI * 2); ctx.fill();
  ctx.restore();
}

function base() {
  ctx.fillStyle = colors.background; ctx.fillRect(0, 0, 640, 640);
  ctx.strokeStyle = colors.panel; ctx.lineWidth = 10;
  ctx.beginPath(); ctx.arc(320, 320, 302, 0, Math.PI * 2); ctx.stroke();
  ctx.strokeStyle = colors.blue; ctx.lineWidth = 3;
  ctx.beginPath(); ctx.arc(320, 320, 293, Math.PI * 1.19, Math.PI * 1.81); ctx.stroke();
}

function thermal(now, readings) {
  text('PIXEL OPS', 320, 86, 30, colors.blue);
  text('THERMAL FIELD', 320, 125, 16, colors.muted);
  ball(320, 188, 22, Math.round(Math.sin(now / 3000) * 2));
  for (const [key, label, x] of [['cpu', 'CPU', 194], ['gpu', 'GPU', 446]]) {
    const value = readings[key];
    text(label, x, 255, 25, colors.muted);
    text(value == null ? '--' : `${Math.round(value)}°`, x, 316, 64);
    ctx.fillStyle = colors.panel; ctx.fillRect(x - 76, 367, 152, 7);
    ctx.fillStyle = value >= 85 ? colors.warm : colors.green;
    if (value != null) ctx.fillRect(x - 76, 367, 152 * Math.min(1, value / 100), 7);
  }
  text('COOLANT', 320, 424, 18, colors.muted);
  text(readings.liquid == null ? '--' : `${readings.liquid.toFixed(1)}°C`, 320, 466, 34, colors.green);
}

function meeting(view, now) {
  const remaining = countdown(view.starts_at, now);
  text(remaining === 'NOW' ? 'MEETING STARTING' : 'MEETING IN', 320, 112, 24, colors.blue);
  text(remaining, 320, 205, remaining === 'NOW' ? 58 : 72, colors.warm);
  lines(view.title, 298, 27, 470, 3);
  text(fit(view.calendar, 20, 410), 320, 445, 20, colors.green);
  text(`Starts ${view.time_label}`, 320, 486, 22);
}

function battle(view, now) {
  text('PR ENCOUNTER', 320, 88, 25, colors.blue);
  const heading = battleHeading(view);
  let size = 20;
  while (size > 14) {
    ctx.font = `${size}px PixelOps, monospace`;
    if (ctx.measureText(heading).width <= 450) break;
    size -= 1;
  }
  ctx.font = `${size}px PixelOps, monospace`;
  const twoLines = ctx.measureText(heading).width > 450;
  if (twoLines) {
    const number = prReference(view).slice((view.repository || 'PR').length);
    ctx.font = '14px PixelOps, monospace';
    const repository = fit(view.repository || 'PR', 14, 450 - ctx.measureText(number).width);
    text(repository + number, 320, 119, 14, colors.green);
    text(view.pokemon, 320, 143, 16, colors.green);
  } else text(heading, 320, 126, size, colors.green);
  const imageY = twoLines ? 164 : 148;
  const imageHeight = 469 - imageY;
  const imageWidth = Math.round(imageHeight * 384 / 280);
  if (battleImage) {
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(battleImage, 320 - imageWidth / 2, imageY, imageWidth, imageHeight);
  } else {
    ball(320, 300, 46, Math.round(Math.sin(now / 300) * 3));
  }
  // All text is diegetic or repository identity; no PR body or coding content.
  text(fit(view.label, 20, 440), 320, 494, 20, colors.ink);
}

function demoState(now) {
  const starts = demoStarted + 4 * 60000;
  return {
    mode: demo, observed_at: new Date(now).toISOString(),
    meeting: { title: 'Sample team standup', calendar: 'Sample calendar', starts_at: new Date(starts).toISOString(), ends_at: new Date(starts + 60000).toISOString(), time_label: new Date(starts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false }) },
    battle: { number: 25, pokemon: 'PIKACHU', repository: 'demo/sample-project', pr_number: 42, label: 'ASH used POKE BALL!', phase: 'ash_throws' },
  };
}

function draw(timestamp) {
  const requested = Number(window.nzxt?.v1?.targetFps);
  const fps = Number.isFinite(requested) && requested > 0 ? Math.min(30, requested) : 10;
  if (timestamp - lastRender < 1000 / fps) return;
  lastRender = timestamp;
  const device = window.nzxt?.v1;
  const width = Number(device?.width), height = Number(device?.height);
  const validDimensions = width >= 100 && width <= 2048 && height >= 100 && height <= 2048;
  if (validDimensions && (canvas.width !== width || canvas.height !== height)) { canvas.width = width; canvas.height = height; }
  const scale = Math.min(canvas.width, canvas.height) / 640;
  ctx.setTransform(scale, 0, 0, scale, (canvas.width - 640 * scale) / 2, (canvas.height - 640 * scale) / 2);
  ctx.save();
  if (device?.shape !== 'square') { ctx.beginPath(); ctx.arc(320, 320, 320, 0, 2 * Math.PI); ctx.clip(); }
  const now = Date.now();
  const current = demo ? demoState(now) : state;
  const mode = modeAt(current, now);
  const readings = demo ? { cpu: 47, gpu: 42, liquid: 32.5 } : withFallback(timestamp - sensorAt <= 5000 ? temperatures : { cpu: null, gpu: null, liquid: null }, current, now);
  base();
  if (mode === 'meeting') meeting(current.meeting, now);
  else if (mode === 'battle') battle(current.battle, now);
  else thermal(now, readings);
  if (mode !== 'thermal') {
    const reading = value => value == null ? '--' : `${Math.round(value)}°`;
    text(`CPU ${reading(readings.cpu)} / GPU ${reading(readings.gpu)} / H2O ${reading(readings.liquid)}`, 320, 536, 16, colors.muted);
  } else {
    const liveTime = new Date(now).toLocaleTimeString([], {hour12: false});
    text(demo ? 'PREVIEW / SAMPLE DATA' : timestamp - sensorAt > 5000 ? 'WAITING FOR CAM SENSORS' : `CAM LIVE / ${liveTime}`, 320, 535, 14, colors.muted);
  }
  if (demo && mode !== 'thermal') text('PREVIEW / SAMPLE DATA', 320, 576, 12, colors.muted);
  ctx.restore();
}

async function poll() {
  try {
    const response = await fetch('/kraken/state', { cache: 'no-store', signal: AbortSignal.timeout(2000) });
    if (!response.ok) throw new Error('PixelOps unavailable');
    state = await response.json();
    document.querySelector('#connection').textContent = state.available === false ? 'Waiting for the display runtime.' : 'Connected to PixelOps.';
    if (!demo && modeAt(state) === 'battle' && state.frame !== lastFrame) {
      const image = new Image();
      image.src = `/kraken/frame.png?frame=${encodeURIComponent(state.frame)}`;
      await image.decode();
      battleImage = image; lastFrame = state.frame;
    } else if (modeAt(state) !== 'battle') { battleImage = null; lastFrame = null; }
  } catch {
    document.querySelector('#connection').textContent = 'Reconnecting to PixelOps…';
  } finally {
    setTimeout(poll, !demo && modeAt(state) === 'battle' ? 100 : 500);
  }
}

document.fonts.ready.then(() => {
  function animate(timestamp) { draw(timestamp); requestAnimationFrame(animate); }
  requestAnimationFrame(animate);
  // CAM renders offscreen. Keep readings alive if Chromium suspends RAF while hidden.
  setInterval(() => {
    const now = performance.now();
    if (now - lastRender > 500) draw(now);
  }, 250);
});
poll();
