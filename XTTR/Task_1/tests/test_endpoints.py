from unittest.mock import AsyncMock, patch

from database import Subscribers


def test_index_render_template(mock_get_current_user, client):
    mock_get_current_user.return_value = None
    response = client.get("/")
    assert response.status_code == 200  # Статус редиректа
    assert "Добро пожаловать в Telegram Summary" in response.text


@patch("main.get_current_user")
def test_dashboard(mock_get_current_user, client):
    mock_user = AsyncMock()
    mock_user.get_me.return_value.first_name = "John"
    mock_get_current_user.return_value = mock_user

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert "John" in response.text

@patch("main.get_current_user")
def test_subscribe_to_channel(mock_get_current_user, client, db_session):

    mock_user = AsyncMock()
    mock_user.get_me.return_value.id = 123  # ID пользователя
    mock_user.username = "John"
    mock_get_current_user.return_value = mock_user

    channel_id = "channel123"

    response = client.post(f"/subscribe/{channel_id}")


    subscription = db_session.query(Subscribers).filter_by(
            user_id=123, channel_id=channel_id).first()


    assert response.status_code == 201
    assert subscription is not None, "Подписка не была записана в базу данных"
    assert subscription.user_id == 123, f"Ожидался user_id 123, но получено {subscription.user_id}"
    assert subscription.channel_id == channel_id, f"Ожидался channel_id {channel_id}, но получено {subscription.channel_id}"


    #
    # def test_create_survey_no_auth(self, client):
    #     response = client.post("/api/surveys/collector-survey/")
    #     assert response.status_code == 401
    #     assert response.json().get("detail") == "Not authenticated"
    #
    # def test_read_survey_which_not_created_yet(self, client, auth_token: dict):
    #     response = client.get("/api/surveys/collector-survey/", headers=auth_token)
    #     assert "user's Survey" in response.json().get("detail")
    #
    # def test_create_survey_ok(self, client, auth_token: dict):
    #     survey_params = {
    #         "user_id": 1,
    #         "survey_steps": [
    #             {"paintings": [1, 2, 3], "selected": [1], "painting_set_id": 0},
    #             {"paintings": [1, 2, 3], "selected": [2], "painting_set_id": 0},
    #             {"paintings": [1, 2, 3], "selected": [3], "painting_set_id": 0},
    #             {"paintings": [1, 2, 3], "selected": [2], "painting_set_id": 0},
    #             {"paintings": [1, 2, 3], "selected": [1], "painting_set_id": 0},
    #         ],
    #     }
    #     response = client.post(
    #         "/api/surveys/collector-survey/", json=survey_params, headers=auth_token
    #     )
    #     assert response.status_code == 201
    #
    # def test_read_survey(self, client, auth_token: dict):
    #     response = client.get("/api/surveys/collector-survey/", headers=auth_token)
    #     assert response.status_code == 200
    #     assert response.json().get("user_id") == 1
    #     assert len(response.json().get("survey_steps")) == 5
    #
    # def test_create_survey_wrong_selected(self, client, auth_token: dict):
    #     survey_params = {
    #         "user_id": 1,
    #         "survey_steps": [
    #             {"paintings": [1, 2, 3], "selected": [1], "painting_set_id": 0},
    #             {"paintings": [1, 2, 3], "selected": [2], "painting_set_id": 0},
    #             {"paintings": [1, 2, 3], "selected": [5], "painting_set_id": 0},
    #             {"paintings": [1, 2, 3], "selected": [2], "painting_set_id": 0},
    #             {"paintings": [1, 2, 3], "selected": [5], "painting_set_id": 0},
    #         ],
    #     }
    #     response = client.post(
    #         "/api/surveys/collector-survey/", json=survey_params, headers=auth_token
    #     )
    #     assert response.status_code == 400
    #     assert (
    #         "Выбранная картина не соответствует предложенным вариантам в шаге 3!"
    #         in response.json().get("detail")
    #     )
    #
    # def test_create_survey_wrong_set(self, client, auth_token: dict):
    #     survey_params = {
    #         "user_id": 1,
    #         "survey_steps": [
    #             {"paintings": [1, 2, 3], "selected": [1], "painting_set_id": 0},
    #             {"paintings": [1, 2, 3], "selected": [2], "painting_set_id": 0},
    #             {"paintings": [1, 2, 3], "selected": [5], "painting_set_id": 0},
    #             {"paintings": [1, 2, 3], "selected": [2], "painting_set_id": 0},
    #             {"paintings": [1, 2, 3], "selected": [5], "painting_set_id": 1},
    #         ],
    #     }
    #     response = client.post(
    #         "/api/surveys/collector-survey/", json=survey_params, headers=auth_token
    #     )
    #     assert response.status_code == 400
    #     assert (
    #         "Картина не входит в набор или набор не существует в шаге 5!"
    #         in response.json().get("detail")
    #     )
    #
    # def test_create_survey_wrong_user_id(self, client, auth_token: dict):
    #     survey_params = {
    #         "user_id": 2,
    #         "survey_steps": [
    #             {"paintings": [1, 2, 3], "selected": [1], "painting_set_id": 0},
    #             {"paintings": [1, 2, 3], "selected": [2], "painting_set_id": 0},
    #             {"paintings": [1, 2, 3], "selected": [5], "painting_set_id": 0},
    #             {"paintings": [1, 2, 3], "selected": [2], "painting_set_id": 0},
    #             {"paintings": [1, 2, 3], "selected": [5], "painting_set_id": 0},
    #         ],
    #     }
    #     response = client.post(
    #         "/api/surveys/collector-survey/", json=survey_params, headers=auth_token
    #     )
    #     assert response.status_code == 400
    #     assert (
    #         "Пользователь в анкете не совпадает с активным пользователем!"
    #         in response.json().get("detail")
    #     )
    #
    # def test_create_survey_wrong_steps(self, client, auth_token: dict):
    #     survey_params = {
    #         "user_id": 2,
    #         "survey_steps": [
    #             {"paintings": [1, 2, 3], "selected": [1], "painting_set_id": 0},
    #             {"paintings": [1, 2, 3], "selected": [2], "painting_set_id": 0},
    #         ],
    #     }
    #     response = client.post(
    #         "/api/surveys/collector-survey/", json=survey_params, headers=auth_token
    #     )
    #     assert response.status_code == 400
    #     assert "Поле survey_steps должно содержать 5 шагов!" in response.json().get(
    #         "detail"
    #     )
