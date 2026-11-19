export function sensor(value, min = 0, max = 150) {
  return typeof value === 'number' && Number.isFinite(value) && value >= min && value <= max ? value : null;
}

export function monitoring(data) {
  const gpus = Array.isArray(data?.gpus) ? data.gpus : [];
  const discrete = gpus.find(gpu => /nvidia|geforce|rtx/i.test(gpu?.name ?? ''));
  const gpu = discrete ?? gpus.find(gpu => sensor(gpu?.temperature) != null);
  return {
    cpu: sensor(data?.cpus?.[0]?.temperature),
    gpu: sensor(gpu?.temperature),
    liquid: sensor(data?.kraken?.liquidTemperature),
  };
}

export function withFallback(readings, state, now = Date.now()) {
  const age = now - Date.parse(state?.temperatures?.observed_at);
  return { ...readings, gpu: readings.gpu ?? (age >= 0 && age <= 10000 ? sensor(state.temperatures.gpu) : null) };
}

export function modeAt(state, now = Date.now()) {
  const observed = Date.parse(state?.observed_at);
  if (!Number.isFinite(observed) || now - observed > 5000 || now < observed - 5000) return 'thermal';
  if (state.mode === 'battle') return 'battle';
  const start = Date.parse(state?.meeting?.starts_at);
  const end = Date.parse(state?.meeting?.ends_at);
  if (state.mode === 'meeting' && now >= start - 300000 && now < end) return 'meeting';
  return 'thermal';
}

export function countdown(startsAt, now = Date.now()) {
  const seconds = Math.max(0, Math.ceil((Date.parse(startsAt) - now) / 1000));
  return seconds ? `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}` : 'NOW';
}

export function prReference(view) {
  const repository = view?.repository || 'PR';
  const number = Number(view?.pr_number);
  return repository + (Number.isInteger(number) && number > 0 ? `#${number}` : '');
}

export function battleHeading(view) {
  return `${prReference(view)} ${view?.pokemon ?? ''}`.trim();
}
