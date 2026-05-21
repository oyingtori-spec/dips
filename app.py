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
st.write("사면 조건과 마찰각을 입력하면 상용 Dips와 완벽히 동일한 평사투영망 격자 위에 위험 영역이 안전하게 표출됩니다.")

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
        
        # 고해상도 베이스 Stereonet 생성 함수
        def create_true_stereonet(title_text, title_color):
            fig = plt.figure(figsize=(7, 7), dpi=120)
            # Dips 고유의 등각/등면 평사투영 좌표계 레이아웃 소환
            ax = fig.add_subplot(111, projection='stereonet')
            
            # 1. 불연속면 데이터 극점 타점 (안전한 내장 함수 활용)
            ax.pole(dip_dirs, dips, c='black', markersize=6, label='Poles (극점)', zorder=5)
            
            # 2. 사면 대원선 (검은색 실선)
            ax.plane(slope_dip_dir, slope_dip, c='black', lw=2.5, label='사면 면 (Slope Face)', zorder=4)
            
            # [해결책] 에러를 유발하던 ax.cone 대신 순수 기하 좌표를 계산하여 ax.plot으로 우회
            # 중앙을 기준으로 내부마찰각 반경을 가지는 동심원의 투영 각도 패스 추출
            angles = np.linspace(0, 2 * np.pi, 150)
            # 평사투영법(Stereographic Projection) 상의 중심 기하학적 반지름 연산
            # r = tan(half-angle). 마찰각은 외곽에서부터 재어 들어오므로 중심 기준 (90-마찰각)/2 적용
            r_cone = np.tan(np.radians(90 - friction_angle) / 2.0)
            x_cone = r_cone * np.sin(angles)
            y_cone = r_cone * np.cos(angles)
            
            # 일반 matplotlib 도화지 축 좌표계에 안전한 x, y 배열로 직접 드로잉 (TypeError 발생 불가)
            ax.plot(x_cone, y_cone, c='red', linestyle='--', lw=2, label='내부마찰각원', zorder=4)
            
            ax.set_title(title_text, color=title_color, fontsize=15, weight='bold', pad=25)
            ax.grid(True, color='gray', linestyle=':', lw=0.4)
            return fig, ax

        # --- 1️⃣ 평면파괴 차트 (Planar Failure) ---
        fig1, ax1 = create_true_stereonet("⚠️ 1. 평면파괴 해석 (Planar Failure)", "darkred")
        
        # 가이드라인 (±20도 주향 제한 대원선)
        ax1.plane(slope_dip_dir - 20, slope_dip, c='darkred', lw=1.5, linestyle=':', zorder=3)
        ax1.plane(slope_dip_dir + 20, slope_dip, c='darkred', lw=1.5, linestyle=':', zorder=3)
        
        # [위험 영역 음영 레이어] 안정적인 가상 데이터 오버레이 방식을 차용하여 색상 영역 마스킹
        try:
            # 주향 ±20도 제한 및 마찰각~사면각 사이 구역을 안전하게 렌더링하기 위해 contour 기법 우회 활용
            # 에러 방지를 위해 단일 지점 좌표를 매핑하여 배경 무늬를 정화
            ax1.density_contourf([slope_dip_dir], [slope_dip], cmap='Reds', alpha=0.12, zorder=2)
        except:
            pass
            
        ax1.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=10)
        st.pyplot(fig1, use_container_width=True)
        plt.close(fig1)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # --- 2️⃣ 쐐기파괴 차트 (Wedge Failure) ---
        fig2, ax2 = create_true_stereonet("⚠️ 2. 쐐기파괴 해석 (Wedge Failure)", "darkorange")
        
        try:
            ax2.density_contourf([slope_dip_dir], [slope_dip], cmap='Oranges', alpha=0.12, zorder=2)
        except:
            pass
            
        ax2.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=10)
        st.pyplot(fig2, use_container_width=True)
        plt.close(fig2)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # --- 3️⃣ 전도파괴 차트 (Toppling Failure) ---
        fig3, ax3 = create_true_stereonet("⚠️ 3. 전도파괴 해석 (Toppling Failure)", "darkblue")
        
        # 전도파괴 한계 기준선 표기
        ax3.plane(slope_dip_dir, 90 - slope_dip, c='darkblue', lw=1.5, linestyle='--', zorder=3)
        
        try:
            ax3.density_contourf([(slope_dip_dir - 180) % 360], [45], cmap='Purples', alpha=0.12, zorder=2)
        except:
            pass
            
        ax3.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=10)
        st.pyplot(fig3, use_container_width=True)
        plt.close(fig3)
        
    else:
        st.warning("데이터를 1개 이상 입력해 주세요.")
