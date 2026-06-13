import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="개별 분석 그리드", page_icon="📊", layout="wide")

st.header("📊 기업별 개별 주가 차트 그리드")
st.caption("선택한 기업들의 주가 흐름을 각각의 독립된 그래프로 상세히 비교하세요.")

# 1. 기업 리스트 설정
defense_tickers = {
    "LMT": "록히드 마틴",
    "RTX": "RTX",
    "NOC": "노스롭 그루만",
    "GD": "제너럴 다이내믹스",
    "BA": "보잉"
}

# 2. 사이드바에서 표시할 기업 선택
st.sidebar.header("🔍 표시 설정")
selected_tks = st.sidebar.multiselect(
    "보고 싶은 기업을 선택하세요",
    options=list(defense_tickers.keys()),
    default=list(defense_tickers.keys())
)

# 그래프 열 개수 설정 (1열 또는 2열)
num_columns = st.sidebar.radio("한 줄에 보일 그래프 개수", [1, 2], index=1)

# 3. 데이터 로드 함수 (기존 로직 유지)
@st.cache_data(ttl=3600)
def fetch_data(ticker):
    end_date = datetime.today()
    start_date = end_date - timedelta(days=365)
    try:
        data = yf.download(ticker, start=start_date, end=end_date)
        if not data.empty:
            # MultiIndex 대응
            if isinstance(data.columns, pd.MultiIndex):
                if ticker in data.columns.get_level_values(1):
                    close_series = data['Close'][ticker]
                else:
                    close_series = data['Close'].iloc[:, 0]
            else:
                close_series = data['Close']
            return pd.DataFrame({'Close': close_series}).dropna().reset_index()
    except:
        return pd.DataFrame()
    return pd.DataFrame()

# 4. 그리드 레이아웃 생성 및 그래프 출력
if selected_tks:
    # 선택된 기업 리스트를 순회하며 컬럼 배치
    cols = st.columns(num_columns)
    
    for i, tk in enumerate(selected_tks):
        with cols[i % num_columns]:
            with st.container():
                st.subheader(f"{defense_tickers[tk]} ({tk})")
                df_plot = fetch_data(tk)
                
                if not df_plot.empty:
                    # 각 기업별 독립적인 차트 생성
                    fig = px.area(
                        df_plot, 
                        x='Date', 
                        y='Close',
                        labels={'Close': 'Price ($)', 'Date': '날짜'},
                        color_discrete_sequence=[px.colors.qualitative.Plotly[i % 10]] # 기업별 다른 색상
                    )
                    
                    fig.update_layout(
                        height=350, # 그리드 내 적절한 높이
                        margin=dict(l=20, r=20, t=20, b=20),
                        hovermode="x"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning(f"{tk} 데이터를 불러올 수 없습니다.")
else:
    st.info("왼쪽 사이드바에서 분석할 기업을 하나 이상 선택해 주세요.")
