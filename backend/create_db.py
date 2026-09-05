import asyncio
import asyncpg

async def main():
    try:
        conn = await asyncpg.connect(
            user="postgres",
            password="admin",
            database="postgres",
            host="127.0.0.1",
            port=5432
        )
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = 'billing_db'")
        if not exists:
            await conn.execute("CREATE DATABASE billing_db;")
            print("Database 'billing_db' created successfully.")
        else:
            print("Database 'billing_db' already exists.")
        await conn.close()
    except Exception as e:
        print(f"Error ensuring database exists: {e}")

if __name__ == "__main__":
    asyncio.run(main())
