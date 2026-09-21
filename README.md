# Olist 리뷰·평점 기반 CX 개선 대시보드

Olist Brazilian E-Commerce 데이터로 저평점의 원인과 개선 우선순위를 보여주는 Streamlit 대시보드입니다.

## 구성 (6탭)
① 평점 현황 · ② 리뷰 원인 · ③ 배송 영향 · ④ 작성 행동 · ⑤ 판매자 관리 · ⑥ 개선 우선순위

## 로컬 실행
```bash
pip install -r requirements.txt
streamlit run app.py
```

## 데이터
`data/` 폴더의 Olist 원본 CSV 7종을 사용합니다 (읽기 전용).
출처: Olist Brazilian E-Commerce Public Dataset (Kaggle)
