const talkButton = document.getElementById('talk-button');
const interruptButton = document.getElementById('interrupt-button');
const stopButton = document.getElementById('stop-button');
const thoughtBubble = document.getElementById('thought-bubble');
const recordingLabel = document.getElementById('recording-label');
const dialogAiImage = document.getElementById('dialog-ai-image');

talkButton.addEventListener('click', () => {
  console.log('Talk button clicked');
  window.electronAPI.startListening();
});

interruptButton.addEventListener('click', () => {
  console.log('Interrupt button clicked');
  window.electronAPI.interruptConversation();
});

stopButton.addEventListener('click', () => {
  console.log('Stop button clicked');
  window.electronAPI.stopApp();
});

// Listen for updates from the main process
window.electronAPI.onUpdateThoughtBubble((message) => {
  thoughtBubble.textContent = message;
});

window.electronAPI.onConversationEnd(() => {
  talkButton.disabled = false;
  thoughtBubble.textContent = 'Conversation ended or "goodbye" detected.';
});

window.electronAPI.onRecordingStateChange((isRecording) => {
  recordingLabel.style.visibility = isRecording ? 'visible' : 'hidden';
  talkButton.disabled = isRecording; // Disable talk button while recording/processing
});

window.electronAPI.onChangeBackgroundImage((imageName) => {
    if (imageName === 'bg.png') {
        dialogAiImage.src = '../assets/bg.png';
    } else if (imageName === 'bg2.png') {
        dialogAiImage.src = '../assets/bg2.png';
    }
    // Add more conditions if other images are needed
});


// Initial state
thoughtBubble.textContent = ' ';
recordingLabel.style.visibility = 'hidden';
talkButton.disabled = false;

console.log('Renderer script loaded and event listeners attached.');
