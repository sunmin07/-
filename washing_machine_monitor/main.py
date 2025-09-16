import asyncio
from tapo import ApiClient

# --- ❗️여기에 본인의 정보를 입력하세요 ---
TAPO_IP = "172.16.4.90"  # Tapo 플러그의 IP 주소
TAPO_USERNAME = "h92364155@gmail.com"  # Tapo 앱 로그인 이메일
TAPO_PASSWORD = "onetwo02015"      # Tapo 앱 로그인 비밀번호
# ------------------------------------

async def main():
    """Tapo P110M 플러그를 제어하는 메인 함수"""
    print("--- 스크립트 실행 시작 ---")
    try:
        print("1. API 클라이언트 생성 시도...")
        client = ApiClient(TAPO_USERNAME, TAPO_PASSWORD)
        
        print(f"2. 플러그 접속 시도... (IP: {TAPO_IP})")
        p110 = await client.p110(TAPO_IP) # <-- 여기서 멈출 가능성이 높습니다.
        print("3. 플러그 접속 성공!")

        # 1. 플러그 켜기
        print("플러그를 켭니다...")
        await p110.on()
        await asyncio.sleep(2)

        # 2. 현재 전력 사용량 가져오기
        energy_usage = await p110.get_current_power()
        print(f"✅ 현재 전력 사용량: {energy_usage.current_power / 1000} W")
        await asyncio.sleep(2)

        # 3. 플러그 끄기
        print("플러그를 끕니다...")
        await p110.off()

    except Exception as e:
        print(f"🛑 오류가 발생했습니다: {e}")
    
    print("--- 스크립트 실행 종료 ---")


if __name__ == "__main__":
    asyncio.run(main())