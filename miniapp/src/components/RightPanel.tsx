import type { BodyPart, Tattoo, TattooSize } from '../types';

type RightPanelProps = {
  tattoo: Tattoo;
  size: TattooSize;
  selectedBodyPart: BodyPart;
  onSizeChange: (size: TattooSize) => void;
};

export function RightPanel({ tattoo, size, selectedBodyPart, onSizeChange }: RightPanelProps) {
  return (
    <aside className="right-panel">
      <div className="tattoo-card">
        <img src={`/assets/tattoos/${tattoo.id}.png`} alt={tattoo.name} />
        <div>
          <p className="tattoo-name">{tattoo.name}</p>
          <p className="tattoo-style">{tattoo.style}</p>
        </div>
      </div>
      <p className="body-part-label">Зона: {selectedBodyPart}</p>
      <div>
        <p className="control-label">Размер</p>
        <div className="seg-row three">
          <button
            type="button"
            className={`seg-btn${size === 's' ? ' active' : ''}`}
            onClick={() => onSizeChange('s')}
          >
            S
          </button>
          <button
            type="button"
            className={`seg-btn${size === 'm' ? ' active' : ''}`}
            onClick={() => onSizeChange('m')}
          >
            M
          </button>
          <button
            type="button"
            className={`seg-btn${size === 'l' ? ' active' : ''}`}
            onClick={() => onSizeChange('l')}
          >
            L
          </button>
        </div>
      </div>
    </aside>
  );
}
