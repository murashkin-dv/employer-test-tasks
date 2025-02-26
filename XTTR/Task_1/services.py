import logging

import openai

# Настройка логирования
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def summarize_text(text: str) -> tuple[str, int]:
    """Функция для обобщения текста с учётом ограничений токенов"""

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that summarizes "
                    "Telegram channel messages.",
                },
                {
                    "role": "user",
                    "content": f"Расскажи, что нового и интересного произошло в "
                    f"этих сообщениях? Дай ответ только по основным и "
                    f"значимым событиям. Частей с текстом "
                    f"может быть несколько, поэтому отвечай в контексте "
                    f"полученных сообщений. Текст для анализа: :\n\n{text}.",
                },
            ],
            max_tokens=4000,  # Ограничение на выходные токены
            temperature=1,
        )
        summary = response.choices[0].message.content.strip()
        return summary, True
    except Exception as e:
        logger.error(f"Ошибка при обобщении: {e}")
        return "Не удалось получить ответ.", False
