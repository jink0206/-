import React from "react";
import { CREAM, FONT, NAVY, YELLOW } from "./theme";

// ── 게시물마다 문구가 달라지는 오버레이 (data 파일 하나로 PNG를 뽑는다) ──

export type HookProps = {
  readonly text: string; // 첫 3초에 띄울 훅 문구 (줄바꿈은 \n)
};

// 영상 맨 위에 얹는 훅 자막. 글자 수에 따라 크기를 줄여 1080px 안에 들어오게 한다.
export const HookCaption: React.FC<HookProps> = ({ text }) => {
  const lines = text.split("\n");
  const longest = Math.max(...lines.map((l) => Array.from(l).length));
  const fontSize = Math.max(64, Math.min(120, Math.floor(840 / Math.max(longest, 1) / 0.95)));

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
          background: YELLOW,
          border: `14px solid ${NAVY}`,
          borderRadius: 48,
          boxShadow: "0 12px 0 rgba(0,0,0,0.28)",
          padding: "34px 54px",
          color: NAVY,
          fontSize,
          lineHeight: 1.25,
          textAlign: "center",
          whiteSpace: "nowrap",
          maxWidth: 960,
        }}
      >
        {lines.map((l, i) => (
          <div key={i}>{l}</div>
        ))}
      </div>
    </div>
  );
};

export type PriceProps = {
  readonly name: string; // 메뉴명
  readonly price: string; // 가격 (예: 9,000원)
};

// 메뉴 컷 위에 얹는 "메뉴명 | 가격" 라벨
export const PriceTag: React.FC<PriceProps> = ({ name, price }) => {
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
          display: "flex",
          alignItems: "stretch",
          border: `10px solid ${NAVY}`,
          borderRadius: 60,
          overflow: "hidden",
          boxShadow: "0 8px 0 rgba(0,0,0,0.28)",
          fontSize: 72,
          whiteSpace: "nowrap",
        }}
      >
        <div style={{ background: CREAM, color: NAVY, padding: "16px 40px" }}>
          {name}
        </div>
        <div style={{ background: YELLOW, color: NAVY, padding: "16px 40px" }}>
          {price}
        </div>
      </div>
    </div>
  );
};
