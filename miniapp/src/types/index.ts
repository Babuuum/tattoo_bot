export type Gender = 'm' | 'f';
export type BodyType = 'slim' | 'std' | 'bulk';
export type BodyView = 'front' | 'back';
export type TattooSize = 's' | 'm' | 'l';
export type TattooStyle = 'linework' | 'blackwork' | 'minimal' | 'japan';
export type BodyPart = 'arm' | 'leg' | 'back' | 'chest' | 'neck' | 'other';

export type Tattoo = {
  id: string;
  name: string;
  style: TattooStyle;
  tags: string[];
};
