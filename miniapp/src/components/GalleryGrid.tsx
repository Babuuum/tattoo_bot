import type { Tattoo } from '../types';

type GalleryGridProps = {
  items: Tattoo[];
  selectedTattooId: string;
  onSelect: (item: Tattoo) => void;
};

export function GalleryGrid({ items, selectedTattooId, onSelect }: GalleryGridProps) {
  if (items.length === 0) {
    return <p className="empty-state">Ничего не найдено. Попробуйте другой запрос.</p>;
  }

  return (
    <div className="gallery-grid">
      {items.map((item) => (
        <button
          type="button"
          key={item.id}
          className={`gallery-item${selectedTattooId === item.id ? ' active' : ''}`}
          onClick={() => onSelect(item)}
        >
          <img src={`/assets/tattoos/${item.id}.png`} alt={item.name} />
          <span>{item.name}</span>
        </button>
      ))}
    </div>
  );
}
