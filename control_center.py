# -*- coding: utf-8 -*-
"""Olist CX Control Center — 'Olist_CX_대시보드_시안' 구성을 실제 데이터로 구현한 Streamlit 대시보드
실행: streamlit run control_center.py"""
import html
import numpy as np, pandas as pd, streamlit as st
import plotly.express as px, plotly.graph_objects as go
import cx_core as C

st.set_page_config(page_title="Olist CX Control Center", page_icon="📊", layout="wide")

# ─────────────────────────── 디자인 (시안 팔레트) ───────────────────────────
INK="#17211d"; MUTED="#66736d"; LINE="#dce4df"
GREEN="#146b50"; GREEN_DARK="#0e4938"; GREEN_SOFT="#e0f0e9"
ORANGE="#d95f32"; ORANGE_SOFT="#fae8dc"; RED="#bd443b"; RED_SOFT="#f7e3e1"
BLUE="#3e6099"; BLUE_SOFT="#e5ebf4"; YELLOW="#c79a27"
RCOLORS=["#bd443b","#dd7635","#c79a27","#82a773","#4f875f"]
GRADE_COLOR={"위험":RED,"개선 필요":ORANGE,"우수·고거래":BLUE,"우수":GREEN,"판단 보류":MUTED}
GRADE_SOFT={"위험":RED_SOFT,"개선 필요":ORANGE_SOFT,"우수·고거래":BLUE_SOFT,"우수":GREEN_SOFT,"판단 보류":"#eef2f0"}
FONT="Pretendard Variable, Pretendard, Malgun Gothic, sans-serif"

st.markdown(f"""<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.css');
html, body, .stApp, [class*="css"], button, input, select, textarea {{ font-family:{FONT}; }}
.stApp {{ background:#f5f7f4; color:{INK}; }}
.block-container {{ padding-top:3.2rem; padding-bottom:2.5rem; max-width:1400px; }}
[data-testid="stSidebar"] {{ background:#12221c; }}
[data-testid="stSidebar"] * {{ color:#d8e2dd; }}
[data-testid="stSidebar"] [role="radiogroup"], [data-testid="stSidebar"] [data-testid="stRadio"] > div {{ width:100%; }}
[data-testid="stSidebar"] [role="radiogroup"] label {{ padding:12px 14px; border-radius:10px; margin:0 0 5px; width:100%; display:flex; }}
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child {{ display:none; }}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {{ background:#1c342b; }}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{ background:{GREEN}; }}
[data-testid="stSidebar"] [role="radiogroup"] label p {{ font-weight:700; font-size:15px; }}
.brand small {{ display:block; color:#7fc7aa !important; font-weight:700; letter-spacing:.08em; margin-bottom:6px; font-size:12px; }}
.brand strong {{ font-size:23px; line-height:1.2; color:#fff !important; }}
.brand p {{ color:#aabbb3 !important; font-size:13px; line-height:1.5; margin:10px 0 18px; }}
.side-note {{ border-top:1px solid #31463e; padding-top:14px; color:#91a39a !important; font-size:12px; line-height:1.6; }}
.head h1 {{ font-size:30px; margin:0 0 4px; letter-spacing:-.03em; color:{INK}; }}
.head p {{ margin:0 0 6px; color:{MUTED}; }}
.badge {{ display:inline-block; color:{ORANGE}; background:{ORANGE_SOFT}; font-weight:800; padding:6px 10px; border-radius:8px; font-size:12px; }}
.kpis {{ display:grid; grid-template-columns:repeat(6,minmax(0,1fr)); gap:10px; margin:4px 0 16px; }}
.kpi {{ background:#fff; border-top:3px solid {GREEN}; padding:15px 15px 13px; min-height:112px; }}
.kpi.alert {{ border-top-color:{RED}; }} .kpi.orange {{ border-top-color:{ORANGE}; }} .kpi.blue {{ border-top-color:{BLUE}; }}
.kpi .label {{ display:block; color:{MUTED}; font-size:12px; font-weight:700; margin-bottom:10px; }}
.kpi b {{ display:block; font-size:27px; letter-spacing:-.03em; color:{INK}; font-variant-numeric:tabular-nums; }}
.kpi small {{ display:block; color:{MUTED}; margin-top:6px; font-size:11px; }}
.stMarkdown p.desc, p.desc {{ color:{MUTED}; font-size:12.5px !important; margin:-4px 0 10px; line-height:1.5; }}
[data-testid="stHeading"] h3, .stMarkdown h3 {{ font-size:19px !important; font-weight:800; padding:0 0 6px; letter-spacing:-.02em; }}
.sec h2 {{ font-size:23px; font-weight:800; margin:6px 0 2px; letter-spacing:-.02em; color:{INK}; padding:0; }}
.sec p {{ margin:0 0 12px; color:{MUTED}; font-size:12.5px; }}
.insight {{ margin-top:6px; padding:13px 15px; background:{GREEN_SOFT}; color:{GREEN_DARK}; line-height:1.55; font-weight:650; font-size:14px; }}
.minis {{ display:grid; grid-template-columns:repeat(2,1fr); gap:10px; }}
.mini {{ padding:15px; background:#f2f5f3; }} .mini span {{ font-size:12px; color:{MUTED}; }} .mini b {{ font-size:23px; display:block; margin-top:6px; }}
.review {{ padding:14px 0; border-bottom:1px solid {LINE}; }}
.review-head {{ display:flex; gap:7px; align-items:center; flex-wrap:wrap; margin-bottom:7px; font-size:13px; }}
.score {{ font-weight:900; }} .tag {{ font-size:10.5px; padding:3px 7px; font-weight:800; border-radius:4px; }}
.review p {{ margin:0; line-height:1.55; font-size:14px; }} .review p.orig {{ margin-top:4px; color:{MUTED}; font-size:12.5px; line-height:1.45; }} .review small {{ display:block; color:{MUTED}; margin-top:5px; font-size:11.5px; }}
.gradecards {{ display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-bottom:14px; }}
.gc {{ background:#fff; padding:14px 15px; }} .gc .t {{ font-weight:800; font-size:13px; }} .gc b {{ display:block; font-size:24px; margin-top:4px; }} .gc small {{ color:{MUTED}; font-size:11.5px; }}
button[kind="primary"] {{ background:{GREEN}; border-color:{GREEN}; }}
button[kind="primary"]:hover {{ background:{GREEN_DARK}; border-color:{GREEN_DARK}; }}
@media (max-width:1100px) {{ .kpis {{ grid-template-columns:repeat(3,1fr); }} .gradecards {{ grid-template-columns:repeat(2,1fr); }} }}
@media (max-width:640px) {{ .kpis {{ grid-template-columns:repeat(2,1fr); }} .minis {{ grid-template-columns:1fr; }} }}
</style>""", unsafe_allow_html=True)

def style_fig(fig, h=330):
    fig.update_layout(height=h, margin=dict(t=10,b=10,l=10,r=10), font=dict(family=FONT, color=INK, size=13),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
    fig.update_xaxes(gridcolor="#e8eeea", zeroline=False); fig.update_yaxes(gridcolor="#e8eeea", zeroline=False)
    return fig

def pct(x, d=1): return "–" if pd.isna(x) else f"{x*100:.{d}f}%"

# ─────────────────────────── 데이터 ───────────────────────────
o=C.load_base()
types=C.review_types()
grades=C.seller_grades()

# ─────────────────────────── 사이드바 (시안 메뉴) ───────────────────────────
PAGES=["CX 현황 요약","배송·지역 분석","상품·판매자 관리","리뷰 VOC 탐색"]
with st.sidebar:
    st.markdown("""<div class="brand"><small>OLIST CX PROJECT</small><strong>Olist CX<br>Control Center</strong>
      <p>리뷰·배송·상품·판매자 데이터를 연결한 고객경험 위험 모니터링</p></div>""", unsafe_allow_html=True)
    page=st.radio("메뉴", PAGES, label_visibility="collapsed", key="page")
    st.markdown(f"""<div class="side-note">데이터: Olist Brazilian E-Commerce (Kaggle)<br>주문 {len(o):,}건 · 2016-09 ~ 2018-10<br>
      리뷰 유형·판매자 등급은 팀 분석 결과표 기준</div>""", unsafe_allow_html=True)

# ─────────────────────────── 헤더 + 공통 필터 ───────────────────────────
st.markdown("""<div class="head"><h1>고객경험 위험 모니터링</h1>
  <p>문제 구간을 찾고, 개선 대상 판매자와 주문을 바로 내려받습니다.</p></div>""", unsafe_allow_html=True)

state_order=o.customer_state.value_counts().index.tolist()
cat_order=o.loc[o.category!="(미상)","category"].value_counts().index.tolist()
with st.container(border=True):
    c1,c2,c3,c4=st.columns([1,1.3,1,1.2])
    sel_state=c1.selectbox("지역 (고객 주)", ["all"]+state_order, format_func=lambda s:"전체 지역" if s=="all" else C.state_label(s), key="f_state")
    sel_cat=c2.selectbox("카테고리", ["all"]+cat_order, format_func=lambda c:"전체 카테고리" if c=="all" else C.cat_label(c), key="f_cat")
    sel_grade=c3.selectbox("판매자 등급", ["all"]+C.GRADE_ORDER, format_func=lambda g:"전체 등급" if g=="all" else g, key="f_grade")

f=o
if sel_state!="all": f=f[f.customer_state==sel_state]
if sel_cat!="all": f=f[f.category==sel_cat]
if sel_grade!="all": f=f[f.grade==sel_grade]
c4.markdown(f"<div style='padding-top:30px;color:{MUTED};font-size:12.5px'>필터 적용 주문 <b style='color:{INK}'>{len(f):,}</b>건 / 전체 {len(o):,}건</div>", unsafe_allow_html=True)

if len(f)==0:
    st.warning("선택한 조건에 맞는 주문이 없습니다. 필터를 바꿔 주세요."); st.stop()

r=f[f.has_review==1]                                   # 리뷰가 있는 주문
ft=types[types.order_id.isin(f.order_id)].merge(f[["order_id","customer_state","category","seller_id","grade","order_purchase_timestamp"]],on="order_id",how="left")

# ═══════════════════════════ ① CX 현황 요약 ═══════════════════════════
if page=="CX 현황 요약":
    one=ft[ft.review_score==1]
    nd=one["미도착·미수령"].mean() if len(one) else np.nan
    st.markdown(f"""<div class="kpis">
      <article class="kpi"><span class="label">주문 수</span><b>{len(f):,}</b><small>필터 적용 기준</small></article>
      <article class="kpi blue"><span class="label">리뷰 커버리지</span><b>{pct(f.has_review.mean())}</b><small>주문 대비 별점 보유</small></article>
      <article class="kpi"><span class="label">평균 별점</span><b>{r.review_score.mean():.2f}</b><small>5점 만점</small></article>
      <article class="kpi alert"><span class="label">저평점률</span><b>{pct(r.low.mean())}</b><small>1~2점 비율</small></article>
      <article class="kpi orange"><span class="label">텍스트 리뷰</span><b>{pct(r.wrote_text.mean())}</b><small>제목 또는 본문 작성</small></article>
      <article class="kpi alert"><span class="label">1점 리뷰 중 미도착</span><b>{pct(nd)}</b><small>1점 텍스트 {len(one):,}건 기준</small></article>
    </div>""", unsafe_allow_html=True)

    a,b=st.columns([1.25,1])
    with a, st.container(border=True):
        st.subheader("별점 분포")
        st.markdown("<p class='desc'>전체 별점은 5점에 몰리지만, 1점이 2·3점을 합친 것보다 많은 J자형입니다.</p>", unsafe_allow_html=True)
        vc=r.review_score.value_counts().reindex([1,2,3,4,5]).fillna(0); sh=vc/vc.sum()*100
        fig=go.Figure(go.Bar(x=[f"{i}점" for i in vc.index], y=sh, marker_color=RCOLORS,
            text=[f"{v:.1f}%" for v in sh], textposition="outside", cliponaxis=False,
            hovertemplate="%{x}: %{y:.1f}% (%{customdata:,}건)<extra></extra>", customdata=vc.astype(int)))
        fig.update_yaxes(title="점유율 %", range=[0, max(sh)*1.18 if sh.max()>0 else 1])
        st.plotly_chart(style_fig(fig,330), width="stretch", config={"displayModeBar":False})
    with b, st.container(border=True):
        st.subheader("저평점 불만 원인")
        basis=st.radio("기준", ["1점 리뷰","1~2점 리뷰"], horizontal=True, label_visibility="collapsed")
        low=ft[ft.review_score==1] if basis=="1점 리뷰" else ft[ft.review_score<=2]
        st.markdown(f"<p class='desc'>{basis} 텍스트 {len(low):,}건 기준 · 한 리뷰에 여러 원인이 들어갈 수 있습니다.</p>", unsafe_allow_html=True)
        if len(low)>=5:
            sh=(low[C.COMP_TYPES].mean()*100).sort_values()
            col=[RED if k in ("미도착·미수령","오배송·누락·부족","배송 지연") else (BLUE if k.startswith("환불") else ORANGE) for k in sh.index]
            fig=go.Figure(go.Bar(x=sh.values, y=sh.index, orientation="h", marker_color=col,
                text=[f"{v:.1f}%" for v in sh.values], textposition="outside", cliponaxis=False,
                hovertemplate="%{y}: %{x:.1f}%<extra></extra>"))
            fig.update_xaxes(range=[0, sh.max()*1.22], title=None)
            st.plotly_chart(style_fig(fig,250), width="stretch", config={"displayModeBar":False})
            st.markdown(f"<p class='desc'>빨강 = 배송 계열 · 주황 = 상품 계열 · 파랑 = 응대·환불</p>", unsafe_allow_html=True)
            top=sh.idxmax()
            st.markdown(f"<div class='insight'>{basis}의 최대 불만은 <b>{top} {sh.max():.1f}%</b>입니다. "
                        f"단순 지연보다 미도착·미수령과 오배송·누락을 먼저 관리해야 합니다.</div>", unsafe_allow_html=True)
        else:
            st.info("이 조건에는 저평점 텍스트 리뷰가 5건 미만이라 원인 비율을 계산하지 않습니다.")

# ═══════════════════════════ ② 배송·지역 분석 ═══════════════════════════
elif page=="배송·지역 분석":
    st.markdown("<div class='sec'><h2>배송·지역 위험 분석</h2><p>배송완료 주문 기준입니다. 저평점률과 운송일을 함께 보고 개선 우선 지역을 찾습니다.</p></div>", unsafe_allow_html=True)
    # 지역 차트는 지역 필터를 빼고 계산해 다른 지역과 비교할 수 있게 한다 (선택 지역은 강조)
    g=o[(o.order_status=="delivered")&(o.has_review==1)]
    if sel_cat!="all": g=g[g.category==sel_cat]
    if sel_grade!="all": g=g[g.grade==sel_grade]
    d=f[(f.order_status=="delivered")&(f.has_review==1)]
    a,b=st.columns([1.25,1])
    with a, st.container(border=True):
        st.subheader("지역별 저평점률")
        rg=g.groupby("customer_state").agg(주문=("order_id","size"),저평점률=("low","mean"),운송일=("transit_days","mean"))
        min_n=300 if sel_cat=="all" and sel_grade=="all" else 50
        rg=rg[rg.주문>=min_n].copy()
        if len(rg):
            avg=g.low.mean()
            show=rg.sort_values("저평점률",ascending=False).head(10)
            for must in [s for s in ("SP",sel_state) if s!="all" and s in rg.index and s not in show.index]:
                show=pd.concat([show, rg.loc[[must]]])
            show=show.sort_values("저평점률")
            col=[(RED if v>=avg*1.3 else ORANGE if v>avg else GREEN) for v in show.저평점률]
            fig=go.Figure(go.Bar(y=[C.state_label(s) for s in show.index], x=show.저평점률*100, orientation="h",
                marker=dict(color=col, line=dict(color=[INK if s==sel_state else "rgba(0,0,0,0)" for s in show.index], width=2.5)),
                text=[f"{v*100:.1f}% · {n:,}건" for v,n in zip(show.저평점률, show.주문)], textposition="outside", cliponaxis=False,
                customdata=show.운송일, hovertemplate="%{y}<br>저평점률 %{x:.1f}%<br>평균 운송 %{customdata:.1f}일<extra></extra>"))
            fig.add_vline(x=avg*100, line_dash="dot", line_color=MUTED)
            fig.update_xaxes(range=[0, show.저평점률.max()*100*1.35], title="저평점률 %")
            st.plotly_chart(style_fig(fig,380), width="stretch", config={"displayModeBar":False})
            st.markdown(f"<p class='desc'>저평점률 상위 10개 주 + 기준 SP (주문 {min_n}건 이상). 점선 = 전체 평균 {avg*100:.1f}% · 빨강 = 평균의 1.3배 이상 · 테두리 = 선택 지역.</p>", unsafe_allow_html=True)
        else:
            st.info("비교할 만큼 주문이 있는 지역이 없습니다.")
    with b, st.container(border=True):
        st.subheader("배송 단계 진단")
        dd=d[(d.proc_days>=0)&(d.transit_days>=0)]
        late=dd.late_days>0
        if late.sum()>=10 and (~late).sum()>=10:
            t_on, t_late = dd.loc[~late,"transit_days"].mean(), dd.loc[late,"transit_days"].mean()
            p_on, p_late = dd.loc[~late,"proc_days"].mean(), dd.loc[late,"proc_days"].mean()
            corr=dd[["transit_days","review_score"]].corr().iloc[0,1]
            st.markdown(f"""<p class='desc'>지연 주문은 판매자 처리보다 운송 단계에서 시간이 더 크게 늘었습니다.</p>
            <div class="minis"><div class="mini"><span>정시 주문 운송</span><b>{t_on:.0f}일</b></div>
            <div class="mini"><span>지연 주문 운송</span><b>{t_late:.0f}일</b></div>
            <div class="mini"><span>운송 증가폭 (처리 증가폭)</span><b style="color:{RED}">+{t_late-t_on:.0f}일 <small style="font-size:13px;color:{MUTED}">(+{p_late-p_on:.0f}일)</small></b></div>
            <div class="mini"><span>운송일–별점 상관</span><b style="color:{BLUE}">{corr:+.3f}</b></div></div>""", unsafe_allow_html=True)
            fig=go.Figure()
            fig.add_bar(name="처리(판매자)", x=["정시","지연"], y=[p_on,p_late], marker_color="#9bb7d4", hovertemplate="처리 %{y:.1f}일<extra></extra>")
            fig.add_bar(name="운송(물류)", x=["정시","지연"], y=[t_on,t_late], marker_color=BLUE, text=[f"{t_on:.0f}일",f"{t_late:.0f}일"], textposition="inside", hovertemplate="운송 %{y:.1f}일<extra></extra>")
            fig.update_layout(barmode="stack"); fig.update_yaxes(title="일")
            fig=style_fig(fig,200); fig.update_layout(showlegend=True, legend=dict(orientation="h", y=1.15, x=0))
            st.plotly_chart(fig, width="stretch", config={"displayModeBar":False})
            st.markdown("<div class='insight'>상관관계이며 인과는 아닙니다. 개선 효과는 지역 파일럿 전후 비교로 확인합니다.</div>", unsafe_allow_html=True)
        else:
            st.info("정시·지연 주문이 각각 10건 이상일 때 진단합니다.")
    with st.container(border=True):
        st.subheader("지연 일수별 평균 별점")
        st.markdown("<p class='desc'>예정일보다 3일 넘게 늦으면 별점이 급락합니다.</p>", unsafe_allow_html=True)
        x=d.dropna(subset=["late_days"]).copy()
        x["bin"]=pd.cut(x.late_days,[-999,-10,-3,0,3,7,15,999],labels=["10일+ 조기","3~10일 조기","0~3일 조기","0~3일 지연","3~7일 지연","7~15일 지연","15일+ 지연"])
        gb=x.groupby("bin",observed=False).agg(별점=("review_score","mean"),건수=("order_id","size")).reset_index()
        gb=gb[gb.건수>=20]
        if len(gb):
            fig=go.Figure(go.Bar(x=gb.bin.astype(str), y=gb.별점, marker_color=[GREEN if "조기" in s else (ORANGE if s.startswith("0~3") else RED) for s in gb.bin.astype(str)],
                text=[f"{v:.2f}" for v in gb.별점], textposition="outside", cliponaxis=False, customdata=gb.건수,
                hovertemplate="%{x}: 평균 %{y:.2f}점 (%{customdata:,}건)<extra></extra>"))
            fig.update_yaxes(range=[0,5.4], title="평균 별점")
            st.plotly_chart(style_fig(fig,260), width="stretch", config={"displayModeBar":False})

# ═══════════════════════════ ③ 상품·판매자 관리 ═══════════════════════════
elif page=="상품·판매자 관리":
    st.markdown("<div class='sec'><h2>상품·판매자 관리</h2><p>저평점률과 거래 규모를 함께 보고 실제 관리 대상을 고릅니다. 우선순위 = 저평점 건수(심각도 × 규모).</p></div>", unsafe_allow_html=True)
    # 등급별 판매자 수 (필터 내 주문이 있는 판매자 기준)
    sellers_in=f.seller_id.dropna().unique()
    gs=grades[grades.seller_id.isin(sellers_in)]
    cnt=gs.grade.value_counts()
    cards="".join(f"""<div class="gc" style="border-top:3px solid {GRADE_COLOR[k]}"><span class="t" style="color:{GRADE_COLOR[k]}">{k}</span>
        <b>{int(cnt.get(k,0)):,}명</b><small>{pct(cnt.get(k,0)/max(len(gs),1),0)} · 평균 별점 {gs[gs.grade==k].avg_review.mean():.2f}</small></div>"""
        for k in ["위험","개선 필요","우수·고거래","우수"])
    st.markdown(f"<div class='gradecards'>{cards}</div>", unsafe_allow_html=True)

    # 판매자별 주요 불만 (필터 내 저평점 텍스트 기준)
    lowt=ft[ft.review_score<=2]
    main_issue={}
    if len(lowt):
        s=lowt.groupby("seller_id")[C.COMP_TYPES].sum()
        s=s[s.sum(axis=1)>0]
        main_issue=s.idxmax(axis=1).to_dict()
    fs=f[f.has_review==1].groupby("seller_id").agg(필터주문=("order_id","size"),필터저평점=("low","sum"))
    T=gs.merge(fs,left_on="seller_id",right_index=True,how="left")
    T["주요 문제"]=T.seller_id.map(main_issue).fillna("—")
    T["권장 액션"]=T["주요 문제"].map(C.ACTION).fillna("모니터링")
    T["저평점 건수"]=(T.low_rate*T.n_orders).round().astype(int)
    T=T.sort_values(["저평점 건수"],ascending=False)
    view=T.rename(columns={"seller_id":"판매자 ID","grade":"등급","n_orders":"주문 수","avg_review":"평균 별점",
        "low_rate":"저평점률","on_time_deliv":"정시배송률","gmv":"거래액(R$)","필터주문":"필터 내 주문"})
    cols=["판매자 ID","등급","주문 수","저평점 건수","평균 별점","저평점률","정시배송률","거래액(R$)","필터 내 주문","주요 문제","권장 액션"]
    show_cols=["판매자","등급","주문 수","저평점 건수","평균 별점","저평점률","정시배송률","필터 내 주문","주요 문제","권장 액션"]
    with st.container(border=True):
        h1,h2=st.columns([3,1.2])
        h1.subheader("개선 대상 판매자")
        # 등급 필터가 '전체'면 관리 대상(위험·개선 필요)만 기본 표시
        show_all=h2.toggle("우수 등급도 표시", value=False, disabled=sel_grade!="all")
        if sel_grade=="all" and not show_all: view=view[view["등급"].isin(["위험","개선 필요"])]
        st.markdown(f"<p class='desc'>필터 조건에 주문이 있는 판매자 {len(view):,}명 (주문 5건 이상). 저평점 건수 순 · 판매자 지표는 전체 기간 기준 · 주요 문제는 필터 내 저평점 리뷰 기준.</p>", unsafe_allow_html=True)
        def color_grade(v): return f"background-color:{GRADE_SOFT.get(v,'')};color:{GRADE_COLOR.get(v,INK)};font-weight:700"
        disp=view.head(200).copy(); disp["판매자"]=disp["판매자 ID"].str[:8]+"…"
        sty=(disp[show_cols].style.map(color_grade, subset=["등급"])
             .format({"평균 별점":"{:.2f}","저평점률":"{:.1%}","정시배송률":"{:.1%}","주문 수":"{:,}","필터 내 주문":"{:,.0f}"}))
        cfg={"판매자":st.column_config.TextColumn(width=92, help="앞 8자리. 전체 ID는 CSV에 있습니다."),"등급":st.column_config.TextColumn(width=80),
             "주문 수":st.column_config.Column(width=66),"저평점 건수":st.column_config.Column(width=80),
             "평균 별점":st.column_config.Column(width=70),"저평점률":st.column_config.Column(width=70),
             "정시배송률":st.column_config.Column(width=80),"필터 내 주문":st.column_config.Column(width=82),
             "주요 문제":st.column_config.TextColumn(width=120),"권장 액션":st.column_config.TextColumn(width=170)}
        st.dataframe(sty, width="stretch", height=360, hide_index=True, column_config=cfg)
        cc=st.columns([3,1])
        cc[0].markdown(f"<p class='desc'>상위 200명만 표시합니다. CSV에는 조건에 맞는 {len(view):,}명 전체와 seller_id 원문이 들어갑니다.</p>", unsafe_allow_html=True)
        csv=view[cols].to_csv(index=False).encode("utf-8-sig")
        cc[1].download_button("개선 대상 CSV 다운로드", csv, "olist_target_sellers.csv", "text/csv", type="primary", width="stretch")

    with st.container(border=True):
        st.subheader("카테고리 우선순위 — 건수 vs 비율")
        st.markdown("<p class='desc'>오른쪽 위 = 규모도 크고 저평점률도 높은 최우선 영역. 원 크기 = 저평점 건수. 이름은 건수 상위 4개·비율 상위 3개만 표시(나머지는 마우스를 올리면 보입니다).</p>", unsafe_allow_html=True)
        cg=f[f.has_review==1].groupby("category").agg(주문수=("order_id","size"),저평점률=("low","mean"),저평점건수=("low","sum"))
        cg=cg[(cg.주문수>=(300 if sel_cat=="all" else 1))&(cg.index!="(미상)")].reset_index()
        if len(cg)>=2:
            key_pts=list(dict.fromkeys(cg.nlargest(4,"저평점건수").category.tolist()+cg.nlargest(3,"저평점률").category.tolist()))
            cg["label"]=np.where(cg.category.isin(key_pts), cg.category.map(C.cat_short), "")
            POS=["top center","bottom center","middle left","top left","bottom right","middle right","top right"]
            pos_map={c:POS[i%len(POS)] for i,c in enumerate(cg[cg.category.isin(key_pts)].sort_values("주문수").category)}
            pos_map[cg.loc[cg.주문수.idxmax(),"category"]]="top left"   # 가장 오른쪽 점은 라벨을 안쪽으로
            cg["name"]=cg.category.map(C.cat_label)
            fig=px.scatter(cg, x="주문수", y=cg.저평점률*100, size="저평점건수", text="label", size_max=42,
                color=cg.저평점률*100, color_continuous_scale=[[0,"#82a773"],[0.5,YELLOW],[1,RED]],
                hover_name="name", hover_data={"주문수":":,","저평점건수":":,.0f","label":False})
            fig.update_traces(textposition=[pos_map.get(c,"top center") for c in cg.category], textfont=dict(size=12, color=INK))
            fig.add_hline(y=cg.저평점률.median()*100, line_dash="dot", line_color=MUTED)
            fig.add_vline(x=cg.주문수.median(), line_dash="dot", line_color=MUTED)
            lx=np.log10(cg.주문수)
            fig.update_xaxes(title="주문 수 (로그)", type="log", range=[lx.min()-0.12, lx.max()+0.12]); fig.update_yaxes(title="저평점률 %")
            fig=style_fig(fig,400); fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, width="stretch", config={"displayModeBar":False})
        else:
            st.info("비교할 카테고리가 2개 이상일 때 표시합니다. (카테고리 필터를 '전체'로 두세요)")

# ═══════════════════════════ ④ 리뷰 VOC 탐색 ═══════════════════════════
else:
    st.markdown("<div class='sec'><h2>리뷰 VOC 탐색</h2><p>별점과 실제 텍스트를 함께 확인해 숫자만으로 보이지 않는 원인을 찾습니다. 원문은 포르투갈어이며, 1~2점·불일치 리뷰는 한국어 기계 번역을 함께 보여줍니다.</p></div>", unsafe_allow_html=True)
    TOPICS=["전체 텍스트 리뷰"]+C.COMP_TYPES+["불일치: 고평점·부정","불일치: 저평점·긍정"]
    counts={t:(len(ft) if t=="전체 텍스트 리뷰" else int(ft[t].sum())) for t in TOPICS}
    a,b=st.columns([1,2.2])
    with a, st.container(border=True):
        st.subheader("불만 유형")
        st.markdown("<p class='desc'>유형을 고르면 오른쪽 리뷰가 바뀝니다. 괄호는 필터 내 건수.</p>", unsafe_allow_html=True)
        topic=st.radio("유형", TOPICS, format_func=lambda t:f"{t}  ({counts[t]:,})", label_visibility="collapsed")
        stars=st.multiselect("별점", [1,2,3,4,5], default=[], placeholder="전체 별점")
        q=st.text_input("리뷰 검색 (한국어·원문)", placeholder="예: 도착, 파손, nao chegou")
        order_by=st.radio("정렬", ["무작위 표본","최근 주문 순","낮은 별점 순"], horizontal=True)
        has_ko=ft["txt_ko"].notna().any()
        show_ko=st.toggle("한국어 번역으로 보기", value=bool(has_ko), disabled=not has_ko)
        st.markdown("<p class='desc'>번역 대상: 1~2점·불일치 리뷰 · 무료 기계 번역(NLLB-200)이라 오역이 있을 수 있어 원문을 함께 표시합니다.</p>"
                    if has_ko else "<p class='desc'>번역 파일(data/review_ko.csv)이 없어 원문만 표시합니다.</p>", unsafe_allow_html=True)
    with b, st.container(border=True):
        sub=ft if topic=="전체 텍스트 리뷰" else ft[ft[topic]==1]
        if stars: sub=sub[sub.review_score.isin(stars)]
        if q.strip():
            qq=q.strip()
            sub=sub[sub.txt.str.contains(qq, case=False, regex=False, na=False) | sub.txt_ko.fillna("").str.contains(qq, case=False, regex=False)]
        if order_by=="최근 주문 순": sub=sub.sort_values("order_purchase_timestamp", ascending=False)
        elif order_by=="낮은 별점 순": sub=sub.sort_values(["review_score","order_purchase_timestamp"], ascending=[True,False])
        else: sub=sub.sample(frac=1, random_state=7)
        n=len(sub); per=10; pages=max(1,(n+per-1)//per)
        h1,h2=st.columns([3,1])
        h1.subheader("리뷰 확인")
        pg=h2.number_input("페이지", 1, pages, 1, label_visibility="collapsed") if pages>1 else 1
        st.markdown(f"<p class='desc'>{n:,}건 중 {min(n,(pg-1)*per+1) if n else 0}–{min(n,pg*per)}번째 · {order_by}</p>", unsafe_allow_html=True)
        if n==0:
            st.info("조건에 맞는 리뷰가 없습니다.")
        out=[]
        for _,x in sub.iloc[(pg-1)*per:pg*per].iterrows():
            sc=int(x.review_score); scol=RED if sc<=2 else (YELLOW if sc==3 else GREEN)
            tags="".join(f"<span class='tag' style='background:{RED_SOFT};color:{RED}'>{k}</span>" for k in C.COMP_TYPES if x[k]==1)
            if x["불일치: 고평점·부정"]==1: tags+=f"<span class='tag' style='background:{ORANGE_SOFT};color:#b74923'>고평점·부정</span>"
            if x["불일치: 저평점·긍정"]==1: tags+=f"<span class='tag' style='background:{BLUE_SOFT};color:{BLUE}'>저평점·긍정</span>"
            if isinstance(x.get("만족유형"),str) and x["만족유형"]:
                tags+="".join(f"<span class='tag' style='background:{GREEN_SOFT};color:{GREEN}'>{html.escape(k)}</span>" for k in x["만족유형"].split("|"))
            meta=" · ".join(v for v in [C.state_label(x.customer_state) if isinstance(x.customer_state,str) else "",
                C.cat_short(x.category) if isinstance(x.category,str) and x.category!="(미상)" else "",
                f"판매자 {str(x.seller_id)[:8]}" if isinstance(x.seller_id,str) else "",
                f"등급 {x.grade}" if isinstance(x.grade,str) and x.grade!="판단 보류" else ""] if v)
            date=x.order_purchase_timestamp.strftime("%Y-%m-%d") if pd.notna(x.order_purchase_timestamp) else ""
            ko=x.get("txt_ko")
            if show_ko and isinstance(ko,str) and ko.strip():
                tags+=f"<span class='tag' style='background:#eef2f0;color:{MUTED}'>기계 번역</span>"
                body=f"<p>{html.escape(ko)}</p><p class='orig'>원문: {html.escape(str(x.txt))}</p>"
            else:
                body=f"<p>{html.escape(str(x.txt))}</p>"
            out.append(f"""<div class="review"><div class="review-head"><span class="score" style="color:{scol}">{sc}점</span>{tags}</div>
              {body}<small>{html.escape(meta)} · 주문 {date}</small></div>""")
        st.markdown("".join(out), unsafe_allow_html=True)

st.caption("데이터: Olist Brazilian E-Commerce Public Dataset. 리뷰 유형·불일치·판매자 등급은 팀 분석 결과표(CSV)를 사용합니다. "
           "모든 관계는 상관이며 인과가 아닙니다. 텍스트 리뷰는 전체의 약 43%인 부분집합입니다.")
