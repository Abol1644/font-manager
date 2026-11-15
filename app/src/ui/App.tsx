import { useEffect, useMemo, useState, type ReactNode } from 'react';

type LibraryCategory = 'All fonts' | 'Installed';
type LibraryFont = {
  id: string;
  family: string;
  faces: GlyphInstalledFont[];
  category: 'Installed';
  description: string;
};
const categories: LibraryCategory[] = ['All fonts', 'Installed'];

function groupInstalledFonts(installed: GlyphInstalledFont[]): LibraryFont[] {
  const groups = new Map<string, GlyphInstalledFont[]>();
  for (const face of installed) {
    const key = face.family.toLocaleLowerCase();
    const group = groups.get(key) ?? [];
    group.push(face);
    groups.set(key, group);
  }
  return [...groups.values()]
    .map((faces) => ({
      id: faces[0].family.toLocaleLowerCase(),
      family: faces[0].family,
      faces: faces.sort(
        (a, b) => a.weight - b.weight || a.faceName.localeCompare(b.faceName),
      ),
      category: 'Installed' as const,
      description: `${faces.length} installed font ${faces.length === 1 ? 'file' : 'files'}`,
    }))
    .sort((a, b) => a.family.localeCompare(b.family));
}

function formatFileSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function GlyphMark() {
  return (
    <div className="brand-mark" aria-hidden="true">
      <span>g</span>
      <i />
    </div>
  );
}

function Icon({
  name,
}: {
  name:
    | 'search'
    | 'sliders'
    | 'grid'
    | 'list'
    | 'chevron'
    | 'close'
    | 'type'
    | 'plus'
    | 'refresh';
}) {
  const paths: Record<typeof name, ReactNode> = {
    search: (
      <>
        <circle cx="11" cy="11" r="6.5" />
        <path d="m16 16 4 4" />
      </>
    ),
    sliders: (
      <>
        <path d="M4 7h9M17 7h3M4 17h3m4 0h9" />
        <circle cx="15" cy="7" r="2" />
        <circle cx="9" cy="17" r="2" />
      </>
    ),
    grid: (
      <>
        <rect x="4" y="4" width="6" height="6" rx="1" />
        <rect x="14" y="4" width="6" height="6" rx="1" />
        <rect x="4" y="14" width="6" height="6" rx="1" />
        <rect x="14" y="14" width="6" height="6" rx="1" />
      </>
    ),
    list: (
      <>
        <path d="M9 6h11M9 12h11M9 18h11" />
        <path d="M4 6h.01M4 12h.01M4 18h.01" />
      </>
    ),
    chevron: <path d="m8 10 4 4 4-4" />,
    close: (
      <>
        <path d="m6 6 12 12M18 6 6 18" />
      </>
    ),
    type: (
      <>
        <path d="M4 7V4h16v3M12 4v16M8 20h8" />
      </>
    ),
    plus: (
      <>
        <path d="M12 5v14M5 12h14" />
      </>
    ),
    refresh: (
      <path d="M20 7v5h-5M4 17v-5h5m-3.2-3A7 7 0 0 1 18.2 7L20 12M4 12l1.8 5A7 7 0 0 0 18.2 15" />
    ),
  };
  return (
    <svg
      viewBox="0 0 24 24"
      aria-hidden="true"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {paths[name]}
    </svg>
  );
}

function WindowControlIcon({
  name,
}: {
  name: 'minimize' | 'maximize' | 'restore' | 'close';
}) {
  const paths: Record<typeof name, ReactNode> = {
    minimize: <path d="M5 12h14" />,
    maximize: <rect x="5.5" y="5.5" width="13" height="13" />,
    restore: (
      <>
        <path d="M8 8V5.5h10.5V16H16" />
        <rect x="5.5" y="8" width="10.5" height="10.5" />
      </>
    ),
    close: <path d="m6 6 12 12M18 6 6 18" />,
  };

  return (
    <svg
      viewBox="0 0 24 24"
      aria-hidden="true"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="square"
    >
      {paths[name]}
    </svg>
  );
}

function App() {
  const [isMaximized, setIsMaximized] = useState(false);
  const [fonts, setFonts] = useState<LibraryFont[]>([]);
  const [isLoadingFonts, setIsLoadingFonts] = useState(true);
  const [fontLoadError, setFontLoadError] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState<LibraryCategory>('All fonts');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [phrase, setPhrase] = useState(
    'The quick brown fox jumps over the lazy dog.',
  );
  const [size, setSize] = useState(54);
  const [styleIndex, setStyleIndex] = useState(0);
  const [view, setView] = useState<'list' | 'grid'>('list');
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    void window.glyphWindow.isMaximized().then(setIsMaximized);
    return window.glyphWindow.onMaximizedChanged(setIsMaximized);
  }, []);

  useEffect(() => {
    let active = true;
    setIsLoadingFonts(true);
    window.glyphWindow
      .listInstalledFonts()
      .then((installed) => {
        if (!active) return;
        const discovered = groupInstalledFonts(installed);
        setFonts(discovered);
        setSelectedId(discovered[0]?.id ?? null);
        setFontLoadError(null);
      })
      .catch((error: unknown) => {
        if (!active) return;
        setFontLoadError(
          error instanceof Error
            ? error.message
            : 'Could not read installed fonts',
        );
      })
      .finally(() => {
        if (active) setIsLoadingFonts(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const refreshFonts = async () => {
    setIsLoadingFonts(true);
    try {
      const installed = await window.glyphWindow.refreshInstalledFonts();
      const discovered = groupInstalledFonts(installed);
      setFonts(discovered);
      setSelectedId((current) =>
        current && discovered.some((font) => font.id === current)
          ? current
          : (discovered[0]?.id ?? null),
      );
      setStyleIndex(0);
      setFontLoadError(null);
    } catch (error) {
      setFontLoadError(
        error instanceof Error
          ? error.message
          : 'Could not refresh installed fonts',
      );
    } finally {
      setIsLoadingFonts(false);
    }
  };

  const visibleFonts = useMemo(
    () =>
      fonts.filter((font) => {
        const matchesQuery = font.family
          .toLowerCase()
          .includes(query.trim().toLowerCase());
        return (
          matchesQuery && (category === 'All fonts' || category === 'Installed')
        );
      }),
    [fonts, query, category],
  );

  const selectedFont: LibraryFont | undefined = fonts.find(
    (font) => font.id === selectedId,
  );
  const selectedStyle =
    selectedFont?.faces[
      Math.min(styleIndex, (selectedFont?.faces.length ?? 1) - 1)
    ];

  const chooseFont = (font: LibraryFont) => {
    setSelectedId(font.id);
    setStyleIndex(0);
    setPhrase('The quick brown fox jumps over the lazy dog.');
  };

  return (
    <main className="app-shell">
      <div
        className={`window-chrome ${window.glyphWindow.platform === 'darwin' ? 'is-macos' : ''}`}
      >
        <div className="window-chrome-brand" aria-label="Glyph Font Manager">
          <GlyphMark />
          <span>GLYPH</span>
          <i />
          <span className="window-chrome-subtitle">FONT WORKSPACE</span>
        </div>
        <div className="window-chrome-drag-space">
          <div className="window-chrome-drag-zone" aria-hidden="true" />
          <button
            type="button"
            className="window-chrome-title"
            aria-label="Double-click to maximize or restore window"
            title="Double-click to maximize or restore"
            onDoubleClick={() =>
              void window.glyphWindow.toggleMaximize().then(setIsMaximized)
            }
          >
            FONT MANAGER
          </button>
          <div className="window-chrome-drag-zone" aria-hidden="true" />
        </div>
        <div className="window-controls" aria-label="Window controls">
          <button
            type="button"
            className="window-control minimize"
            aria-label="Minimize window"
            title="Minimize"
            onClick={() => void window.glyphWindow.minimize()}
          >
            <WindowControlIcon name="minimize" />
          </button>
          <button
            type="button"
            className="window-control maximize"
            aria-label={isMaximized ? 'Restore window' : 'Maximize window'}
            title={isMaximized ? 'Restore' : 'Maximize'}
            aria-pressed={isMaximized}
            onClick={() =>
              void window.glyphWindow.toggleMaximize().then(setIsMaximized)
            }
          >
            <WindowControlIcon name={isMaximized ? 'restore' : 'maximize'} />
          </button>
          <button
            type="button"
            className="window-control close"
            aria-label="Close window"
            title="Close"
            onClick={() => void window.glyphWindow.close()}
          >
            <WindowControlIcon name="close" />
          </button>
        </div>
      </div>
      <aside className="sidebar">
        <div className="brand-lockup">
          <GlyphMark />
          <div>
            <strong>glyph</strong>
            <span>FONT WORKSPACE</span>
          </div>
        </div>
        <div className="side-section-label">LIBRARY</div>
        <button
          className={`nav-item ${category === 'All fonts' ? 'active' : ''}`}
          onClick={() => setCategory('All fonts')}
        >
          <span className="nav-glyph">Aa</span>
          <span>All fonts</span>
          <span className="nav-count">{fonts.length}</span>
        </button>
        <div className="side-section-label category-label">CATEGORIES</div>
        {categories.slice(1).map((item) => (
          <button
            key={item}
            className={`nav-item ${category === item ? 'active' : ''}`}
            onClick={() => setCategory(item)}
          >
            <span
              className={`category-dot dot-${item.toLowerCase().replace(' ', '-')}`}
            />
            <span>{item}</span>
            <span className="nav-count">{fonts.length}</span>
          </button>
        ))}
        <div className="sidebar-bottom">
          <div className="local-library-icon">⌘</div>
          <div>
            <strong>Local library</strong>
            <span>Windows installed fonts</span>
          </div>
          <span className="status-dot" />
        </div>
      </aside>

      <section className="catalog-panel">
        <header className="catalog-header">
          <div>
            <div className="eyebrow">YOUR TYPE COLLECTION</div>
            <h1>Font library</h1>
            <p>Explore the details behind every letter.</p>
          </div>
          <span className="demo-badge">
            {isLoadingFonts ? 'SCANNING' : 'LIVE LOCAL'}
          </span>
        </header>
        <div className="catalog-tools">
          <label className="search-field">
            <Icon name="search" />
            <input
              aria-label="Search font families"
              placeholder="Search typefaces..."
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
            <kbd>⌘ K</kbd>
          </label>
          <button
            className={`tool-button ${showFilters ? 'tool-active' : ''}`}
            aria-label="Toggle filters"
            onClick={() => setShowFilters(!showFilters)}
          >
            <Icon name="sliders" />
          </button>
          <button
            className="tool-button"
            aria-label="Refresh installed fonts"
            title="Rescan Windows font registrations"
            disabled={isLoadingFonts}
            onClick={() => void refreshFonts()}
          >
            <Icon name="refresh" />
          </button>
          <div className="view-switch" aria-label="Catalog view">
            <button
              className={view === 'list' ? 'chosen' : ''}
              aria-label="List view"
              onClick={() => setView('list')}
            >
              <Icon name="list" />
            </button>
            <button
              className={view === 'grid' ? 'chosen' : ''}
              aria-label="Grid view"
              onClick={() => setView('grid')}
            >
              <Icon name="grid" />
            </button>
          </div>
        </div>
        {showFilters && (
          <div className="filter-strip">
            <span>Show</span>
            {categories.map((item) => (
              <button
                key={item}
                className={category === item ? 'filter-selected' : ''}
                onClick={() => setCategory(item)}
              >
                {item}
              </button>
            ))}
          </div>
        )}
        <div className="catalog-meta">
          <span>{visibleFonts.length} typefaces</span>
          <span>
            Sorted by name <Icon name="chevron" />
          </span>
        </div>
        <div className={`font-list ${view === 'grid' ? 'font-grid' : ''}`}>
          {visibleFonts.map((font, index) => (
            <button
              key={font.id}
              className={`font-row ${selectedId === font.id ? 'selected' : ''}`}
              onClick={() => chooseFont(font)}
            >
              <span className="font-index">
                {String(index + 1).padStart(2, '0')}
              </span>
              <span className="font-row-main">
                <span
                  className="font-family"
                  style={{ fontFamily: `"${font.family}", sans-serif` }}
                >
                  {font.family}
                </span>
                <span className="font-description">
                  {font.faces.length}{' '}
                  {font.faces.length === 1 ? 'face' : 'faces'} <i>·</i>{' '}
                  {
                    new Set(font.faces.map((face) => face.path.toLowerCase()))
                      .size
                  }{' '}
                  {font.faces.length === 1 ? 'file' : 'files'}
                </span>
              </span>
              <span
                className="font-glyph-sample"
                style={{ fontFamily: `"${font.family}", serif` }}
              >
                Ag
              </span>
            </button>
          ))}
          {!isLoadingFonts && fontLoadError && (
            <div className="empty-state">
              <div className="empty-glyph">!</div>
              <strong>Could not load installed fonts</strong>
              <p>{fontLoadError}</p>
              <button onClick={() => window.location.reload()}>
                Try again
              </button>
            </div>
          )}
          {!isLoadingFonts && !fontLoadError && visibleFonts.length === 0 && (
            <div className="empty-state">
              <div className="empty-glyph">Aa</div>
              <strong>
                {fonts.length
                  ? 'No typefaces found'
                  : 'No installed fonts found'}
              </strong>
              <p>
                {fonts.length
                  ? 'Try another name.'
                  : 'Windows did not return any installed font families.'}
              </p>
              <button
                onClick={() => {
                  setQuery('');
                  setCategory('All fonts');
                }}
              >
                Clear search
              </button>
            </div>
          )}
        </div>
        <footer className="catalog-footer">
          <span>
            {isLoadingFonts
              ? 'Reading local font collection…'
              : `${fonts.length} installed families`}
          </span>
          <span>Read-only · This device</span>
        </footer>
      </section>

      <section className="specimen-panel">
        {selectedFont && selectedStyle ? (
          <>
            <header className="specimen-header">
              <div>
                <div className="eyebrow">TYPE SPECIMEN</div>
                <h2>{selectedFont.family}</h2>
                <p>{selectedFont.description}</p>
              </div>
              <button
                className="icon-button"
                aria-label="Clear selection"
                onClick={() => setSelectedId(null)}
              >
                <Icon name="close" />
              </button>
            </header>
            <div className="specimen-stage">
              <div className="specimen-stage-top">
                <span>LIVE PREVIEW</span>
                <span>{selectedFont.category.toUpperCase()}</span>
              </div>
              <div
                className="specimen-big"
                style={{
                  fontFamily: `"${selectedFont.family}", sans-serif`,
                  fontSize: `${Math.min(size, 92)}px`,
                  fontWeight: selectedStyle.weight,
                  fontStyle: selectedStyle.style.toLowerCase(),
                }}
              >
                {phrase || 'Type something...'}
              </div>
              <div className="specimen-baseline">
                <span>ABCDEFGHIJKLMNOPQRSTUVWXYZ</span>
                <span>abcdefghijklmnopqrstuvwxyz</span>
                <span>0123456789</span>
              </div>
            </div>
            <div className="control-section">
              <div className="control-heading">
                <label htmlFor="specimen-phrase">Your specimen</label>
                <span>EDIT TEXT</span>
              </div>
              <textarea
                id="specimen-phrase"
                value={phrase}
                onChange={(event) => setPhrase(event.target.value)}
                rows={2}
                placeholder="Type your own specimen..."
              />
            </div>
            <div className="control-section size-control">
              <div className="control-heading">
                <label htmlFor="font-size">Preview size</label>
                <output>{size} px</output>
              </div>
              <input
                id="font-size"
                type="range"
                min="18"
                max="92"
                value={size}
                onChange={(event) => setSize(Number(event.target.value))}
              />
            </div>
            <div className="control-section">
              <div className="control-heading">
                <label htmlFor="font-style">Style & weight</label>
                <span>{selectedFont.faces.length} INSTALLED FACES</span>
              </div>
              <div className="style-select-wrap">
                <select
                  id="font-style"
                  value={styleIndex}
                  onChange={(event) =>
                    setStyleIndex(Number(event.target.value))
                  }
                >
                  {selectedFont.faces.map((face, index) => (
                    <option key={face.id} value={index}>
                      {face.faceName} · {face.weight} · {face.style}
                    </option>
                  ))}
                </select>
                <Icon name="chevron" />
              </div>
            </div>
            <div className="specimen-details">
              <div>
                <span>FAMILY</span>
                <strong>{selectedFont.family}</strong>
              </div>
              <div>
                <span>STATUS</span>
                <strong>Installed</strong>
              </div>
              <div>
                <span>AVAILABLE STYLES</span>
                <strong>{selectedFont.faces.length}</strong>
              </div>
              <div>
                <span>FONT FILE</span>
                <strong title={selectedStyle.fileName}>
                  {selectedStyle.fileName}
                </strong>
              </div>
              <div>
                <span>FILE SIZE</span>
                <strong>{formatFileSize(selectedStyle.fileSize)}</strong>
              </div>
              <div>
                <span>FORMAT / SOURCE</span>
                <strong>
                  {selectedStyle.extension.slice(1).toUpperCase()} /{' '}
                  {selectedStyle.source}
                </strong>
              </div>
              <div>
                <span>WEIGHT / WIDTH</span>
                <strong>
                  {selectedStyle.weightName} / {selectedStyle.stretch}
                </strong>
              </div>
              <div>
                <span>MAPPED CHARACTERS</span>
                <strong>
                  {selectedStyle.characterMapCount.toLocaleString()}
                </strong>
              </div>
              <div>
                <span>FONT VERSION</span>
                <strong>{selectedStyle.version || 'Not reported'}</strong>
              </div>
              <div>
                <span>FILE MODIFIED</span>
                <strong>
                  {new Date(selectedStyle.modifiedAt).toLocaleDateString()}
                </strong>
              </div>
              <div className="file-path-detail">
                <span>INSTALLED PATH</span>
                <strong title={selectedStyle.path}>{selectedStyle.path}</strong>
              </div>
            </div>
            <div className="preview-disclaimer">
              Family and available styles are read from Windows. Preview uses
              the installed family through the system font renderer.
            </div>
          </>
        ) : (
          <div className="no-selection">
            <div className="no-selection-mark">Aa</div>
            <h2>Choose a typeface</h2>
            <p>
              Select a family from the library to open its specimen and preview
              controls.
            </p>
            <button
              onClick={() => {
                setCategory('All fonts');
                setSelectedId(fonts[0]?.id ?? null);
              }}
            >
              Browse all fonts
            </button>
          </div>
        )}
      </section>
    </main>
  );
}

export default App;
