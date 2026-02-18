import { useEffect } from 'react';

type TgWebApp = {
  ready?: () => void;
  expand?: () => void;
};

type TgWindow = Window & {
  Telegram?: {
    WebApp?: TgWebApp;
  };
};

export function useTelegramWebApp(): void {
  useEffect(() => {
    const tg = (window as TgWindow).Telegram?.WebApp;
    if (!tg) {
      return;
    }
    tg.ready?.();
    tg.expand?.();
  }, []);
}
