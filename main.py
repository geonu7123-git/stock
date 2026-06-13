import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(
    page_title="주요 주가 분석 대시보드 (최근 1년)",
    page_icon="📈",
    layout="wide"
)

st.title("📈 주요 기업 주가 변동 분석 대시보드")
st.markdown("최근 1개년 간의 **삼성전자, SK하이닉스, 구글, 마이크로소프트, 애플**의 주가 추이를 분석합니다.")

# 2. 주식 티커 설정
# 국내 주식은 야후 파이낸스 기준 .KS 접미사가 필요합니다.
ticker_dict = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "구글 (Alphabet)": "GOOGL",
    "마이크로소프트 (MS)": "MSFT",
    "애플 (Apple)": "AAPL"
}

# 3. 데이터 로드 (최근 1년)
@st.cache_data(ttl=3600)  # 1시간 동안 데이터 캐싱하여 성능 최적화
def load_stock_data():
    end_date = datetime.today()
    start_date = end_date - timedelta(days=365)
    
    combined_df = pd.DataFrame()
    
    for name, ticker in ticker_dict.items():
        try:
            # 주가 데이터 다운로드
            data = yf.download(ticker, start=start_date, end=end_date)
            if not data.empty:
                # 2차원 컬럼 구조(MultiIndex) 대응 및 'Close' 가격 추출
                if isinstance(data.columns, pd.MultiIndex):
                    close_series = data['Close'][ticker]
                else:
                    close_series = data['Close']
                
                # 데이터 프레임 구성
                df = pd.DataFrame({'Close': close_series})
                df['Ticker_Name'] = name
                df = df.reset_index()
                
                # 누적 수익률 계산 (첫 거래일 종가 대비 변동률 %)
                first_price = df['Close'].iloc[0]
                df['Return_Pct'] = ((df['Close'] - first_price) / first_price) * 100
                
                combined_df = pd.concat([combined_df, df], ignore_index=True)
        except Exception as e:
            st.error(f"{name} 데이터를 가져오는 중 오류 발생: {e}")
            
    return combined_df

with st.spinner("야후 파이낸스에서 실시간 주가 데이터를 가져오는 중..."):
    df_stocks = load_stock_data()

# 데이터 로드가 성공한 경우에만 시각화 진행
if not df_stocks.empty:
    
    # 사이드바 토글을 이용한 자산 선택
    st.sidebar.header("⚙️ 필터 설정")
    selected_companies = st.sidebar.multiselect(
        "분석할 기업을 선택하세요",
        options=list(ticker_dict.keys()),
        default=list(ticker_dict.keys())
    )
    
    # 선택된 기업 데이터만 필터링
    filtered_df = df_stocks[df_stocks['Ticker_Name'].isin(selected_companies)]
    
    # --- 레이아웃 분할 ---
    tab1, tab2, tab3 = st.tabs(["📊 1년 누적 수익률 비교", "💵 개별 종가 추이", "🔍 최근 데이터 보기"])
    
    with tab1:
        st.subheader("서로 다른 통화(원/달러) 주식의 변동률 비교")
        st.caption("최근 1년 전 첫 거래일의 주가를 0%로 잡고 누적 수익률 추이를 비교합니다.")
        
        # Plotly Express Line Chart
        fig_return = px.line(
            filtered_df,
            x='Date',
            y='Return_Pct',
            color='Ticker_Name',
            labels={'Return_Pct': '누적 수익률 (%)', 'Date': '날짜', 'Ticker_Name': '기업명'},
            title='최근 1개년 누적 수익률(%) 추이'
        )
        fig_return.update_layout(hovermode="x unified")
        st.plotly_chart(fig_return, use_container_width=True)
        
    with tab2:
        st.subheader("기업별 절대 종가 추이")
        st.caption("국내 주식은 원화(KRW), 미국 주식은 달러(USD) 기준 단독 가격입니다.")
        
        # 선택된 기업 중 개별 가격 확인을 위한 셀렉트박스
        single_company = st.selectbox("상세 주가를 볼 기업을 선택하세요", options=selected_companies)
        single_df = filtered_df[filtered_df['Ticker_Name'] == single_company]
        
        # Plotly Area/Line chart
        fig_close = go.Figure()
        fig_close.add_trace(go.Scatter(
            x=single_df['Date'], 
            y=single_df['Close'], 
            mode='lines',
            name=single_company,
            fill='tozeroy' # 하단 채우기로 시각적 효과 부여
        ))
        
        currency = "원(KRW)" if single_company in ["삼성전자", "SK하이닉스"] else "달러(USD)"
        fig_close.update_layout(
            title=f"{single_company} 최근 1년 종가 추이",
            xaxis_title="날짜",
            yaxis_title=f"주가 ({currency})",
            hovermode="x"
        )
        st.plotly_chart(fig_close, use_container_width=True)
        
    with tab3:
        st.subheader("가장 최근 거래일 데이터 요약")
        
        # 각 기업별 가장 최근 날짜의 주가 추출
        latest_data = []
        for company in selected_companies:
            comp_df = filtered_df[filtered_df['Ticker_Name'] == company]
            if not comp_df.empty:
                latest_row = comp_df.sort_values(by='Date').iloc[-1]
                latest_data.append({
                    "기업명": company,
                    "최종 거래일": latest_row['Date'].strftime('%Y-%m-%d'),
                    "종가": f"{latest_row['Close']:.2f}",
                    "1년 누적 수익률": f"{latest_row['Return_Pct']:.2f}%"
                })
        
        st.dataframe(pd.DataFrame(latest_data), use_container_width=True)

else:
    st.error("데이터를 불러오지 못했습니다. 티커 설정이나 네트워크 상태를 확인해주세요.")
