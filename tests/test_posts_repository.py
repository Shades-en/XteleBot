import unittest

from telebot.common.constants import CREATOR_STYLE_EXAMPLE_FETCH_LIMIT
from telebot.common.enums import PostPurpose
from telebot.db.repositories.posts import PostRepository
from telebot.db.social_models import Post


class FakeResult:
    def __init__(self, post=None, posts=None) -> None:
        self.post = post
        self.posts = posts or []

    def scalar_one_or_none(self):
        return self.post

    def scalars(self):
        return self

    def all(self):
        return self.posts


class FakeSession:
    def __init__(self, result: FakeResult) -> None:
        self.result = result
        self.last_stmt = None

    async def execute(self, stmt):
        self.last_stmt = stmt
        return self.result


class PostRepositoryTests(unittest.IsolatedAsyncioTestCase):
    async def test_best_researched_post_for_creator_filters_by_purpose(self) -> None:
        expected = Post(post_id="p-1", purpose=PostPurpose.QUOTE.value)
        session = FakeSession(FakeResult(post=expected))
        repo = PostRepository(session)

        result = await repo.best_researched_post_for_creator(101, PostPurpose.QUOTE)

        self.assertIs(result, expected)
        sql = str(session.last_stmt.compile(compile_kwargs={"literal_binds": True}))
        self.assertIn("posts.purpose = 'Quote'", sql)
        self.assertIn("posts.own_posts IS false", sql)
        self.assertIn("LIMIT 1", sql)

    async def test_recent_own_posts_for_creator_style_filters_bad_examples(self) -> None:
        good_recent = Post(post_id="own-1", text="This is a useful product take with enough texture.")
        mention_reply = Post(post_id="own-2", text="@someone totally agree")
        too_short = Post(post_id="own-3", text="short thought")
        good_older = Post(post_id="own-4", text="Distribution gets easier when the product already teaches.")
        session = FakeSession(FakeResult(posts=[good_recent, mention_reply, too_short, good_older]))
        repo = PostRepository(session)

        results = await repo.recent_own_posts_for_creator_style(101, limit=2)

        self.assertEqual([post.post_id for post in results], ["own-1", "own-4"])
        sql = str(session.last_stmt.compile(compile_kwargs={"literal_binds": True}))
        self.assertIn("posts.own_posts IS true", sql)
        self.assertIn("ORDER BY posts.posted_at DESC", sql)
        self.assertIn(f"LIMIT {CREATOR_STYLE_EXAMPLE_FETCH_LIMIT}", sql)


if __name__ == "__main__":
    unittest.main()
