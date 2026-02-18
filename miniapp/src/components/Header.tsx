export function Header() {
  return (
    <header className="header">
      <div className="header-title">
        <span className="dot" aria-hidden>
          ●
        </span>
        <span>Примерка</span>
      </div>
      <div className="header-icons" aria-hidden>
        <button type="button" className="icon-btn">
          ?
        </button>
        <button type="button" className="icon-btn">
          ⚙
        </button>
      </div>
    </header>
  );
}
