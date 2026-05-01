import requests
import json

API_URL = "http://127.0.0.1:8000/api"

# 샘플 크루 데이터
sample_crews = [
    {
        "name": "서울 시티 런 (SCR)",
        "description": "서울의 야경을 즐기며 함께 달리는 크루입니다. 매주 수요일 저녁 8시 반포 한강지구에서 만나요!",
        "image": "https://images.unsplash.com/photo-1552674605-db6ffd4facb5?w=500&q=80"
    },
    {
        "name": "모닝 조깅 클럽",
        "description": "아침 공기를 마시며 활기차게 하루를 시작하는 사람들입니다. 초보자 환영!",
        "image": "https://images.unsplash.com/photo-1476480862126-209bfaa8edc8?w=500&q=80"
    },
    {
        "name": "불광천 거북이들",
        "description": "천천히 오래 달리는 것을 지향합니다. 페이스 상관없이 즐겁게 달려요.",
        "image": "https://images.unsplash.com/photo-1447452030438-65c287a73e4b?w=500&q=80"
    }
]

def seed():
    # 먼저 첫 번째 사용자 ID를 가져옴 (생성자로 등록하기 위함)
    try:
        users_res = requests.get(f"{API_URL}/users")
        if not users_res.ok:
            print("사용자 목록을 가져오는데 실패했습니다.")
            return
        
        users = users_res.json()
        if not users:
            print("등록된 사용자가 없습니다. 먼저 회원가입을 해주세요.")
            return
            
        user_id = users[0]['id']
        
        for crew in sample_crews:
            res = requests.post(f"{API_URL}/crews?user_id={user_id}", json=crew)
            if res.ok:
                print(f"크루 생성 완료: {crew['name']}")
            else:
                print(f"크루 생성 실패: {crew['name']} - {res.text}")
                
    except Exception as e:
        print(f"에러 발생: {e}")

if __name__ == "__main__":
    seed()
