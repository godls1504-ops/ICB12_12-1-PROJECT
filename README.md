# Olist 리뷰·평점 기반 CX 개선 대시보드

Olist Brazilian E-Commerce 데이터로 저평점의 원인과 개선 우선순위를 보여주는 Streamlit 대시보드입니다.

## 구성 (6탭)
① 평점 현황 · ② 리뷰 원인 · ③ 배송 영향 · ④ 작성 행동 · ⑤ 판매자 관리 · ⑥ 개선 우선순위

## 로컬 실행
```bash
pip install -r requirements.txt
streamlit run app.py
```

## CX Control Center (시안 구현판)
`Olist_CX_대시보드_시안.html` 구성을 실제 데이터로 옮긴 운영형 대시보드입니다.

```bash
streamlit run control_center.py
```

- 화면 4개: CX 현황 요약 · 배송·지역 분석 · 상품·판매자 관리 · 리뷰 VOC 탐색
- 공통 필터: 지역(고객 주) · 카테고리 · 판매자 등급
- 리뷰 유형·불일치 리뷰·판매자 등급은 팀 분석 결과표를 그대로 읽어 발표 수치와 맞춥니다
  - `data/review_types.csv` ← CSV/리뷰_텍스트_유형분류.csv
  - `data/mismatch_high_negative.csv`, `data/mismatch_low_positive.csv` ← CSV/불일치_*.csv
  - `data/seller_clusters_k4.csv` ← CSV/판매자_군집결과.csv (군집 0=우수, 3=우수·고거래, 1=개선 필요, 2=위험)
  - `data/review_ko.csv` — 리뷰 VOC 화면의 불만 유형·불일치 목록 리뷰 14,009문장의 한국어 기계 번역 (무료 로컬 모델 NLLB-200 600M, 제목·본문 분리 번역). 원문과 함께 표시되며 오역이 있을 수 있어 참고용입니다. '전체 텍스트 리뷰' 목록의 4~5점 칭찬 리뷰 대부분은 원문으로 나옵니다.
- 공통 로직은 `cx_core.py`에 있습니다. `.streamlit/config.toml`은 포인트 색(초록)과 툴바 숨김 설정입니다.

## 데이터
`data/` 폴더의 Olist 원본 CSV 7종을 사용합니다 (읽기 전용).
출처: Olist Brazilian E-Commerce Public Dataset (Kaggle)
