import test from 'node:test';
import assert from 'node:assert/strict';
import { localAccountRequest } from './codexAccount.ts';

function request(address = '127.0.0.1', headers = {}) {
  return { socket: { remoteAddress: address }, headers: { host: 'localhost:5174', ...headers } };
}
test('account controls accept local same-origin requests', () => {
  assert.equal(localAccountRequest(request()), true);
  assert.equal(localAccountRequest(request('::1', { origin: 'http://localhost:5174' })), true);
});
test('reject remote, cross-site and rebinding requests', () => {
  assert.equal(localAccountRequest(request('192.168.1.50')), false);
  assert.equal(localAccountRequest(request('127.0.0.1', { origin: 'https://evil.example' })), false);
  assert.equal(localAccountRequest(request('127.0.0.1', { host: 'evil.example:5174' })), false);
  assert.equal(localAccountRequest(request('127.0.0.1', { 'sec-fetch-site': 'cross-site' })), false);
});
