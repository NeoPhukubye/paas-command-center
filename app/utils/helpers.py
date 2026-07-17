from fastapi import HTTPException
from app.config import settings

try:
    import snowflake.connector
    HAS_SNOWFLAKE = True
except ImportError:
    HAS_SNOWFLAKE = False

from cryptography.hazmat.primitives import serialization


def _get_private_key_bytes():
    """Parse the PEM private key from the SNOWFLAKE_PRIVATE_KEY env var."""
    key_data = settings.SNOWFLAKE_PRIVATE_KEY
    if not key_data:
        return None
    # Render env vars replace newlines with literal \n
    key_data = key_data.replace("\\n", "\n")
    p_key = serialization.load_pem_private_key(key_data.encode(), password=None)
    return p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def get_connection():
    if not HAS_SNOWFLAKE:
        raise HTTPException(status_code=503, detail="snowflake-connector-python not installed")
    if not settings.SNOWFLAKE_ACCOUNT:
        raise HTTPException(status_code=503, detail="Snowflake credentials not configured")

    private_key_bytes = _get_private_key_bytes()

    if private_key_bytes:
        return snowflake.connector.connect(
            account=settings.SNOWFLAKE_ACCOUNT,
            user=settings.SNOWFLAKE_USER,
            private_key=private_key_bytes,
            warehouse=settings.SNOWFLAKE_WAREHOUSE,
            database=settings.SNOWFLAKE_DATABASE,
            schema=settings.SNOWFLAKE_SCHEMA,
            role=settings.SNOWFLAKE_ROLE,
        )
    else:
        return snowflake.connector.connect(
            account=settings.SNOWFLAKE_ACCOUNT,
            user=settings.SNOWFLAKE_USER,
            password=settings.SNOWFLAKE_PASSWORD,
            warehouse=settings.SNOWFLAKE_WAREHOUSE,
            database=settings.SNOWFLAKE_DATABASE,
            schema=settings.SNOWFLAKE_SCHEMA,
            role=settings.SNOWFLAKE_ROLE,
        )


def query(sql: str, params: tuple = ()) -> list[dict]:
    try:
        conn = get_connection()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        columns = [desc[0].lower() for desc in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()
