import { app, BrowserWindow, ipcMain, type IpcMainInvokeEvent } from 'electron';
import { execFile } from 'node:child_process';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { promisify } from 'node:util';
import path from 'node:path';
import started from 'electron-squirrel-startup';

// Handle creating/removing shortcuts on Windows when installing/uninstalling.
if (started) {
  app.quit();
}

let mainWindowRef: BrowserWindow | null = null;
const execFileAsync = promisify(execFile);

interface InstalledFontFace {
  id: string;
  family: string;
  faceName: string;
  weightName: string;
  weight: number;
  stretch: string;
  style: string;
  path: string;
  fileName: string;
  extension: string;
  fileSize: number;
  modifiedAt: string;
  characterMapCount: number;
  version: string;
  source: 'User' | 'System';
}

async function scanInstalledFonts(): Promise<InstalledFontFace[]> {
  if (process.platform !== 'win32') {
    throw new Error(
      `Installed font discovery is not implemented for ${process.platform} yet`,
    );
  }

  // Read the actual font files registered for the current user and machine,
  // then ask WPF's GlyphTypeface to extract each file's face metadata.
  const script = [
    '[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding',
    'Add-Type -AssemblyName PresentationCore',
    '$registrations = @()',
    'foreach ($key in @("HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Fonts", "HKCU:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Fonts")) {',
    '  if (-not (Test-Path -LiteralPath $key)) { continue }',
    '  $source = if ($key.StartsWith("HKCU:")) { "User" } else { "System" }',
    '  $properties = (Get-ItemProperty -LiteralPath $key).PSObject.Properties | Where-Object { $_.Name -notlike "PS*" }',
    '  foreach ($property in $properties) { $registrations += @{ displayName = $property.Name; registeredPath = [string]$property.Value; source = $source } }',
    '}',
    '$seen = @{}',
    '$result = foreach ($registration in $registrations) {',
    '  $registeredPath = [Environment]::ExpandEnvironmentVariables($registration.registeredPath.Trim())',
    '  if ([IO.Path]::IsPathRooted($registeredPath)) { $candidate = $registeredPath } else { $candidate = Join-Path $env:WINDIR ("Fonts\\" + $registeredPath) }',
    '  if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) { $candidate = Join-Path $env:LOCALAPPDATA ("Microsoft\\Windows\\Fonts\\" + $registeredPath) }',
    '  if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) { continue }',
    '  $extension = [IO.Path]::GetExtension($candidate).ToLowerInvariant()',
    '  if ($extension -notin @(".ttf", ".otf", ".ttc", ".otc")) { continue }',
    '  $canonicalPath = [IO.Path]::GetFullPath($candidate)',
    '  $identity = $canonicalPath.ToLowerInvariant()',
    '  if ($seen.ContainsKey($identity)) { continue }',
    '  $seen[$identity] = $true',
    '  try {',
    '    $typeface = New-Object System.Windows.Media.GlyphTypeface -ArgumentList ([Uri]::new($canonicalPath))',
    '    $family = if ($typeface.FamilyNames.ContainsKey("en-us")) { $typeface.FamilyNames["en-us"] } else { [string]($typeface.FamilyNames.Values | Select-Object -First 1) }',
    '    $faceName = if ($typeface.FaceNames.ContainsKey("en-us")) { $typeface.FaceNames["en-us"] } else { [string]($typeface.FaceNames.Values | Select-Object -First 1) }',
    '    $weightName = $typeface.Weight.ToString()',
    '    $weight = switch -Regex ($weightName) { "Thin" { 100; break } "ExtraLight|UltraLight" { 200; break } "Light" { 300; break } "Normal|Regular" { 400; break } "Medium" { 500; break } "SemiBold|DemiBold" { 600; break } "ExtraBold|UltraBold" { 800; break } "Bold" { 700; break } "Black|Heavy" { 900; break } default { 400 } }',
    '    $file = Get-Item -LiteralPath $canonicalPath',
    '    @{ id = $identity; family = [string]$family; faceName = [string]$faceName; weightName = $weightName; weight = $weight; stretch = $typeface.Stretch.ToString(); style = $typeface.Style.ToString(); path = $canonicalPath; fileName = $file.Name; extension = $extension; fileSize = [long]$file.Length; modifiedAt = $file.LastWriteTimeUtc.ToString("o"); characterMapCount = [int]$typeface.CharacterToGlyphMap.Count; version = [string]$typeface.Version; source = $registration.source }',
    '  } catch { continue }',
    '}',
    '$result | ConvertTo-Json -Depth 4 -Compress',
  ].join('; ');

  const { stdout } = await execFileAsync(
    'powershell.exe',
    ['-NoLogo', '-NoProfile', '-NonInteractive', '-Command', script],
    { windowsHide: true, maxBuffer: 8 * 1024 * 1024, timeout: 120_000 },
  );
  const parsed: unknown = JSON.parse(stdout.trim() || '[]');
  const entries = Array.isArray(parsed) ? parsed : [parsed];
  return entries as InstalledFontFace[];
}

async function discoverInstalledFonts(
  forceRefresh = false,
): Promise<InstalledFontFace[]> {
  const cachePath = path.join(
    app.getPath('userData'),
    'installed-fonts-cache.json',
  );
  if (!forceRefresh) {
    try {
      const cached = JSON.parse(await readFile(cachePath, 'utf8')) as {
        version?: number;
        faces?: InstalledFontFace[];
      };
      if (cached.version === 1 && Array.isArray(cached.faces))
        return cached.faces;
    } catch {
      // A missing or invalid cache triggers a fresh local scan.
    }
  }

  const faces = await scanInstalledFonts();
  await mkdir(path.dirname(cachePath), { recursive: true });
  await writeFile(cachePath, JSON.stringify({ version: 1, faces }), 'utf8');
  return faces;
}

function getTrustedWindow(event: IpcMainInvokeEvent, args: unknown[]) {
  if (args.length !== 0) throw new Error('IPC actions do not accept arguments');

  const window = BrowserWindow.fromWebContents(event.sender);
  if (
    !window ||
    window !== mainWindowRef ||
    event.senderFrame !== event.sender.mainFrame
  ) {
    throw new Error('Untrusted window IPC sender');
  }

  return window;
}

ipcMain.handle('window:minimize', (event, ...args: unknown[]) => {
  getTrustedWindow(event, args).minimize();
});

ipcMain.handle('window:toggle-maximize', (event, ...args: unknown[]) => {
  const window = getTrustedWindow(event, args);
  if (window.isMaximized()) window.unmaximize();
  else window.maximize();
  return window.isMaximized();
});

ipcMain.handle('window:close', (event, ...args: unknown[]) => {
  getTrustedWindow(event, args).close();
});

ipcMain.handle('window:is-maximized', (event, ...args: unknown[]) => {
  return getTrustedWindow(event, args).isMaximized();
});

ipcMain.handle('fonts:list-installed', (event, ...args: unknown[]) => {
  getTrustedWindow(event, args);
  return discoverInstalledFonts();
});

ipcMain.handle('fonts:refresh-installed', (event, ...args: unknown[]) => {
  getTrustedWindow(event, args);
  return discoverInstalledFonts(true);
});

const createWindow = () => {
  const window = new BrowserWindow({
    width: 1500,
    height: 960,
    minWidth: 1040,
    minHeight: 700,
    resizable: true,
    backgroundColor: '#0a0a0a',
    title: 'Glyph — Font Manager',
    frame: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      webSecurity: true,
    },
  });

  // Keep the active window available to the validated window-control handlers.
  mainWindowRef = window;

  const publishMaximizedState = () => {
    if (!window.isDestroyed()) {
      window.webContents.send('window:maximized-changed', window.isMaximized());
    }
  };
  window.on('maximize', publishMaximizedState);
  window.on('unmaximize', publishMaximizedState);
  window.on('closed', () => {
    if (mainWindowRef === window) mainWindowRef = null;
  });

  window.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
  window.webContents.on('will-navigate', (event, url) => {
    if (url !== MAIN_WINDOW_VITE_DEV_SERVER_URL) event.preventDefault();
  });

  // and load the index.html of the app.
  if (MAIN_WINDOW_VITE_DEV_SERVER_URL) {
    window.loadURL(MAIN_WINDOW_VITE_DEV_SERVER_URL);
  } else {
    window.loadFile(
      path.join(__dirname, `../renderer/${MAIN_WINDOW_VITE_NAME}/index.html`),
    );
  }
};

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.whenReady().then(() => {
  createWindow();

  // On OS X it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// In this file you can include the rest of your app's specific main process
// code. You can also put them in separate files and import them here.
