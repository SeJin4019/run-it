import requests
import sys

def test_history():
    url = "http://localhost:8000/api/chatbot"
    history_url = "http://localhost:8000/api/chatbot/history/1"
    
    # 1. 첫 번째 메시지 전송
    print("Sending message 1...", flush=True)
    try:
        r1 = requests.post(url, json={"message": "안녕, 내 이름은 세진이야.", "user_id": 1}, timeout=30)
        print(f"Msg 1 Status: {r1.status_code}", flush=True)
    except Exception as e:
        print(f"Msg 1 Error: {e}", flush=True)
    
    # 2. 두 번째 메시지 전송
    print("Sending message 2...", flush=True)
    try:
        r2 = requests.post(url, json={"message": "내 이름이 뭐라고?", "user_id": 1}, timeout=30)
        print(f"AI Response: {r2.json().get('response', 'Error')}", flush=True)
    except Exception as e:
        print(f"Msg 2 Error: {e}", flush=True)
    
    # 3. 히스토리 조회
    print("\nFetching history...", flush=True)
    try:
        history = requests.get(history_url, timeout=10)
        for m in history.json():
            print(f"[{m['role']}] {m['content']}", flush=True)
    except Exception as e:
        print(f"History Error: {e}", flush=True)

if __name__ == "__main__":
    test_history()
