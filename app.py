import streamlit as st
import numpy as np
import matplotlib
matplotlib.use('Agg')  # GUI 충돌 방지
import matplotlib.pyplot as plt
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
st.write("사면 조건과 마찰각을 입력하면 평면·쐐기·전도파괴의 '위험 영역(Hazard Zone)'만 실제 Dips처럼 투명하게 색칠되어 출력됩니다.")

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
    except:
        dip_dirs, dips = [], []

    if len(dip_dirs) > 0 and len(dips) > 0:
        
        # [근본적 해결책] 버전을 전혀 타지 않는 순수 마일리 표형 Polar Projection 커스텀 생성기
        def create_dips_base(title_text, title_color):
            fig = plt.figure(figsize=(7, 7), dpi=120)
            ax = fig.add_subplot(111, projection='polar')
            
            # 북향(0도)이 상단으로 가도록 세팅 및 시계방향 회전 설정 (Dips 표준 규격)
            ax.set_theta_zero_location('N')
            ax.set_theta_direction(-1)
            
            # 반지름 범위 설정 (중심 경사각 0도 ~ 외곽 90도 구조 마스킹)
            ax.set_ylim(0, 90)
            ax.set_yticks([30, 60, 90])
            ax.set_yticklabels(['60°', '30°', '0°'], fontsize=8, color='gray') # 투영 특성상 반대로 표기
            ax.set_xticklabels(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'], fontsize=9, weight='bold')
            
            # 1. 기본 불연속면 극점(Poles) 타점 (경사각 0도일 때 외곽인 평사투영 좌표 변환 반영)
            r_poles = 90 - dips
            theta_poles = np.radians((dip_dirs + 180) % 360) # 극점은 반대 방향 매핑
            ax.scatter(theta_poles, r_poles, c='black', s=35, edgecolors='white', linewidths=0.5, label='Poles (극점)', zorder=5)
            
            # 2. 사면 대원의 흔적선 그리기
            s_angles = np.linspace(0, 2*np.pi, 200)
            # 사면면의 평사투영 궤적 기하 연산
            slope_rad = np.radians(slope_dip_dir)
            # 대원 궤적 공식 유도 적용
            def get_plane_r(ang):
                rel_ang = ang - slope_rad
                # 평사투영상 대원의 반지름 좌표 계산
                with np.errstate(divide='ignore', invalid='ignore'):
                    denom = np.cos(rel_ang)
                    if np.abs(denom) < 1e-5: return 90
                    val = np.tan(np.radians(slope_dip)) * denom
                    r = 90 - np.degrees(np.arctan(val))
                    return np.clip(r, 0, 90)
            
            # 3. 내부마찰각원 그리기 (반지름 = 90 - 마찰각)
            ax.plot(s_angles, np.full_like(s_angles, 90 - friction_angle), c='red', linestyle='--', lw=2, label='내부마찰각원', zorder=4)
            
            ax.set_title(title_text, color=title_color, fontsize=15, weight='bold', pad=25)
            ax.grid(True, color='lightgray', linestyle=':', lw=0.5)
            return fig, ax

        # --- 1️⃣ 평면파괴 차트 (Planar Failure) ---
        fig1, ax1 = create_dips_base("⚠️ 1. 평면파괴 해석 (Planar Failure)", "darkred")
        
        # 위험 영역 색칠: 주향 ±20도 범위 내, 내부마찰각원 바깥, 사면각 안쪽 (극점 범주)
        # 극점 기준이므로 사면 경사방향의 반대편(±180도) 활성창 영역 채우기
        p_center = (slope_dip_dir + 180) % 360
        theta_p = np.radians(np.linspace(p_center - 20, p_center + 20, 100))
        
        r_inner_p = np.full_like(theta_p, 90 - slope_dip)       # 사면각선 (극점은 고각일수록 중심에 위치)
        r_outer_p = np.full_like(theta_p, 90 - friction_angle)  # 마찰각선
        
        ax1.fill_between(theta_p, r_inner_p, r_outer_p, color='red', alpha=0.25, label='위험 영역 (Hazard Zone)', zorder=2)
        
        ax1.legend(loc='upper left', bbox_to_anchor=(1.1, 1), fontsize=10)
        st.pyplot(fig1, use_container_width=True)
        plt.close(fig1)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # --- 2️⃣ 쐐기파괴 차트 (Wedge Failure) ---
        fig2, ax2 = create_dips_base("⚠️ 2. 쐐기파괴 해석 (Wedge Failure)", "darkorange")
        
        # 쐐기파괴 위험 영역 (교선 기준 랜드마크): 사면면 내부이면서 내부마찰각원 외부 (초승달 형상)
        w_center = slope_dip_dir
        theta_w = np.radians(np.linspace(w_center - 90, w_center + 90, 100))
        
        # 초승달 바운더리 연산 (사면면 대원선 자체가 외곽선 경계가 됨)
        r_inner_w = np.zeros_like(theta_w) # 중심점 방향 경사면 상부 한계
        slope_rad = np.radians(slope_dip_dir)
        
        r_outer_w = []
        for t in theta_w:
            rel_ang = t - slope_rad
            val = np.tan(np.radians(slope_dip)) * np.cos(rel_ang)
            r_plane = 90 - np.degrees(np.arctan(np.maximum(val, 0)))
            # 마찰각원 한계선과의 상호 제약 필터링
            r_outer_w.append(np.clip(r_plane, 0, 90 - friction_angle))
            
        ax2.fill_between(theta_w, r_inner_w, r_outer_w, color='orange', alpha=0.25, label='위험 영역 (Hazard Zone)', zorder=2)
        
        ax2.legend(loc='upper left', bbox_to_anchor=(1.1, 1), fontsize=10)
        st.pyplot(fig2, use_container_width=True)
        plt.close(fig2)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # --- 3️⃣ 전도파괴 차트 (Toppling Failure) ---
        fig3, ax3 = create_dips_base("⚠️ 3. 전도파괴 해석 (Toppling Failure)", "darkblue")
        
        # 전도파괴 극점 위험 영역: 사면 경사방향 전방 전도 제약창 (±30도 밴드)
        t_center = slope_dip_dir
        theta_t = np.radians(np.linspace(t_center - 30, t_center + 30, 100))
        
        # 전도 한계 기준 필터링 영역 채우기
        r_inner_t = np.full_like(theta_t, 0)
        r_outer_t = np.full_like(theta_t, 90 - friction_angle)
        
        ax3.fill_between(theta_t, r_inner_t, r_outer_t, color='purple', alpha=0.25, label='위험 영역 (Hazard Zone)', zorder=2)
        
        ax3.legend(loc='upper left', bbox_to_anchor=(1.1, 1), fontsize=10)
        st.pyplot(fig3, use_container_width=True)
        plt.close(fig3)
        
    else:
        st.warning("데이터를 1개 이상 입력해 주세요.")
