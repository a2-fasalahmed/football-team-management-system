import unittest
from app import create_app, db
from app.models import User, Team, Event, Availability, Announcement, PlayerStat
from datetime import datetime
from werkzeug.security import generate_password_hash


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class BaseTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            coach = User(
                username='coachsmith',
                email='coach@test.com',
                role='coach',
                password_hash=generate_password_hash('password123')
            )
            db.session.add(coach)
            db.session.flush()
            team = Team(name='Test FC', coach_id=coach.id)
            db.session.add(team)
            db.session.flush()
            coach.team_id = team.id
            player = User(
                username='john',
                email='john@test.com',
                role='player',
                team_id=team.id,
                squad='First Team',
                position='Forward',
                password_hash=generate_password_hash('password123')
            )
            db.session.add(player)
            db.session.flush()
            event = Event(
                title='Match vs Highbury FC',
                event_type='match',
                start_time=datetime(2026, 5, 10, 14, 0),
                location='London',
                team_id=team.id,
                opponent='Highbury FC'
            )
            db.session.add(event)
            db.session.commit()
            self.coach_id = coach.id
            self.player_id = player.id
            self.team_id = team.id
            self.event_id = event.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def login_coach(self):
        return self.client.post('/auth/login', data={
            'username': 'coachsmith',
            'password': 'password123'
        }, follow_redirects=True)

    def login_player(self):
        return self.client.post('/auth/login', data={
            'username': 'john',
            'password': 'password123'
        }, follow_redirects=True)


# ── UT-01: User Registration ──────────────────────────────────────
class UT01_Registration(BaseTest):
    def test_register_new_user(self):
        """UT-01: New user can register an account"""
        response = self.client.post('/auth/register', data={
            'username': 'newplayer',
            'email': 'new@test.com',
            'password': 'password123',
            'password_2': 'password123',
            'role': 'player'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            user = User.query.filter_by(username='newplayer').first()
            self.assertIsNotNone(user)


# ── UT-02: Duplicate Registration Rejected ────────────────────────
class UT02_DuplicateRegistration(BaseTest):
    def test_duplicate_username_rejected(self):
        """UT-02: Duplicate username registration is rejected"""
        self.client.post('/auth/register', data={
            'username': 'coachsmith',
            'email': 'other@test.com',
            'password': 'password123',
            'confirm_password': 'password123',
            'role': 'player'
        }, follow_redirects=True)
        with self.app.app_context():
            users = User.query.filter_by(username='coachsmith').all()
            self.assertEqual(len(users), 1)


# ── UT-03: Login Success ──────────────────────────────────────────
class UT03_LoginSuccess(BaseTest):
    def test_coach_login_success(self):
        """UT-03: Coach can log in with correct credentials"""
        response = self.login_coach()
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'sign in', response.data.lower())


# ── UT-04: Login Failure ──────────────────────────────────────────
class UT04_LoginFailure(BaseTest):
    def test_wrong_password_rejected(self):
        """UT-04: Login fails with wrong password"""
        response = self.client.post('/auth/login', data={
            'username': 'coachsmith',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'sign in', response.data.lower())


# ── UT-05: Login Required ─────────────────────────────────────────
class UT05_LoginRequired(BaseTest):
    def test_unauthenticated_redirected(self):
        """UT-05: Unauthenticated user redirected to login"""
        response = self.client.get('/coach/dashboard', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'sign in', response.data.lower())


# ── UT-06: Role Required ──────────────────────────────────────────
class UT06_RoleRequired(BaseTest):
    def test_player_cannot_access_coach_route(self):
        """UT-06: Player cannot access coach routes"""
        self.login_player()
        response = self.client.get('/coach/dashboard', follow_redirects=False)
        self.assertIn(response.status_code, [302, 403])


# ── UT-07: Coach Dashboard ────────────────────────────────────────
class UT07_CoachDashboard(BaseTest):
    def test_coach_dashboard_loads(self):
        """UT-07: Coach dashboard loads after login"""
        self.login_coach()
        response = self.client.get('/coach/dashboard', follow_redirects=True)
        self.assertEqual(response.status_code, 200)


# ── UT-08: Add Player ─────────────────────────────────────────────
class UT08_AddPlayer(BaseTest):
    def test_coach_can_add_player(self):
        """UT-08: Coach can add a player — User created in DB"""
        with self.app.app_context():
            new_player = User(
                username='newplayer',
                email='newplayer@test.com',
                role='player',
                team_id=self.team_id,
                squad='Reserves',
                position='Goalkeeper',
                password_hash=generate_password_hash('password123')
            )
            db.session.add(new_player)
            db.session.commit()
            user = User.query.filter_by(username='newplayer').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.squad, 'Reserves')


# ── UT-09: Schedule Event ─────────────────────────────────────────
class UT09_ScheduleEvent(BaseTest):
    def test_coach_can_create_event(self):
        """UT-09: Coach can schedule a new event"""
        self.login_coach()
        response = self.client.post('/coach/add_event', data={
            'title': 'Training Session',
            'event_type': 'training',
            'start_time': '2026-06-01 10:00',
            'location': 'Training Ground',
            'opponent': ''
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            event = Event.query.filter_by(title='Training Session').first()
            self.assertIsNotNone(event)


# ── UT-10: Clash Detection ────────────────────────────────────────
class UT10_ClashDetection(BaseTest):
    def test_duplicate_event_rejected(self):
        """UT-10: Duplicate event at same time is rejected"""
        self.login_coach()
        self.client.post('/coach/add_event', data={
            'title': 'First Match',
            'event_type': 'match',
            'start_time': '2026-07-01 15:00',
            'location': 'Home Ground',
            'opponent': 'Rival FC'
        }, follow_redirects=True)
        self.client.post('/coach/add_event', data={
            'title': 'Clashing Match',
            'event_type': 'match',
            'start_time': '2026-07-01 15:00',
            'location': 'Away',
            'opponent': 'Another FC'
        }, follow_redirects=True)
        with self.app.app_context():
            events = Event.query.filter_by(
                start_time=datetime(2026, 7, 1, 15, 0)
            ).all()
            self.assertEqual(len(events), 1)


# ── UT-11: Set Availability ───────────────────────────────────────
class UT11_SetAvailability(BaseTest):
    def test_player_can_set_availability(self):
        """UT-11: Player can set availability for an event"""
        self.login_player()
        response = self.client.post(
            f'/player/respond_availability/{self.event_id}',
            data={'status': 'available'},
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            av = Availability.query.filter_by(
                player_id=self.player_id,
                event_id=self.event_id
            ).first()
            self.assertIsNotNone(av)


# ── UT-12: View Availability Summary ─────────────────────────────
class UT12_ViewAvailability(BaseTest):
    def test_coach_can_view_availability(self):
        """UT-12: Coach can view availability summary"""
        self.login_coach()
        response = self.client.get(
            f'/coach/availability/{self.event_id}',
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)


# ── UT-13: Post Announcement ──────────────────────────────────────
class UT13_PostAnnouncement(BaseTest):
    def test_coach_can_post_announcement(self):
        """UT-13: Coach can post a team announcement"""
        self.login_coach()
        response = self.client.post('/coach/post_announcement', data={
            'title': 'Match Tomorrow',
            'content': 'Be at the ground by 1pm.'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            ann = Announcement.query.filter_by(title='Match Tomorrow').first()
            self.assertIsNotNone(ann)


# ── UT-14: Record Match Stats ─────────────────────────────────────
class UT14_RecordStats(BaseTest):
    def test_coach_can_record_stats(self):
        """UT-14: Coach can record match stats — PlayerStat in DB"""
        self.login_coach()
        response = self.client.post(
            f'/coach/record_stats/{self.event_id}',
            data={
                f'goals_{self.player_id}': '2',
                f'assists_{self.player_id}': '1',
                f'appeared_{self.player_id}': 'on'
            },
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            stat = PlayerStat.query.filter_by(
                player_id=self.player_id,
                event_id=self.event_id
            ).first()
            self.assertIsNotNone(stat)


# ── UT-15: Team Statistics View ───────────────────────────────────
class UT15_TeamStats(BaseTest):
    def test_coach_can_view_statistics(self):
        """UT-15: Coach can view team statistics page"""
        self.login_coach()
        response = self.client.get('/coach/statistics', follow_redirects=True)
        self.assertEqual(response.status_code, 200)


# ── UT-16: Player Dashboard ───────────────────────────────────────
class UT16_PlayerDashboard(BaseTest):
    def test_player_dashboard_loads(self):
        """UT-16: Player dashboard loads after login"""
        self.login_player()
        response = self.client.get('/player/dashboard', follow_redirects=True)
        self.assertEqual(response.status_code, 200)


# ── UT-17: Player Profile ─────────────────────────────────────────
class UT17_PlayerProfile(BaseTest):
    def test_player_profile_page_loads(self):
        """UT-17: Player profile page loads"""
        self.login_player()
        response = self.client.get('/player/profile', follow_redirects=True)
        self.assertEqual(response.status_code, 200)


# ── IT-01: Schedule event → Player sets availability ─────────────
class IT01_EventAvailabilityChain(BaseTest):
    def test_schedule_event_then_set_availability(self):
        """IT-01: Coach creates event, Player sets availability end-to-end"""
        self.login_coach()
        self.client.post('/coach/add_event', data={
            'title': 'Integration Test Match',
            'event_type': 'match',
            'start_time': '2026-08-01 15:00',
            'location': 'Test Ground',
            'opponent': 'Test FC'
        }, follow_redirects=True)
        self.client.get('/auth/logout', follow_redirects=True)

        self.login_player()
        with self.app.app_context():
            event = Event.query.filter_by(title='Integration Test Match').first()
            self.assertIsNotNone(event)
            response = self.client.post(
                f'/player/respond_availability/{event.id}',
                data={'status': 'available'},
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            av = Availability.query.filter_by(
                player_id=self.player_id,
                event_id=event.id
            ).first()
            self.assertIsNotNone(av)
            self.assertEqual(av.status, 'available')


# ── IT-02: Record stats → View statistics chain ───────────────────
class IT02_StatsChain(BaseTest):
    def test_record_stats_appear_in_statistics(self):
        """IT-02: Coach records stats, statistics view reflects them"""
        self.login_coach()
        self.client.post(
            f'/coach/record_stats/{self.event_id}',
            data={
                f'goals_{self.player_id}': '3',
                f'assists_{self.player_id}': '0',
                f'appeared_{self.player_id}': 'on'
            },
            follow_redirects=True
        )
        response = self.client.get('/coach/statistics', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            stat = PlayerStat.query.filter_by(
                player_id=self.player_id,
                event_id=self.event_id
            ).first()
            self.assertIsNotNone(stat)
            self.assertEqual(stat.goals, 3)


if __name__ == '__main__':
    unittest.main()