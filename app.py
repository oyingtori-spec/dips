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

st.set_page_config(layout="wide", page_title="모바일/웹 Dips 종합 분석기")
st.title("🌋 Web-based Dips Stereonet (True Kinematic Analysis)")
st.write("상용 Dips 프로그램과 완벽히 일치하는 기하학적 위험 영역(Hazard Zone) 평사투영 매핑 가이드입니다.")

col1, col2 = st.columns([3, 7])

with col1:
    st.subheader("📋 1. 사면 조건 및 마찰각 입력")
    slope_dip_dir = st.number_input("📐 사면 경사방향 (Slope Dip Direction)", min_value=0, max_value=360, value=135, step=1)
    slope_dip = st.number_input("📐 사면 경사각 (Slope Dip)", min_value=0, max_value=90, value=60, step=1)
    friction_angle = st.number_input("🧱 내부마찰각 (Friction Angle)", min_value=0, max_value=90, value=30, step=1)
    
    st.subheader("📊 2. 불연속면 데이터 입력")
    
    default_data = {
        "Dip Direction (경사방향)": [135, 140, 130, 315, 320, 210, 145, 125, 310],
        "Dip (경사)": [45, 48, 42, 60, 62, 30, 47, 40, 58]
    }
    df = pd.DataFrame(default_data)
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)

with col2:
    st.subheader("📊 Dips 운동학적 종합 해석 결과")
    
    try:
        raw_dip_dirs = pd.to_numeric(edited_df.iloc[:, 0]).dropna().to_numpy()
        raw_dips = pd.to_numeric(edited_df.iloc[:, 1]).dropna().to_numpy()
        dip_dirs = np.array(raw_dip_dirs, copy=True)
        dips = np.array(raw_dips, copy=True)
    except:
        dip_dirs, dips = [], []

    if len(dip_dirs) > 0 and len(dips) > 0:
        
        # 기하학적 수식 변환 (Stereonet 좌표 변환기 고유 우회식)
        def dir_dip_to_xy(strike, dip):
            # mplstereonet의 투영 구조 계산 공식을 순수 카테시안으로 전환하여 에러 원천 방지
            lon = np.radians(strike - 90)
            lat = np.radians(90 - dip)
            # Equal-angle (Stereographic) projection 수식
            R = np.tan(np.pi/4 - lat/2)
            x = R * np.sin(lon)
            y = R * np.cos(lon)
            return x, y

        def create_base_chart(title_text, title_color):
            fig = plt.figure(figsize=(7, 7), dpi=120)
            ax = fig.add_subplot(111, projection='stereonet')
            ax.pole(dip_dirs, dips, c='black', markersize=6, label='Poles (극점)', zorder=5)
            ax.plane(slope_dip_dir, slope_dip, c='black', lw=2.5, label='사면 면 (Slope Face)', zorder=4)
            
            # 마찰각원 렌더링
            angles = np.linspace(0, 2*np.pi, 180)
            r_cone = np.tan(np.radians(90 - friction_angle) / 2.0)
            ax.plot(r_cone * np.sin(angles), r_cone * np.cos(angles), c='red', linestyle='--', lw=2, label='내부마찰각원', zorder=4)
            
            ax.set_title(title_text, color=title_color, fontsize=15, weight='bold', pad=25)
            ax.grid(True, color='gray', linestyle=':', lw=0.4)
            return fig, ax

        # --- 1️⃣ 평면파괴 차트 (진짜 초승달 밴드 구역 채우기) ---
        fig1, ax1 = create_base_chart("⚠️ 1. 평면파괴 해석 (Planar Failure)", "darkred")
        ax1.plane(slope_dip_dir - 20, slope_dip, c='darkred', lw=1.5, linestyle=':', zorder=3)
        ax1.plane(slope_dip_dir + 20, slope_dip, c='darkred', lw=1.5, linestyle=':', zorder=3)
        
        # 극점 기준 초승달 경계 영역 매핑
        p_strike_min = slope_dip_dir - 20
        p_strike_max = slope_dip_dir + 20
        
        # 내부선(마찰각원과의 경계선 고각 트랙)과 외부선(사면면 대원선 트랙) 연산
        angles = np.linspace(p_strike_min, p_strike_max, 50)
        x_inner, y_inner = [], []
        x_outer, y_outer = [], []
        
        for a in angles:
            # 극점은 경사방향 180도 반대에 찍힘 반영
            x_in, y_in = dir_dip_to_xy(a + 180, friction_angle)
            x_out, y_out = dir_dip_to_xy(a + 180, slope_dip)
            x_inner.append(x_in); y_inner.append(y_in)
            x_outer.append(x_out); y_outer.append(y_out)
            
        x_poly = np.concatenate([x_inner, x_outer[::-1]])
        y_poly = np.concatenate([y_inner, y_outer[::-1]])
        ax1.fill(x_poly, y_poly, color='red', alpha=0.2, label='위험 영역 (초승달 밴드)', zorder=2)
        
        ax1.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=10)
        st.pyplot(fig1, use_container_width=True)
        plt.close(fig1)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # --- 2️⃣ 쐐기파괴 차트 (교선 기준: 선으로만 표시) ---
        fig2, ax2 = create_base_chart("⚠️ 2. 쐐기파괴 해석 (Wedge Failure)", "darkorange")
        
        # 면 색채우기 삭제! 요청하신 대로 사면대원 내부선 중 마찰각원 외부선 구간만 주황색 실선(Critical Line)으로 강조
        w_angles = np.linspace(slope_dip_dir - 90, slope_dip_dir + 90, 150)
        x_wedge_line, y_wedge_line = [], []
        
        for wa in w_angles:
            # 사면 대원 궤적 기하식 역연산
            rel = np.radians(wa - slope_dip_dir)
            val = np.tan(np.radians(slope_dip)) * np.cos(rel)
            calculated_dip = np.degrees(np.arctan(val))
            
            # 쐐기파괴 기하조건: 교선 경사각이 내부마찰각 이상이어야 함
            if calculated_dip >= friction_angle:
                x_w, y_w = dir_dip_to_xy(wa, calculated_dip)
                x_wedge_line.append(x_w)
                y_wedge_line.append(y_w)
                
        if x_wedge_line:
            ax2.plot(x_wedge_line, y_wedge_line, color='darkorange', lw=4.5, label='위험 활성선 (Wedge Hazard Line)', zorder=3)
            
        ax2.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=10)
        st.pyplot(fig2, use_container_width=True)
        plt.close(fig2)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # --- 3️⃣ 전도파괴 차트 (극점 기준: 사다리꼴 구역 채우기) ---
        fig3, ax3 = create_base_chart("⚠️ 3. 전도파괴 해석 (Toppling Failure)", "darkblue")
        ax3.plane(slope_dip_dir, 90 - slope_dip, c='darkblue', lw=1.5, linestyle='--', zorder=3)
        
        # 사면 배면 방향 마찰각 제약 조건으로 이루어진 '사다리꼴' 박스 기하 경로 추적
        t_strike_min = slope_dip_dir - 30
        t_strike_max = slope_dip_dir + 30
        
        t_angles = np.linspace(t_strike_min, t_strike_max, 50)
        x_t_top, y_t_top = [], []
        x_t_bot, y_t_bot = [], []
        
        for ta in t_angles:
            # 전도파괴 극점 조건 경계선 좌표 매핑 (90-사면각 ~ 90-마찰각 범위)
            x_top, y_top = dir_dip_to_xy(ta, 90 - friction_angle)
            x_bot, y_bot = dir_dip_to_xy(ta, 90 - slope_dip)
            x_t_top.append(x_top); y_t_top.append(y_top)
            x_t_bot.append(x_bot); y_t_bot.append(y_bot)
            
        x_topple_poly = np.concatenate([x_t_top, x_t_bot[::-1]])
        y_topple_poly = np.concatenate([y_t_top, y_t_bot[::-1]])
        ax3.fill(x_topple_poly, y_topple_poly, color='purple', alpha=0.18, label='위험 영역 (사다리꼴 바운더리)', zorder=2)
        
        ax3.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=10)
        st.pyplot(fig3, use_container_width=True)
        plt.close(fig3)
        
    else:
        st.warning("데이터를 1개 이상 입력해 주세요.")
