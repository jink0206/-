import { Composition, Folder, Still } from "remotion";
import catalog from "./catalog.json";
import { EndCard } from "./EndCard";
import { HookCaption, PriceTag } from "./PostOverlays";
import { Chip, chipWidth, Stamp } from "./Sticker";

// 이 파일의 스티커·엔딩카드는 catalog.json 하나로 관리한다 (Studio에서 개별 편집이 필요 없는 묶음 템플릿).
export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Folder name="Stickers">
        {catalog.stamps.map((s) => (
          <Still
            key={s.id}
            id={s.id}
            component={Stamp}
            width={1000}
            height={560}
            defaultProps={{
              label: s.label,
              main: s.main,
              tone: s.tone as "yellow" | "navy",
            }}
          />
        ))}
        {catalog.chips.map((c) => (
          <Still
            key={c.id}
            id={c.id}
            component={Chip}
            width={chipWidth(c.text)}
            height={170}
            defaultProps={{ text: c.text }}
          />
        ))}
      </Folder>

      <Folder name="EndCards">
        {catalog.endcards.map((e) => (
          <Composition
            key={e.id}
            id={e.id}
            component={EndCard}
            durationInFrames={90}
            fps={30}
            width={1080}
            height={1920}
            defaultProps={{
              label: e.label,
              main: e.main,
              tone: e.tone as "yellow" | "navy",
            }}
          />
        ))}
      </Folder>

      <Folder name="PerPost">
        <Still
          id="hook-caption"
          component={HookCaption}
          width={1080}
          height={440}
          defaultProps={{ text: "[훅 문구]" }}
        />
        <Still
          id="price-tag"
          component={PriceTag}
          width={1080}
          height={220}
          defaultProps={{ name: "[메뉴명]", price: "[가격]원" }}
        />
      </Folder>
    </>
  );
};
