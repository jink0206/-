import React from "react";
import { CREAM, FONT, NAVY, YELLOW } from "./theme";

export type StampProps = {
  readonly label: string; // 위쪽 작은 글씨 (예: 눈치 없는 판결)
  readonly main: string; // 큰 글씨 (예: 재방문 O)
  readonly tone: "yellow" | "navy";
};

// 투명 배경 PNG로 뽑아 영상 편집 앱에서 얹어 쓰는 "판결 도장"
export const Stamp: React.FC<StampProps> = ({ label, main, tone }) => {
  const bg = tone === "yellow" ? YELLOW : NAVY;
  const fg = tone === "yellow" ? NAVY : YELLOW;
  const border = tone === "yellow" ? NAVY : YELLOW;
  // 글자가 많은 문구("구매 추천 O")는 박스 안에 들어오도록 크기를 줄인다
  const mainSize = Array.from(main).length > 5 ? 132 : 176;

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: FONT,
      }}
    >
      <div
        style={{
          width: 800,
          height: 380,
          rotate: "-5deg",
          background: bg,
          border: `16px solid ${border}`,
          borderRadius: 56,
          boxShadow: "0 14px 0 rgba(0,0,0,0.28)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 6,
          color: fg,
        }}
      >
        <div style={{ fontSize: 76, letterSpacing: 2 }}>{label}</div>
        <div
          style={{ fontSize: mainSize, lineHeight: 1.1, whiteSpace: "nowrap" }}
        >
          {main}
        </div>
      </div>
    </div>
  );
};

export type ChipProps = {
  readonly text: string;
};

// 글자 수로 스티커 가로폭을 추정 (한글 70px, 공백 28px, 기본 여백 130px)
export const chipWidth = (text: string): number =>
  Array.from(text).reduce((w, c) => w + (c === " " ? 28 : 70), 0) + 130;

export const Chip: React.FC<ChipProps> = ({ text }) => {
  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: FONT,
      }}
    >
      <div
        style={{
          width: chipWidth(text) - 20,
          height: 130,
          background: CREAM,
          border: `10px solid ${NAVY}`,
          borderRadius: 65,
          boxShadow: "0 8px 0 rgba(0,0,0,0.28)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: NAVY,
          fontSize: 72,
          whiteSpace: "nowrap",
        }}
      >
        {text}
      </div>
    </div>
  );
};
