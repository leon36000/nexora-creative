import { useId, useState } from 'react';
import type { KeyboardEvent, MouseEvent } from 'react';

type Position = readonly [number, number];
const FLECHES = new Map<string, Position>([
  ['ArrowLeft', [-1, 0]], ['ArrowRight', [1, 0]],
  ['ArrowUp', [0, -1]], ['ArrowDown', [0, 1]],
]);
const borner = (n: number) => Math.min(100, Math.max(0, n));

export interface MattePointageProps {
  disabled: boolean;
  onPoint: (x: number, y: number, negatif: boolean) => void;
  label: (xPourcent: number, yPourcent: number) => string;
  help: string;
}

/** Couche transparente ; les coordonnées du clavier restent entières en %. */
export function MattePointage({ disabled, onPoint, label, help }: Readonly<MattePointageProps>) {
  const [curseur, setCurseur] = useState<Position>([50, 50]);
  const [visible, setVisible] = useState(false);
  const aideId = useId();

  function poser(negatif: boolean) {
    if (!disabled) onPoint(curseur[0] / 100, curseur[1] / 100, negatif);
  }

  function pointer(e: MouseEvent<HTMLButtonElement>, negatif: boolean) {
    if (disabled) return;
    const r = e.currentTarget.getBoundingClientRect();
    if (!(r.width > 0 && r.height > 0)) return;
    const x = Math.min(1, Math.max(0, (e.clientX - r.left) / r.width));
    const y = Math.min(1, Math.max(0, (e.clientY - r.top) / r.height));
    setCurseur([Math.round(x * 100), Math.round(y * 100)]);
    setVisible(false);
    onPoint(x, y, negatif);
  }

  function clavier(e: KeyboardEvent<HTMLButtonElement>) {
    if (disabled || e.ctrlKey || e.metaKey) return;
    const delta = FLECHES.get(e.key);
    if (delta && !e.altKey) {
      e.preventDefault();
      e.stopPropagation();
      const pas = e.shiftKey ? 10 : 1;
      setCurseur(([x, y]) => [borner(x + delta[0] * pas), borner(y + delta[1] * pas)]);
      setVisible(true);
      return;
    }
    if (e.key !== 'Enter' && e.key !== ' ') return;
    e.preventDefault();
    e.stopPropagation();
    if (e.repeat) return;
    setVisible(true);
    poser(e.altKey || e.shiftKey);
  }

  function cliquer(e: MouseEvent<HTMLButtonElement>) {
    // Activation assistive sans coordonnées : utilise la cible du clavier.
    if (e.detail === 0 && e.clientX === 0 && e.clientY === 0) {
      setVisible(true);
      poser(e.altKey || e.shiftKey);
      return;
    }
    pointer(e, e.altKey || e.shiftKey);
  }

  return <>
    <button type="button" disabled={disabled} aria-label={label(...curseur)} aria-describedby={aideId}
      onFocus={() => setVisible(true)} onBlur={() => setVisible(false)}
      onKeyDown={clavier} onClick={cliquer}
      onContextMenu={(e) => { e.preventDefault(); pointer(e, true); }}
      style={{ position: 'absolute', inset: 0, padding: 0, border: 0, borderRadius: 0,
        background: 'transparent', boxShadow: 'none', cursor: 'crosshair', outlineOffset: 3 }}>
      {visible && <span aria-hidden="true" style={{ position: 'absolute',
        left: `${curseur[0]}%`, top: `${curseur[1]}%`, transform: 'translate(-50%, -50%)',
        width: 16, height: 16, border: '2px solid white', borderRadius: '50%',
        boxShadow: '0 0 0 1px black', pointerEvents: 'none' }} />}
    </button>
    <span id={aideId} hidden>{help}</span>
  </>;
}
