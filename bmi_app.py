import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --------------------
# 1. 페이지 설정
# --------------------
st.set_page_config(layout="wide", page_title="개인 건강 대시보드")

# --------------------
# 2. 함수 정의 (BMI 계산, 판정, 저장)
# --------------------
def BMI_calc(weight, height):
    return weight / (height / 100) ** 2

def bmi_status(bmi):
    if bmi < 18.5:
        return "저체중"
    elif bmi < 23:
        return "정상체중"
    elif bmi < 25:
        return "과체중"
    elif bmi < 30:
        return "1단계 비만"
    elif bmi < 35:
        return "2단계 비만"
    else:
        return "고도비만"

def save_to_csv(filename, record_data):
    if os.path.exists(filename):
        df = pd.read_csv(filename)
        df = pd.concat([df, pd.DataFrame([record_data])], ignore_index=True)
    else:
        df = pd.DataFrame([record_data])
    # 한글 깨짐 방지를 위해 utf-8-sig 인코딩 사용
    df.to_csv(filename, index=False, encoding="utf-8-sig")

# --------------------
# 3. 사이드바 UI (모든 입력은 여기서!)
# --------------------
with st.sidebar:
    st.header("👤 개인정보")
    
    user_name = st.text_input("이름", placeholder="이름을 입력하세요")
    
    # [입력창 통합] 키와 몸무게는 사이드바에서만 받습니다.
    height = st.number_input("키 (cm)", min_value=0.0, step=0.1, value=170.0)
    weight = st.number_input("몸무게 (kg)", min_value=0.0, step=0.1, value=70.0)
    
    target_bmi_input = st.number_input("🎯 목표 BMI", min_value=10.0, step=0.1, value=22.0)

    st.markdown("---")

    st.header("🚶 신체 정보")
    gender = st.radio("성별", ["남성", "여성"])
    age = st.number_input("나이", min_value=0, max_value=120, value=30)
    activity_level = st.selectbox("활동량", [
        "거의 없음 (운동 안함)",
        "조금 있음 (주 1-3회)",
        "보통 (주 3-5회)",
        "많음 (주 6-7회)",
        "매우 많음 (육체 노동 등)"
    ])
    
    st.markdown("---")
    
    # 저장 버튼
    save_btn = st.button("➕ BMI 기록 저장", type="primary")

# --------------------
# 4. 메인 화면 구성
# --------------------
st.title("📊 BMI 계산기 및 기록 관리")

# [수정 완료] 메인 화면에 있던 불필요한 입력창들을 모두 삭제했습니다.
if not user_name:
    st.info("👈 왼쪽 사이드바에서 사용자 정보를 입력해 주세요.")
else:
    st.success(f"반갑습니다, **{user_name}**님! 건강 관리를 시작해보세요.")

# --------------------
# 5. 데이터 저장 및 처리 로직
# --------------------
target_file = "bmi_records.csv"

if save_btn:
    if height > 0 and weight > 0 and user_name:
        current_bmi = BMI_calc(weight, height)
        status = bmi_status(current_bmi)

        # 저장할 데이터
        record = {
            "날짜": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "이름": user_name,
            "성별": gender,
            "나이": age,
            "키(cm)": height,
            "몸무게(kg)": weight,
            "BMI": round(current_bmi, 1),
            "판정": status,
            "목표BMI": target_bmi_input,
            "활동량": activity_level
        }
        
        # 파일 저장
        save_to_csv(target_file, record)
        
        st.toast(f"✅ 기록 저장 완료! (BMI: {current_bmi:.1f})") # 알림 메시지
    else:
        st.error("⚠️ 이름, 키, 몸무게를 모두 입력해주세요.")

# --------------------
# 6. 저장된 기록 보기 (표 & 그래프)
# --------------------
st.divider()
# --------------------
# 6. 저장된 기록 보기 (표 & 그래프)
# --------------------
st.divider()
st.subheader("📂 저장된 BMI 기록")

col1, col2 = st.columns([1, 1])

if os.path.exists(target_file):
    df = pd.read_csv(target_file)
    
    if not df.empty:
        df["날짜"] = pd.to_datetime(df["날짜"])
        
        with col1:
            # 최근 기록 표 (위에서부터 최신순)
            available_cols = [col for col in df.columns if col in ["날짜", "이름", "키(cm)", "몸무게(kg)", "BMI", "판정"]]
            if available_cols:
                st.dataframe(df[available_cols].sort_values(by="날짜", ascending=False).head(10), use_container_width=True)

        with col2:
            # 그래프
            st.caption("📈 BMI 변화 추이")
            if user_name and '이름' in df.columns:
                user_df = df[df['이름'] == user_name]
                if not user_df.empty:
                    st.line_chart(user_df.set_index("날짜")["BMI"])
                else:
                    st.line_chart(df.set_index("날짜")["BMI"])
            else:
                st.line_chart(df.set_index("날짜")["BMI"])
    else:
        st.info("아직 저장된 기록이 없습니다.")
else:
    st.info("아직 저장된 기록이 없습니다.")
# --------------------
# 7. 목표 몸무게 시뮬레이터 (요청하신 디자인 적용)
# --------------------
st.divider()
st.subheader("🎯 목표 몸무게 시뮬레이터")

if height > 0:
    st.caption("슬라이더를 움직여 목표 체중을 설정해보세요. BMI 구간에 따라 색상이 변합니다.")

    # 슬라이더 (기본값은 현재 몸무게)
    target_weight = st.slider("목표 몸무게 설정 (kg)", min_value=17.5*height**2/10000, max_value=weight, value=weight)

    # 목표 BMI 계산
    target_bmi_sim = target_weight / (height / 100) ** 2
    
    # 단백질 및 팁 설정
    if target_bmi_sim >= 18.5:
        protein_multiplier = 2.0
        nutrition_tip = "근육량 증가/유지를 위해 **고단백 식단** 추천"
    else:
        protein_multiplier = 1.5
        nutrition_tip = "건강한 증량을 위해 **탄수화물 섭취 비중 늘리기**"

    target_protein = target_weight * protein_multiplier

    # [디자인 적용] 상태에 따른 색상 박스 출력
    if target_bmi_sim < 18.5:
        # 저체중 (노랑)
        st.warning(f"🟡 [저체중] 목표 체중 {target_weight}kg의 예상 BMI는 {target_bmi_sim:.1f}입니다.")
        st.info(f"💪 {nutrition_tip} (권장 단백질: 약 {target_protein:.1f}g)")
        
    elif 18.5 <= target_bmi_sim < 23:
        # 정상 (초록)
        st.success(f"🟢 [정상 범위] 목표 체중 {target_weight}kg의 예상 BMI는 {target_bmi_sim:.1f}입니다.")
        st.success(f"💪 {nutrition_tip} (권장 단백질: 약 {target_protein:.1f}g)")
        
    else:
        # 과체중/비만 (빨강)
        st.error(f"🔴 [과체중/비만] 목표 체중 {target_weight}kg의 예상 BMI는 {target_bmi_sim:.1f}입니다.")
        st.error(f"💪 {nutrition_tip} (권장 단백질: 약 {target_protein:.1f}g)")

else:
    st.warning("👈 시뮬레이터를 사용하려면 왼쪽 사이드바에서 '키(cm)'를 입력해주세요.")