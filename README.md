# Hardware Monitoring Selector

벤더별(BMC) 수집 방식을 선택하는 정적 페이지입니다. 제조사/모델에 따라 Redfish 또는 IPMI를 추천하고, 샘플 명령을 보여줍니다.

## 사용 방법
1) `index.html`을 브라우저로 열어 제조사를 선택합니다.
2) BMC IP와 계정을 입력하면 샘플 Redfish/IPMI 명령이 해당 값으로 자동 채워집니다.

## 컨셉
- 신형/지원 장비: Redfish REST 우선.
- 구형/혼합 환경: IPMI SEL/센서 수집 대체.
- 벤더 확장(iLO/iDRAC/XCC)은 추후 플러그인으로 확장 예정.

## 다음 스텝
- API 서버와 연동해 선택 결과를 저장/배포하도록 연결.
- 장비 등록/인증서 검증 플로우 추가.
- Redfish/Ipmi 호출을 서버에서 실제로 실행하는 모듈을 붙여서 실데이터를 렌더링.

## Backend (FastAPI)
경로: `backend/app/main.py`

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r ../requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

엔드포인트:
- `GET /health`
- `POST /predict` (샘플 위험도 스코어; 실제 모델로 교체 필요)
