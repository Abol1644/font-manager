export {};

declare global {
  interface GlyphInstalledFont {
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

  interface Window {
    glyphWindow: {
      platform: NodeJS.Platform;
      listInstalledFonts: () => Promise<GlyphInstalledFont[]>;
      refreshInstalledFonts: () => Promise<GlyphInstalledFont[]>;
      minimize: () => Promise<void>;
      toggleMaximize: () => Promise<boolean>;
      close: () => Promise<void>;
      isMaximized: () => Promise<boolean>;
      onMaximizedChanged: (
        callback: (isMaximized: boolean) => void,
      ) => () => void;
    };
  }
}
