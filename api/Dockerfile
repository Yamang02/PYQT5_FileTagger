# Python 3.9 버전을 기반 이미지로 사용
FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /usr/src/app

# API 서버에 필요한 라이브러리 목록 복사
# (현재는 비어 있지만, 나중에 FastAPI, Pymongo 등을 추가)
COPY api/requirements.txt ./

# 라이브러리 설치
RUN pip install --no-cache-dir -r requirements.txt

# API 서버 소스 코드 복사
COPY ./api /usr/src/app/api
COPY ./core /usr/src/app/core

# 서버 실행 (예: FastAPI 서버 실행 명령어)
# CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8000"]
