import streamlit as st
import numpy as np
import matplotlib
matplotlib.use('Agg')  # GUI 충돌 방지
import matplotlib.pyplot as plt
import mplstereonet
import pandas as pd
import matplotlib.font_manager as fm
import urllib.request

# 인터넷에서 나눔고딕 폰트를 다운로드하여 한글 깨짐을 완전히 방지합니다.
@st.cache_data
def load_korean_font():
    try:
        font_url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
        font_path = "NanumGothic.ttf"
        urllib.request.urlretrieve(font_url, font_path)
        fm.fontManager.addfont(font_path)
        matplotlib.rc('font', family='NanumGothic')
    except:
        pass

load_korean_font()

# 1. 웹 페이지 제목 설정
st.set_page_config(layout="wide", page_title="모바일/웹 Dips 종합 분석기")
st.title("🌋 Web-based Dips Stereonet (Multi-Kinematic Analysis)")
st.write("사면 조건과 마찰각을 입력하면 평면·쐐기·전도파괴 해석 결과가 동시에 출력됩니다.")

# 화면을 좌우로 분할 (좌측: 입력창 고정, 우측: 결과 차트들 배열)
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📋 1. 사면 조건 및 마찰각 입력")
    slope_dip_dir = st.number_input("📐 사면 경사방향 (Slope Dip Direction) [0 ~ 360]", min_value=0, max_value=360, value=135, step=1)
    slope_dip = st.number_input("📐 사면 경사각 (Slope Dip) [0 ~ 90]", min_value=0, max_value=90, value=60, step=1)
    friction_angle = st.number_input("🧱 내부마찰각 (Friction Angle) [0 ~ 90]", min_value=0, max_value=90, value=30, step=1)
    
    st.subheader("📊 2. 불연속면 데이터 입력")
    st.info("💡 아래 표에 현장 측정 데이터를 입력하세요. (엑셀 붙여넣기 가능)")
    
    default_data = {
        "Dip Direction (경사방향)": [135, 140, 130, 315, 320, 210, 145, 125, 310],
        "Dip (경사)": [45, 48, 42, 60, 62, 30, 47, 40, 58]
    }
    df = pd.DataFrame(default_data)
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)

with col2:
    st.subheader("📊 Dips 운동학적 종합 해석 결과")
    
    # 데이터 추출
    try:
        raw_dip_dirs = pd.to_numeric(edited_df.iloc[:, 0]).dropna().to_numpy()
        raw_dips = pd.to_numeric(edited_df.iloc[:, 1]).dropna().to_numpy()
        
        dip_dirs = np.array(raw_dip_dirs, copy=True)
        dips = np.array(raw_dips, copy=True)
        dip_dirs.flags.writeable = True
        dips.flags.writeable = True
    except:
        dip_dirs, dips = [], []

    if len(dip_dirs) > 0 and len(dips) > 0:
        # 공통 차트 생성 함수 정의 (코드 중복 방지)
        def create_base_stereonet(title_text, title_color):
            fig = plt.figure(figsize=(5, 5))
            ax = fig.add_subplot(111, projection='stereonet')
            
            # 기본 등고선 및 극점 타점
            ax.density_contourf(dip_dirs, dips, cmap='jet', alpha=0.5)
            ax.density_contour(dip_dirs, dips, colors='black', linewidths=0.3)
            ax.pole(dip_dirs, dips, c='black', markersize=5, label='Poles', zorder=5)
            
            # 사면 면 및 마찰각 기본선
            ax.plane(slope_dip_dir, slope_dip, c='black', lw=2, label='사면 면 (Slope Face)')
            theta = np.linspace(0, 2*np.pi, 100)
            ax.plot(theta, np.full_like(theta, 90 - friction_angle), c='red', linestyle='--', lw=1.5, label='내부마찰각')
            
            ax.set_title(title_text, color=title_color, fontsize=12, weight='bold', pad=20)
            ax.grid(True, color='lightgray', linestyle=':')
            ax.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=8)
            return fig, ax

        # --- 1. 평면파괴 차트 ---
        st.markdown("### 1️⃣ 평면파괴 해석 (Planar Failure)")
        fig1, ax1 = create_base_stereonet("⚠️ 평면파괴 가이드라인", "darkred")
        ax1.plane(slope_dip_dir - 20, slope_dip, c='orange', lw=1.2, linestyle=':')
        ax1.plane(slope_dip_dir + 20, slope_dip, c='orange', lw=1.2, linestyle=':')
        st.pyplot(fig1, width=420)
        plt.close(fig1)
        
        st.markdown("---")
        
        # --- 2. 쐐기파괴 차트 ---
        st.markdown("### 2️⃣ 쐐기파괴 해석 (Wedge Failure)")
        fig2, ax2 = create_base_stereonet("⚠️ 쐐기파괴 가이드라인", "darkorange")
        ax2.plane(slope_dip_dir, slope_dip, c='darkorange', lw=1, linestyle='--')
        st.pyplot(fig2, width=420)
        plt.close(fig2)
        
        st.markdown("---")
        
        # --- 3. 전도파괴 차트 ---
        st.markdown("### 3️⃣ 전도파괴 해석 (Toppling Failure)")
        fig3, ax3 = create_base_stereonet("⚠️ 전도파괴 가이드라인", "darkblue")
        ax3.plane(slope_dip_dir, 90 - slope_dip, c='purple', lw=1.2, linestyle='--')
        ax3.plane(slope_dip_dir - 180, 90 - slope_dip, c='purple', lw=1.2, linestyle=':')
        st.pyplot(fig3, width=420)
        plt.close(fig3)
        
    else:
        st.warning("데이터를 1개 이상 입력해 주세요.")
