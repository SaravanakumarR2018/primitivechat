# config.py
import os

# Test token configurations
TEST_TOKEN_PREFIX = "test_"
TEST_SECRET = "test_secret"

# Clerk configurations (example)
CLERK_SECRET_KEY = os.getenv('CLERK_SECRET_KEY')
JWKS_URL = os.getenv('JWKS_URL')
