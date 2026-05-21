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
st.write("사면 조건과 마찰각을 입력하면 각 파괴 모드별 위험 영역(Hazard Zone)에 속하는 극점(Poles)들이 색상으로 하이라이트됩니다.")

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
            
            # 사면 대원선 및 내부마찰각 원선 기본 드로잉
            ax.plane(slope_dip_dir, slope_dip, c='black', lw=2.5, label='사면 면 (Slope Face)', zorder=4)
            theta = np.linspace(0, 2*np.pi, 100)
            ax.plot(theta, np.full_like(theta, 90 - friction_angle), c='red', linestyle='--', lw=2, label='내부마찰각원', zorder=4)
            
            ax.set_title(title_text, color=title_color, fontsize=15, weight='bold', pad=25)
            ax.grid(True, color='gray', linestyle=':', lw=0.5)
            return fig, ax

        # --- 1️⃣ 평면파괴 차트 (Planar Failure) ---
        fig1, ax1 = create_large_stereonet("⚠️ 1. 평면파괴 해석 (Planar Failure)", "darkred")
        ax1.plane(slope_dip_dir - 20, slope_dip, c='darkred', lw=1.5, linestyle=':', label='주향 제약선(±20°)')
        ax1.plane(slope_dip_dir + 20, slope_dip, c='darkred', lw=1.5, linestyle=':')
        
        # 평면파괴 수학적 매칭 알고리즘 적용 (에러 우회)
        # 극점은 경사방향 180도 반대편에 맺힘을 반영하여 각도 마스킹
        rel_dir_p = (dip_dirs - slope_dip_dir + 180) % 360 - 180
        planar_idx = (np.abs(rel_dir_p) <= 20) & (dips >= friction_angle) & (dips <= slope_dip)
        
        # 일반 극점과 위험 영역 진입 극점 구분 분기
        ax1.pole(dip_dirs[~planar_idx], dips[~planar_idx], c='black', markersize=6, label='안전 극점 (Safe)', zorder=5)
        if np.any(planar_idx):
            ax1.pole(dip_dirs[planar_idx], dips[planar_idx], c='red', markersize=8, marker='s', label='위험 극점 (Planar Critical)', zorder=6)
            
        ax1.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=10)
        st.pyplot(fig1, use_container_width=True)
        plt.close(fig1)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # --- 2️⃣ 쐐기파괴 차트 (Wedge Failure) ---
        fig2, ax2 = create_large_stereonet("⚠️ 2. 쐐기파괴 해석 (Wedge Failure)", "darkorange")
        
        # 쐐기파괴 교선 위험조건: 불연속면들의 교선이 사면대원 내부 및 내부마찰각 외부 영역에 유치
        # 두 불연속면들의 교선을 계산하여 판단 (mplstereonet 내장 함수 활용)
        danger_intersections_dir = []
        danger_intersections_dip = []
        safe_intersections_dir = []
        safe_intersections_dip = []
        
        # 모든 불연속면 쌍의 교선 연산
        for i in range(len(dip_dirs)):
            for j in range(i + 1, len(dip_dirs)):
                # 두 평면의 교선 구하기
                int_strike, int_dip = mplstereonet.intersection(dip_dirs[i]-90, dips[i], dip_dirs[j]-90, dips[j])
                if len(int_strike) > 0:
                    i_dir = (int_strike[0] + 90) % 360
                    i_dip = int_dip[0]
                    
                    # 사면 전방 활성창 검증
                    rel_dir_w = (i_dir - slope_dip_dir + 180) % 360 - 180
                    if (np.abs(rel_dir_w) <= 90) & (i_dip >= friction_angle) & (i_dip <= slope_dip):
                        danger_intersections_dir.append(i_dir)
                        danger_intersections_dip.append(i_dip)
                    else:
                        safe_intersections_dir.append(i_dir)
                        safe_intersections_dip.append(i_dip)

        # 교점(Intersections) 플로팅
        if safe_intersections_dir:
            ax2.pole(safe_intersections_dir, safe_intersections_dip, c='gray', markersize=5, marker='x', label='안전 교점', zorder=5)
        if danger_intersections_dir:
            ax2.pole(danger_intersections_dir, danger_intersections_dip, c='orange', markersize=8, marker='X', label='위험 교점 (Wedge Critical)', zorder=6)
            
        ax2.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=10)
        st.pyplot(fig2, use_container_width=True)
        plt.close(fig2)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # --- 3️⃣ 전도파괴 차트 (Toppling Failure) ---
        fig3, ax3 = create_large_stereonet("⚠️ 3. 전도파괴 해석 (Toppling Failure)", "darkblue")
        ax3.plane(slope_dip_dir, 90 - slope_dip, c='darkblue', lw=1.5, linestyle='--', label='전도 한계선')
        
        # 전도파괴 극점 위험조건 판별
        rel_dir_t = (dip_dirs - (slope_dip_dir - 180) + 180) % 360 - 180
        toppling_idx = (np.abs(rel_dir_t) <= 30) & (dips <= (90 - friction_angle)) & (dips >= (90 - slope_dip))
        
        ax3.pole(dip_dirs[~toppling_idx], dips[~toppling_idx], c='black', markersize=6, label='안전 극점 (Safe)', zorder=5)
        if np.any(toppling_idx):
            ax3.pole(dip_dirs[toppling_idx], dips[toppling_idx], c='purple', markersize=8, marker='^', label='위험 극점 (Toppling Critical)', zorder=6)
            
        ax3.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=10)
        st.pyplot(fig3, use_container_width=True)
        plt.close(fig3)
        
    else:
        st.warning("데이터를 1개 이상 입력해 주세요.")
