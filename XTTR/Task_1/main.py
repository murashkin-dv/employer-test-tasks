import datetime
import logging
import os
from typing import List

import nest_asyncio
import openai
import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse
from telethon import TelegramClient, functions, types
from telethon.sessions import StringSession

from database import Base, SessionLocal, Subscribers, engine
from services import summarize_text

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Настройка OpenAI
# API информация (использованы переменные окружения для безопасности)
API_ID = int(os.getenv("TELEGRAM_API_ID", "111111"))  # Преобразование в integer
API_HASH = os.getenv("TELEGRAM_API_HASH", "111111111")
openai.api_key = os.getenv("OPENAI_API_KEY", "111111")

# Создание всех таблиц в базе данных
Base.metadata.create_all(bind=engine)

# Инициализация планировщика для отсылки сообщений
scheduler = AsyncIOScheduler()

# Настройка клиента Telegram
client = TelegramClient("user", API_ID, API_HASH)


# Настройка планировщика
async def lifespan(_app: FastAPI):
    scheduler.add_job(
        send_summaries, "interval", seconds=10
    )  # Запускать каждые 10 секунд
    scheduler.start()
    logger.info("Планировщик задач запущен.")
    yield
    scheduler.shutdown()
    logger.info("Планировщик задач остановлен.")


# Настройка FastAPI
app = FastAPI(
    lifespan=lifespan,
)

# Добавление Middleware для сессий
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY", "your_default_secret_key"),
)

# Настройка шаблонов
templates = Jinja2Templates(directory="templates")

# Подключение статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")


# Pydantic модели (при необходимости)
class ChannelInfo(BaseModel):
    channel_link: str


# Сессия для базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(request: Request) -> TelegramClient | None:
    """Функция для получения текущего пользователя из сессии"""
    session_str = request.session.get("session_str")
    if not session_str:
        return None
    try:
        logger.debug(f"Session String in FastAPI: {session_str}")
        user_client = TelegramClient(StringSession(session_str), API_ID, API_HASH)

        # Регистрация Handlers для пользователя - должна быть здесь (при необходимости)

        await user_client.connect()
        if not await user_client.is_user_authorized():
            logger.warning("User is not authorized.")
            return None
        return user_client
    except Exception as e:
        logger.error(f"Authorization Error: {e}")
        return None


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Главная страница"""
    user_client = await get_current_user(request)
    if user_client:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/authenticate", response_class=HTMLResponse)
async def authenticate_form(request: Request):
    """Страница авторизации - ввод номера телефона"""
    return templates.TemplateResponse(
        "authenticate.html", {"request": request, "message": ""}
    )


@app.post("/authenticate", response_class=HTMLResponse)
async def authenticate_submit(request: Request, phone_number: str = Form(...)):
    """Обработка ввода номера телефона и отправка кода подтверждения"""
    user_client = TelegramClient(StringSession(), API_ID, API_HASH)
    await user_client.connect()
    try:
        # Отправка запроса на код подтверждения и получение phone_code_hash
        send_code_response = await user_client(
            functions.auth.SendCodeRequest(
                phone_number=phone_number,
                api_id=API_ID,
                api_hash=API_HASH,
                settings=types.CodeSettings(),
            )
        )

        # Сохранение временной сессии, номера телефона и phone_code_hash в сессии
        # пользователя
        request.session["temp_session"] = getattr(user_client, "session").save()
        request.session["phone_number"] = phone_number
        request.session["phone_code_hash"] = send_code_response.phone_code_hash

        await user_client.disconnect()
        return RedirectResponse(url="/complete-login", status_code=303)
    except Exception as e:
        await user_client.disconnect()
        logger.error(f"Ошибка при отправке кода подтверждения: {e}")
        return templates.TemplateResponse(
            "authenticate.html", {"request": request, "message": f"Ошибка: {e}"}
        )


@app.get("/complete-login", response_class=HTMLResponse)
async def complete_login_form(request: Request):
    """Страница ввода кода подтверждения"""
    temp_session = request.session.get("temp_session")
    phone_number = request.session.get("phone_number")
    if not temp_session or not phone_number:
        return RedirectResponse(url="/authenticate")
    return templates.TemplateResponse(
        "complete_login.html", {"request": request, "message": ""}
    )


@app.post("/complete-login", response_class=HTMLResponse)
async def complete_login_submit(request: Request, code: str = Form(...)):
    """Обработка ввода кода подтверждения"""
    temp_session = request.session.get("temp_session")
    phone_number = request.session.get("phone_number")
    phone_code_hash = request.session.get("phone_code_hash")

    if not temp_session or not phone_number or not phone_code_hash:
        return RedirectResponse(url="/authenticate")

    user_client = TelegramClient(StringSession(temp_session), API_ID, API_HASH)

    await user_client.connect()
    try:
        # Завершение авторизации с использованием phone_code_hash
        await user_client.sign_in(phone_number, code, phone_code_hash=phone_code_hash)

        session_str = getattr(user_client, "session").save()

        # Сохранение строки сессии в сессии пользователя
        request.session["session_str"] = session_str

        # Очистка временных данных
        request.session.pop("temp_session", None)
        request.session.pop("phone_number", None)
        request.session.pop("phone_code_hash", None)

        await user_client.disconnect()
        logger.info("Пользователь успешно авторизовался.")
        return RedirectResponse(url="/dashboard", status_code=303)
    except Exception as e:
        await user_client.disconnect()
        logger.error(f"Ошибка при завершении авторизации: {e}")
        return templates.TemplateResponse(
            "complete_login.html", {"request": request, "message": f"Ошибка: {e}"}
        )


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Основная страница панели управления"""
    user_client = await get_current_user(request)
    user_me = await user_client.get_me()

    if not user_client:
        return RedirectResponse(url="/authenticate")

    all_resources: List[dict] = list()
    all_resources_sorted: List[dict] = list()

    # Получение списка всех чатов
    try:
        dialogs = await user_client.get_dialogs()
        all_chats = [dialog for dialog in dialogs if dialog.is_user]
        logger.info(f"Найдено {len(all_chats)} чатов.")
    except Exception as e:
        all_chats = []
        logger.error(f"Ошибка при получении чатов: {e}")

    # Получение списка всех групповых публичных чатов
    try:
        dialogs = await user_client.get_dialogs()
        all_group_chats = [
            dialog.entity.username
            for dialog in dialogs
            if dialog.is_channel and dialog.entity.broadcast is False
        ]

        logger.info(f"Найдено {len(all_group_chats)} групповых чатов.")
    except Exception as e:
        all_group_chats = []
        logger.error(f"Ошибка при получении групповых чатов: {e}")

    # Получение списка всех каналов
    try:
        dialogs = await user_client.get_dialogs()
        all_channels = [
            dialog.entity.username
            for dialog in dialogs
            if dialog.is_channel and dialog.entity.username and dialog.entity.broadcast
        ]
        logger.info(f"Найдено {len(all_channels)} каналов.")
    except Exception as e:
        all_channels = []
        logger.error(f"Ошибка при получении каналов: {e}")

    # Получение существующих папок (фильтров диалогов)
    try:
        # Обновление кэша диалогов
        await user_client.get_dialogs()

        dialog_filters = await user_client(functions.messages.GetDialogFiltersRequest())
        existing_filters = dialog_filters.filters
        logger.info(f"Получено {len(existing_filters)} фильтров диалогов.")
    except Exception as e:
        existing_filters = []
        logger.error(f"Ошибка при получении фильтров диалогов: {e}")

    # Создание списка групп с их каналами
    groups_with_channels = []

    for dialog_filter in existing_filters:

        group_chats = []
        group_group_chats = []
        group_channels = []

        filter_title = getattr(
            dialog_filter,
            "title",
            f"Фильтр {getattr(dialog_filter, 'id', 'unknown or default')}",
        )
        include_peers = getattr(dialog_filter, "include_peers", [])
        logger.info(
            f"Фильтр: {filter_title}, количество include_peers: "
            f"{len(include_peers)}"
        )

        for included_peer in include_peers:
            try:
                if isinstance(included_peer, types.InputPeerChannel):
                    channel_id = included_peer.channel_id
                    entity = await user_client.get_entity(channel_id)

                    # Преобразуем entity в InputChannel
                    input_channel = types.InputChannel(entity.id, entity.access_hash)

                    # Получаем полную информацию о канале/группе
                    full_channel = await user_client(
                        functions.channels.GetFullChannelRequest(channel=input_channel)
                    )

                    # количество подписчиков/участников группы
                    participants_count = full_channel.full_chat.participants_count

                    # количество непрочитанных сообщений
                    unread_count = await get_unread_message_count(
                        user_client, entity.id
                    )

                    if isinstance(entity, types.Channel):
                        if entity.broadcast is True:
                            # Каналы
                            if entity.username:
                                title = f"{entity.username}"
                            else:
                                title = f"{entity.title} (ID: {entity.id})"

                            group_channels.append(title)
                            all_resources.append(
                                {
                                    "type": "channel",
                                    "title": title,
                                    "unread_count": unread_count,
                                    "participants_count": participants_count,
                                }
                            )

                        else:
                            # Публичные групповые чаты
                            if entity.username:
                                title = f"{entity.username}"
                            else:
                                title = f"{entity.title} (ID: {entity.id})"
                                group_group_chats.append(title)

                            group_group_chats.append(title)
                            all_resources.append(
                                {
                                    "type": "public group chat",
                                    "title": title,
                                    "unread_count": unread_count,
                                    "participants_count": participants_count,
                                }
                            )

                elif isinstance(included_peer, types.InputPeerUser):
                    user_id = included_peer.user_id
                    entity = await user_client.get_entity(user_id)

                    # количество непрочитанных сообщений
                    unread_count = await get_unread_message_count(
                        user_client, entity.id
                    )

                    # количество участников всегда 2 для чата 1 на 1
                    participants_count = 2

                    # Публичные чаты
                    if isinstance(entity, types.User):
                        name_draft = (
                            f"{entity.first_name or ''} " f"{entity.last_name or ''}"
                        ).strip()
                        name = f"{name_draft} (ID: {entity.id})"

                        group_chats.append((entity.username, name))

                        all_resources.append(
                            {
                                "type": "public chat",
                                "title": (
                                    entity.username,
                                    f"{name} (@{entity.username})",
                                ),
                                "unread_count": unread_count,
                                "participants_count": participants_count,
                            }
                        )

                else:
                    logger.info(f"Неизвестный тип peer: {included_peer}")
            except Exception as e:
                logger.error(f"Ошибка при обработке peer {included_peer}: {e}")
                continue

        # Сортируем сначала по участникам, затем по непрочитанным
        all_resources_sorted = sorted(
            all_resources,
            key=lambda chat: (chat["unread_count"], chat["participants_count"]),
            reverse=True,
        )

        groups_with_channels.append(
            {
                "filter_name": filter_title,
                "channels": group_channels,
                "chats": group_chats,
                "group_chats": group_group_chats,
            }
        )

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user_me": user_me.first_name,
            # сортированный список всех ресурсов:
            "all_resources": all_resources_sorted,
            # публичные чаты:
            "chats": all_chats,
            # публичные групповые чаты:
            "group_chats": all_group_chats,
            # каналы:
            "channels": all_channels,
            # папки с каналами:
            "groups": groups_with_channels,
            # папки пользователя:
            "filters": existing_filters,
            "message": "",
        },
    )


@app.get("/last-messages/{channel_link}", response_class=HTMLResponse)
async def last_messages(request: Request, channel_link: str):
    """Страница отображения сообщений из канала"""
    user_client = await get_current_user(request)
    if not user_client:
        return RedirectResponse(url="/authenticate")

    final_response = await get_last_messages(user_client, channel_link)

    if not final_response:
        # Переадресация на Dashboard
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse(
        "messages.html",
        {**{"request": request}, **final_response},
    )


@app.post("/subscribe/{channel_id}", response_class=JSONResponse)
async def subscribe_to_channel(
    request: Request,
    channel_id: str,
    _session: SessionLocal = Depends(get_db),
):
    """Подписка пользователя на канал с отправкой сообщений раз в сутки"""

    user_client = await get_current_user(request)
    user_me = await user_client.get_me()
    user_id = user_me.id

    return Subscribers.toggle_subscription(_session, user_id, channel_id)


@app.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    """Выход из системы"""
    request.session.clear()
    logger.info("Пользователь вышел из системы.")
    return RedirectResponse(url="/", status_code=303)


async def get_unread_message_count(user_client: TelegramClient, entity_id: int) -> int:
    """Поиск количества непрочитанных сообщений"""

    # Получаем диалог для сущности
    dialogs = await user_client.get_dialogs()

    # Находим нужный диалог
    target_dialog = None
    for dialog in dialogs:
        if dialog.entity.id == entity_id:
            target_dialog = dialog
            break

    # возвращаем количество непрочитанных сообщений в диалоге
    return target_dialog.unread_count


async def get_last_messages(user_client: TelegramClient, channel_link: str):
    """Получаем и обобщаем сообщения из канала"""

    try:
        entity = await user_client.get_entity(channel_link)

        messages = []
        messages_to_summarize = []

        unread_count = await get_unread_message_count(user_client, entity.id)

        # Ограничение количества сообщений: если непрочитанных меньше 100,
        # то подгружаем их и ещё 100 из истории.
        # Если больше 100, то берем только 100 новых сообщений

        max_messages = (100 + unread_count) if unread_count <= 100 else 100

        total_count = 0
        async for message in user_client.iter_messages(entity, limit=max_messages):
            if message.text:
                total_count += 1
                messages.append(
                    {
                        "id": message.id,
                        "text": message.text,
                        "date": message.date.strftime("%Y-%m-%d %H:%M:%S"),
                        "label": f"History #{total_count}: ",
                    }
                )
                messages_to_summarize.append(message.text)
        # запрос OpenAI и получение ответа
        if not messages_to_summarize:
            final_summary = "Нет сообщений для обобщения."
        else:
            # Объединение сообщений для запроса
            combined_messages = "\n\n".join(messages_to_summarize)

            # Разделение на части, если текст слишком длинный
            MAX_CHARS = 2000  # Примерное ограничение, зависит от модели и токенов
            parts = [
                combined_messages[i : i + MAX_CHARS]
                for i in range(0, len(combined_messages), MAX_CHARS)
            ]

            summaries = []
            for part in parts:
                summary, status = summarize_text(part)
                summaries.append(summary)
            final_summary = "\n\n".join(summaries)

        return {
            "channel": channel_link,
            "messages": messages,
            "unread_count": unread_count,
            "total_count": total_count,
            "summary": final_summary,
        }

    except Exception as e:
        logger.error(
            f"Ошибка при получении сообщений из канала {channel_link}."
            f"Произошла переадресация на Dashboard: {e}"
        )
        return None


async def send_summaries():
    """Сбор и отправка обобщений планировщиком"""
    with SessionLocal() as session:
        active_subscriptions = Subscribers.get_active_subscriptions(session)
        logger.info("Подготовка спам-обобщения..")
        for sub in active_subscriptions:
            try:
                # Необходимо добавить функцию get_user_client, которая возвращает
                # TelegramClient пользователя по его сессии. Сессию можно сохранить в
                # базе данных. Необходимо будет провести авторизацию пользователя.
                user_client = await get_user_client(sub.user_id)
                if not user_client:
                    logger.warning(f"Не найден клиент для {sub.user_id}")
                    continue

                response_data = await get_last_messages(user_client, sub.channel_id)

                summary_response = response_data["summary"]

                # Отправляем пользователю
                await client.send_message(sub.user_id, summary_response)
                logger.info("Спам-обобщение отправлено успешно!")
                # обновляем время последней рассылки
                sub.last_sent = datetime.datetime.now(datetime.timezone.utc)
                session.add(sub)
                session.commit()

            except Exception as e:
                logger.error(
                    f"Ошибка при отправке обобщений пользователю {sub.user_id}: {e}"
                )


if __name__ == "__main__":
    nest_asyncio.apply()
    uvicorn.run(app, host="0.0.0.0", port=8000)
