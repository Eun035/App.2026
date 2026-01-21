import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
import platform
import matplotlib.gridspec as gridspec
import numpy as np

# ==============================================================================
# 1. 한글 폰트 설정 (Streamlit 캐싱 적용)
# ==============================================================================
@st.cache_resource
def set_korean_font():
    plt.style.use('seaborn-v0_8-whitegrid')
    
    system_name = platform.system()
    if system_name == 'Windows':
        plt.rc('font', family='Malgun Gothic')
    elif system_name == 'Darwin':
        plt.rc('font', family='AppleGothic')
    else:
        plt.rc('font', family='NanumGothic')
    
    plt.rc('axes', unicode_minus=False)

# ==============================================================================
# 2. 데이터 로드 및 전처리
# ==============================================================================
@st.cache_data
def load_and_preprocess(file_path):
    encoders = ['euc-kr', 'cp949', 'utf-8']
    df = None
    for enc in encoders:
        try:
            df = pd.read_csv(file_path, encoding=enc)
            break
        except UnicodeDecodeError:
            continue
    
    if df is None:
        return None

    def parse_combined_value(val):
        if pd.isna(val) or val == '-': return 0.0, 0.0
        if isinstance(val, (int, float)): return float(val), 0.0
        
        val_str = str(val).replace(',', '')
        match = re.search(r'([0-9.]+)\s*\(([0-9.]+)\)', val_str)
        if match:
            return float(match.group(1)), float(match.group(2))
        
        match_single = re.search(r'([0-9.]+)', val_str)
        if match_single:
            return float(match_single.group(1)), 0.0
            
        return 0.0, 0.0

    cols_to_parse = [('재산피해규모 전국(전남)_억 원', '재산피해'), 
                     ('복구액 전국(전남)_억 원', '복구액')]
    
    for col_name, prefix in cols_to_parse:
        if col_name in df.columns:
            parsed = df[col_name].apply(parse_combined_value)
            df[f'{prefix}_전국'] = [x[0] for x in parsed]
            df[f'{prefix}_전남'] = [x[1] for x in parsed]

    return df

# ==============================================================================
# 3. 시각화 함수 (Figure 객체 반환하도록 수정됨)
# ==============================================================================
def create_dashboard_figure(df):
    # Figure 객체 생성
    fig = plt.figure(figsize=(22, 16), facecolor='white')
    
    # GridSpec 설정
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.4, wspace=0.3)
    
    fig.suptitle('전라남도 태풍 피해 현황 분석 대시보드 (2005~2023)', 
                 fontsize=28, fontweight='bold', y=0.96)

    # -------------------------------------------------------------------------
    # Chart 1: 연도별 전남 재산 피해액 추이 (Broken Axis)
    # -------------------------------------------------------------------------
    gs_chart1 = gridspec.GridSpecFromSubplotSpec(2, 1, subplot_spec=gs[0, 0], 
                                                 height_ratios=[1, 3], hspace=0.05)
    
    ax1_top = fig.add_subplot(gs_chart1[0])
    ax1_btm = fig.add_subplot(gs_chart1[1])

    max_damage_val = df['재산피해_전남'].max()
    second_max_val = df['재산피해_전남'].sort_values(ascending=False).iloc[1]
    
    colors = ['#d62728' if v == max_damage_val else '#ff9999' for v in df['재산피해_전남']]
    
    ax1_top.bar(range(len(df)), df['재산피해_전남'], color=colors, edgecolor='darkred')
    ax1_btm.bar(range(len(df)), df['재산피해_전남'], color=colors, edgecolor='darkred')

    ax1_top.set_ylim(max_damage_val * 0.9, max_damage_val * 1.1)
    ax1_btm.set_ylim(0, second_max_val * 1.2)

    ax1_top.spines['bottom'].set_visible(False)
    ax1_btm.spines['top'].set_visible(False)
    ax1_top.xaxis.tick_top()
    ax1_top.tick_params(labeltop=False)
    ax1_btm.xaxis.tick_bottom()

    d = .015  
    kwargs = dict(transform=ax1_top.transAxes, color='k', clip_on=False)
    ax1_top.plot((-d, +d), (-d, +d), **kwargs)        
    ax1_top.plot((1 - d, 1 + d), (-d, +d), **kwargs)

    kwargs.update(transform=ax1_btm.transAxes) 
    ax1_btm.plot((-d, +d), (1 - d, 1 + d), **kwargs)  
    ax1_btm.plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)

    ax1_btm.set_xticks(range(0, len(df), 2))
    ax1_btm.set_xticklabels(df['연도'].astype(str)[::2], rotation=45, fontsize=12)
    ax1_top.set_title('연도별 재산 피해액 추이 (구간 축소)', fontsize=18, fontweight='bold', pad=20)
    
    max_idx = df['재산피해_전남'].idxmax()
    max_year = df.loc[max_idx, '연도']
    x_pos = list(df.index).index(max_idx)
    
    ax1_top.annotate(f'{max_year}년 최대 피해\n{max_damage_val:,.0f}억', 
                     xy=(x_pos, max_damage_val), 
                     xytext=(x_pos + 4, max_damage_val),
                     arrowprops=dict(arrowstyle='->', color='darkred', lw=1.5),
                     bbox=dict(boxstyle='round,pad=0.5', fc='white', ec='darkred', alpha=0.9),
                     ha='left', va='center', fontsize=12, fontweight='bold')

    ax1_btm.set_ylabel('피해액 (억 원)', fontsize=14, fontweight='bold')
    ax1_btm.grid(axis='y', alpha=0.3, linestyle='--')

    # -------------------------------------------------------------------------
    # Chart 2: 피해액 상위 5개 태풍
    # -------------------------------------------------------------------------
    ax2 = fig.add_subplot(gs[0, 1])
    top5 = df.sort_values(by='재산피해_전남', ascending=True).tail(5).copy()
    y_pos = range(len(top5))
    ax2.barh(y_pos, top5['재산피해_전남'], color='#ff6b6b', edgecolor='darkred', height=0.6)
    
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels([f"{row['태풍명']}" for _, row in top5.iterrows()], fontsize=12, fontweight='bold')
    ax2.set_xlabel('피해액 (억 원)', fontsize=14)
    ax2.set_title('역대 피해액 상위 5개 태풍', fontsize=18, fontweight='bold', pad=15)
    
    ax2.set_xlim(0, top5['재산피해_전남'].max() * 1.25) 
    
    for i, v in enumerate(top5['재산피해_전남']):
        ax2.text(v + 50, i, f'{v:,.0f}억', va='center', fontsize=12, fontweight='bold')

    # -------------------------------------------------------------------------
    # Chart 3: 피해액 vs 복구액 상관관계
    # -------------------------------------------------------------------------
    ax3 = fig.add_subplot(gs[1, 0])
    valid_df = df[df['재산피해_전남'] > 0].copy()
    
    ax3.scatter(valid_df['재산피해_전남'], valid_df['복구액_전남'], 
                s=150, alpha=0.7, c='#1f77b4', edgecolors='white')
    
    if len(valid_df) > 1:
        z = np.polyfit(valid_df['재산피해_전남'], valid_df['복구액_전남'], 1)
        p = np.poly1d(z)
        x_line = np.linspace(valid_df['재산피해_전남'].min(), valid_df['재산피해_전남'].max(), 100)
        ax3.plot(x_line, p(x_line), "r--", alpha=0.6, label='추세선')

    ax3.set_title('재산 피해액과 복구액의 상관관계', fontsize=18, fontweight='bold', pad=15)
    ax3.set_xlabel('재산 피해액 (억 원)', fontsize=14)
    ax3.set_ylabel('복구액 (억 원)', fontsize=14)
    ax3.grid(True, alpha=0.3, linestyle='--')

    for idx, row in valid_df.nlargest(2, '재산피해_전남').iterrows():
        ax3.annotate(f"{row['태풍명']}\n({int(row['연도'])})", 
                     xy=(row['재산피해_전남'], row['복구액_전남']),
                     xytext=(-40, 40), textcoords='offset points',
                     arrowprops=dict(arrowstyle='->', color='black'),
                     bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='gray', alpha=0.8),
                     fontsize=11, fontweight='bold')

    # -------------------------------------------------------------------------
    # Chart 4: 전국 대비 전남 피해 비중
    # -------------------------------------------------------------------------
    ax4 = fig.add_subplot(gs[1, 1])
    total_national = df['재산피해_전국'].sum()
    total_jeonnam = df['재산피해_전남'].sum()
    others = total_national - total_jeonnam
    
    if total_national > 0:
        labels = ['전라남도', '그 외 전국']
        sizes = [total_jeonnam, others]
        colors_pie = ['#ff6b6b', '#d3d3d3']
        explode = (0.1, 0)
        
        wedges, texts, autotexts = ax4.pie(sizes, explode=explode, labels=labels, colors=colors_pie, 
                                           autopct='%1.1f%%', shadow=True, startangle=140,
                                           textprops={'fontsize': 13, 'fontweight': 'bold'},
                                           pctdistance=0.8)
        
        ax4.text(1.3, 1.0, f"전남 누적 피해액:\n{total_jeonnam:,.0f}억 원", 
                 ha='center', va='center', fontsize=12, fontweight='bold',
                 bbox=dict(boxstyle='round,pad=0.5', fc='white', ec='red', ls='--'))

    ax4.set_title('전국 대비 전남 피해액 비중 (누적)', fontsize=18, fontweight='bold', pad=15)

    # [핵심 수정] plt.show() 대신 Figure 객체 반환
    return fig

# ==============================================================================
# 4. Streamlit 실행부
# ==============================================================================
# 페이지 설정
st.set_page_config(layout="wide", page_title="태풍 피해 분석")

st.title("전라남도 태풍 피해 현황 분석")

# 폰트 설정 실행
set_korean_font()

# 파일 경로 (같은 폴더에 위치해야 함)
file_path = '전라남도_연도별 태풍피해 현황_20251104.csv'

try:
    df = load_and_preprocess(file_path)
    
    if df is not None:
        # [핵심 수정] 함수에서 반환된 fig 객체를 받아서
        fig = create_dashboard_figure(df)
        
        # [핵심 수정] Streamlit 함수로 출력
        st.pyplot(fig)
        st.success("대시보드 생성이 완료되었습니다.")
    else:
        st.error("데이터를 불러오지 못했습니다. 파일 경로와 인코딩을 확인해주세요.")
        
except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")