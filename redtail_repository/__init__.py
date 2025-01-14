from collections import OrderedDict
from typing import Dict

from flask import Flask, session, request, has_request_context

from flask_babel import Babel
from flask_assets import Environment
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

try:
    from flask_debugtoolbar import DebugToolbarExtension
except ImportError:
    DebugToolbarExtension = None

babel = Babel()
db = SQLAlchemy()
environment = Environment()
migrate = Migrate()
login_manager = LoginManager()

if DebugToolbarExtension is not None:
    toolbar = DebugToolbarExtension()
else:
    toolbar = None


from config import configurations

@login_manager.user_loader
def user_loader(login: str):
    from .models import User
    return db.session.query(User).filter_by(login=login).first()

def create_app(config_name: str = 'default') -> Flask:
    app = Flask(__name__)
    app.config.from_object(configurations[config_name])

    # Initialize extensions
    db.init_app(app)
    environment.init_app(app)
    babel.init_app(app, locale_selector=get_locale)
    migrate.init_app(app, db)
    if toolbar is not None:
        toolbar.init_app(app)
    login_manager.init_app(app)

    import redtail_repository.models # noqa

    # Register bundles
    from .bundles import register_bundles
    register_bundles(environment)

    # Register endpoints
    from .views.public import public_endpoint

    app.register_blueprint(public_endpoint, url_prefix='/')

    def _list_languages() -> Dict[str, str]:
        global SUPPORTED_LANGUAGES                                                  
        if SUPPORTED_LANGUAGES is None:
            SUPPORTED_LANGUAGES = OrderedDict()                                         
                                       
            translations = babel.list_translations()
            for language in sorted(translations, key=lambda x: x.language):
                try:
                    display_name = language.get_display_name(language).title()
                except:
                    display_name = language
                SUPPORTED_LANGUAGES[language.language] = display_name

        return SUPPORTED_LANGUAGES
        
    @app.context_processor
    def inject_vars():  
        return dict(list_languages=_list_languages, locale=get_locale())

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

    session['locale'] = locale

    return locale
