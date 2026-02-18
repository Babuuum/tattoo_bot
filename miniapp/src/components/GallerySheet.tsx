import { useEffect } from 'react';

import { STYLE_FILTERS } from '../data/tattoos';
import type { Tattoo, TattooStyle } from '../types';
import { GalleryGrid } from './GalleryGrid';

type GallerySheetProps = {
  isOpen: boolean;
  search: string;
  styleFilter: 'all' | TattooStyle;
  items: Tattoo[];
  selectedTattooId: string;
  onClose: () => void;
  onSearchChange: (value: string) => void;
  onStyleFilterChange: (value: 'all' | TattooStyle) => void;
  onSelectTattoo: (tattoo: Tattoo) => void;
};

export function GallerySheet({
  isOpen,
  search,
  styleFilter,
  items,
  selectedTattooId,
  onClose,
  onSearchChange,
  onStyleFilterChange,
  onSelectTattoo,
}: GallerySheetProps) {
  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const onEsc = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', onEsc);
    return () => window.removeEventListener('keydown', onEsc);
  }, [isOpen, onClose]);

  if (!isOpen) {
    return null;
  }

  return (
    <div className="sheet-root" role="dialog" aria-modal="true" aria-label="Галерея тату">
      <button type="button" className="sheet-overlay" onClick={onClose} aria-label="Закрыть" />
      <section className="sheet-panel">
        <div className="sheet-header">
          <h2>Галерея</h2>
          <button type="button" className="icon-btn" onClick={onClose}>
            ✕
          </button>
        </div>

        <input
          className="search-input"
          type="text"
          value={search}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder="Поиск эскиза"
        />

        <div className="filters-row">
          {STYLE_FILTERS.map((filter) => (
            <button
              key={filter.value}
              type="button"
              className={`chip${styleFilter === filter.value ? ' active' : ''}`}
              onClick={() => onStyleFilterChange(filter.value)}
            >
              {filter.label}
            </button>
          ))}
        </div>

        <div className="sheet-scroll">
          <GalleryGrid
            items={items}
            selectedTattooId={selectedTattooId}
            onSelect={(item) => {
              onSelectTattoo(item);
              onClose();
            }}
          />
        </div>
      </section>
    </div>
  );
}
