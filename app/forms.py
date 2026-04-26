from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, BooleanField, SubmitField,
                     SelectField, TextAreaField, IntegerField, DateTimeField)
from wtforms.validators import DataRequired, Email, EqualTo, Optional, ValidationError
from app.models import User


class LoginForm(FlaskForm):
    username    = StringField('Username',  validators=[DataRequired()])
    password    = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit      = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username   = StringField('Username',      validators=[DataRequired()])
    email      = StringField('Email',         validators=[DataRequired(), Email()])
    password   = PasswordField('Password',    validators=[DataRequired()])
    password_2 = PasswordField('Repeat Password',
                               validators=[DataRequired(), EqualTo('password')])
    role       = SelectField('Role',
                             choices=[('player', 'Player'), ('coach', 'Coach')],
                             validators=[DataRequired()])
    submit     = SubmitField('Register')

    def validate_username(self, username):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError('Please use a different email address.')


class TeamForm(FlaskForm):
    name   = StringField('Team Name', validators=[DataRequired()])
    submit = SubmitField('Create Team')


class AddPlayerForm(FlaskForm):
    username = StringField('Username',            validators=[DataRequired()])
    email    = StringField('Email',               validators=[DataRequired(), Email()])
    password = PasswordField('Temporary Password', validators=[DataRequired()])
    position = StringField('Position',            validators=[Optional()])
    squad    = SelectField('Squad',
                           choices=[('First Team', 'First Team'),
                                    ('Reserves',   'Reserves')],
                           validators=[Optional()])
    submit   = SubmitField('Add Player')

    def validate_username(self, username):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError('Username already taken.')

    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError('Email already registered.')


class EventForm(FlaskForm):
    title       = StringField('Title',       validators=[DataRequired()])
    description = TextAreaField('Description')
    event_type  = SelectField('Event Type',
                              choices=[('match', 'Match'), ('training', 'Training')],
                              validators=[DataRequired()])
    start_time  = DateTimeField('Start Time',
                                format='%Y-%m-%d %H:%M',
                                validators=[DataRequired()])
    location    = StringField('Location',    validators=[DataRequired()])
    opponent    = StringField('Opponent (matches only)', validators=[Optional()])
    submit      = SubmitField('Save Event')


class AnnouncementForm(FlaskForm):
    title   = StringField('Title',   validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    submit  = SubmitField('Post Announcement')


class PlayerStatForm(FlaskForm):
    goals          = IntegerField('Goals',         default=0)
    assists        = IntegerField('Assists',        default=0)
    yellow_cards   = IntegerField('Yellow Cards',   default=0)
    red_cards      = IntegerField('Red Cards',      default=0)
    minutes_played = IntegerField('Minutes Played', default=0)
    submit         = SubmitField('Save Stats')
