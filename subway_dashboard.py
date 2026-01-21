import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import platform

# ==============================================================================
# 1. 기본 설정 및 폰트 세팅
# ==============================================================================
st.set_page_config(layout="wide", page_title="대구 도시철도 소화기 현황 대시보드")

@st.cache_resource
def set_korean_font():
    # OS별 한글 폰트 설정
    system_name = platform.system()
    if system_name == 'Windows':
        plt.rc('font', family='Malgun Gothic')
    elif system_name == 'Darwin':  # Mac
        plt.rc('font', family='AppleGothic')
    else:
        plt.rc('font', family='NanumGothic')
    
    plt.rc('axes', unicode_minus=False) # 마이너스 기호 깨짐 방지

set_korean_font()

# ==============================================================================
# 2. 데이터 로드 및 전처리 함수
# ==============================================================================
@st.cache_data
def load_data():
    # 파일 경로 설정 (같은 폴더에 위치해야 함)
    file_1 = '국가철도공단_대구1호선_소화기설비_20250630.csv'
    file_3 = '국가철도공단_대구3호선_소화기설비_20250630.csv'
    
    # 인코딩 자동 감지 로직
    encoders = ['euc-kr', 'cp949', 'utf-8']
    
    def read_csv_safe(path):
        for enc in encoders:
            try:
                return pd.read_csv(path, encoding=enc)
            except UnicodeDecodeError:
                continue
        return None

    df1 = read_csv_safe(file_1)
    df3 = read_csv_safe(file_3)
    
    if df1 is None or df3 is None:
        return None

    # 데이터 전처리: 노선 구분 컬럼 추가
    df1['Line'] = '1호선 (지하)'
    df3['Line'] = '3호선 (지상)'
    
    # 위치 카테고리화 함수 (승강장, 대합실, 기타)
    def categorize_loc(text):
        if pd.isna(text): return '기타'
        if '승강장' in text: return '승강장'
        elif '대합실' in text: return '대합실'
        else: return '기타'

    df1['Location_Cat'] = df1['상세위치'].apply(categorize_loc)
    df3['Location_Cat'] = df3['상세위치'].apply(categorize_loc)

    # 데이터 합치기
    df_combined = pd.concat([df1, df3], ignore_index=True)
    
    return df1, df3, df_combined

# ==============================================================================
# 3. 메인 대시보드 UI 구성
# ==============================================================================
st.title("🚇 대구 도시철도 소화기 설비 비교 분석")
st.markdown("### 지하(1호선) vs 지상(3호선) 환경에 따른 소화기 배치 차이")

# 데이터 로드
data = load_data()

if data:
    df1, df3, df_all = data
    
    # --- [Section 1] 핵심 지표 (KPI) ---
    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    
    # 1호선 통계
    stations_1 = df1['역명'].nunique()
    total_1 = df1['보유대수'].sum()
    avg_1 = total_1 / stations_1 if stations_1 > 0 else 0
    
    # 3호선 통계
    stations_3 = df3['역명'].nunique()
    total_3 = df3['보유대수'].sum()
    avg_3 = total_3 / stations_3 if stations_3 > 0 else 0

    col1.metric("1호선(지하) 총 보유대수", f"{total_1}대", delta="가장 많음")
    col2.metric("1호선 역당 평균", f"{avg_1:.1f}대", delta=f"3호선보다 +{avg_1 - avg_3:.1f}")
    col3.metric("3호선(지상) 총 보유대수", f"{total_3}대")
    col4.metric("3호선 역당 평균", f"{avg_3:.1f}대")

    # --- [Section 2] 시각화 차트 ---
    st.divider()
    st.subheader("📊 시각화 비교 분석")
    
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("#### 1. 노선별 총 소화기 수량 비교")
        fig1, ax1 = plt.subplots(figsize=(8, 6))
        
        sns.barplot(data=df_all, x='Line', y='보유대수', estimator=sum, errorbar=None, 
                    palette=['#1f77b4', '#ff7f0e'], ax=ax1)
        
        # 값 표시
        for p in ax1.patches:
            ax1.annotate(f'{int(p.get_height())}대', 
                         (p.get_x() + p.get_width() / 2., p.get_height()), 
                         ha='center', va='bottom', fontsize=12, fontweight='bold')
            
        ax1.set_ylabel("보유 대수 (누적)")
        ax1.set_xlabel("")
        ax1.set_ylim(0, total_1 * 1.2) # 여백 확보
        st.pyplot(fig1)

    with chart_col2:
        st.markdown("#### 2. 주요 위치별(승강장/대합실) 분포")
        # 그룹핑 데이터 생성
        loc_group = df_all.groupby(['Line', 'Location_Cat'])['보유대수'].sum().reset_index()
        
        fig2, ax2 = plt.subplots(figsize=(8, 6))
        sns.barplot(data=loc_group, x='Location_Cat', y='보유대수', hue='Line', 
                    palette=['#1f77b4', '#ff7f0e'], ax=ax2)
        
        ax2.set_ylabel("보유 대수")
        ax2.set_xlabel("설치 위치")
        ax2.legend(title='노선 구분')
        st.pyplot(fig2)

    st.divider()
    
    chart_col3, chart_col4 = st.columns(2)
    
    with chart_col3:
        st.markdown("#### 3. 역별 보유량 분포 (Box Plot)")
        st.caption("1호선은 역마다 편차가 크고, 3호선은 균일하게 배치된 특징을 보입니다.")
        
        # 역별 합계 데이터 생성
        station_sum = df_all.groupby(['Line', '역명'])['보유대수'].sum().reset_index()
        
        fig3, ax3 = plt.subplots(figsize=(8, 5))
        sns.boxplot(data=station_sum, x='Line', y='보유대수', palette=['#aec7e8', '#ffbb78'], ax=ax3)
        sns.stripplot(data=station_sum, x='Line', y='보유대수', color='black', alpha=0.3, ax=ax3) # 점 찍기
        
        ax3.set_ylabel("역당 보유 대수")
        ax3.set_xlabel("")
        st.pyplot(fig3)

    with chart_col4:
        st.markdown("#### 4. 역별 보유대수 Top 5 (1호선 vs 3호선)")
        
        tab1, tab2 = st.tabs(["1호선 Top 5", "3호선 Top 5"])
        
        with tab1:
            top5_1 = df1.groupby('역명')['보유대수'].sum().sort_values(ascending=False).head(5)
            st.dataframe(top5_1, use_container_width=True)
            
        with tab2:
            top5_3 = df3.groupby('역명')['보유대수'].sum().sort_values(ascending=False).head(5)
            st.dataframe(top5_3, use_container_width=True)

    # --- [Section 3] 상세 데이터 보기 ---
    st.divider()
    with st.expander("📂 전체 데이터 원본 보기 (클릭하여 펼치기)"):
        st.dataframe(df_all)

else:
    st.error("⚠️ 데이터 파일을 찾을 수 없습니다. 폴더에 csv 파일이 있는지 확인해주세요.")