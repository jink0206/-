import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { BRAND, CREAM, FONT, HANDLE, NAVY, YELLOW } from "./theme";

export type EndCardProps = {
  readonly label: string; // 눈치 없는 판결
  readonly main: string; // 재방문 O
  readonly tone: "yellow" | "navy";
};

// 릴스 맨 끝에 붙이는 3초짜리 엔딩 카드 (판결 도장이 쾅 찍힘)
export const EndCard: React.FC<EndCardProps> = ({ label, main, tone }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const bg = tone === "yellow" ? YELLOW : NAVY;
  const fg = tone === "yellow" ? NAVY : YELLOW;
  // 글자가 많은 문구("구매 추천 O")는 박스 안에 들어오도록 크기를 줄인다
  const mainSize = Array.from(main).length > 5 ? 150 : 200;

  return (
    <AbsoluteFill
      style={{
        background: CREAM,
        fontFamily: FONT,
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {/* 인스타 UI에 가려지지 않도록 위아래 약 280px는 비워 둔다 */}
      <div
        style={{
          position: "absolute",
          top: 300,
          width: "100%",
          textAlign: "center",
          color: NAVY,
          fontSize: 64,
          opacity: interpolate(frame, [0, 0.4 * fps], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        {BRAND}
      </div>

      <div
        style={{
          width: 820,
          height: 460,
          background: bg,
          border: `18px solid ${NAVY}`,
          borderRadius: 64,
          boxShadow: "0 18px 0 rgba(0,0,0,0.25)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 8,
          color: fg,
          scale: interpolate(frame, [0.4 * fps, 0.9 * fps], [2.2, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.out(Easing.back(1.6)),
          }),
          rotate: interpolate(frame, [0.4 * fps, 0.9 * fps], ["-14deg", "-5deg"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.out(Easing.cubic),
          }),
          opacity: interpolate(frame, [0.4 * fps, 0.55 * fps], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        <div style={{ fontSize: 84, letterSpacing: 2 }}>{label}</div>
        <div
          style={{ fontSize: mainSize, lineHeight: 1.1, whiteSpace: "nowrap" }}
        >
          {main}
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          bottom: 330,
          width: "100%",
          textAlign: "center",
          color: NAVY,
          opacity: interpolate(frame, [1.1 * fps, 1.6 * fps], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        <div style={{ fontSize: 66 }}>자세한 후기는</div>
        <div style={{ fontSize: 66 }}>프로필 링크 블로그에서</div>
        <div style={{ fontSize: 54, marginTop: 28 }}>{HANDLE}</div>
      </div>
    </AbsoluteFill>
  );
};
