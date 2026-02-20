import {AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate} from 'remotion';
import {COLORS} from '../constants';

export const Background = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const drift = interpolate(frame, [0, 10 * fps], [0, 60]);
  const glow = interpolate(frame, [0, 6 * fps, 12 * fps], [0.12, 0.3, 0.18], {
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill
      style={{
        backgroundImage: `radial-gradient(60% 60% at 20% 20%, ${COLORS.accent}${Math.round(glow * 255).toString(16).padStart(2, '0')} 0%, transparent 60%),
          radial-gradient(55% 55% at 80% 10%, ${COLORS.secondary}e6 0%, transparent 70%),
          linear-gradient(120deg, ${COLORS.bg} 0%, ${COLORS.primary} 45%, ${COLORS.secondary} 100%)`,
        backgroundPosition: `${drift}px ${-drift}px`,
        backgroundSize: 'cover',
      }}
    />
  );
};
