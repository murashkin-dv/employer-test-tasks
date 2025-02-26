import datetime
import logging

from sqlalchemy import (Column, DateTime, Integer, String, create_engine, func,
                        or_, select)
from sqlalchemy.orm import declarative_base, sessionmaker
from starlette.responses import JSONResponse

# Настройка логирования
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Настройка базы данных
DATABASE_URL = "sqlite:///./database/telegram_summary.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Subscribers(Base):
    __tablename__ = "subscribers"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=True)
    channel_id = Column(String(50))
    date_created = Column(DateTime, default=func.now())
    last_sent = Column(DateTime, nullable=True)

    @classmethod
    def get_subscription_by_user_channel(
        cls, session: SessionLocal, user_id: int, channexl_id: str
    ):
        try:
            query = session.execute(
                select(Subscribers).filter(
                    Subscribers.user_id == user_id, Subscribers.channel_id == channel_id
                )
            )
            user_subs = query.one()
            if user_subs is not None:
                return {"result": True, "user_subs": user_subs.to_dict}
            else:
                return {"result": False, "message": "Подписка не найдена"}
        except Exception as e:
            return JSONResponse(
                {"result": False, "message": f"Ошибка: {e}"}, status_code=400
            )

    @classmethod
    def create_subscription(cls, session: SessionLocal, user_id: int, channel_id: str):
        """create new subscription"""
        try:
            new_subscription = Subscribers(user_id=user_id, channel_id=channel_id)
            session.add(new_subscription)
            session.commit()
            return JSONResponse(
                {
                    "result": True,
                    "message": f"Вы подписались на канал {channel_id}",
                },
                status_code=201,
            )
        except Exception as e:
            return JSONResponse(
                {"result": False, "message": f"Ошибка: {e}"}, status_code=400
            )

    @classmethod
    def toggle_subscription(cls, session: SessionLocal, user_id: int, channel_id: str):
        """toggle subscription: create or delete"""
        try:
            # get a record
            query = session.execute(
                select(Subscribers).filter(
                    Subscribers.user_id == user_id, Subscribers.channel_id == channel_id
                )
            )
            user_sub = query.scalar_one_or_none()
            if user_sub:
                # delete subscription if found
                session.delete(user_sub)
                session.commit()
                return JSONResponse(
                    {
                        "result": True,
                        "message": f"Вы отписались от канала {channel_id}",
                    },
                    status_code=200,
                )
            else:
                # create subscription
                return cls.create_subscription(session, user_id, channel_id)

        except Exception as e:
            return JSONResponse(
                {"result": False, "message": f"Ошибка: {e}"}, status_code=400
            )

    @classmethod
    def get_active_subscriptions(cls, _session: SessionLocal):
        """Получаем список подписчиков и каналов, которым нужно отправить обобщение"""
        try:
            yesterday = datetime.datetime.now(
                datetime.timezone.utc
            ) - datetime.timedelta(days=1)
            query = _session.execute(
                select(Subscribers.user_id, Subscribers.channel_id).filter(
                    or_(
                        Subscribers.last_sent is None, Subscribers.last_sent < yesterday
                    )
                )
            )
            result = query.all()
            logger.info("! %s ", result)
            return result
        except Exception as e:
            logger.error(f"Ошибка при получении активных подписок: {e}")
            return []
