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
st.write("사면 조건과 마찰각을 입력하면 평면·쐐기·전도파괴 해석 결과가 실제 Dips 위험 구역 레이어와 함께 고해상도로 동시에 출력됩니다.")

# 좌측 입력창 비율(3), 우측 그래프 영역 비율(7) 조정
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
        
        # 고해상도 베이스 Stereonet 생성 함수
        def create_large_stereonet(title_text, title_color):
            fig = plt.figure(figsize=(7, 7), dpi=120)
            ax = fig.add_subplot(111, projection='stereonet')
            
            # 밀도 등고선 및 극점 타점 (Dips 스타일 선명한 칼라)
            ax.density_contourf(dip_dirs, dips, cmap='jet', alpha=0.5)
            ax.density_contour(dip_dirs, dips, colors='black', linewidths=0.3)
            ax.pole(dip_dirs, dips, c='black', markersize=6, label='Poles (극점)', zorder=5)
            
            # 사면 대원선 및 마찰각 원선 그리기
            ax.plane(slope_dip_dir, slope_dip, c='black', lw=2.5, label='사면 면 (Slope Face)')
            
            # 마찰각 Cone 표현
            theta = np.linspace(0, 2*np.pi, 100)
            ax.plot(theta, np.full_like(theta, 90 - friction_angle), c='red', linestyle='--', lw=2, label='내부마찰각원')
            
            ax.set_title(title_text, color=title_color, fontsize=15, weight='bold', pad=25)
            ax.grid(True, color='gray', linestyle=':', lw=0.5)
            return fig, ax

        # --- 1️⃣ 평면파괴 차트 (Planar Failure) ---
        fig1, ax1 = create_large_stereonet("⚠️ 1. 평면파괴 해석 (Planar Failure)", "darkred")
        
        # 평면파괴 기하학 제약조건 라인 생성
        ax1.plane(slope_dip_dir - 20, slope_dip, c='darkred', lw=1.5, linestyle=':')
        ax1.plane(slope_dip_dir + 20, slope_dip, c='darkred', lw=1.5, linestyle=':')
        
        # Dips와 동일하게 평면파괴 위험 구역(Hazard Zone) 채우기
        # 조건: 주향 ±20도 이내, 사면 경사각 이하, 마찰각 이상 영역
        p_dip = np.linspace(friction_angle, slope_dip, 20)
        p_dir = np.linspace(slope_dip_dir - 20, slope_dip_dir + 20, 30)
        PD, DD = np.meshgrid(p_dip, p_dir)
        ax1.fill_between_bands(DD.flatten(), PD.flatten(), color='red', alpha=0.15, label='위험 영역 (Hazard Zone)')
        
        ax1.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=10)
        st.pyplot(fig1, use_container_width=True)
        plt.close(fig1)
        
        # [에러 수정] unsafe_allow_html=True 로 변경하여 간격 확보
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # --- 2️⃣ 쐐기파괴 차트 (Wedge Failure) ---
        fig2, ax2 = create_large_stereonet("⚠️ 2. 쐐기파괴 해석 (Wedge Failure)", "darkorange")
        
        # 쐐기파괴 위험 구역 채우기 (사면 대원 내부 및 내부마찰각 외부 영역 전체가 교선 위험대)
        w_dip = np.linspace(friction_angle, slope_dip, 20)
        w_dir = np.linspace(slope_dip_dir - 90, slope_dip_dir + 90, 40)
        WD, WD_dir = np.meshgrid(w_dip, w_dir)
        ax2.fill_between_bands(WD_dir.flatten(), WD.flatten(), color='orange', alpha=0.15, label='위험 영역 (Hazard Zone)')
        
        ax2.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=10)
        st.pyplot(fig2, use_container_width=True)
        plt.close(fig2)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # --- 3️⃣ 전도파괴 차트 (Toppling Failure) ---
        fig3, ax3 = create_large_stereonet("⚠️ 3. 전도파괴 해석 (Toppling Failure)", "darkblue")
        
        # 전도파괴 제약 경계 대원선 표기
        ax3.plane(slope_dip_dir, 90 - slope_dip, c='darkblue', lw=1.5, linestyle='--')
        
        # 전도파괴 극점 위험 영역 오버레이 (사면 배면 방향 마찰각 제약 영역)
        t_dip = np.linspace(0, 90 - friction_angle, 20)
        t_dir = np.linspace(slope_dip_dir - 180 - 20, slope_dip_dir - 180 + 20, 30)
        TD, TD_dir = np.meshgrid(t_dip, t_dir)
        ax3.fill_between_bands(TD_dir.flatten(), TD.flatten(), color='purple', alpha=0.15, label='위험 영역 (Hazard Zone)')
        
        ax3.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=10)
        st.pyplot(fig3, use_container_width=True)
        plt.close(fig3)
        
    else:
        st.warning("데이터를 1개 이상 입력해 주세요.")
