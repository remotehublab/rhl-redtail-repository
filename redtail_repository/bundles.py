from flask_assets import Bundle, Environment

BOOTSTRAP_VERSION = '5.3.8'

CSS_FILTER = 'cssmin'
JS_FILTER = 'jsmin'


def register_bundles(assets: Environment):
    """
    Registers the bundles for the assets.
    :param assets: The assets environment.
    """
    bootstrap_css = Bundle(
            'node_modules/bootstrap/dist/css/bootstrap.min.css',
            filters=CSS_FILTER,
            output="gen/bootstrap-" + BOOTSTRAP_VERSION + "/css/bootstrap.%(version)s.min.css")

    bootstrap_js = Bundle(
            'node_modules/bootstrap/dist/js/bootstrap.bundle.min.js',
            filters=JS_FILTER,
            output="gen/bootstrap-" + BOOTSTRAP_VERSION + "/js/bootstrap.%(version)s.min.js")

    assets.register('bootstrap_css', bootstrap_css)
    assets.register('bootstrap_js', bootstrap_js)


    fontawesome_css = Bundle(
            'node_modules/@fortawesome/fontawesome-free/css/all.min.css',
            filters='cssrewrite,' + CSS_FILTER,
            output="gen/fontawesome/css/all.%(version)s.min.css")

    fontawesome_js = Bundle(
            'node_modules/@fortawesome/fontawesome-free/js/all.min.js',
            filters=JS_FILTER,
            output="gen/fontawesome/js/all.%(version)s.min.js")

    assets.register('fontawesome_css', fontawesome_css)
    assets.register('fontawesome_js', fontawesome_js)

    vendor_js = Bundle(
            "node_modules/jquery/dist/jquery.min.js",
            filters=JS_FILTER,
            output="gen/vendor.%(version)s.min.js")

    assets.register('vendor_js', vendor_js)

    site_css = Bundle(
            'css/redtail.css',
            filters=CSS_FILTER,
            output='gen/redtail/css/redtail.%(version)s.min.css')

    site_js = Bundle(
            'js/redtail.js',
            filters=JS_FILTER,
            output='gen/redtail/js/redtail.%(version)s.min.js')

    assets.register('site_css', site_css)
    assets.register('site_js', site_js)
