from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from app import db
from app.player import bp
from app.models import Team, User, Event, Announcement, Availability, PlayerStat
from app.decorators import role_required


@bp.route('/dashboard')
@login_required
@role_required('player')
def dashboard():
    team          = current_user.team
    events        = []
    announcements = []
    stats         = []
    availabilities = {}
    confirmed_events = 0
    if team:
        events        = team.events.order_by(Event.start_time.asc()).all()
        announcements = team.announcements.order_by(Announcement.timestamp.desc()).limit(5).all()
        stats         = current_user.player_stats.all()
        avs           = Availability.query.filter_by(player_id=current_user.id).all()
        availabilities   = {av.event_id: av.status for av in avs}
        confirmed_events = len([av for av in avs if av.status == 'available'])
    return render_template('player/dashboard.html',
                           title='Player Dashboard',
                           team=team,
                           events=events,
                           announcements=announcements,
                           stats=stats,
                           availabilities=availabilities,
                           confirmed_events=confirmed_events)


@bp.route('/join_team', methods=['GET', 'POST'])
@login_required
@role_required('player')
def join_team():
    if request.method == 'POST':
        team_id = request.form.get('team_id')
        team    = Team.query.get(team_id)
        if team:
            current_user.team_id = team.id
            db.session.commit()
            flash(f'Joined team {team.name}!', 'success')
            return redirect(url_for('player.dashboard'))
    teams = Team.query.all()
    return render_template('player/join_team.html', title='Join Team', teams=teams)


@bp.route('/respond_availability/<int:event_id>', methods=['POST'])
@login_required
@role_required('player')
def respond_availability(event_id):
    status = request.form.get('status')
    av = Availability.query.filter_by(
        player_id=current_user.id, event_id=event_id).first()
    if av:
        av.status = status
    else:
        av = Availability(player_id=current_user.id, event_id=event_id, status=status)
        db.session.add(av)
    db.session.commit()
    return redirect(request.referrer or url_for('player.dashboard'))


@bp.route('/events')
@login_required
@role_required('player')
def events():
    team        = current_user.team
    events_list = team.events.order_by(Event.start_time.asc()).all() if team else []
    availabilities = {av.event_id: av.status for av in
                      Availability.query.filter_by(player_id=current_user.id).all()}
    return render_template('player/events.html',
                           title='Events',
                           events=events_list,
                           availabilities=availabilities)


@bp.route('/match_history')
@login_required
@role_required('player')
def match_history():
    team         = current_user.team
    match_events = (team.events.filter_by(event_type='match')
                    .order_by(Event.start_time.desc()).all()) if team else []
    stats_dict   = {s.event_id: s for s in current_user.player_stats.all()}
    return render_template('player/match_history.html',
                           title='Match History',
                           match_events=match_events,
                           stats=stats_dict)


@bp.route('/profile', methods=['GET', 'POST'])
@login_required
@role_required('player')
def profile():
    if request.method == 'POST':
        current_user.email = request.form.get('email', current_user.email)
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('player.profile'))
    return render_template('player/profile.html', title='My Profile')
