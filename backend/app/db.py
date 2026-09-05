from prisma import Prisma

prisma = Prisma(auto_register=True)

async def get_db() -> Prisma:
    if not prisma.is_connected():
        await prisma.connect()
    return prisma
