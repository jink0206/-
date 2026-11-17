import { loadFont } from "@remotion/google-fonts/BlackHanSans";

// 남편의 리뷰생활 브랜드 컬러 (카드뉴스 템플릿과 동일)
export const NAVY = "#1B2A41";
export const YELLOW = "#FFC93C";
export const CREAM = "#FFF8E7";

export const HANDLE = "@nampyeon.review";
export const BRAND = "남편의 리뷰생활";

// 한글 디스플레이 폰트 (Black Han Sans). 렌더 전에 로딩이 끝날 때까지 자동으로 대기한다.
export const { fontFamily: FONT } = loadFont("normal", {
  ignoreTooManyRequestsWarning: true,
});
