import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import mplstereonet
import pandas as pd

# 1. 웹 페이지 제목 및 레이아웃 설정
st.set_page_config(layout="wide", page_title="모바일/웹 Dips 분석기")
st.title("🌋 Web-based Dips Stereonet Analysis")
st.write("인터넷 창에서 불연속면 데이터를 입력하고 Dips와 동일한 등고선 플롯을 확인하세요.")

# 화면을 좌우로 분할 (좌측: 입력 데이터, 우측: Dips 결과 차트)
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📋 불연속면 데이터 입력")
    st.info("💡 아래 표에 데이터를 직접 입력하거나, 엑셀 데이터를 붙여넣으세요.")
    
    # 초기에 보여줄 샘플 데이터 구조 정의
    default_data = {
        "Dip Direction (경사방향)": [135, 140, 130, 315, 320, 210, 145, 125, 310],
        "Dip (경사)": [45, 48, 42, 60, 62, 30, 47, 40, 58]
    }
    df = pd.DataFrame(default_data)
    
    # 엑셀 스타일의 라이브 입력 편집기 제공 (인터넷 창에서 행 추가/삭제 가능)
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)

with col2:
    st.subheader("📊 Dips Contour Plot 결과")
    
    # 입력된 데이터 추출
    # 수정 후 코드 (이걸로 바꾸어 붙여넣으세요)
dip_dirs = pd.to_numeric(edited_df.iloc[:, 0]).dropna().to_numpy()
dips = pd.to_numeric(edited_df.iloc[:, 1]).dropna().to_numpy()
    
    if len(dip_dirs) > 0 and len(dips) > 0:
        # matplotlib 플롯 생성 시 폰트 깨짐 방지 및 크기 설정
        fig = plt.figure(figsize=(6, 6))
        ax = fig.add_subplot(111, projection='stereonet')
        
        try:
            # 1. Dips 스타일 알록달록한 밀도 등고선 채우기 (Jet 테마)
            ax.density_contourf(dip_dirs, dips, cmap='jet', alpha=0.8)
            ax.density_contour(dip_dirs, dips, colors='black', linewidths=0.5)
            
            # 2. 극점(Pole Plot) 타점
            ax.pole(dip_dirs, dips, c='black', markersize=5, label='Poles')
            
            # 3. 격자망 및 스타일링
            ax.grid(True, color='lightgray', linestyle=':')
            
            # 인터넷 창에 그래프 출력
            st.pyplot(fig)
            
            # 이미지 다운로드 버튼 제공
            plt.savefig("dips_output.png", bbox_inches='tight', dpi=300)
            with open("dips_output.png", "rb") as file:
                st.download_button(
                    label="💾 Dips 차트 이미지 다운로드",
                    data=file,
                    file_name="dips_stereonet.png",
                    mime="image/png"
                )
        except Exception as e:
            st.error(f"계산 오류: 입력 데이터를 확인해 주세요. ({e})")
    else:
        st.warning("데이터를 1개 이상 입력해 주세요.")
