import { useCallback, useRef } from 'react';
import { useSettings } from '../contexts/SettingsContext';

/**
 * Tiny synthesized UI sound effects via the Web Audio API.
 * No assets, no network — and fully muted when the user disables sound.
 */
export function useSound() {
  const { settings } = useSettings();
  const ctxRef = useRef(null);

  const ctx = useCallback(() => {
    if (!ctxRef.current) {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return null;
      ctxRef.current = new AC();
    }
    if (ctxRef.current.state === 'suspended') ctxRef.current.resume();
    return ctxRef.current;
  }, []);

  const tone = useCallback(
    (freq, duration = 0.08, type = 'sine', gain = 0.04) => {
      if (!settings.sound) return;
      const ac = ctx();
      if (!ac) return;
      const osc = ac.createOscillator();
      const g = ac.createGain();
      osc.type = type;
      osc.frequency.setValueAtTime(freq, ac.currentTime);
      g.gain.setValueAtTime(0, ac.currentTime);
      g.gain.linearRampToValueAtTime(gain, ac.currentTime + 0.01);
      g.gain.exponentialRampToValueAtTime(0.0001, ac.currentTime + duration);
      osc.connect(g).connect(ac.destination);
      osc.start();
      osc.stop(ac.currentTime + duration);
    },
    [ctx, settings.sound]
  );

  const play = useCallback(
    (name) => {
      switch (name) {
        case 'send':
          tone(620, 0.07, 'triangle', 0.05);
          setTimeout(() => tone(880, 0.06, 'triangle', 0.04), 55);
          break;
        case 'receive':
          tone(440, 0.07, 'sine', 0.045);
          setTimeout(() => tone(660, 0.09, 'sine', 0.04), 60);
          break;
        case 'error':
          tone(200, 0.16, 'sawtooth', 0.05);
          break;
        case 'key':
          tone(1200, 0.02, 'square', 0.012);
          break;
        case 'toggle':
          tone(520, 0.05, 'square', 0.03);
          break;
        case 'open':
          tone(360, 0.05, 'sine', 0.035);
          setTimeout(() => tone(540, 0.06, 'sine', 0.03), 45);
          break;
        default:
          tone(500, 0.05);
      }
    },
    [tone]
  );

  return play;
}
