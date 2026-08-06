from collections import OrderedDict
from typing import Any, Dict, Mapping, Optional

from flask import Flask, has_request_context, request, session
from flask_assets import Environment
from flask_babel import Babel
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from config import configurations

try:
    from flask_debugtoolbar import DebugToolbarExtension
except ImportError:
    DebugToolbarExtension = None

babel = Babel()
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

if DebugToolbarExtension is not None:
    toolbar = DebugToolbarExtension()
else:
    toolbar = None

def create_app(
    config_name: str = 'default',
    config_overrides: Optional[Mapping[str, Any]] = None,
) -> Flask:
    global SUPPORTED_LANGUAGES, SUPPORTED_TRANSLATIONS

    app = Flask(__name__)
    app.config.from_object(configurations[config_name])
    if config_overrides:
        app.config.from_mapping(config_overrides)

    SUPPORTED_LANGUAGES = None
    SUPPORTED_TRANSLATIONS = None

    # Initialize extensions
    db.init_app(app)
    assets_environment = Environment()
    assets_environment.init_app(app)
    babel.init_app(app, locale_selector=get_locale)
    migrate.init_app(app, db)
    if toolbar is not None:
        toolbar.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login.login'

    from .views.admin import init_admin
    init_admin(app)

    import redtail_repository.models # noqa

    # Register bundles
    from .bundles import register_bundles
    register_bundles(assets_environment)

    # Register blueprint
    from .views.login import login_blueprint
    from .views.public import public_blueprint

    app.register_blueprint(public_blueprint, url_prefix='/')
    app.register_blueprint(login_blueprint, url_prefix='/')

    from .seo import robots_directive

    @app.after_request
    def apply_response_policies(response):
        directive = robots_directive(response.status_code)
        if directive:
            response.headers.setdefault("X-Robots-Tag", directive)

        if response.status_code < 400:
            endpoint = request.endpoint or ""
            filename = (request.view_args or {}).get("filename", "")
            if endpoint == "static" and filename.startswith("gen/"):
                response.headers["Cache-Control"] = (
                    "public, max-age=31536000, immutable"
                )
            elif endpoint == "static":
                response.headers["Cache-Control"] = (
                    "public, max-age=604800, stale-while-revalidate=86400"
                )
            elif endpoint == "public.serve_public":
                response.headers["Cache-Control"] = (
                    "public, max-age=3600, stale-while-revalidate=86400"
                )
            elif endpoint == "public.serve_uploads":
                response.headers["Cache-Control"] = "private, no-store"
        return response

    def _list_languages() -> Dict[str, str]:
        global SUPPORTED_LANGUAGES                                                  
        if SUPPORTED_LANGUAGES is None:
            SUPPORTED_LANGUAGES = OrderedDict()                                         
                                       
            translations = babel.list_translations()
            for language in sorted(translations, key=lambda x: x.language):
                try:
                    display_name = language.get_display_name(language).title()
                except Exception:
                    display_name = language.language
                SUPPORTED_LANGUAGES[language.language] = display_name

        return SUPPORTED_LANGUAGES
        
    @app.context_processor
    def inject_vars():
        return dict(
            list_languages=_list_languages,
            locale=get_locale(),
            seo_robots=robots_directive(),
        )

    return app

SUPPORTED_TRANSLATIONS = None
SUPPORTED_LANGUAGES = None

def get_locale():
    """ Defines what's the current language for the user. It uses different approaches. """
    # 'en' is supported by default
    global SUPPORTED_TRANSLATIONS
    if SUPPORTED_TRANSLATIONS is None:
        supported_languages = ['en']
        for translation in babel.list_translations():
            if translation.territory:
                iter_language = '{}_{}'.format(translation.language, translation.territory)
            else:
                iter_language = translation.language
            if iter_language not in supported_languages:
                supported_languages.append(iter_language)

        SUPPORTED_TRANSLATIONS = supported_languages
    else:
        supported_languages = SUPPORTED_TRANSLATIONS

    locale = None

    # This is used also from tasks (which are not in a context environment)
    if has_request_context():
        # If user accesses ?locale=es force it to Spanish, for example
        locale = request.args.get('locale', None)
        if locale not in supported_languages:
            locale = None

    # Otherwise, check what the web browser is using (the web browser might state multiple
    # languages)
    if has_request_context():
        if locale is None:
            if session.get('locale') is not None:
                locale = session['locale']

        if locale is None:
            locale = request.accept_languages.best_match(supported_languages)

    # Otherwise... use the default one (English)
    if locale is None:
        locale = 'en'

    if has_request_context():
        session['locale'] = locale

    return locale
