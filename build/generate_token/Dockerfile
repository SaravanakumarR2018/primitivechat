FROM python:3.9-slim

WORKDIR /app

COPY build/generate_token/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-c", "import sys; from api_utils import create_test_token; print(create_test_token(sys.argv[1], sys.argv[2]))", "--", "$ORG_ID", "$ORG_ROLE"] 