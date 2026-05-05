import requests

def test_rag():
    url = "http://localhost:8000/api/chatbot"
    # DB에 있는 코스와 관련된 질문 (예: "남산" 또는 "초보자")
    payload = {
        "message": "초보자가 뛰기 좋은 난이도 하 코스를 알려줘",
        "user_id": 1
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_rag()
