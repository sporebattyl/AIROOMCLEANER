/**
 * @jest-environment jsdom
 */
import { handleAnalyzeRoom } from './eventHandlers';
import * as api from './api';
import * as ui from './ui';
import * as state from './state';

jest.mock('./api');
jest.mock('./ui');
jest.mock('./state');

describe('Event Handlers', () => {
  beforeEach(() => {
    // Set up our document body and UI elements
    document.body.innerHTML = `
      <input type="file" id="file-input" />
      <ul id="messes-list"></ul>
      <span id="cleanliness-score"></span>
      <div id="results-container"></div>
      <div id="loading-overlay"></div>
      <div id="error-toast"></div>
    `;
    state.getUIElements.mockReturnValue({
      fileInput: document.getElementById('file-input'),
      messesList: document.getElementById('messes-list'),
      cleanlinessScore: document.getElementById('cleanliness-score'),
      resultsContainer: document.getElementById('results-container'),
      loadingOverlay: document.getElementById('loading-overlay'),
      errorToast: document.getElementById('error-toast'),
    });
  });

  test('handleAnalyzeRoom should call api, ui, and state functions', async () => {
    const mockAnalysisResult = {
      tasks: [{ mess: 'Dirty sock' }],
      cleanliness_score: 50,
    };
    api.analyzeRoom.mockResolvedValue(mockAnalysisResult);
    
    // Mock the file input
    const fileInput = document.getElementById('file-input');
    const file = new File(['content'], 'test.jpg', { type: 'image/jpeg' });
    Object.defineProperty(fileInput, 'files', {
      value: [file]
    });

    await handleAnalyzeRoom();

    expect(ui.showLoading).toHaveBeenCalled();
    expect(api.analyzeRoom).toHaveBeenCalledWith(file);
    expect(ui.updateMessesList).toHaveBeenCalledWith(mockAnalysisResult.tasks, expect.any(Object));
    expect(ui.updateCleanlinessScore).toHaveBeenCalledWith(mockAnalysisResult.cleanliness_score);
    expect(ui.showResults).toHaveBeenCalled();
    expect(ui.hideLoading).toHaveBeenCalled();
  });
});