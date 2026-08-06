from types import SimpleNamespace

from redtail_repository.seo import (
    _plain_text,
    learning_resource_schema,
    people_schema,
    public_asset_url,
)


def test_plain_text_truncates_long_descriptions_at_a_word_boundary():
    description = "remote laboratory " * 20

    shortened = _plain_text(description, "fallback", limit=80)

    assert shortened.endswith("…")
    assert len(shortened) <= 80
    assert not shortened.endswith(" …")


def test_public_asset_url_accepts_http_images_and_rejects_protocol_relative_urls(app):
    with app.test_request_context("/"):
        assert public_asset_url("https://images.example.test/cover.png") == (
            "https://images.example.test/cover.png"
        )
        assert public_asset_url("//images.example.test/cover.png") == (
            "https://redtail.example.test/static/img/redtail-social-card.png"
        )


def test_schema_helpers_omit_empty_optional_author_and_date_fields(app):
    author = SimpleNamespace(name="No-link Author", link=None)

    with app.test_request_context("/"):
        assert people_schema([author]) == [
            {"@type": "Person", "name": "No-link Author"}
        ]
        resource = learning_resource_schema(
            name="Test resource",
            description="Test description",
            path="/simulations/test-resource",
            image_url=None,
            resource_type="Simulation",
            authors=[author],
        )

    assert "dateModified" not in resource
