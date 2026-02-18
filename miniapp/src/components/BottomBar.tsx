import { PriceCalculator } from './PriceCalculator';
import type { BodyPart, TattooSize, TattooStyle } from '../types';

type BottomBarProps = {
  size: TattooSize;
  style: TattooStyle;
  bodyPart: BodyPart;
};

export function BottomBar({ size, style, bodyPart }: BottomBarProps) {
  return (
    <footer className="bottom-bar">
      <div className="price-wrap">
        <p>Итоговая цена</p>
        <strong>
          <PriceCalculator size={size} style={style} bodyPart={bodyPart} />
        </strong>
      </div>
      <button type="button" className="cta-btn">
        Продолжить
      </button>
    </footer>
  );
}
