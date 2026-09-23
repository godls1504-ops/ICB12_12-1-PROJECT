# -*- coding: utf-8 -*-
"""Olist 리뷰·평점 CX 개선 대시보드 (Streamlit) — 기획안 6탭 구성"""
import os, re, unicodedata
import numpy as np, pandas as pd, streamlit as st
import plotly.express as px, plotly.graph_objects as go
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

st.set_page_config(page_title="Olist CX 대시보드", page_icon="📊", layout="wide")
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data")

# 팔레트
GREEN="#146b50"; ORANGE="#d85f32"; RED="#b5423a"; BLUE="#3a5a91"; INK="#17211d"; MUTED="#6a746e"
RCOLORS=["#b5423a","#d1723a","#c9a24a","#7fa86a","#4a7c4e"]
st.markdown(f"""<style>
  .stApp {{ background:#faf9f5; }}
  h1,h2,h3 {{ letter-spacing:-.02em; }}
  [data-testid="stMetricValue"] {{ font-weight:800; }}
  .block-container {{ padding-top:1.4rem; }}
</style>""", unsafe_allow_html=True)

# ─────────────────────────── 데이터 로드 ───────────────────────────
@st.cache_data(show_spinner="데이터 로딩·집계 중…")
def load_base():
    orders=pd.read_csv(f"{RAW}/olist_orders_dataset.csv")
    items=pd.read_csv(f"{RAW}/olist_order_items_dataset.csv")
    rev=pd.read_csv(f"{RAW}/olist_order_reviews_dataset.csv")
    prod=pd.read_csv(f"{RAW}/olist_products_dataset.csv")
    tr=pd.read_csv(f"{RAW}/product_category_name_translation.csv")
    cust=pd.read_csv(f"{RAW}/olist_customers_dataset.csv")
    pay=pd.read_csv(f"{RAW}/olist_order_payments_dataset.csv")
    for c in ["order_purchase_timestamp","order_delivered_carrier_date","order_delivered_customer_date","order_estimated_delivery_date"]:
        orders[c]=pd.to_datetime(orders[c],errors="coerce")
    # 리뷰: 주문당 최신 1건 + 텍스트/불만유형
    rev["wrote_text"]=(rev["review_comment_message"].notna()|rev["review_comment_title"].notna()).astype(int)
    rev["txt"]=(rev["review_comment_title"].fillna("")+" "+rev["review_comment_message"].fillna("")).str.strip()
    rev=rev.sort_values("review_answer_timestamp").drop_duplicates("order_id",keep="last")
    # 품목 집계 + 카테고리 + 단독판매자
    spo=items.groupby("order_id")["seller_id"].nunique().rename("n_sellers")
    it=items.merge(prod[["product_id","product_category_name"]],on="product_id",how="left").merge(tr,on="product_category_name",how="left")
    og=it.groupby("order_id").agg(seller_id=("seller_id","first"),order_price=("price","sum"),
        order_freight=("freight_value","sum"),n_products=("product_id","nunique"),
        category=("product_category_name_english","first")).join(spo)
    pg=pay.groupby("order_id")["payment_installments"].max().rename("installments")
    # 병합
    o=orders.merge(rev[["order_id","review_score","wrote_text","txt"]],on="order_id",how="inner")
    o=o.merge(og,on="order_id",how="left").merge(cust[["customer_id","customer_state"]],on="customer_id",how="left").merge(pg,on="order_id",how="left")
    o["low"]=(o.review_score<=2).astype(int)
    o["late_days"]=(o.order_delivered_customer_date-o.order_estimated_delivery_date).dt.total_seconds()/86400
    o["on_time"]=(o.late_days<=0).astype(float)
    o["proc_days"]=(o.order_delivered_carrier_date-o.order_purchase_timestamp).dt.total_seconds()/86400
    o["transit_days"]=(o.order_delivered_customer_date-o.order_delivered_carrier_date).dt.total_seconds()/86400
    o["freight_ratio"]=o.order_freight/o.order_price.replace(0,np.nan)
    o["category"]=o.category.fillna("(미상)")
    o["month"]=o.order_purchase_timestamp.dt.to_period("M").astype(str)
    return o

# 불만/만족 유형 분류 (포르투갈어 규칙기반)
COMP={"미도착·미수령":["nao chegou","nao recebi","nao veio","nunca chegou","ainda nao receb","nao entregue","aguardando"],
"배송 지연":["atras","demor","fora do prazo","fora de prazo","muito tempo"],
"오배송·누락":["errad","falta","faltou","faltando","incomplet","apenas um","apenas uma","so recebi","difere"],
"품질·파손":["pessim","ruim","defeit","quebrad","danificad","estragad","mal acabad","inferior","nao funciona","fragil"],
"기대이하·불일치":["gato por lebre","propaganda","nao era","esperava","decepcion","enganos","nao corresponde"],
"환불·응대":["reembols","estorno","devoluc","devolver","cancel","sem resposta","nao responde","contato"]}
POS={"상품 만족·품질":["otim","excelent","maravilhos","adorei","amei","perfeit","bom produto","boa qualidade","gostei","lind","bonit","top"],
"빠른·정시 배송":["antes do prazo","antes do previsto","no prazo","rapid","chegou antes","super rapido","entrega rapida"],
"추천·재구매":["recomend","super recomendo"],"판매자 신뢰":["confiav","loja nota","responsav","atencios"]}
def _norm(s): return re.sub(r"\s+"," "," "+unicodedata.normalize("NFKD",str(s)).encode("ascii","ignore").decode().lower()+" ")

@st.cache_data(show_spinner="텍스트 유형 분류 중…")
def classify_types(order_ids, texts, scores):
    df=pd.DataFrame({"order_id":order_ids,"txt":texts,"score":scores})
    df=df[df.txt.str.strip()!=""].copy(); df["n"]=df.txt.map(_norm)
    for k,ws in {**COMP,**POS}.items():
        df[k]=df["n"].apply(lambda t:any(w in t for w in ws)).astype(int)
    return df

@st.cache_data(show_spinner="판매자 군집 계산 중…")
def seller_clusters(o):
    g=o.groupby("seller_id")
    S=pd.DataFrame({"avg_review":g.review_score.mean(),"low_rate":g.low.mean(),
        "on_time_deliv":g.on_time.mean(),"avg_late":g.late_days.mean(),
        "avg_freight":g.order_freight.mean(),"n_orders":g.order_id.nunique(),
        "gmv":g.order_price.sum(),"n_reviews":g.review_score.count()})
    A=S[S.n_orders>=5].dropna(subset=["avg_review"]).copy()
    CV=["avg_review","low_rate","on_time_deliv","avg_late","avg_freight"]
    X=A[CV].copy(); X["avg_freight"]=np.log1p(X["avg_freight"])
    A["cluster"]=KMeans(4,random_state=42,n_init=10).fit_predict(StandardScaler().fit_transform(X.fillna(X.median())))
    # 등급 라벨: 평균평점 순
    order=A.groupby("cluster").avg_review.mean().sort_values(ascending=False).index.tolist()
    lab={order[0]:"우수",order[1]:"우수·고거래",order[2]:"개선필요",order[3]:"위험"}
    A["등급"]=A.cluster.map(lab)
    return A

o=load_base()

# ─────────────────────────── 사이드바 필터 ───────────────────────────
st.sidebar.header("🔎 필터")
delivered_only=st.sidebar.checkbox("배송완료 주문만", value=True)
cats=sorted(o.category.unique().tolist())
sel_cat=st.sidebar.multiselect("카테고리", cats, default=[])
states=sorted(o.customer_state.dropna().unique().tolist())
sel_state=st.sidebar.multiselect("고객 주(state)", states, default=[])
sel_rating=st.sidebar.multiselect("평점(별점) 선택", [1,2,3,4,5], default=[1,2,3,4,5])
st.sidebar.caption("필터는 탭 1~4·6에 적용됩니다. (판매자 탭은 전체 기준)")

f=o.copy()
if delivered_only: f=f[f.order_status=="delivered"]
if sel_cat: f=f[f.category.isin(sel_cat)]
if sel_state: f=f[f.customer_state.isin(sel_state)]
if sel_rating: f=f[f.review_score.isin(sel_rating)]

st.title("Olist 리뷰·평점 기반 CX 개선 대시보드")
st.caption(f"필터 적용 주문 {len(f):,}건 · 전체 {len(o):,}건 · 데이터: Olist Brazilian E-Commerce (Kaggle)")

T1,T2,T3,T4,T5,T6=st.tabs(["① 평점 현황","② 리뷰 원인","③ 배송 영향","④ 작성 행동","⑤ 판매자 관리","⑥ 개선 우선순위"])

# ── TAB1 평점 현황 ──
with T1:
    c=st.columns(4)
    c[0].metric("주문 수", f"{len(f):,}")
    c[1].metric("평균 평점", f"{f.review_score.mean():.2f}")
    c[2].metric("저평점률(1~2점)", f"{f.low.mean()*100:.1f}%")
    c[3].metric("정시 배송률", f"{f.on_time.mean()*100:.1f}%")
    a,b=st.columns([1,1])
    with a:
        st.subheader("별점 점유율")
        vc=f.review_score.value_counts().reindex([1,2,3,4,5]).fillna(0)
        fig=px.bar(x=[f"{i}점" for i in vc.index], y=(vc/vc.sum()*100).round(1),
            color=[str(i) for i in vc.index], color_discrete_sequence=RCOLORS, text=(vc/vc.sum()*100).round(1))
        fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="%", height=360, margin=dict(t=10,b=10))
        st.plotly_chart(fig, width="stretch")
    with b:
        st.subheader("월별 저평점률 추이")
        m=f.groupby("month").low.mean().mul(100).reset_index()
        m=m[m.month>="2017-01"]
        fig=px.line(m, x="month", y="low", markers=True, color_discrete_sequence=[RED])
        fig.update_layout(xaxis_title="", yaxis_title="저평점률 %", height=360, margin=dict(t=10,b=10))
        st.plotly_chart(fig, width="stretch")

# ── TAB2 리뷰 원인 ──
with T2:
    st.subheader("저평점 리뷰 불만 유형 / 고평점 만족 유형")
    tdf=classify_types(f.order_id.tolist(), f.txt.tolist(), f.review_score.tolist())
    low_t=tdf[tdf.score<=2]; hi_t=tdf[tdf.score>=4]
    a,b=st.columns(2)
    with a:
        if len(low_t):
            comp=(low_t[list(COMP)].mean()*100).sort_values()
            fig=px.bar(x=comp.values, y=comp.index, orientation="h", text=comp.round(1),
                color_discrete_sequence=[RED]); fig.update_layout(xaxis_title="1~2점 텍스트 대비 %",yaxis_title="",height=360,margin=dict(t=10))
            st.plotly_chart(fig, width="stretch")
        else: st.info("해당 필터에 저평점 텍스트 리뷰가 없습니다.")
        st.caption(f"저평점 텍스트 리뷰 {len(low_t):,}건")
    with b:
        if len(hi_t):
            pos=(hi_t[list(POS)].mean()*100).sort_values()
            fig=px.bar(x=pos.values, y=pos.index, orientation="h", text=pos.round(1),
                color_discrete_sequence=[GREEN]); fig.update_layout(xaxis_title="4~5점 텍스트 대비 %",yaxis_title="",height=360,margin=dict(t=10))
            st.plotly_chart(fig, width="stretch")
        else: st.info("해당 필터에 고평점 텍스트 리뷰가 없습니다.")
        st.caption(f"고평점 텍스트 리뷰 {len(hi_t):,}건")
    # 평점대별 유형 분포 히트맵
    st.markdown("---")
    st.subheader("평점대별 유형 분포 (선택 평점 대상 · 텍스트 리뷰 기준 %)")
    present=sorted(int(s) for s in tdf.score.unique())
    if present:
        cc=st.columns(2)
        comp_hm=pd.DataFrame({f"{s}점":(tdf[tdf.score==s][list(COMP)].mean()*100) for s in present}).round(1)
        fig=px.imshow(comp_hm, text_auto=".1f", color_continuous_scale="OrRd", aspect="auto", labels=dict(color="%"))
        fig.update_layout(height=330, margin=dict(t=34,b=10), title="불만 유형 × 평점", coloraxis_showscale=False)
        cc[0].plotly_chart(fig, width="stretch")
        pos_hm=pd.DataFrame({f"{s}점":(tdf[tdf.score==s][list(POS)].mean()*100) for s in present}).round(1)
        fig=px.imshow(pos_hm, text_auto=".1f", color_continuous_scale="Greens", aspect="auto", labels=dict(color="%"))
        fig.update_layout(height=330, margin=dict(t=34,b=10), title="만족 유형 × 평점", coloraxis_showscale=False)
        cc[1].plotly_chart(fig, width="stretch")
    else:
        st.info("선택한 평점에 텍스트 리뷰가 없습니다.")
    # 워드클라우드 이미지(있으면)
    imgs=[("wc_negative_kr.png","저평점 불만 (한국어)"),("wc_positive.png","고평점 만족 (원어)")]
    cols=st.columns(2)
    for i,(fn,cap) in enumerate(imgs):
        p=os.path.join(HERE,fn)
        if os.path.exists(p): cols[i].image(p, caption=cap, width="stretch")

# ── TAB3 배송 영향 ──
with T3:
    d=f.dropna(subset=["late_days"])
    c=st.columns(3)
    c[0].metric("정시 배송 평균평점", f"{d[d.on_time==1].review_score.mean():.2f}")
    c[1].metric("지연 배송 평균평점", f"{d[d.on_time==0].review_score.mean():.2f}")
    c[2].metric("저평점 중 정시배송 비율", f"{d[d.low==1].on_time.mean()*100:.1f}%")
    a,b=st.columns(2)
    with a:
        st.subheader("배송 시간 분해 (정시 vs 지연)")
        dd=d[(d.proc_days>=0)&(d.transit_days>=0)]
        grp=dd.assign(g=np.where(dd.late_days>0,"지연","정시")).groupby("g")[["proc_days","transit_days"]].mean()
        fig=go.Figure()
        fig.add_bar(name="처리(판매자)", x=grp.index, y=grp.proc_days, marker_color="#9bb7d4")
        fig.add_bar(name="운송(물류)", x=grp.index, y=grp.transit_days, marker_color=BLUE)
        fig.update_layout(barmode="stack", height=360, yaxis_title="일", margin=dict(t=10))
        st.plotly_chart(fig, width="stretch")
    with b:
        st.subheader("지연 일수별 평균 평점")
        dd=d.copy(); dd["bin"]=pd.cut(dd.late_days,[-999,-1,0,3,7,14,999],labels=["일찍","정시","1~3일","4~7일","8~14일","15일+"])
        gb=dd.groupby("bin",observed=True).review_score.mean().reset_index()
        fig=px.bar(gb, x="bin", y="review_score", text=gb.review_score.round(2), color_discrete_sequence=[ORANGE])
        fig.update_layout(xaxis_title="지연 구간", yaxis_title="평균 평점", height=360, margin=dict(t=10))
        st.plotly_chart(fig, width="stretch")
    st.subheader("지역(주)별 저평점률 — 상위 15")
    rg=f.dropna(subset=["customer_state"]).groupby("customer_state").agg(주문=("order_id","size"),저평점률=("low","mean"),운송일=("transit_days","mean"))
    rg=rg[rg.주문>=100]; rg["저평점률"]=rg["저평점률"]*100
    rg=rg.sort_values("저평점률",ascending=False).head(15).reset_index()
    fig=px.bar(rg, x="customer_state", y="저평점률", color="운송일", color_continuous_scale="OrRd", text=rg.저평점률.round(1))
    fig.update_layout(height=340, xaxis_title="", margin=dict(t=10))
    st.plotly_chart(fig, width="stretch")

# ── TAB4 작성 행동 ──
with T4:
    st.subheader("텍스트 후기 작성률 — 무엇이 고객을 글 쓰게 하나")
    c=st.columns(2)
    with c[0]:
        wr=f.groupby("review_score").wrote_text.mean().mul(100).reindex([1,2,3,4,5])
        fig=px.bar(x=[f"{i}점" for i in wr.index], y=wr.values, text=wr.round(1).values, color=[str(i) for i in wr.index], color_discrete_sequence=RCOLORS)
        fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="작성률 %", height=380, margin=dict(t=55,l=10,r=30), title="별점별 작성률 (U자)")
        st.plotly_chart(fig, width="stretch")
    with c[1]:
        rows=[]
        d=f.dropna(subset=["late_days"])
        rows.append(("정시 배송", d[d.on_time==1].wrote_text.mean()*100))
        rows.append(("지연 배송", d[d.on_time==0].wrote_text.mean()*100))
        rows.append(("단일 품목", f[f.n_products==1].wrote_text.mean()*100))
        rows.append(("다품목", f[f.n_products>1].wrote_text.mean()*100))
        rd=pd.DataFrame(rows,columns=["요인","작성률"])
        fig=px.bar(rd, x="작성률", y="요인", orientation="h", text=rd.작성률.round(1), color_discrete_sequence=[BLUE])
        fig.update_layout(xaxis_title="작성률 %", yaxis_title="", height=380, margin=dict(t=55,l=10,r=30), title="요인별 작성률")
        st.plotly_chart(fig, width="stretch")
    st.info("작성 방아쇠는 '불만'(저평점 U자). 지연·다품목도 작성을 늘리나, 평점을 통제하면 지연 효과는 사라짐 → 텍스트는 극단 의견의 부분집합.")

# ── TAB5 판매자 관리 ──
with T5:
    A=seller_clusters(o)
    st.subheader("판매자 CX 군집 (전체 판매자 기준)")
    c=st.columns(4)
    dist=A.등급.value_counts()
    for i,g in enumerate(["우수","우수·고거래","개선필요","위험"]):
        c[i].metric(g, f"{int(dist.get(g,0)):,}명", f"{dist.get(g,0)/len(A)*100:.0f}%")
    a,b=st.columns([1.2,1])
    with a:
        fig=px.scatter(A, x="on_time_deliv", y="low_rate", size="n_reviews", color="등급",
            color_discrete_map={"우수":GREEN,"우수·고거래":BLUE,"개선필요":ORANGE,"위험":RED},
            hover_data=["avg_review","n_orders","gmv"], labels={"on_time_deliv":"정시배송률","low_rate":"저평점률"})
        fig.update_layout(height=420, margin=dict(t=10))
        st.plotly_chart(fig, width="stretch")
    with b:
        st.markdown("**판매자 조회**")
        sid=st.selectbox("seller_id 선택", A.sort_values("n_orders",ascending=False).index.tolist())
        r=A.loc[sid]
        st.metric("등급", r["등급"])
        st.write(f"- 평균 평점: **{r.avg_review:.2f}**")
        st.write(f"- 저평점률: **{r.low_rate*100:.1f}%**")
        st.write(f"- 정시 배송률: **{r.on_time_deliv*100:.1f}%**")
        st.write(f"- 주문 수 / 거래액: **{int(r.n_orders)}건 / R${r.gmv:,.0f}**")
    st.markdown("**위험·개선필요 판매자 목록 (다운로드)**")
    risk=A[A.등급.isin(["위험","개선필요"])].reset_index()[["seller_id","등급","avg_review","low_rate","on_time_deliv","n_orders","gmv"]]
    st.dataframe(risk.round(3), width="stretch", height=240)
    st.download_button("CSV 다운로드 (위험·개선필요 판매자)", risk.to_csv(index=False).encode("utf-8-sig"), "관리대상_판매자.csv", "text/csv")

# ── TAB6 개선 우선순위 ──
with T6:
    st.subheader("카테고리 우선순위 매트릭스 — 저평점률 × 규모")
    cg=f.groupby("category").agg(주문수=("order_id","size"),저평점률=("low","mean"),저평점건수=("low","sum"),평균평점=("review_score","mean"))
    cg=cg[cg.주문수>=300].copy(); cg["저평점률"]=cg["저평점률"]*100; cg=cg.reset_index()
    fig=px.scatter(cg, x="주문수", y="저평점률", size="저평점건수", color="저평점률",
        color_continuous_scale="OrRd", hover_name="category", size_max=45)
    fig.add_hline(y=cg.저평점률.median(), line_dash="dot", line_color=MUTED)
    fig.add_vline(x=cg.주문수.median(), line_dash="dot", line_color=MUTED)
    fig.update_layout(height=420, margin=dict(t=10))
    st.plotly_chart(fig, width="stretch")
    st.caption("오른쪽 위 = 규모도 크고 저평점률도 높은 최우선. 원 크기 = 저평점 절대 건수(임팩트).")
    st.markdown("**저평점 건수 TOP 15 (개선 임팩트 순)**")
    top=cg.sort_values("저평점건수",ascending=False).head(15)[["category","주문수","저평점건수","저평점률","평균평점"]]
    st.dataframe(top.round({"저평점률":1,"평균평점":2}), width="stretch", height=300)

st.caption("※ 상관 기반 우선순위이며 인과 아님. 텍스트 리뷰는 부분집합. 규칙기반 감성은 부정어 한계 존재.")
