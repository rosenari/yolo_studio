from sqlalchemy.ext.asyncio import AsyncSession
import inspect


# 파일 크기를 적절한 단위(byte, KB, MB, GB)로 변환
def format_file_size(size_in_bytes: int) -> str:
        if size_in_bytes < 1024:
            return f"{size_in_bytes} B"
        elif size_in_bytes < 1024 ** 2:
            return f"{size_in_bytes / 1024:.2f} KB"
        elif size_in_bytes < 1024 ** 3:
            return f"{size_in_bytes / (1024 ** 2):.2f} MB"
        else:
            return f"{size_in_bytes / (1024 ** 3):.2f} GB"
        


def transactional(func):
    async def wrapper(self, *args, **kwargs):
        # self 객체에서 AsyncSession 타입의 속성을 찾음
        session = next(
            (value for _, value in inspect.getmembers(self) if isinstance(value, AsyncSession)),
            None
        )

        if session is None:
            raise ValueError("AsyncSession 타입의 세션이 제공되지 않았습니다.")

        if session.in_transaction():
            return await func(self, *args, **kwargs)

        async with session.begin():
            try:
                return await func(self, *args, **kwargs)
            except Exception:
                await session.rollback()
                raise

    return wrapper