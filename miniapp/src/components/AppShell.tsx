import type { PropsWithChildren } from 'react';

type AppShellProps = PropsWithChildren<{
  sheetOpen: boolean;
}>;

export function AppShell({ sheetOpen, children }: AppShellProps) {
  return <div className={`app-shell${sheetOpen ? ' sheet-open' : ''}`}>{children}</div>;
}
