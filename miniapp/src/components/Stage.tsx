import { anchorForBodyPart, zonesForView } from '../data/bodyZones';
import type { BodyPart, BodyView, Tattoo } from '../types';

type StageProps = {
  modelSrc: string;
  view: BodyView;
  selectedBodyPart: BodyPart;
  onSelectBodyPart: (bodyPart: BodyPart) => void;
  tattoo: Tattoo;
  tattooScale: number;
  onOpenGallery: () => void;
};

export function Stage({
  modelSrc,
  view,
  selectedBodyPart,
  onSelectBodyPart,
  tattoo,
  tattooScale,
  onOpenGallery,
}: StageProps) {
  const zones = zonesForView(view);
  const tattooAnchor = anchorForBodyPart(selectedBodyPart, view);
  const spriteX = view === 'front' ? 0 : -100;
  const stageHeight = 133.333;
  const tattooBaseSize = 18;
  const tattooSize = tattooBaseSize * tattooScale;

  return (
    <section className="stage-card" aria-label="Сцена примерки">
      <button type="button" className="gallery-open" onClick={onOpenGallery}>
        Галерея →
      </button>

      <div className="stage-canvas">
        <svg className="model-svg" viewBox={`0 0 100 ${stageHeight}`} aria-label="Модель с зонами тела">
          <defs>
            <clipPath id="stage-half-clip">
              <rect x="0" y="0" width="100" height={stageHeight} />
            </clipPath>
          </defs>

          <g clipPath="url(#stage-half-clip)">
            <image
              href={modelSrc}
              x={spriteX}
              y="0"
              width="200"
              height={stageHeight}
              preserveAspectRatio="xMidYMid meet"
            />
          </g>

          <g className="zone-layer">
            {zones.map((zone) => (
              <polygon
                key={zone.id}
                points={zone.points}
                className={`zone-hit${selectedBodyPart === zone.bodyPart ? ' active' : ''}`}
                onPointerDown={() => onSelectBodyPart(zone.bodyPart)}
              />
            ))}
          </g>
          <image
            className="tattoo-svg-image"
            href={`/assets/tattoos/${tattoo.id}.png`}
            x={tattooAnchor.x - tattooSize / 2}
            y={tattooAnchor.y - tattooSize / 2}
            width={tattooSize}
            height={tattooSize}
            preserveAspectRatio="xMidYMid meet"
          />
        </svg>
      </div>
    </section>
  );
}
