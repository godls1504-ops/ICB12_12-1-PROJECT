# -*- coding: utf-8 -*-
"""Olist CX Control Center 공통 로직 — 데이터 로드, 팀 분석 결과표(리뷰 유형·판매자 등급) 연결"""
import os
import numpy as np, pandas as pd, streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data")

# ─────────────────────────── 표시용 이름 ───────────────────────────
STATE_KR = {"AC":"아크리","AL":"알라고아스","AP":"아마파","AM":"아마조나스","BA":"바이아","CE":"세아라",
    "DF":"연방구","ES":"이스피리투산투","GO":"고이아스","MA":"마라냥","MT":"마투그로수","MS":"마투그로수두술",
    "MG":"미나스제라이스","PA":"파라","PB":"파라이바","PR":"파라나","PE":"페르남부쿠","PI":"피아우이",
    "RJ":"리우데자네이루","RN":"히우그란지두노르치","RS":"히우그란지두술","RO":"혼도니아","RR":"호라이마",
    "SC":"산타카타리나","SP":"상파울루","SE":"세르지피","TO":"토칸칭스"}
CAT_KR = {"bed_bath_table":"침구·욕실","health_beauty":"건강·뷰티","sports_leisure":"스포츠·레저",
    "computers_accessories":"컴퓨터 액세서리","furniture_decor":"가구·데코","housewares":"생활용품",
    "watches_gifts":"시계·선물","telephony":"통신","auto":"자동차용품","toys":"완구","cool_stuff":"잡화",
    "garden_tools":"정원용품","perfumery":"향수","baby":"유아용품","electronics":"전자제품","stationery":"문구",
    "fashion_bags_accessories":"패션 가방·액세서리","pet_shop":"반려동물","office_furniture":"사무가구",
    "consoles_games":"콘솔·게임","luggage_accessories":"여행가방","construction_tools_construction":"건축 공구",
    "home_appliances":"가전","musical_instruments":"악기","small_appliances":"소형가전",
    "home_construction":"건축 자재","books_general_interest":"일반 도서","food":"식품",
    "furniture_living_room":"거실 가구","home_confort":"홈 컴포트","drinks":"음료","audio":"오디오",
    "computers":"컴퓨터","market_place":"마켓플레이스","kitchen_dining_laundry_garden_furniture":"주방·정원 가구",
    "air_conditioning":"냉난방","home_appliances_2":"가전 2","industry_commerce_and_business":"산업·비즈니스",
    "fixed_telephony":"유선 전화","art":"미술","tablets_printing_image":"태블릿·인쇄","pc_gamer":"게이밍 PC",
    "portateis_cozinha_e_preparadores_de_alimentos":"휴대용 주방기기"}
def cat_label(c): return f"{CAT_KR[c]} ({c})" if c in CAT_KR else c
def cat_short(c): return CAT_KR.get(c, c)
def state_label(s): return f"{STATE_KR.get(s, s)} {s}"

# 팀 리뷰 분류 결과표의 불만 유형 (발표 슬라이드 9·11과 같은 분류)
COMP_TYPES=["미도착·미수령","오배송·누락·부족","품질·파손","배송 지연","기대 이하·불일치","환불·취소·응대불만"]
ACTION={"미도착·미수령":"수령 확인 알림·CS 이관","배송 지연":"운송 구간·파트너 점검",
        "오배송·누락·부족":"바코드 대조·다품목 체크","품질·파손":"출고 전 표본검수·포장",
        "기대 이하·불일치":"상품정보 기준 보완","환불·취소·응대불만":"응답 SLA·개선계획 요청"}
GRADE_ORDER=["위험","개선 필요","우수·고거래","우수","판단 보류"]
GRADE_LABEL={0:"우수",3:"우수·고거래",1:"개선 필요",2:"위험"}   # 판매자 군집 결과보고서의 군집 번호 → 등급

# ─────────────────────────── 데이터 로드 ───────────────────────────
@st.cache_data(show_spinner="데이터 로딩·집계 중…")
def load_base():
    orders=pd.read_csv(f"{RAW}/olist_orders_dataset.csv")
    items=pd.read_csv(f"{RAW}/olist_order_items_dataset.csv")
    rev=pd.read_csv(f"{RAW}/olist_order_reviews_dataset.csv")
    prod=pd.read_csv(f"{RAW}/olist_products_dataset.csv")
    tr=pd.read_csv(f"{RAW}/product_category_name_translation.csv")
    cust=pd.read_csv(f"{RAW}/olist_customers_dataset.csv")
    for c in ["order_purchase_timestamp","order_delivered_carrier_date","order_delivered_customer_date","order_estimated_delivery_date"]:
        orders[c]=pd.to_datetime(orders[c],errors="coerce")
    # 리뷰: 주문당 최신 1건 (중복 제거)
    rev["wrote_text"]=(rev["review_comment_message"].notna()|rev["review_comment_title"].notna()).astype(int)
    rev=rev.sort_values("review_answer_timestamp").drop_duplicates("order_id",keep="last")
    # 품목: 대표 카테고리·판매자 (번역표에 없는 2개 카테고리는 원본명 유지 → 73개 기준)
    it=items.merge(prod[["product_id","product_category_name"]],on="product_id",how="left").merge(tr,on="product_category_name",how="left")
    it["category"]=it.product_category_name_english.fillna(it.product_category_name)
    og=it.sort_values("order_item_id").groupby("order_id").agg(seller_id=("seller_id","first"),
        order_price=("price","sum"),category=("category","first"))
    # 주문 기준 표 (리뷰 없는 주문도 유지 → 커버리지 계산)
    o=orders.merge(rev[["order_id","review_score","wrote_text"]],on="order_id",how="left")
    o=o.merge(og,on="order_id",how="left").merge(cust[["customer_id","customer_state"]],on="customer_id",how="left")
    o["has_review"]=o.review_score.notna().astype(int)
    o["low"]=(o.review_score<=2).astype(float).where(o.has_review==1)
    o["late_days"]=(o.order_delivered_customer_date-o.order_estimated_delivery_date).dt.total_seconds()/86400
    o["on_time"]=(o.late_days<=0).astype(float).where(o.late_days.notna())
    o["proc_days"]=(o.order_delivered_carrier_date-o.order_purchase_timestamp).dt.total_seconds()/86400
    o["transit_days"]=(o.order_delivered_customer_date-o.order_delivered_carrier_date).dt.total_seconds()/86400
    o["category"]=o.category.fillna("(미상)")
    # 판매자 등급 (팀 군집 결과: 주문 5건 이상 1,794명, 나머지는 판단 보류)
    g=seller_grades()
    o=o.merge(g[["seller_id","grade"]],on="seller_id",how="left")
    o["grade"]=o.grade.fillna("판단 보류")
    return o

@st.cache_data
def seller_grades():
    """판매자 군집 결과보고서(K-means k=4, 7변수)의 결과표를 그대로 사용 → 발표 수치(990·328·425·51명)와 일치."""
    g=pd.read_csv(f"{RAW}/seller_clusters_k4.csv")
    g["grade"]=g.cluster.map(GRADE_LABEL)
    return g

@st.cache_data(show_spinner="리뷰 유형 결과 불러오는 중…")
def review_types():
    """팀 리뷰 텍스트 유형 분류 결과표. 한 리뷰에 여러 유형이 '|'로 붙어 있다."""
    t=pd.read_csv(f"{RAW}/review_types.csv")   # 리뷰 행 그대로 사용 → 발표 수치(1점 미도착 31.8% 등)와 일치
    lab=t["불만유형"].fillna("")
    for k in COMP_TYPES:
        t[k]=lab.str.contains(k,regex=False).astype(int)
    hi=set(pd.read_csv(f"{RAW}/mismatch_high_negative.csv").order_id)
    lo=set(pd.read_csv(f"{RAW}/mismatch_low_positive.csv").order_id)
    t["불일치: 고평점·부정"]=t.order_id.isin(hi).astype(int)
    t["불일치: 저평점·긍정"]=t.order_id.isin(lo).astype(int)
    return t
