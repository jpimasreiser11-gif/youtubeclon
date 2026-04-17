import React from 'react';
import {Composition, registerRoot, AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';

const Intro = ({title, color}: {title: string; color: string}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 20], [0, 1], {extrapolateRight: 'clamp'});
  const scale = interpolate(frame, [0, 60], [0.9, 1], {extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{backgroundColor: '#0A0A0A', justifyContent: 'center', alignItems: 'center'}}>
      <div
        style={{
          color,
          fontSize: 88,
          letterSpacing: 3,
          fontFamily: 'Inter, sans-serif',
          fontWeight: 800,
          opacity,
          transform: `scale(${scale})`,
          textShadow: `0 0 24px ${color}66`,
        }}
      >
        {title}
      </div>
    </AbsoluteFill>
  );
};

const RemotionRoot = () => (
  <>
    <Composition
      id="ImpactoMundialIntro"
      component={() => <Intro title="IMPACTO MUNDIAL" color="#C8A829" />}
      durationInFrames={75}
      fps={30}
      width={1920}
      height={1080}
    />
    <Composition
      id="MentesRotasIntro"
      component={() => <Intro title="MENTES ROTAS" color="#DC143C" />}
      durationInFrames={75}
      fps={30}
      width={1920}
      height={1080}
    />
    <Composition
      id="LocoIAIntro"
      component={() => <Intro title="EL LOCO DE LA IA" color="#00E5FF" />}
      durationInFrames={75}
      fps={30}
      width={1920}
      height={1080}
    />
    <Composition
      id="MindWarpIntro"
      component={() => <Intro title="MIND WARP" color="#7B1FA2" />}
      durationInFrames={75}
      fps={30}
      width={1920}
      height={1080}
    />
    <Composition
      id="WealthFilesIntro"
      component={() => <Intro title="WEALTH FILES" color="#FFD700" />}
      durationInFrames={75}
      fps={30}
      width={1920}
      height={1080}
    />
    <Composition
      id="DarkScienceIntro"
      component={() => <Intro title="DARK SCIENCE" color="#1565C0" />}
      durationInFrames={75}
      fps={30}
      width={1920}
      height={1080}
    />
  </>
);

registerRoot(RemotionRoot);

