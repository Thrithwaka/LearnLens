from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string
import json
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# Role model for user roles
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.String(100))
    users = db.relationship('User', backref='role', lazy=True)

# User model with enhanced features
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unique_id = db.Column(db.String(20), unique=True, nullable=False)  # Format: ccf@FFLL1234
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    profile_pic = db.Column(db.String(200), nullable=True, default='default.png')
    created_at = db.Column(db.DateTime, default=datetime.now)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    created_quizzes = db.relationship('Quiz', backref='creator', lazy=True, foreign_keys='Quiz.creator_id')
    quiz_attempts = db.relationship('Attempt', backref='user', lazy=True)
    
    @staticmethod
    def generate_unique_id(first_name, last_name):
        """Generate a unique ID for the user in format ccf@FFLL1234"""
        prefix = f"ccf@{first_name[:2].upper()}{last_name[:2].upper()}"
        random_part = ''.join(random.choices(string.digits, k=4))
        return f"{prefix}{random_part}"
    
    def set_password(self, password):
        """Set hashed password"""
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password, password)

# Quiz model with enhanced features
class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    duration = db.Column(db.Integer, nullable=False)  # in minutes (for the whole quiz)
    quiz_type = db.Column(db.String(20), nullable=False)  # 'live' or 'scheduled'
    status = db.Column(db.String(20), default='draft')  # 'draft', 'scheduled', 'active', 'ended'
    access_code = db.Column(db.String(6), unique=True, nullable=False)
    share_link = db.Column(db.String(150), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    started_at = db.Column(db.DateTime)
    ended_at = db.Column(db.DateTime)
    scheduled_time = db.Column(db.DateTime)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    questions = db.relationship('Question', backref='quiz', lazy=True, cascade="all, delete-orphan")
    attempts = db.relationship('Attempt', backref='quiz', lazy=True, cascade="all, delete-orphan")
    feedback = db.relationship('QuizFeedback', backref='quiz', lazy=True, cascade="all, delete-orphan")
    
    @staticmethod
    def generate_access_code():
        """Generate a random 6-digit access code"""
        return ''.join(random.choices(string.digits, k=6))
    
    def update_status(self):
        """Update the status of the quiz based on current time"""
        now = datetime.now()
        
        if self.status == 'draft':
            return
            
        if self.quiz_type == 'live':
            if not self.started_at:
                self.status = 'scheduled'
            elif now < self.started_at + timedelta(minutes=self.duration):
                self.status = 'active'
            else:
                self.status = 'ended'
        else:  # scheduled quiz
            if not self.scheduled_time:
                self.status = 'scheduled'
            elif now < self.scheduled_time:
                self.status = 'scheduled'
            elif now < self.scheduled_time + timedelta(minutes=self.duration):
                self.status = 'active'
            else:
                self.status = 'ended'
        
        db.session.commit()
    
    @property
    def current_status(self):
        """Get the current status of the quiz"""
        # Update status before returning
        self.update_status()
        return self.status
    
    def get_time_status_display(self):
        """Get a human-readable time status"""
        now = datetime.now()
        
        if self.quiz_type == 'live':
            if self.started_at:
                end_time = self.started_at + timedelta(minutes=self.duration)
                if now < end_time:
                    return f"Ends at {end_time.strftime('%H:%M')}"
                else:
                    return "Completed"
            return "Not started"
        else:  # scheduled quiz
            if self.status == 'scheduled':
                return f"Starts at {self.scheduled_time.strftime('%Y-%m-%d %H:%M')}"
            elif self.status == 'active':
                end_time = self.scheduled_time + timedelta(minutes=self.duration)
                return f"Ends at {end_time.strftime('%H:%M')}"
            return "Completed"
    
    def calculate_results(self):
        """Calculate overall quiz results and analytics"""
        results = {
            'total_participants': 0,
            'average_score': 0,
            'highest_score': 0,
            'lowest_score': 0,
            'question_stats': [],
            'emotion_data': {}
        }
        
        # Get all completed attempts
        completed_attempts = [a for a in self.attempts if a.completed_at is not None]
        
        if not completed_attempts:
            return results
        
        results['total_participants'] = len(completed_attempts)
        
        # Calculate scores
        scores = []
        all_emotions = {}
        
        for attempt in completed_attempts:
            score = attempt.calculate_score()
            scores.append(score)
            
            # Aggregate emotions
            for answer in attempt.answers:
                if answer.emotions:
                    emotions_data = json.loads(answer.emotions) if isinstance(answer.emotions, str) else answer.emotions
                    question_id = str(answer.question_id)
                    
                    if question_id not in all_emotions:
                        all_emotions[question_id] = {}
                    
                    for emotion, value in emotions_data.items():
                        if emotion not in all_emotions[question_id]:
                            all_emotions[question_id][emotion] = []
                        all_emotions[question_id][emotion].append(value)
        
        # Calculate average scores
        results['average_score'] = sum(scores) / len(scores) if scores else 0
        results['highest_score'] = max(scores) if scores else 0
        results['lowest_score'] = min(scores) if scores else 0
        
        # Process question stats
        for question in self.questions:
            question_stats = {
                'id': question.id,
                'text': question.text,
                'correct_answers': 0,
                'incorrect_answers': 0,
                'average_time': 0
            }
            
            answer_times = []
            
            for attempt in completed_attempts:
                for answer in attempt.answers:
                    if answer.question_id == question.id:
                        if answer.user_answer == question.correct_answer:
                            question_stats['correct_answers'] += 1
                        else:
                            question_stats['incorrect_answers'] += 1
                        
                        if answer.answer_time:
                            answer_times.append(answer.answer_time)
            
            if answer_times:
                question_stats['average_time'] = sum(answer_times) / len(answer_times)
            
            results['question_stats'].append(question_stats)
        
        # Process emotion data - calculate averages
        emotion_averages = {}
        for question_id, emotions in all_emotions.items():
            emotion_averages[question_id] = {}
            for emotion, values in emotions.items():
                emotion_averages[question_id][emotion] = sum(values) / len(values) if values else 0
        
        results['emotion_data'] = emotion_averages
        
        return results

# Question model with enhanced features
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    text = db.Column(db.Text)
    image = db.Column(db.String(200))
    option1 = db.Column(db.String(200), nullable=False)
    option2 = db.Column(db.String(200), nullable=False)
    option3 = db.Column(db.String(200), nullable=False)
    option4 = db.Column(db.String(200), nullable=False)
    correct_answer = db.Column(db.String(200), nullable=False)
    time_limit = db.Column(db.Integer, nullable=False)  # in seconds for this specific question
    order = db.Column(db.Integer, default=0)  # For ordering questions within a quiz
    
    # Relationships
    answers = db.relationship('Answer', backref='question', lazy=True, cascade="all, delete-orphan")
    
    def get_statistics(self):
        """Calculate statistics for this question"""
        stats = {
            'correct_count': 0,
            'incorrect_count': 0,
            'average_time': 0,
            'emotion_data': {}
        }
        
        answers = self.answers
        if not answers:
            return stats
        
        # Calculate correct/incorrect counts
        answer_times = []
        all_emotions = {}
        
        for answer in answers:
            if answer.user_answer == self.correct_answer:
                stats['correct_count'] += 1
            else:
                stats['incorrect_count'] += 1
            
            if answer.answer_time:
                answer_times.append(answer.answer_time)
            
            # Process emotions
            if answer.emotions:
                emotions_data = json.loads(answer.emotions) if isinstance(answer.emotions, str) else answer.emotions
                for emotion, value in emotions_data.items():
                    if emotion not in all_emotions:
                        all_emotions[emotion] = []
                    all_emotions[emotion].append(value)
        
        # Calculate average time
        if answer_times:
            stats['average_time'] = sum(answer_times) / len(answer_times)
        
        # Calculate average emotions
        for emotion, values in all_emotions.items():
            stats['emotion_data'][emotion] = sum(values) / len(values) if values else 0
        
        return stats

# Quiz attempt model
class Attempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.now)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    answers = db.relationship('Answer', backref='attempt', lazy=True, cascade="all, delete-orphan")
    
    def calculate_score(self):
        """Calculate the score for this attempt"""
        if not self.answers:
            return 0
        
        correct_answers = sum(1 for answer in self.answers 
                             if answer.user_answer == answer.question.correct_answer)
        
        return (correct_answers / len(self.answers)) * 100 if self.answers else 0
    
    def get_emotion_summary(self):
        """Get a summary of emotions across all answers"""
        emotions_summary = {}
        
        for answer in self.answers:
            if answer.emotions:
                emotions_data = json.loads(answer.emotions) if isinstance(answer.emotions, str) else answer.emotions
                for emotion, value in emotions_data.items():
                    if emotion not in emotions_summary:
                        emotions_summary[emotion] = []
                    emotions_summary[emotion].append(value)
        
        # Calculate averages
        return {emotion: sum(values)/len(values) if values else 0 
                for emotion, values in emotions_summary.items()}

# Answer model with facial expression data
class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('attempt.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    user_answer = db.Column(db.String(200))
    answer_time = db.Column(db.Float)  # Time taken to answer in seconds
    emotions = db.Column(db.JSON)  # Stores facial expression data as JSON
    answered_at = db.Column(db.DateTime, default=datetime.now)
    
    def get_correctness(self):
        """Check if the answer is correct"""
        return self.user_answer == self.question.correct_answer

# Feedback for quizzes
class QuizFeedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer)  # 1-5 stars
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationship
    user = db.relationship('User', backref='feedback_given', foreign_keys=[user_id])

# Home page content management for admin
class PageContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page_name = db.Column(db.String(50), nullable=False)
    section_name = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text)
    last_updated = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Define a unique constraint for page and section
    __table_args__ = (db.UniqueConstraint('page_name', 'section_name', name='unique_page_section'),)

# Emotion analysis model configurations
class EmotionConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    config_params = db.Column(db.JSON)  # Store model parameters as JSON
    last_updated = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))

# System settings
class SystemSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(50), unique=True, nullable=False)
    setting_value = db.Column(db.Text)
    description = db.Column(db.Text)
    last_updated = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))

# Create default admin function
def create_default_admin():
    # Check if admin role exists
    admin_role = Role.query.filter_by(name='Admin').first()
    if not admin_role:
        admin_role = Role(name='Admin', description='Administrator with full access')
        db.session.add(admin_role)
        db.session.commit()
    
    # Check if default admin exists
    admin = User.query.filter_by(username='Admin').first()
    if not admin:
        admin = User(
            unique_id=User.generate_unique_id('Admin', 'User'),
            username='Admin',
            email='admin@quizplatform.com',
            first_name='Admin',
            last_name='User',
            role_id=admin_role.id,
            is_admin=True
        )
        admin.set_password('20030909')
        db.session.add(admin)
        db.session.commit()