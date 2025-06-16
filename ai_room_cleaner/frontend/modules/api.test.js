/**
 * @jest-environment jsdom
 */
import { analyzeRoom, getHistory } from './api';
import * as config from '../config.js';

jest.mock('../config.js', () => ({
    ...jest.requireActual('../config.js'),
    getApiConfig: jest.fn(),
    getConfig: jest.fn(),
}));

// Mock fetch
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({}),
  })
);

describe('API Functions', () => {
  beforeEach(() => {
    fetch.mockClear();
    config.getConfig.mockResolvedValue({
        apiUrl: 'http://localhost/api',
    });
    config.getApiConfig.mockReturnValue({
        apiUrl: 'http://localhost/api',
    });
  });

  test('analyzeRoom should send a POST request with form data', async () => {
    const imageFile = new File(['(⌐□_□)'], 'chucknorris.png', { type: 'image/png' });
    await analyzeRoom(imageFile);
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/v1/analyze-room-secure'), expect.any(Object));
    const fetchOptions = fetch.mock.calls[0][1];
    expect(fetchOptions.method).toBe('POST');
    expect(fetchOptions.body).toBeInstanceOf(FormData);
  });

  test('getHistory should send a GET request', async () => {
    await getHistory();
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/history'), expect.any(Object));
  });
});