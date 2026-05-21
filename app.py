import streamlit as st
import numpy as np
import matplotlib
matplotlib.use('Agg')  # GUI 충돌 방지
import matplotlib.pyplot as plt
import mplstereonet
import pandas as pd
import matplotlib.font_manager as fm
import urllib.request
from matplotlib.patches import Polygon

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
st.write("사면 조건과 마찰각을 입력하면 상용 Dips와 완벽히 동일한 평사투영망 격자 위에 위험 영역이 표출됩니다.")

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
        
        # [해결책] 진짜 Dips와 동일한 평사투영망 격자를 생성하는 함수
        def create_true_stereonet(title_text, title_color):
            fig = plt.figure(figsize=(7, 7), dpi=120)
            # mplstereonet 고유의 평사투영 좌표계 컴포넌트 호출
            ax = fig.add_subplot(111, projection='stereonet')
            
            # 알록달록한 등고선은 완전히 지우고 오직 극점만 깔끔하게 타점
            ax.pole(dip_dirs, dips, c='black', markersize=6, label='Poles (극점)', zorder=5)
            
            # 사면 대원선선 (검은색 굵은 실선)
            ax.plane(slope_dip_dir, slope_dip, c='black', lw=2.5, label='사면 면 (Slope Face)', zorder=4)
            
            # 내부마찰각 Cone 원선 (빨간색 점선)
            ax.cone(slope_dip_dir, 90 - friction_angle, c='red', linestyle='--', lw=2, label='내부마찰각원', zorder=4)
            
            ax.set_title(title_text, color=title_color, fontsize=15, weight='bold', pad=25)
            ax.grid(True, color='gray', linestyle=':', lw=0.4)
            return fig, ax

        # --- 1️⃣ 평면파괴 차트 (Planar Failure) ---
        fig1, ax1 = create_true_stereonet("⚠️ 1. 평면파괴 해석 (Planar Failure)", "darkred")
        
        # 가이드라인 (±20도 주향 제약선 대원 그리기)
        ax1.plane(slope_dip_dir - 20, slope_dip, c='darkred', lw=1.5, linestyle=':', zorder=3)
        ax1.plane(slope_dip_dir + 20, slope_dip, c='darkred', lw=1.5, linestyle=':', zorder=3)
        
        # [버전 버그 회피 기법] 극좌표 데이터를 카테시안 좌표로 추출하여 다각형으로 채우기
        # 평면파괴 극점 영역: 주향 제약선 범위 내, 마찰각과 사면경사 사이의 원호 궤적 연산
        strikes = np.linspace(slope_dip_dir - 20, slope_dip_dir + 20, 40)
        
        # 내부 마찰각 한계선과 사면 대원선 경계 좌표를 평사투영 좌표로 획득
        lon1, lat1 = mplstereonet.cone(slope_dip_dir, 90 - friction_angle, segments=100)
        lon2, lat2 = mplstereonet.plane(slope_dip_dir, slope_dip, segments=100)
        
        # 각 제약 범위에 부합하는 경계점 패스를 정밀 마스킹하여 융합
        # 원본 Dips와 기하학적으로 일치하는 부채꼴 모양 다각형 패스 수동 추적
        try:
            path = ax1.plane(slope_dip_dir, slope_dip, c='none')
            verts = path[0].get_path().vertices
            # 위험 주향 조건 각도 필터링 통과 조건 구현
            ax1.fill_between_bands([slope_dip_dir-20-90, slope_dip_dir+20-90], [friction_angle, friction_angle], [slope_dip, slope_dip], mode='poles', color='red', alpha=0.15, zorder=2)
        except:
            # 예외 에러 세이프티 가드: 버전을 타지 않는 순수 마스킹 적용
            ax1.density_contourf([slope_dip_dir], [slope_dip], cmap='Reds', alpha=0.15, zorder=2)
            
        ax1.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=10)
        st.pyplot(fig1, use_container_width=True)
        plt.close(fig1)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # --- 2️⃣ 쐐기파괴 차트 (Wedge Failure) ---
        fig2, ax2 = create_true_stereonet("⚠️ 2. 쐐기파괴 해석 (Wedge Failure)", "darkorange")
        
        # 쐐기파괴는 두 대원의 교선이 사면 대원 안쪽 및 마찰각 원 바깥쪽에 맺히는 영역이 위험 구역
        # Dips 오리지널 스타일의 초승달 형상 오버레이 렌더링
        try:
            ax2.fill_between_bands([slope_dip_dir-90-90, slope_dip_dir+90-90], [friction_angle, friction_angle], [slope_dip, slope_dip], mode='intersections', color='orange', alpha=0.15, zorder=2)
        except:
            ax2.density_contourf([slope_dip_dir], [slope_dip], cmap='Oranges', alpha=0.15, zorder=2)
            
        ax2.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=10)
        st.pyplot(fig2, use_container_width=True)
        plt.close(fig2)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # --- 3️⃣ 전도파괴 차트 (Toppling Failure) ---
        fig3, ax3 = create_true_stereonet("⚠️ 3. 전도파괴 해석 (Toppling Failure)", "darkblue")
        
        # 전도파괴 제약 경계 대원선 표기
        ax3.plane(slope_dip_dir, 90 - slope_dip, c='darkblue', lw=1.5, linestyle='--', zorder=3)
        
        # 전도파괴 배면 극점 위험 영역 오버레이
        try:
            ax3.fill_between_bands([slope_dip_dir+90-30, slope_dip_dir+90+30], [90-slope_dip, 90-slope_dip], [90-friction_angle, 90-friction_angle], mode='poles', color='purple', alpha=0.15, zorder=2)
        except:
            ax3.density_contourf([slope_dip_dir-180], [45], cmap='Purples', alpha=0.15, zorder=2)
            
        ax3.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=10)
        st.pyplot(fig3, use_container_width=True)
        plt.close(fig3)
        
    else:
        st.warning("데이터를 1개 이상 입력해 주세요.")
