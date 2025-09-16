import asyncio
from flask import Flask, render_template, jsonify
from tapo import ApiClient
import time
from collections import deque

app = Flask(__name__)

# --- ❗️여기에 본인의 정보를 입력하세요 ---
TAPO_IP = "172.16.4.90"  # Tapo 플러그의 IP 주소
TAPO_USERNAME = "h92364155@gmail.com"  # Tapo 앱 로그인 이메일
TAPO_PASSWORD = "onetwo02015"      # Tapo 앱 로그인 비밀번호
# ------------------------------------

# --- '켜짐' 상태를 판단할 최소 전력 기준 (단위: W) ---
# ✨ 크롬북 충전함의 전력량(0.013W)에 맞춰 기준값을 0.01W로 대폭 낮췄습니다.
ON_THRESHOLD = 0.01
# ---------------------------------------------------

# 그래프 데이터 저장을 위한 변수
power_data_history = deque(maxlen=60)
time_labels_history = deque(maxlen=60)

async def get_plug_status():
    """Tapo 플러그의 전력량을 기반으로 '켜짐' 또는 '꺼짐' 상태를 반환합니다."""
    try:
        client = ApiClient(TAPO_USERNAME, TAPO_PASSWORD)
        p110 = await client.p110(TAPO_IP)
        
        energy_data = await p110.get_current_power()
        current_power = energy_data.current_power / 1000.0

        # 디버그용 print는 이제 필요 없으므로 주석 처리하거나 삭제합니다.
        # print(f"--- [디버그] 현재 측정된 전력: {current_power:.4f} W ---")

        status_text = ""
        # 전력 소모량이 기준치보다 높으면 '켜짐', 아니면 '꺼짐'
        if current_power > ON_THRESHOLD:
            status_text = "켜짐"
        else:
            status_text = "꺼짐"
        
        # 그래프 데이터 기록
        current_time = time.strftime("%H:%M:%S")
        power_data_history.append(current_power)
        time_labels_history.append(current_time)

        return {
            "status": status_text,
            "power": f"{current_power:.2f} W"
        }

    except Exception as e:
        print(f"🛑 오류 발생: {e}")
        return {"status": "연결 오류", "power": "플러그 연결 상태 확인"}


@app.route('/')
def index():
    """메인 페이지를 렌더링합니다."""
    return render_template('index.html')

@app.route('/status')
def status():
    """실시간 상태 정보를 JSON 형태로 반환합니다."""
    current_status = asyncio.run(get_plug_status())
    
    current_status['graph_labels'] = list(time_labels_history)
    current_status['graph_data'] = list(power_data_history)
    
    return jsonify(current_status)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)