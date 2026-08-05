import os

import pytest

from redtail_repository import create_app, db
from redtail_repository.models import Author, LaboratoryExercise, User

pytestmark = pytest.mark.mysql


@pytest.fixture(scope="module")
def mysql_app():
    database_url = os.environ.get("MYSQL_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("MYSQL_TEST_DATABASE_URL is not configured")

    app = create_app(
        "testing",
        {
            "SQLALCHEMY_DATABASE_URI": database_url,
            "SERVER_NAME": "redtail.mysql.test",
        },
    )
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def test_mysql_crud_relationships_and_authentication(mysql_app):
    with mysql_app.app_context():
        author = Author(login="mysql-author", name="MySQL Author")
        user = User(login="mysql-user", name="MySQL User", verified=True)
        user.role = "instructor"
        user.set_password("mysql-password")
        user.author = author
        exercise = LaboratoryExercise(
            name="MySQL Exercise",
            slug="mysql-exercise",
            short_description="Runs against MySQL.",
            active=True,
        )
        exercise.authors.append(author)
        db.session.add_all([user, exercise])
        db.session.commit()

        loaded = db.session.get(User, user.id)
        assert loaded.check_password("mysql-password")
        assert loaded.author.name == "MySQL Author"
        assert loaded.author.laboratory_exercises[0].slug == "mysql-exercise"
