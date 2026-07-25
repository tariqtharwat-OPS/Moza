import { app, BrowserWindow } from "electron";
import { spawn, type ChildProcess } from "node:child_process";
import path from "node:path";

const IS_DEV = !app.isPackaged;
let pythonProcess: ChildProcess | null = null;
let mainWindow: BrowserWindow | null = null;

function getPythonCommand(): string {
  const candidates = ["python", "python3", "uv run python"];
  for (const cmd of candidates) {
    try {
      const result = require("child_process").spawnSync(cmd, [
        "--version",
      ]);
      if (result.status === 0) return cmd;
    } catch {
      continue;
    }
  }
  return "python";
}

function startBackend(): void {
  const backendDir = path.resolve(__dirname, "..", "..", "..", "backend");
  const pythonCmd = getPythonCommand();

  pythonProcess = spawn(pythonCmd, ["-m", "moza.main"], {
    cwd: backendDir,
    stdio: ["ignore", "pipe", "pipe"],
    env: { ...process.env, PYTHONUNBUFFERED: "1" },
  });

  pythonProcess.stdout?.on("data", (data: Buffer) => {
    console.log(`[backend] ${data.toString().trim()}`);
  });

  pythonProcess.stderr?.on("data", (data: Buffer) => {
    console.error(`[backend:err] ${data.toString().trim()}`);
  });

  pythonProcess.on("exit", (code) => {
    console.log(`[backend] exited with code ${code}`);
    pythonProcess = null;
  });

  pythonProcess.on("error", (err) => {
    console.error(`[backend] failed to start: ${err.message}`);
  });
}

function stopBackend(): void {
  if (pythonProcess) {
    if (process.platform === "win32") {
      spawn("taskkill", ["/pid", String(pythonProcess.pid), "/f", "/t"]);
    } else {
      pythonProcess.kill("SIGTERM");
    }
    pythonProcess = null;
  }
}

async function createWindow(): Promise<void> {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    title: "MOZA",
    webPreferences: {
      preload: path.join(__dirname, "..", "preload", "preload.js"),
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  if (IS_DEV) {
    mainWindow.loadURL("http://localhost:3000");
    mainWindow.webContents.openDevTools();
  } else {
    const frontendDist = path.resolve(
      __dirname,
      "..",
      "..",
      "..",
      "frontend",
      "out",
      "index.html"
    );
    mainWindow.loadFile(frontendDist);
  }

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

app.whenReady().then(async () => {
  startBackend();
  await createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  stopBackend();
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("before-quit", () => {
  stopBackend();
});
