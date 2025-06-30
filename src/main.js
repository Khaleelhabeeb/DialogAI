const { app, BrowserWindow, ipcMain } = require('electron')
const path = require('path')
const { PythonShell } = require('python-shell');

let mainWindow;
let pythonShell = null;

function createWindow () {
  mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      enableRemoteModule: false
    }
  })

  mainWindow.loadFile('src/index.html')
  // mainWindow.webContents.openDevTools(); // For debugging
}

function startPythonProcess() {
  if (pythonShell) {
    console.log("Python script already running or not cleaned up properly.");
    // Optionally, kill existing process before starting a new one
    // pythonShell.kill();
  }

  const options = {
    mode: 'text', // Can be 'json' if Python script outputs JSON
    pythonPath: 'python', // Or specific path to python executable
    pythonOptions: ['-u'], // get print results in real-time
    scriptPath: path.join(__dirname, '../app'), // Path to the app directory
    args: [] // if your python script accepts arguments
  };

  console.log("Starting python script: conversation_manager_electron.py");
  pythonShell = new PythonShell('conversation_manager_electron.py', options);

  pythonShell.on('message', function (message) {
    // Received a message from the Python script
    console.log('PythonShell message:', message);
    try {
      const data = JSON.parse(message);
      if (data.type === 'thought') {
        mainWindow.webContents.send('update-thought-bubble', data.content);
      } else if (data.type === 'status') {
         if (data.content === 'listening') {
            mainWindow.webContents.send('update-thought-bubble', 'Listening...');
            mainWindow.webContents.send('recording-state-change', true);
            mainWindow.webContents.send('change-background-image', 'bg2.png');
        } else if (data.content === 'thinking') {
            mainWindow.webContents.send('update-thought-bubble', 'Thinking...');
            mainWindow.webContents.send('recording-state-change', false); // Not recording when thinking
        } else if (data.content === 'speaking') {
            mainWindow.webContents.send('update-thought-bubble', 'Speaking...');
            mainWindow.webContents.send('recording-state-change', false);
        } else if (data.content === 'ended') {
            mainWindow.webContents.send('conversation-ended');
            mainWindow.webContents.send('change-background-image', 'bg.png');
            mainWindow.webContents.send('recording-state-change', false);
        } else if (data.content === 'ready_to_listen'){
            mainWindow.webContents.send('update-thought-bubble', 'Click Talk to start');
            mainWindow.webContents.send('recording-state-change', false);
            mainWindow.webContents.send('change-background-image', 'bg.png');
        }
      }
    } catch (e) {
      console.error('Error parsing message from Python or unknown message type:', message, e);
      // Send raw message if not JSON or specific format for debugging
      // mainWindow.webContents.send('update-thought-bubble', `PY: ${message}`);
    }
  });

  pythonShell.on('stderr', function (stderr) {
    console.error('PythonShell stderr:', stderr);
    mainWindow.webContents.send('update-thought-bubble', `Error: ${stderr}`);
  });

  pythonShell.on('error', function (err) {
    console.error('PythonShell error:', err);
    mainWindow.webContents.send('update-thought-bubble', `Script Error: ${err.message}`);
  });

  pythonShell.on('close', function () {
    console.log('PythonShell script finished.');
    // mainWindow.webContents.send('conversation-ended'); // Can be handled by 'ended' status
    mainWindow.webContents.send('change-background-image', 'bg.png');
    mainWindow.webContents.send('recording-state-change', false);
    pythonShell = null; // Reset shell instance
  });
}

app.whenReady().then(() => {
  createWindow();
  startPythonProcess(); // Start python backend on app ready

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
      if (!pythonShell) startPythonProcess();
    }
  })
})

app.on('window-all-closed', () => {
  if (pythonShell) {
    console.log("Terminating Python script due to window-all-closed.");
    pythonShell.send('stop_conversation'); // Gracefully stop python
    pythonShell.kill('SIGTERM'); // Force kill if not stopped
    pythonShell = null;
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
})

// IPC Handlers
ipcMain.on('start-listening', () => {
  console.log('IPC: start-listening received');
  if (pythonShell) {
    pythonShell.send('start_listening');
  } else {
    console.error("Python shell not initialized. Cannot start listening.");
    // Optionally, try to restart it
    // startPythonProcess();
    // pythonShell.send('start_listening');
    mainWindow.webContents.send('update-thought-bubble', "Error: Backend not running.");
  }
});

ipcMain.on('interrupt-conversation', () => {
  console.log('IPC: interrupt-conversation received');
  if (pythonShell) {
    pythonShell.send('interrupt_conversation');
  } else {
    console.error("Python shell not initialized. Cannot interrupt.");
    mainWindow.webContents.send('update-thought-bubble', "Error: Backend not running.");
  }
});

ipcMain.on('stop-app', () => {
  console.log('IPC: stop-app received');
  if (pythonShell) {
    pythonShell.send('stop_conversation'); // Tell python script to stop
    // Wait a bit for Python to clean up, then quit.
    // Or listen for 'close' event from pythonShell to quit app.
    // For now, direct quit.
  }
  app.quit();
});
