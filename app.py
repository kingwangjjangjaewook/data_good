from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(page_title="Titanic 대시보드", layout="wide")  # [추가]


# ===== 데이터 처리와 차트 함수 =====
def filter_data(df, sexes, classes, age_range):
    """성별, 등급, 나이 조건을 모두 만족하는 승객을 반환한다."""
    matches = df["sex"].isin(sexes) & df["pclass"].isin(classes)
    if tuple(age_range) != (0, 80):  # [수정] 전체 범위면 나이 결측을 포함
        matches &= df["age"].between(*age_range)
    return df.loc[matches].copy()


def kpi(df):
    """승객 수, 생존율(%), 평균 나이를 반환한다."""
    if df.empty:
        return (0, 0, 0)
    rate = round(float(df["survived"].mean()) * 100, 1)
    average = df["age"].mean()  # pandas는 결측 나이를 평균 계산에서 제외한다.
    age = None if pd.isna(average) else round(float(average), 1)
    return len(df), rate, age


def class_rate_bar(df):
    """객실 등급별 생존율(%)과 승객 수를 막대그래프로 그린다."""
    rates = (
        df.groupby("pclass", as_index=False)
        .agg(rate=("survived", "mean"), count=("survived", "size"))
    )
    rates["rate"] = (rates["rate"] * 100).round(1)
    rates["grade"] = rates["pclass"].map(lambda grade: f"{grade}등급")
    fig = px.bar(
        rates, x="grade", y="rate", text="rate", hover_data=["count"],
        title="객실 등급별 생존율",
        labels={"grade": "객실 등급", "rate": "생존율 (%)", "count": "승객 수"},
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_yaxes(range=[0, 108], tickvals=[0, 25, 50, 75, 100])
    return fig


def age_hist(df):
    """나이가 기록된 승객의 분포를 생존 여부별로 겹쳐 그린다."""
    known_age = df.dropna(subset=["age"]).copy()
    known_age["status"] = known_age["survived"].map({0: "0", 1: "1"})
    fig = px.histogram(
        known_age, x="age", color="status", barmode="overlay",
        title="생존 여부별 나이 분포",
        labels={"age": "나이 (세)", "status": "생존 여부 (0 사망, 1 생존)"},
        category_orders={"status": ["0", "1"]},
        color_discrete_map={"0": "#64748b", "1": "#087f8c"},
    )
    # 두 그룹을 같은 5세 구간으로 나누어 막대를 비교한다.
    fig.update_traces(xbins=dict(start=0, end=85, size=5), bingroup="age", opacity=0.6)
    fig.update_yaxes(title="승객 수 (명)")
    if known_age.empty:
        fig.add_annotation(
            text="나이가 기록된 승객이 없습니다.", showarrow=False,
            xref="paper", yref="paper", x=0.5, y=0.5,
        )
    return fig


# ===== 데이터 읽기 =====
@st.cache_data
def load_data():
    """app.py 옆에 있는 CSV를 읽고 위젯 재실행 때 캐시를 사용한다."""
    csv_path = Path(__file__).resolve().with_name("titanic.csv")
    return pd.read_csv(csv_path)


df = load_data()

# ===== 제목과 사이드바 =====
st.title("타이타닉, 누가 살아남았나?")
st.sidebar.caption("성별, 객실 등급, 나이 범위를 바꿔 생존율을 비교하세요.")
sexes = st.sidebar.multiselect(
    "성별", ["male", "female"], default=["male", "female"], key="sex_filter",
)
classes = st.sidebar.multiselect(
    "객실 등급", [1, 2, 3], default=[1, 2, 3], key="class_filter",
)
ages = st.sidebar.slider("나이 범위 (세)", 0, 80, (0, 80), key="age_filter")


# ===== 선택 확인 및 필터 적용 =====
if not sexes or not classes:  # [수정] 성별이나 등급을 전부 해제한 경우
    st.warning("성별과 등급을 하나 이상 선택하세요.")
    st.stop()


f = filter_data(df, sexes, classes, ages)
if f.empty:  # [수정] 선택 조건에 해당하는 승객이 없는 경우
    st.warning("조건에 맞는 승객이 없습니다.")
    st.stop()


# ===== KPI 숫자 카드 =====
n, rate, age = kpi(f)  # [추가]
c1, c2, c3 = st.columns(3)  # [추가]
c1.metric("승객 수", f"{n}명")  # [추가]
c2.metric("생존율", f"{rate:.1f}%")  # [추가]
age_label = "나이 정보 없음" if age is None else f"{age:.1f}세"
c3.metric("평균 나이", age_label)  # [추가]


# ===== 차트 두 개와 상세 데이터 =====
left, right = st.columns(2)  # [추가]
left.plotly_chart(class_rate_bar(f), key="class_chart")  # [추가]
right.plotly_chart(age_hist(f), key="age_chart")  # [추가]

with st.expander("데이터 보기"):  # [추가]
    st.dataframe(f, hide_index=True)  # [추가]
