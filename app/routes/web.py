"""
Web routes for Torah Search
"""
from flask import Blueprint, render_template_string, current_app
from app.app_factory import cache
import structlog

logger = structlog.get_logger()

bp = Blueprint('web', __name__)


@bp.route('/')
@cache.cached(timeout=300)
def index():
    """Serve the main search interface."""
    return render_template_string(get_main_template())


@bp.route('/about')
@cache.cached(timeout=3600)
def about():
    """About page."""
    return render_template_string(get_about_template())


def get_main_template():
    """Return the main search interface template."""
    return open('/Users/yahavhorev/dev/torah-sod/app/templates/index.html', 'r', encoding='utf-8').read()


def get_about_template():
    """Return the about page template."""
    return open('/Users/yahavhorev/dev/torah-sod/app/templates/about.html', 'r', encoding='utf-8').read()
