import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="수익률 비교", page_icon="📈", layout="wide")

st.header("📈 최근 1개년 누적 수익률 (%) 비교")
st.caption("1년 전 첫 거래일의 주가를 0%로 잡고 변동률을 비교합니다.")

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
    errors = []
    
    for ticker, name in defense_tickers.items():
        try:
            # group_by='ticker' 옵션을 제외하고 개별 다운로드로 안정성 확보
            data = yf.download(ticker, start=start_date, end=end_date)
            
            if not data.empty:
                # 최신 yfinance의 다중 컬럼(MultiIndex) 이슈 방어
                if isinstance(data.columns, pd.MultiIndex):
                    # 컬럼에 티커가 포함되어 있으면 해당 티커의 Close 추출
                    if ticker in data.columns.get_level_values(1):
                        close_series = data['Close'][ticker]
                    else:
                        close_series = data['Close'].iloc[:, 0]
                else:
                    close_series = data['Close']
                
                # 데이터 정제 및 1차원 데이터프레임 생성
                df = pd.DataFrame({'Close': close_series}).dropna()
                
                if not df.empty:
                    df['Company'] = f"{name} ({ticker})"
                    df = df.reset_index()
                    
                    # 수익률 계산
                    first_price = df['Close'].iloc[0]
                    df['Return_Pct'] = ((df['Close'] - first_price) / first_price) * 100
                    
                    combined_df = pd.concat([combined_df, df], ignore_index=True)
            else:
                errors.append(f"{ticker} 데이터가 비어 있습니다.")
        except Exception as e:
            errors.append(f"{ticker} 에러 발생: {str(e)}")
            
    return combined_df, errors

with st.spinner("야후 파이낸스에서 실시간 데이터를 가져오는 중..."):
    df_perf, err_list = load_performance_data()

# 에러가 있었다면 화면에 선제적으로 표시 (디버깅용)
if err_list:
    with st.expander("⚠️ 일부 데이터 로드 로그 확인"):
        for err in err_list:
            st.warning(err)

if not df_perf.empty:
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
    st.error("데이터를 하나도 불러오지 못했습니다. 야후 파이낸스 연결 상태나 라이브러리 버전을 확인하세요.")
