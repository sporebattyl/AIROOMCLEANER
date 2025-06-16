module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['@testing-library/jest-dom', './jest.setup.js'],
  transform: {
    '^.+\\.js$': 'babel-jest',
  },
  globals: {
    global,
  },
};