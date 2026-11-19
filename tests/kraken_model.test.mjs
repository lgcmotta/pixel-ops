import assert from 'node:assert/strict';
import test from 'node:test';
import { monitoring, modeAt, countdown, withFallback, prReference, battleHeading } from '../pixel_ops/web/kraken/model.mjs';

test('encounter heading uses the repository and PR number independently of the Pokemon number', () => {
  const battle = { repository: 'demo/sample-project', pr_number: 42, number: 5, pokemon: 'CHARMELEON' };
  assert.equal(prReference(battle), 'demo/sample-project#42');
  assert.equal(battleHeading(battle), 'demo/sample-project#42 CHARMELEON');
  assert.equal(battleHeading({ ...battle, pr_number: null }), 'demo/sample-project CHARMELEON');
});

test('CAM readings keep zero, reject unsupported values, and do not invent temperatures', () => {
  assert.deepEqual(monitoring({ cpus: [{ temperature: 0 }], gpus: [{ temperature: 42 }], kraken: { liquidTemperature: 31.5 } }), { cpu: 0, gpu: 42, liquid: 31.5 });
  assert.deepEqual(monitoring({ cpus: [{ temperature: null }], gpus: [{ temperature: 'N/A' }], kraken: { liquidTemperature: NaN } }), { cpu: null, gpu: null, liquid: null });
  assert.deepEqual(monitoring(), { cpu: null, gpu: null, liquid: null });
});

test('selects the NVIDIA GPU and uses only a fresh runtime temperature fallback', () => {
  const now = Date.now();
  const readings = monitoring({ gpus: [{ name: 'AMD integrated', temperature: 44 }, { name: 'NVIDIA Sample GPU', temperature: 51 }] });
  assert.equal(readings.gpu, 51);
  const missing = monitoring({ gpus: [{ name: 'AMD integrated', temperature: 44 }, { name: 'NVIDIA Sample GPU' }] });
  assert.equal(missing.gpu, null);
  const state = { temperatures: { gpu: 53, observed_at: new Date(now).toISOString() } };
  assert.equal(withFallback(missing, state, now).gpu, 53);
  assert.equal(withFallback(readings, state, now).gpu, 51);
  assert.equal(withFallback(missing, state, now + 10001).gpu, null);
});

test('meeting countdown expires at its absolute boundary and stalled snapshots fall back', () => {
  const now = Date.parse('2026-10-30T16:00:00Z');
  const state = { mode: 'meeting', observed_at: new Date(now).toISOString(), meeting: { starts_at: new Date(now).toISOString(), ends_at: new Date(now + 60000).toISOString() } };
  assert.equal(modeAt(state, now), 'meeting');
  assert.equal(countdown(state.meeting.starts_at, now - 300000), '5:00');
  assert.equal(countdown(state.meeting.starts_at, now - 1), '0:01');
  assert.equal(countdown(state.meeting.starts_at, now + 1), 'NOW');
  assert.equal(modeAt({ ...state, observed_at: new Date(now + 60000).toISOString() }, now + 60000), 'thermal');
  assert.equal(modeAt({ ...state, mode: 'battle' }, now + 5001), 'thermal');
  assert.equal(modeAt({ ...state, mode: 'battle' }, now), 'battle');
  assert.equal(modeAt(null, now), 'thermal');
});
