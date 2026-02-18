import type { BodyType, BodyView, Gender } from '../types';

type LeftControlsProps = {
  gender: Gender;
  body: BodyType;
  view: BodyView;
  onGenderChange: (value: Gender) => void;
  onBodyChange: (value: BodyType) => void;
  onViewChange: (value: BodyView) => void;
};

function ToggleButton({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button type="button" className={`seg-btn${active ? ' active' : ''}`} onClick={onClick}>
      {label}
    </button>
  );
}

export function LeftControls({
  gender,
  body,
  view,
  onGenderChange,
  onBodyChange,
  onViewChange,
}: LeftControlsProps) {
  return (
    <aside className="left-controls">
      <p className="control-label">Пол</p>
      <div className="seg-row two">
        <ToggleButton label="M" active={gender === 'm'} onClick={() => onGenderChange('m')} />
        <ToggleButton label="Ж" active={gender === 'f'} onClick={() => onGenderChange('f')} />
      </div>

      <p className="control-label">Сложение</p>
      <div className="seg-col">
        <ToggleButton
          label="Худое"
          active={body === 'slim'}
          onClick={() => onBodyChange('slim')}
        />
        <ToggleButton
          label="Стандарт"
          active={body === 'std'}
          onClick={() => onBodyChange('std')}
        />
        <ToggleButton
          label="Плотное"
          active={body === 'bulk'}
          onClick={() => onBodyChange('bulk')}
        />
      </div>

      <p className="control-label">Вид</p>
      <div className="seg-row two">
        <ToggleButton
          label="Front"
          active={view === 'front'}
          onClick={() => onViewChange('front')}
        />
        <ToggleButton label="Back" active={view === 'back'} onClick={() => onViewChange('back')} />
      </div>
    </aside>
  );
}
