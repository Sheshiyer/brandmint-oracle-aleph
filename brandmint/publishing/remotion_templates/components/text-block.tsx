import {useCurrentFrame, useVideoConfig, interpolate, spring} from 'remotion';
import {COLORS, FONTS} from '../constants';

export const TextBlock = ({
  title,
  subtitle,
  align = 'left',
  maxWidth = 960,
}: {
  title: string;
  subtitle?: string;
  align?: 'left' | 'center' | 'right';
  maxWidth?: number;
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const reveal = spring({
    frame,
    fps,
    config: {damping: 200, stiffness: 120, mass: 0.8},
  });
  const opacity = interpolate(frame, [0, 0.7 * fps], [0, 1], {
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        maxWidth,
        textAlign: align,
        color: COLORS.text,
        opacity,
        transform: `translateY(${(1 - reveal) * 18}px)`,
        fontFamily: FONTS.header,
      }}
    >
      <div
        style={{
          fontSize: 72,
          lineHeight: 1.05,
          letterSpacing: '0.5px',
          fontWeight: 700,
        }}
      >
        {title}
      </div>
      {subtitle ? (
        <div
          style={{
            marginTop: 18,
            fontSize: 28,
            lineHeight: 1.4,
            color: COLORS.textMuted,
            fontFamily: FONTS.body,
          }}
        >
          {subtitle}
        </div>
      ) : null}
    </div>
  );
};
