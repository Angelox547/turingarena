import os

from flask import Blueprint, render_template, send_from_directory, current_app, redirect, url_for
from turingarena_web.contest import Contest

from turingarena_web.views.user import get_current_user

root_bp = Blueprint('root', __name__)


@root_bp.route("/")
def home():
    user = get_current_user()
    if user is None:
        return redirect(url_for("user.login"))
    contests = Contest.of_user(user)
    return render_template("home.html", contests=contests, user=user)


@root_bp.route('/favicon.ico')
def favicon():
    # TODO: not all browsers supports SVG favicon. Check if browser is supported and if not serve a standard PNG image
    return send_from_directory(
        directory=os.path.join(current_app.root_path, 'static/img'),
        filename='turingarena_logo.svg'
    )
