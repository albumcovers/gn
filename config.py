import os

config = {
    "database_password": os.environ.get("DATABASE_PASSWORD"),
    "public_api_key": os.environ.get("PUBLIC_API_KEY"),
    "service_role": os.environ.get("SERVICE_ROLE"),
    "db_url": os.environ.get("DB_URL"),
    "jwt_secret": os.environ.get("JWT_SECRET"),
}

def import_config():
    return config
