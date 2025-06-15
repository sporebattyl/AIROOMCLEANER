/**
 * @jest-environment jsdom
 */
import { initializeUIElements, updateMessesList } from './ui';

describe('UI Functions', () => {
  beforeEach(() => {
    // Set up our document body
    document.body.innerHTML = `
      <ul id="messes-list"></ul>
      <span id="tasks-count"></span>
      <div id="empty-state" class="hidden"></div>
      <div id="results-container"></div>
    `;
    initializeUIElements();
  });

  test('updateMessesList should render a list of tasks', () => {
    const tasks = [{ mess: 'Spilled coffee' }, { mess: 'Crumbs on the floor' }];
    updateMessesList(tasks);
    const listItems = document.querySelectorAll('#messes-list li');
    expect(listItems).toHaveLength(2);
    expect(listItems[0].textContent).toBe('Spilled coffee');
    expect(listItems[1].textContent).toBe('Crumbs on the floor');
    expect(document.getElementById('tasks-count').textContent).toBe('2');
  });
});