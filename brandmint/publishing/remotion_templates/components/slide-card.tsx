import {useCurrentFrame, useVideoConfig, interpolate, Img} from 'remotion';
import {COLORS, FONTS} from '../constants';

export const SlideCard = ({
  imageSrc,
  caption,
  index = 0,
}: {
  imageSrc?: string;
  caption: string;
  index?: number;
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const fadeIn = interpolate(frame, [0, 0.5 * fps], [0, 1], {
    extrapolateRight: 'clamp',
  });
  const fadeOut = interpolate(
    frame,
    [fps * 4, fps * 4.5],
    [1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );
  const opacity = Math.min(fadeIn, fadeOut);
  const scale = interpolate(frame, [0, 0.8 * fps], [1.05, 1], {
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        opacity,
        backgroundColor: COLORS.bg,
      }}
    >
      {imageSrc ? (
        <Img
          src={imageSrc}
          style={{
            maxWidth: '80%',
            maxHeight: '70%',
            objectFit: 'contain',
            borderRadius: 12,
            transform: `scale(${scale})`,
          }}
        />
      ) : (
        <div
          style={{
            width: '80%',
            height: '60%',
            background: `linear-gradient(135deg, ${COLORS.primary}, ${COLORS.secondary})`,
            borderRadius: 12,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transform: `scale(${scale})`,
          }}
        >
          <div
            style={{
              fontSize: 120,
              color: COLORS.accent,
              fontFamily: FONTS.header,
              fontWeight: 700,
            }}
          >
            {index + 1}
          </div>
        </div>
      )}
      <div
        style={{
          marginTop: 32,
          fontSize: 32,
          color: COLORS.text,
          fontFamily: FONTS.body,
          textAlign: 'center',
          maxWidth: '70%',
          lineHeight: 1.4,
        }}
      >
        {caption}
      </div>
    </div>
  );
};
