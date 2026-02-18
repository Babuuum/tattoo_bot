import type { BodyPart, BodyView } from '../types';

export type ZoneAnchor = {
  x: number;
  y: number;
};

export type BodyZone = {
  id: string;
  bodyPart: BodyPart;
  points: string;
  anchor: ZoneAnchor;
};

export const zonesFront: BodyZone[] = [
  { id: 'arm_l_front', bodyPart: 'arm', points: '18,34 30,34 28,76 16,78', anchor: { x: 24, y: 50 } },
  { id: 'arm_r_front', bodyPart: 'arm', points: '70,34 82,34 84,78 72,76', anchor: { x: 76, y: 50 } },
  { id: 'leg_l_front', bodyPart: 'leg', points: '37,76 48,76 45,130 34,130', anchor: { x: 40, y: 102 } },
  { id: 'leg_r_front', bodyPart: 'leg', points: '52,76 63,76 66,130 55,130', anchor: { x: 60, y: 102 } },
  { id: 'chest_front', bodyPart: 'chest', points: '33,35 67,35 63,62 37,62', anchor: { x: 50, y: 48 } },
  { id: 'neck_front', bodyPart: 'neck', points: '44,22 56,22 55,34 45,34', anchor: { x: 50, y: 27 } },
  { id: 'other_front', bodyPart: 'other', points: '36,62 64,62 61,78 39,78', anchor: { x: 50, y: 70 } },
];

export const zonesBack: BodyZone[] = [
  { id: 'arm_l_back', bodyPart: 'arm', points: '18,34 30,34 28,76 16,78', anchor: { x: 24, y: 50 } },
  { id: 'arm_r_back', bodyPart: 'arm', points: '70,34 82,34 84,78 72,76', anchor: { x: 76, y: 50 } },
  { id: 'leg_l_back', bodyPart: 'leg', points: '37,76 48,76 45,130 34,130', anchor: { x: 40, y: 102 } },
  { id: 'leg_r_back', bodyPart: 'leg', points: '52,76 63,76 66,130 55,130', anchor: { x: 60, y: 102 } },
  { id: 'back_back', bodyPart: 'back', points: '33,35 67,35 63,70 37,70', anchor: { x: 50, y: 52 } },
  { id: 'neck_back', bodyPart: 'neck', points: '44,22 56,22 55,34 45,34', anchor: { x: 50, y: 27 } },
  { id: 'other_back', bodyPart: 'other', points: '36,70 64,70 61,82 39,82', anchor: { x: 50, y: 76 } },
];

export function zonesForView(view: BodyView): BodyZone[] {
  return view === 'front' ? zonesFront : zonesBack;
}

export function normalizeBodyPartOnView(bodyPart: BodyPart, view: BodyView): BodyPart {
  if (view === 'front' && bodyPart === 'back') {
    return 'chest';
  }
  if (view === 'back' && bodyPart === 'chest') {
    return 'back';
  }
  return bodyPart;
}

export function anchorForBodyPart(bodyPart: BodyPart, view: BodyView): ZoneAnchor {
  const zones = zonesForView(view);
  return zones.find((zone) => zone.bodyPart === bodyPart)?.anchor ?? { x: 50, y: 70 };
}
