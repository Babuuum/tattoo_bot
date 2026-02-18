import { useEffect, useMemo, useState } from 'react';

import { AppShell } from './components/AppShell';
import { BottomBar } from './components/BottomBar';
import { GallerySheet } from './components/GallerySheet';
import { Header } from './components/Header';
import { LeftControls } from './components/LeftControls';
import { RightPanel } from './components/RightPanel';
import { Stage } from './components/Stage';
import { normalizeBodyPartOnView } from './data/bodyZones';
import { TATTOOS } from './data/tattoos';
import { SIZE_SCALE } from './lib/pricing';
import { useTelegramWebApp } from './hooks/useTelegramWebApp';
import type { BodyPart, BodyType, BodyView, Gender, TattooSize, TattooStyle } from './types';

export default function App() {
  useTelegramWebApp();

  const [gender, setGender] = useState<Gender>('m');
  const [body, setBody] = useState<BodyType>('std');
  const [view, setView] = useState<BodyView>('front');
  const [size, setSize] = useState<TattooSize>('m');
  const [selectedBodyPart, setSelectedBodyPart] = useState<BodyPart>('other');
  const [selectedTattooId, setSelectedTattooId] = useState<string>(TATTOOS[0].id);
  const [galleryOpen, setGalleryOpen] = useState<boolean>(false);
  const [search, setSearch] = useState<string>('');
  const [styleFilter, setStyleFilter] = useState<'all' | TattooStyle>('all');

  useEffect(() => {
    document.body.classList.toggle('scroll-locked', galleryOpen);
    return () => document.body.classList.remove('scroll-locked');
  }, [galleryOpen]);

  useEffect(() => {
    setSelectedBodyPart((prev) => normalizeBodyPartOnView(prev, view));
  }, [view]);

  const selectedTattoo = useMemo(
    () => TATTOOS.find((item) => item.id === selectedTattooId) ?? TATTOOS[0],
    [selectedTattooId]
  );

  const filteredTattoos = useMemo(() => {
    const q = search.trim().toLowerCase();
    return TATTOOS.filter((item) => {
      const matchesStyle = styleFilter === 'all' || item.style === styleFilter;
      const haystack = `${item.name} ${item.style} ${item.tags.join(' ')}`.toLowerCase();
      const matchesSearch = q.length === 0 || haystack.includes(q);
      return matchesStyle && matchesSearch;
    });
  }, [search, styleFilter]);

  const modelSrc = `/assets/models/${gender}_${body}.png`;
  const tattooScale = SIZE_SCALE[size];

  return (
    <AppShell sheetOpen={galleryOpen}>
      <Header />

      <main className="main-layout">
        <Stage
          modelSrc={modelSrc}
          view={view}
          selectedBodyPart={selectedBodyPart}
          onSelectBodyPart={setSelectedBodyPart}
          tattoo={selectedTattoo}
          tattooScale={tattooScale}
          onOpenGallery={() => setGalleryOpen(true)}
        />

        <LeftControls
          gender={gender}
          body={body}
          view={view}
          onGenderChange={setGender}
          onBodyChange={setBody}
          onViewChange={setView}
        />

        <RightPanel
          tattoo={selectedTattoo}
          size={size}
          selectedBodyPart={selectedBodyPart}
          onSizeChange={setSize}
        />
      </main>

      <BottomBar size={size} style={selectedTattoo.style} bodyPart={selectedBodyPart} />

      <GallerySheet
        isOpen={galleryOpen}
        search={search}
        styleFilter={styleFilter}
        items={filteredTattoos}
        selectedTattooId={selectedTattoo.id}
        onClose={() => setGalleryOpen(false)}
        onSearchChange={setSearch}
        onStyleFilterChange={setStyleFilter}
        onSelectTattoo={(tattoo) => setSelectedTattooId(tattoo.id)}
      />
    </AppShell>
  );
}
