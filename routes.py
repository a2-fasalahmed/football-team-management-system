from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from app import db
from app.coach import bp
from app.models import Team, User, Event, Announcement, PlayerStat, Availability
from app.forms import TeamForm, EventForm, AnnouncementForm, PlayerStatForm, AddPlayerForm
from app.decorators import role_required


def get_coach_team():
    return Team.query.filter_by(coach_id=current_user.id).first()


@bp.route('/dashboard')
@login_required
@role_required('coach')
def dashboard():
    team = get_coach_team()
    events = []
    announcements = []
    if team:
        events = team.events.order_by(Event.start_time.desc()).limit(5).all()
        announcements = team.announcements.order_by(Announcement.timestamp.desc()).limit(5).all()
    return render_template('coach/dashboard.html',
                           title='Coach Dashboard',
                           team=team,
                           events=events,
                           announcements=announcements)


@bp.route('/create_team', methods=['GET', 'POST'])
@login_required
@role_required('coach')
def create_team():
    form = TeamForm()
    if form.validate_on_submit():
        team = Team(name=form.name.data, coach_id=current_user.id)
        db.session.add(team)
        db.session.commit()
        current_user.team_id = team.id
        db.session.commit()
        flash('Team created successfully!', 'success')
        return redirect(url_for('coach.dashboard'))
    return render_template('coach/create_team.html', title='Create Team', form=form)


@bp.route('/manage_players', methods=['GET', 'POST'])
@login_required
@role_required('coach')
def manage_players():
    team = get_coach_team()
    if not team:
        flash('Create a team first!', 'warning')
        return redirect(url_for('coach.create_team'))

    form = AddPlayerForm()
    if form.validate_on_submit():
        player = User(
            username=form.username.data,
            email=form.email.data,
            role='player',
            team_id=team.id,
            position=form.position.data or None,
            squad=form.squad.data or 'First Team',
            profile_image='default.jpg'
        )
        player.set_password(form.password.data)
        db.session.add(player)
        db.session.commit()
        flash(f'Player {player.username} added successfully!', 'success')
        return redirect(url_for('coach.manage_players'))

    players = team.players.all()
    return render_template('coach/manage_players.html',
                           title='Manage Players',
                           players=players,
                           team=team,
                           form=form)


@bp.route('/add_player', methods=['GET', 'POST'])
@login_required
@role_required('coach')
def add_player():
    return redirect(url_for('coach.manage_players'))


@bp.route('/edit_player/<int:player_id>', methods=['POST'])
@login_required
@role_required('coach')
def edit_player(player_id):
    player = User.query.get_or_404(player_id)
    team = get_coach_team()
    if not team or player.team_id != team.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('coach.manage_players'))
    player.squad    = request.form.get('squad')
    player.position = request.form.get('position')
    db.session.commit()
    flash(f'Player {player.username} updated.', 'success')
    return redirect(url_for('coach.manage_players'))


@bp.route('/remove_player/<int:player_id>', methods=['POST'])
@login_required
@role_required('coach')
def remove_player(player_id):
    player = User.query.get_or_404(player_id)
    team = get_coach_team()
    if not team or player.team_id != team.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('coach.manage_players'))
    player.team_id = None
    db.session.commit()
    flash(f'{player.username} removed from team.', 'info')
    return redirect(url_for('coach.manage_players'))


@bp.route('/events')
@login_required
@role_required('coach')
def events():
    team = get_coach_team()
    if not team:
        flash('Create a team first!', 'warning')
        return redirect(url_for('coach.create_team'))
    all_events = team.events.order_by(Event.start_time.asc()).all()
    return render_template('coach/events.html', title='Events', events=all_events)


@bp.route('/add_event', methods=['GET', 'POST'])
@login_required
@role_required('coach')
def add_event():
    team = get_coach_team()
    if not team:
        flash('Create a team first!', 'warning')
        return redirect(url_for('coach.create_team'))
    form = EventForm()
    if form.validate_on_submit():
        clash = Event.query.filter_by(
            team_id=team.id,
            start_time=form.start_time.data
        ).first()
        if clash:
            flash(f'An event already exists at that date and time.', 'danger')
            return render_template('coach/event_form.html', title='Add Event', form=form)
        event = Event(
            title=form.title.data,
            description=form.description.data,
            event_type=form.event_type.data,
            start_time=form.start_time.data,
            location=form.location.data,
            team_id=team.id
        )
        db.session.add(event)
        db.session.commit()
        flash('Event added successfully!', 'success')
        return redirect(url_for('coach.events'))
    return render_template('coach/event_form.html', title='Add Event', form=form)


@bp.route('/delete_event/<int:event_id>', methods=['POST'])
@login_required
@role_required('coach')
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    team = get_coach_team()
    if not team or event.team_id != team.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('coach.events'))
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted.', 'info')
    return redirect(url_for('coach.events'))


@bp.route('/availability/<int:event_id>')
@login_required
@role_required('coach')
def availability(event_id):
    event = Event.query.get_or_404(event_id)
    team = get_coach_team()
    if not team or event.team_id != team.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('coach.dashboard'))
    players = team.players.all()
    player_availabilities = []
    for player in players:
        av = Availability.query.filter_by(player_id=player.id, event_id=event_id).first()
        player_availabilities.append({
            'player': player,
            'status': av.status.capitalize() if av else 'Pending'
        })
    return render_template('coach/availability.html',
                           title='Availability',
                           event=event,
                           player_availabilities=player_availabilities)


@bp.route('/post_announcement', methods=['GET', 'POST'])
@login_required
@role_required('coach')
def post_announcement():
    team = get_coach_team()
    if not team:
        flash('Create a team first!', 'warning')
        return redirect(url_for('coach.create_team'))
    form = AnnouncementForm()
    if form.validate_on_submit():
        announcement = Announcement(
            title=form.title.data,
            content=form.content.data,
            team_id=team.id
        )
        db.session.add(announcement)
        db.session.commit()
        flash('Announcement posted!', 'success')
        return redirect(url_for('coach.dashboard'))
    return render_template('coach/announcement_form.html',
                           title='Post Announcement', form=form)


@bp.route('/statistics')
@login_required
@role_required('coach')
def statistics():
    team = get_coach_team()
    if not team:
        flash('Create a team first!', 'warning')
        return redirect(url_for('coach.create_team'))
    players = team.players.all()
    events  = team.events.all()
    match_events_count = team.events.filter_by(event_type='match').count()
    players_stats = []
    for player in players:
        stats       = PlayerStat.query.filter_by(player_id=player.id).all()
        appearances = len(stats)
        goals       = sum(s.goals   or 0 for s in stats)
        assists     = sum(s.assists or 0 for s in stats)
        att_percent = (appearances / match_events_count * 100) if match_events_count > 0 else 0
        players_stats.append({
            'player':        player,
            'appearances':   appearances,
            'goals':         goals,
            'assists':       assists,
            'contributions': goals + assists,
            'attendance':    f'{appearances}/{match_events_count}',
            'att_percent':   round(att_percent, 1),
        })
    players_stats.sort(key=lambda x: x['goals'], reverse=True)
    return render_template('coach/statistics.html',
                           title='Team Statistics',
                           players_stats=players_stats,
                           events=events)


@bp.route('/record_stats/<int:event_id>', methods=['GET', 'POST'])
@login_required
@role_required('coach')
def record_stats(event_id):
    event = Event.query.get_or_404(event_id)
    team  = get_coach_team()
    if not team or event.team_id != team.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('coach.dashboard'))
    players = team.players.all()
    if request.method == 'POST':
        for player in players:
            appeared = request.form.get(f'appearance_{player.id}') == 'Yes'
            goals    = request.form.get(f'goals_{player.id}',   0, type=int)
            assists  = request.form.get(f'assists_{player.id}', 0, type=int)
            stat = PlayerStat.query.filter_by(
                player_id=player.id, event_id=event_id).first()
            if not stat:
                stat = PlayerStat(player_id=player.id, event_id=event_id)
                db.session.add(stat)
            stat.goals          = goals
            stat.assists        = assists
            stat.minutes_played = 90 if appeared else 0
        db.session.commit()
        flash('Statistics recorded!', 'success')
        return redirect(url_for('coach.statistics'))
    stats_map   = {s.player_id: s for s in event.stats.all()}
    player_data = []
    for player in players:
        stat = stats_map.get(player.id)
        player_data.append({
            'player':     player,
            'appearance': 'Yes' if stat and stat.minutes_played and stat.minutes_played > 0 else 'No',
            'goals':      stat.goals   if stat else 0,
            'assists':    stat.assists if stat else 0,
        })
    return render_template('coach/record_stats.html',
                           title='Record Stats',
                           event=event,
                           player_data=player_data,
                           players=players)


@bp.route('/squad_management')
@login_required
@role_required('coach')
def squad_management():
    team = get_coach_team()
    if not team:
        flash('Create a team first!', 'warning')
        return redirect(url_for('coach.create_team'))
    players = team.players.all()
    squads  = {}
    for player in players:
        sq = player.squad or 'Unassigned'
        squads.setdefault(sq, []).append(player)
    return render_template('coach/squad_management.html',
                           title='Squad Management',
                           squads=squads,
                           team=team)
