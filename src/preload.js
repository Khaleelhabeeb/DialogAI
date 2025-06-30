const { contextBridge, ipcRenderer } = require('electron')

console.log('Preload script loaded');

contextBridge.exposeInMainWorld('electronAPI', {
  startListening: () => ipcRenderer.send('start-listening'),
  interruptConversation: () => ipcRenderer.send('interrupt-conversation'),
  stopApp: () => ipcRenderer.send('stop-app'),
  onUpdateThoughtBubble: (callback) => ipcRenderer.on('update-thought-bubble', (_event, value) => callback(value)),
  onConversationEnd: (callback) => ipcRenderer.on('conversation-ended', () => callback()),
  onRecordingStateChange: (callback) => ipcRenderer.on('recording-state-change', (_event, isRecording) => callback(isRecording)),
  onChangeBackgroundImage: (callback) => ipcRenderer.on('change-background-image', (_event, imageName) => callback(imageName))
})
