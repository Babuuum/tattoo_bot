import type { BodyPart, TattooSize, TattooStyle } from '../types';

export const BASE_PRICE = 5900;
export const MIN_PRICE = 4900;

export const SIZE_K: Record<TattooSize, number> = {
  s: 1,
  m: 1.25,
  l: 1.55,
};

export const STYLE_K: Record<TattooStyle, number> = {
  linework: 1,
  blackwork: 1.15,
  minimal: 0.95,
  japan: 1.2,
};

// TODO: tune coefficients / load from backend config
export const BODY_PART_K: Record<BodyPart, number> = {
  arm: 1,
  leg: 1,
  back: 1,
  chest: 1,
  neck: 1,
  other: 1,
};

export const SIZE_SCALE: Record<TattooSize, number> = {
  s: 0.92,
  m: 1.05,
  l: 1.18,
};

export function calcPrice(size: TattooSize, style: TattooStyle, bodyPart: BodyPart): number {
  const raw = BASE_PRICE * SIZE_K[size] * STYLE_K[style] * BODY_PART_K[bodyPart];
  return Math.max(MIN_PRICE, Math.round(raw));
}
