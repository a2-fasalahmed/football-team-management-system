from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from app.main import bp

@bp.route('/')
@bp.route('/index')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'coach':
            return redirect(url_for('coach.dashboard'))
        else:
            return redirect(url_for('player.dashboard'))
    return render_template('main/index.html', title='Home')
