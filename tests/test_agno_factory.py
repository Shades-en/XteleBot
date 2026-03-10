import unittest
from unittest.mock import patch

from telebot.common.enums import BotEnv
from telebot.config import Settings
from telebot.agents.factory import AgnoFactory


def sample_settings() -> Settings:
    return Settings(
        telegram_token="token",
        bot_env=BotEnv.DEVELOPMENT,
        proxy_base_url=None,
        proxy_target=None,
        vercel_bypass_token="",
        postgres_url="postgresql+psycopg_async://user:pass@localhost:5432/app?sslmode=disable",
        agno_postgres_url="postgresql+psycopg_async://user:pass@localhost:5432/app?sslmode=disable",
        twitter_api_key="twitter",
        brave_search_api_key="brave",
        openai_api_key="openai",
        auto_create_schema=False,
    )


class AgnoFactoryTests(unittest.TestCase):
    def test_creator_agents_use_db_history_without_learning(self) -> None:
        captured_calls: list[dict] = []

        def fake_agent(**kwargs):
            captured_calls.append(kwargs)
            return kwargs

        with (
            patch("telebot.agents.factory.AsyncPostgresDb", return_value=object()),
            patch("telebot.agents.factory.Agent", side_effect=fake_agent),
        ):
            factory = AgnoFactory(sample_settings())
            factory.build_creator_agent()
            factory.build_creator_refiner_agent()

        self.assertEqual(len(captured_calls), 2)
        for kwargs in captured_calls:
            self.assertTrue(kwargs["add_history_to_context"])
            self.assertEqual(kwargs["num_history_runs"], 4)
            self.assertIn("db", kwargs)
            self.assertNotIn("learning", kwargs)


if __name__ == "__main__":
    unittest.main()
