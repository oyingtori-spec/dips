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

# 1. 웹 페이지 제목 및 레이아웃 설정
st.set_page_config(layout="wide", page_title="모바일/웹 Dips 분석기")
st.title("🌋 Web-based Dips Stereonet (Kinematic Analysis)")
st.write("사면 조건과 마찰각을 숫자로 직접 입력하여 평면·쐐기·전도파괴 위험 영역을 분석하세요.")

# 화면을 좌우로 분할
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📋 1. 사면 조건 및 마찰각 입력")
    slope_dip_dir = st.number_input("📐 사면 경사방향 (Slope Dip Direction) [0 ~ 360]", min_value=0, max_value=360, value=135, step=1)
    slope_dip = st.number_input("📐 사면 경사각 (Slope Dip) [0 ~ 90]", min_value=0, max_value=90, value=60, step=1)
    friction_angle = st.number_input("🧱 내부마찰각 (Friction Angle) [0 ~ 90]", min_value=0, max_value=90, value=30, step=1)
    
    st.subheader("🛡️ 2. 해석할 파괴 모드 선택")
    analysis_mode = st.radio(
        "오버레이할 파괴 기하학을 선택하세요:",
        ("없음 (기본 Dips 플롯)", "평면파괴 (Planar Failure)", "쐐기파괴 (Wedge Failure)", "전도파괴 (Toppling Failure)")
    )
    
    st.subheader("📊 3. 불연속면 데이터 입력")
    st.info("💡 아래 표에 현장 측정 데이터를 입력하세요. (엑셀 붙여넣기 가능)")
    
    default_data = {
        "Dip Direction (경사방향)": [135, 140, 130, 315, 320, 210, 145, 125, 310],
        "Dip (경사)": [45, 48, 42, 60, 62, 30, 47, 40, 58]
    }
    df = pd.DataFrame(default_data)
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)

with col2:
    st.subheader("📊 Dips 운동학적 해석 결과")
    
    # 데이터 추출 파트
    try:
        raw_dip_dirs = pd.to_numeric(edited_df.iloc[:, 0]).dropna().to_numpy()
        raw_dips = pd.to_numeric(edited_df.iloc[:, 1]).dropna().to_numpy()
        
        dip_dirs = np.array(raw_dip_dirs, copy=True)
        dips = np.array(raw_dips, copy=True)
        dip_dirs.flags.writeable = True
        dips.flags.writeable = True
    except:
        dip_dirs, dips = [], []

    # 그래프 그리기 파트 (에러가 나지 않도록 구조 간소화)
    if len(dip_dirs) > 0 and len(dips) > 0:
        fig = plt.figure(figsize=(6, 6))
        ax = fig.add_subplot(111, projection='stereonet')
        
        # 1. 등고선 및 극점 타점
        ax.density_contourf(dip_dirs, dips, cmap='jet', alpha=0.6)
        ax.density_contour(dip_dirs, dips, colors='black', linewidths=0.3)
        ax.pole(dip_dirs, dips, c='black', markersize=5, label='Poles', zorder=5)
        
        # 2. 사면 및 마찰각 기본선 그리기
        ax.plane(slope_dip_dir, slope_dip, c='black', lw=2, label='사면 면 (Slope Face)')
        theta = np.linspace(0, 2*np.pi, 100)
        ax.plot(theta, np.full_like(theta, 90 - friction_angle), c='red', linestyle='--', lw=1.5, label='내부마찰각')

        # 3. 파괴 모드별 가이드라인 레이어 및 제목 패딩 세팅
        if analysis_mode == "평면파괴 (Planar Failure)":
            ax.set_title("⚠️ 평면파괴 분석 모드 (Planar Failure)", color='darkred', fontsize=14, weight='bold', pad=25)
            ax.plane(slope_dip_dir - 20, slope_dip, c='orange', lw=1.2, linestyle=':')
            ax.plane(slope_dip_dir + 20, slope_dip, c='orange', lw=1.2, linestyle=':')
            
        elif analysis_mode == "쐐기파괴 (Wedge Failure)":
            ax.set_title("⚠️ 쐐기파괴 분석 모드 (Wedge Failure)", color='darkorange', fontsize=14, weight='bold', pad=25)
            ax.plane(slope_dip_dir, slope_dip, c='darkorange', lw=1, linestyle='--')
            
        elif analysis_mode == "전도파괴 (Toppling Failure)":
            ax.set_title("⚠️ 전도파괴 분석 모드 (Toppling Failure)", color='darkblue', fontsize=14, weight='bold', pad=25)
            ax.plane(slope_dip_dir, 90 - slope_dip, c='purple', lw=1.2, linestyle='--')
            ax.plane(slope_dip_dir - 180, 90 - slope_dip, c='purple', lw=1.2, linestyle=':')
        else:
            ax.set_title("📊 기본 분석 모드 (All Plots)", fontsize=14, weight='bold', pad=25)

        # 4. 레이아웃 다듬기 및 출력
        ax.grid(True, color='lightgray', linestyle=':')
        ax.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=9)
        st.pyplot(fig, width=450)
        
        # 5. 이미지 다운로드 기능
        plt.savefig("dips_kinematic_output.png", bbox_inches='tight', dpi=300)
        with open("dips_kinematic_output.png", "rb") as file:
            st.download_button(
                label="💾 분석 차트 이미지 다운로드",
                data=file,
                file_name="dips_kinematic.png",
                mime="image/png"
            )
        plt.close(fig)
    else:
        st.warning("데이터를 1개 이상 입력해 주세요.")
