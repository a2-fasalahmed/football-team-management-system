from datetime import datetime
from app import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email         = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role          = db.Column(db.String(20), nullable=False)          # 'coach' or 'player'
    team_id       = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)
    squad         = db.Column(db.String(50), nullable=True)
    position      = db.Column(db.String(50), nullable=True)
    # profile_image defaults to 'default.jpg' so no upload is ever required
    profile_image = db.Column(db.String(120), nullable=False, default='default.jpg')

    # Relationships
    player_stats   = db.relationship('PlayerStat',   backref='player', lazy='dynamic')
    availabilities = db.relationship('Availability', backref='player', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Team(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    name     = db.Column(db.String(100), unique=True, nullable=False)
    coach_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    coach         = db.relationship('User', backref=db.backref('coached_team', uselist=False),
                                    foreign_keys=[coach_id])
    players       = db.relationship('User', backref='team', lazy='dynamic',
                                    foreign_keys=[User.team_id])
    events        = db.relationship('Event',        backref='team', lazy='dynamic')
    announcements = db.relationship('Announcement', backref='team', lazy='dynamic')


class Event(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    event_type  = db.Column(db.String(20), nullable=False)  # 'match' or 'training'
    start_time  = db.Column(db.DateTime,  index=True, nullable=False)
    location    = db.Column(db.String(140))
    opponent    = db.Column(db.String(100))                 # plain text — opposing club name
    team_id     = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)

    availabilities = db.relationship('Availability', backref='event', lazy='dynamic')
    stats          = db.relationship('PlayerStat',   backref='event', lazy='dynamic')


class Availability(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('user.id'),  nullable=False)
    event_id  = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    # 'available', 'unavailable', 'maybe'
    status    = db.Column(db.String(20), nullable=False, default='maybe')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Announcement(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    title     = db.Column(db.String(100), nullable=False)
    content   = db.Column(db.Text,        nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    team_id   = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)


class PlayerStat(db.Model):
    id             = db.Column(db.Integer, primary_key=True)
    player_id      = db.Column(db.Integer, db.ForeignKey('user.id'),  nullable=False)
    event_id       = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    goals          = db.Column(db.Integer, default=0)
    assists        = db.Column(db.Integer, default=0)
    yellow_cards   = db.Column(db.Integer, default=0)
    red_cards      = db.Column(db.Integer, default=0)
    minutes_played = db.Column(db.Integer, default=0)
    appeared       = db.Column(db.Boolean, default=False)   # FR-11: did the player appear?


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
