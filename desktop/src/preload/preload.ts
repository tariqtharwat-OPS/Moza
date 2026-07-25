import { contextBridge, ipcRenderer } from "electron";

contextBridge.exposeInMainWorld("moza", {
  platform: process.platform,
  version: "0.1.0",
  terminal: {
    write: (input: string) => ipcRenderer.invoke("terminal:write", input),
  },
});
