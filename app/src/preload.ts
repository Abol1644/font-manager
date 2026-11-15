import { contextBridge, ipcRenderer } from 'electron';

const channels = {
  listInstalledFonts: 'fonts:list-installed',
  refreshInstalledFonts: 'fonts:refresh-installed',
  minimize: 'window:minimize',
  toggleMaximize: 'window:toggle-maximize',
  close: 'window:close',
  isMaximized: 'window:is-maximized',
  maximizedChanged: 'window:maximized-changed',
} as const;

contextBridge.exposeInMainWorld('glyphWindow', {
  platform: process.platform,
  listInstalledFonts: () => ipcRenderer.invoke(channels.listInstalledFonts),
  refreshInstalledFonts: () =>
    ipcRenderer.invoke(channels.refreshInstalledFonts),
  minimize: () => ipcRenderer.invoke(channels.minimize),
  toggleMaximize: () => ipcRenderer.invoke(channels.toggleMaximize),
  close: () => ipcRenderer.invoke(channels.close),
  isMaximized: () => ipcRenderer.invoke(channels.isMaximized),
  onMaximizedChanged: (callback: (isMaximized: boolean) => void) => {
    const listener = (_event: Electron.IpcRendererEvent, value: boolean) => {
      callback(value);
    };
    ipcRenderer.on(channels.maximizedChanged, listener);
    return () =>
      ipcRenderer.removeListener(channels.maximizedChanged, listener);
  },
});
