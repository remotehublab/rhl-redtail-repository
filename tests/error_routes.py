from flask import abort


def register_test_error_routes(app):
    def forbidden():
        abort(403)

    def explode():
        raise RuntimeError("private test exception")

    app.add_url_rule(
        "/_test/errors/403",
        endpoint="test_forbidden",
        view_func=forbidden,
    )
    app.add_url_rule(
        "/_test/errors/500",
        endpoint="test_internal_server_error",
        view_func=explode,
    )
