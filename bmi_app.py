import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --------------------
# 1. 함수 정의 (BMI 계산 및 판정)
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

# --------------------
# 2. 앱 UI (기본 정보 입력)
# --------------------
st.title("📊 BMI 계산기 & 기록 관리")

# 키와 몸무게 입력 (기본값 설정)
height = st.number_input("키 (cm)", min_value=0.0, step=0.1, value=170.0)
weight = st.number_input("현재 몸무게 (kg)", min_value=0.0, step=0.1, value=70.0)

bmi = 0

# --------------------
# 3. BMI 계산 및 데이터 저장
# --------------------
if st.button("BMI 계산 및 저장"):
    if height == 0:
        st.error("키는 0보다 커야 합니다.")
    else:
        bmi = BMI_calc(weight, height)
        status = bmi_status(bmi)

        st.success(f"BMI 지수: {bmi:.1f}")
        st.info(f"판정 결과: {status}")

        # 데이터 저장 로직
        record = {
            "날짜": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "키(cm)": height,
            "몸무게(kg)": weight,
            "BMI": round(bmi, 1),
            "판정": status
        }

        file_name = "bmi_records.csv"

        if os.path.exists(file_name):
            df = pd.read_csv(file_name)
            df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
        else:
            df = pd.DataFrame([record])

        df.to_csv(file_name, index=False, encoding="utf-8-sig")
        st.success("✅ BMI 기록이 저장되었습니다.")

# --------------------
# 4. 저장된 기록 보기 & 그래프
# --------------------
st.divider()
st.subheader("📂 저장된 BMI 기록")

if os.path.exists("bmi_records.csv"):
    df = pd.read_csv("bmi_records.csv")
    df["날짜"] = pd.to_datetime(df["날짜"]) # 날짜 형식 변환
    
    st.dataframe(df) # 표 출력

    st.subheader("📈 BMI 변화 그래프 (날짜별)")
    df_graph = df.set_index("날짜")
    st.line_chart(df_graph["BMI"]) # 그래프 출력
else:
    st.warning("아직 저장된 BMI 기록이 없습니다.")

# ========================================================
# [추가된 기능] 5. 목표 몸무게 시뮬레이터 (BMI 색상 피드백)
# ========================================================
st.divider()
st.subheader("🎯 목표 몸무게 시뮬레이터")

# 키 정보가 있어야 BMI를 예측할 수 있으므로 체크
if height > 0:
    st.caption("슬라이더를 움직여 목표 체중을 설정해보세요. BMI 구간에 따라 색상이 변합니다.")

    # 목표 몸무게 슬라이더 (기본값은 현재 입력된 몸무게로 설정)
    target_weight = st.slider("목표 몸무게 설정 (kg)", min_value=16*(height/100)**2, max_value=weight, value=weight)

    # 목표 체중에 대한 BMI 계산
    target_bmi = target_weight / (height / 100) ** 2
    
    # [수정] bmi -> target_bmi 로 변경
# 18.5 이상(정상~비만)이면 2.0배, 미만(저체중)이면 1.5배
    if target_bmi >= 18.5:
        target_protein = target_weight * 2.0
    else:
        target_protein = target_weight * 1.5

    # ---------------------------
    # 색상 피드백 로직 (핵심 부분)
    # ---------------------------
    # 18.5 ~ 22.9 : 정상 (초록색 success)
    # 23 이상     : 과체중/비만 (빨간색 error)
    # 그 외(저체중): 노란색 warning
    
    if 18.5 <= target_bmi < 23:
        st.success(f"🟢 [정상 범위] 목표 체중 {target_weight}kg의 예상 BMI는 {target_bmi:.1f}입니다.")
        st.success(f"💪 권장 단백질 섭취량: 약 {target_protein:.1f}g")
        
    elif target_bmi >= 23:
        st.error(f"🔴 [비만 주의] 목표 체중 {target_weight}kg의 예상 BMI는 {target_bmi:.1f}입니다. (과체중 이상)")
        st.error(f"💪 권장 단백질 섭취량: 약 {target_protein:.1f}g (체중 조절이 필요할 수 있습니다.)")
        
    else:
        st.warning(f"🟡 [저체중] 목표 체중 {target_weight}kg의 예상 BMI는 {target_bmi:.1f}입니다.")
        st.warning(f"💪 권장 단백질 섭취량: 약 {target_protein:.1f}g (건강한 증량이 필요합니다.)")

else:
    st.warning("☝️ 위에서 '키(cm)'를 먼저 입력해주세요. 그래야 BMI를 분석할 수 있습니다.")