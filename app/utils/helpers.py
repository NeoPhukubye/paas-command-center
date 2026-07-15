import snowflake.connector
from fastapi import HTTPException
from app.config import settings


def get_connection():
    if not settings.SNOWFLAKE_ACCOUNT:
        raise HTTPException(status_code=503, detail="Snowflake credentials not configured")
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
