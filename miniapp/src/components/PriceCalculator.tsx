import { calcPrice } from '../lib/pricing';
import type { BodyPart, TattooSize, TattooStyle } from '../types';

type PriceCalculatorProps = {
  size: TattooSize;
  style: TattooStyle;
  bodyPart: BodyPart;
};

export function calculateTotalPrice(size: TattooSize, style: TattooStyle, bodyPart: BodyPart): number {
  return calcPrice(size, style, bodyPart);
}

export function PriceCalculator({ size, style, bodyPart }: PriceCalculatorProps) {
  const price = calculateTotalPrice(size, style, bodyPart);
  return <span>{price.toLocaleString('ru-RU')} ₽</span>;
}
