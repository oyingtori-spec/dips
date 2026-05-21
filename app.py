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

# 1. 웹 페이지 제목 및 전체 화면 너비 설정
st.set_page_config(layout="wide", page_title="모바일/웹 Dips 종합 분석기")
st.title("🌋 Web-based Dips Stereonet (Multi-Kinematic Analysis)")
st.write("사면 조건과 마찰각을 입력하면 평면·쐐기·전도파괴 해석 결과가 고해상도로 동시에 출력됩니다.")

# [개선 포인트 1] 좌측 입력창은 작게(3), 우측 그래프 영역은 크게(7) 비율 조정
col1, col2 = st.columns([3, 7])

with col1:
    st.subheader("📋 1. 사면 조건 및 마찰각 입력")
    slope_dip_dir = st.number_input("📐 사면 경사방향 (Slope Dip Direction)", min_value=0, max_value=360, value=135, step=1)
    slope_dip = st.number_input("📐 사면 경사각 (Slope Dip)", min_value=0, max_value=90, value=60, step=1)
    friction_angle = st.number_input("🧱 내부마찰각 (Friction Angle)", min_value=0, max_value=90, value=30, step=1)
    
    st.subheader("📊 2. 불연속면 데이터 입력")
    st.info("💡 아래 표에 데이터를 입력하거나 엑셀에서 복사(Ctrl+C) 후 붙여넣기(Ctrl+V) 하세요.")
    
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
        
        # [개선 포인트 2] 그래프를 큼직하게 그리기 위한 공통 함수 선언 (figsize 증가 및 해상도 업)
        def create_large_stereonet(title_text, title_color):
            # 상용 Dips 크기 느낌을 내기 위해 크기를 7x7인치로 대폭 확대
            fig = plt.figure(figsize=(7, 7), dpi=120)
            ax = fig.add_subplot(111, projection='stereonet')
            
            # 밀도 등고선 및 극점 타점 (Dips 스타일의 진한 칼라 적용)
            ax.density_contourf(dip_dirs, dips, cmap='jet', alpha=0.55)
            ax.density_contour(dip_dirs, dips, colors='black', linewidths=0.4)
            ax.pole(dip_dirs, dips, c='black', markersize=6, label='Poles (극점)', zorder=5)
            
            # 사면 대원 및 내부마찰각 선
            ax.plane(slope_dip_dir, slope_dip, c='black', lw=2.5, label='사면 면 (Slope Face)')
            theta = np.linspace(0, 2*np.pi, 100)
            ax.plot(theta, np.full_like(theta, 90 - friction_angle), c='red', linestyle='--', lw=2, label='내부마찰각원')
            
            # 가독성을 높이기 위해 제목 크기 및 패딩 확대
            ax.set_title(title_text, color=title_color, fontsize=15, weight='bold', pad=25)
            ax.grid(True, color='gray', linestyle=':', lw=0.5)
            
            # 범례 배치 조정
            ax.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=10)
            return fig, ax

        # --- 1️⃣ 평면파괴 차트 ---
        fig1, ax1 = create_large_stereonet("⚠️ 1. 평면파괴 해석 (Planar Failure)", "darkred")
        ax1.plane(slope_dip_dir - 20, slope_dip, c='orange', lw=1.5, linestyle=':')
        ax1.plane(slope_dip_dir + 20, slope_dip, c='orange', lw=1.5, linestyle=':')
        st.pyplot(fig1, use_container_width=True) # [개선 포인트 3] 우측 너비에 맞춰 꽉 차게 채움
        plt.close(fig1)
        
        st.markdown("<br><br>", unsafe_rendering_html=True)
        
        # --- 2️⃣ 쐐기파괴 차트 ---
        fig2, ax2 = create_large_stereonet("⚠️ 2. 쐐기파괴 해석 (Wedge Failure)", "darkorange")
        ax2.plane(slope_dip_dir, slope_dip, c='darkorange', lw=1.5, linestyle='--')
        st.pyplot(fig2, use_container_width=True)
        plt.close(fig2)
        
        st.markdown("<br><br>", unsafe_rendering_html=True)
        
        # --- 3️⃣ 전도파괴 차트 ---
        fig3, ax3 = create_large_stereonet("⚠️ 3. 전도파괴 해석 (Toppling Failure)", "darkblue")
        ax3.plane(slope_dip_dir, 90 - slope_dip, c='purple', lw=1.5, linestyle='--')
        ax3.plane(slope_dip_dir - 180, 90 - slope_dip, c='purple', lw=1.5, linestyle=':')
        st.pyplot(fig3, use_container_width=True)
        plt.close(fig3)
        
    else:
        st.warning("데이터를 1개 이상 입력해 주세요.")
