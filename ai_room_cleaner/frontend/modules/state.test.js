/**
 * @jest-environment jsdom
 */
import { getHistory, setHistory, addToHistory } from './state';

describe('State Management', () => {
  beforeEach(() => {
    // Reset history before each test
    setHistory([]);
  });

  test('should set and get the history', () => {
    const newHistory = [{ id: 1, analysis: 'clean' }];
    setHistory(newHistory);
    const history = getHistory();
    expect(history).toEqual(newHistory);
  });

  test('should add an item to the history', () => {
    const item1 = { id: 1, analysis: 'clean' };
    const item2 = { id: 2, analysis: 'messy' };
    addToHistory(item1);
    addToHistory(item2);
    const history = getHistory();
    expect(history).toHaveLength(2);
    expect(history[0]).toEqual(item2); // most recent item first
  });
});