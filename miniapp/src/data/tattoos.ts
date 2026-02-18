import type { Tattoo, TattooStyle } from '../types';

export const TATTOOS: Tattoo[] = [
  { id: 'rose', name: 'Rose Bloom', style: 'linework', tags: ['flower', 'soft'] },
  { id: 'dragon', name: 'Dragon Arc', style: 'japan', tags: ['myth', 'bold'] },
  { id: 'snake', name: 'Snake Coil', style: 'blackwork', tags: ['dark', 'sharp'] },
  { id: 'lotus', name: 'Lotus Calm', style: 'minimal', tags: ['zen', 'clean'] },
  { id: 'wave', name: 'Wave Crest', style: 'linework', tags: ['sea', 'motion'] },
  { id: 'mask', name: 'Mask Echo', style: 'blackwork', tags: ['neo', 'contrast'] },
];

export const STYLE_FILTERS: Array<{ value: 'all' | TattooStyle; label: string }> = [
  { value: 'all', label: 'Все' },
  { value: 'linework', label: 'Linework' },
  { value: 'blackwork', label: 'Blackwork' },
  { value: 'minimal', label: 'Minimal' },
  { value: 'japan', label: 'Japan' },
];
