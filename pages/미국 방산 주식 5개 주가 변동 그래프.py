import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="수익률 비교", page_icon="📈", layout="wide")

st.header("📈 최근 1개년 누적 수익률 (%) 비교")
st.caption("시점의 차이를 배제하기 위해 1년 전 첫 거래일의 주가를 0%로 잡고 변동률을 비교합니다.")

# 기업 정보 티커 세팅
defense_tickers = {
    "LMT": "록히드 마틴",
    "RTX": "RTX",
    "NOC": "노스롭 그루만",
    "GD": "제너럴 다이내믹스",
    "BA": "보잉"
}

@st.cache_data(ttl=3600)
def load_performance_data():
    end_date = datetime.today()
    start_date = end_date - timedelta(days=365)
    
    combined_df = pd.DataFrame()
    
    for ticker, name in defense_tickers.items():
        try:
            data = yf.download(ticker, start=start_date, end=end_date)
            if not data.empty:
                # 멀티인덱스 컬럼 방지 및 Close 추출
                if isinstance(data.columns, pd.MultiIndex):
                    close_series = data['Close'][ticker]
                else:
                    close_series = data['Close']
                
                df = pd.DataFrame({'Close': close_series})
                df['Company'] = f"{name} ({ticker})"
                df = df.reset_index()
                
                # 수익률 계산
                first_price = df['Close'].iloc[0]
                df['Return_Pct'] = ((df['Close'] - first_price) / first_price) * 100
                
                combined_df = pd.concat([combined_df, df], ignore_index=True)
        except Exception as e:
            st.error(f"{ticker} 데이터 로드 실패: {e}")
    return combined_df

with st.spinner("야후 파이낸스에서 실시간 데이터를 가져오는 중..."):
    df_perf = load_performance_data()

if not df_perf.empty:
    # Plotly 라인 차트 생성
    fig = px.line(
        df_perf,
        x='Date',
        y='Return_Pct',
        color='Company',
        labels={'Return_Pct': '누적 수익률 (%)', 'Date': '날짜', 'Company': '기업명'},
        title='방산 5개사 수익률 트렌드'
    )
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("데이터를 시각화할 수 없습니다.")
