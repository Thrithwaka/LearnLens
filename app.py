from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from authlib.integrations.flask_client import OAuth
from flask_migrate import Migrate
from random import choices, randint
from string import ascii_uppercase
import os
from datetime import datetime, timedelta
import json
import random
import string
import os
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import json
import os
import random
import string
from sqlalchemy import or_, func, Float
from sqlalchemy.orm.exc import NoResultFound
from flask_sqlalchemy import SQLAlchemy
import base64
from datetime import datetime
import json
import random
import string
import base64
import numpy as np
import cv2
from datetime import datetime, timedelta
from deepface import DeepFace
import io
from PIL import Image
from flask import Blueprint, request, jsonify
from typing import Dict, Any
import time
from datetime import datetime







# Initialize Flask app ONCE
app = Flask(__name__)
app.config['SECRET_KEY'] = 'learnlens-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///learnlens.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size


os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'profiles'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'questions'), exist_ok=True)



# Initialize extensions ONCE
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
emotion_api = Blueprint('emotion_api', __name__)
api_bp = Blueprint('api', __name__)
admin_bp = Blueprint('admin', __name__)



oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id='7377312818-8gq8sv66717vfpsh22khu7s1bjgd1a46.apps.googleusercontent.com',
    client_secret='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',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
    client_kwargs={'scope': 'email profile'},
)

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ===== MODEL DEFINITIONS =====

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
    use_facial_analysis = db.Column(db.Boolean, default=False)
    shuffle_questions = db.Column(db.Boolean, default=False)
    shuffle_options = db.Column(db.Boolean, default=False)
    
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
                if not self.ended_at:
                    self.ended_at = self.started_at + timedelta(minutes=self.duration)
        else:  # scheduled quiz
            if not self.scheduled_time:
                self.status = 'scheduled'
            elif now < self.scheduled_time:
                self.status = 'scheduled'
            elif now < self.scheduled_time + timedelta(minutes=self.duration):
                self.status = 'active'
                if not self.started_at:
                    self.started_at = self.scheduled_time
            else:
                self.status = 'ended'
                if not self.ended_at:
                    self.ended_at = self.scheduled_time + timedelta(minutes=self.duration)
        
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
            'emotion_data': {},
            'satisfaction_data': {}
        }
        
        # Get all completed attempts
        completed_attempts = [a for a in self.attempts if a.completed_at is not None]
        
        if not completed_attempts:
            return results
        
        results['total_participants'] = len(completed_attempts)
        
        # Calculate scores
        scores = []
        all_emotions = {}
        satisfaction_scores = {
            'satisfied': 0,
            'unsatisfied': 0,
            'neutral': 0
        }
        
        for attempt in completed_attempts:
            score = attempt.calculate_score()
            scores.append(score)
            
            # Collect emotions data
            for answer in attempt.answers:
                if not answer.emotions:
                    continue
                    
                emotions_data = answer.emotions
                question_id = str(answer.question_id)
                
                if question_id not in all_emotions:
                    all_emotions[question_id] = {}
                
                # Aggregate raw emotions
                for emotion, value in emotions_data.items():
                    if emotion not in all_emotions[question_id]:
                        all_emotions[question_id][emotion] = []
                    
                    all_emotions[question_id][emotion].append(value)
                
                # Count satisfaction levels
                if emotions_data.get('satisfied', 0) > emotions_data.get('unsatisfied', 0):
                    satisfaction_scores['satisfied'] += 1
                elif emotions_data.get('unsatisfied', 0) > emotions_data.get('satisfied', 0):
                    satisfaction_scores['unsatisfied'] += 1
                else:
                    satisfaction_scores['neutral'] += 1
        
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
                'average_time': 0,
                'dominant_emotions': {}
            }
            
            answer_times = []
            question_emotions = {}
            
            for attempt in completed_attempts:
                for answer in attempt.answers:
                    if answer.question_id == question.id:
                        # Count correctness
                        if answer.user_answer == question.correct_answer:
                            question_stats['correct_answers'] += 1
                        else:
                            question_stats['incorrect_answers'] += 1
                        
                        # Track answer time
                        if answer.answer_time:
                            answer_times.append(answer.answer_time)
                        
                        # Collect emotions
                        if answer.emotions:
                            for emotion, value in answer.emotions.items():
                                if emotion not in question_emotions:
                                    question_emotions[emotion] = []
                                question_emotions[emotion].append(value)
            
            # Calculate average answer time
            if answer_times:
                question_stats['average_time'] = sum(answer_times) / len(answer_times)
            
            # Find dominant emotions for this question
            if question_emotions:
                for emotion, values in question_emotions.items():
                    question_stats['dominant_emotions'][emotion] = sum(values) / len(values) if values else 0
            
            results['question_stats'].append(question_stats)
        
        # Process emotion data - calculate averages
        emotion_averages = {}
        for question_id, emotions in all_emotions.items():
            emotion_averages[question_id] = {}
            for emotion, values in emotions.items():
                emotion_averages[question_id][emotion] = sum(values) / len(values) if values else 0
        
        results['emotion_data'] = emotion_averages
        
        # Calculate satisfaction percentages
        total_satisfaction_points = sum(satisfaction_scores.values())
        if total_satisfaction_points > 0:
            for key in satisfaction_scores:
                results['satisfaction_data'][key] = (satisfaction_scores[key] / total_satisfaction_points) * 100
        
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

class Attempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.now)
    completed_at = db.Column(db.DateTime)
    question_order = db.Column(db.JSON)  # Store the shuffled question IDs
    
    # Relationships
    answers = db.relationship('Answer', backref='attempt', lazy=True, cascade="all, delete-orphan")
    
    def calculate_score(self):
        """Calculate the score for this attempt"""
        if not self.answers:
            return 0

        # Get all questions that were asked using question_order if available
        import json
        question_ids = []
        if self.question_order:
            try:
                question_ids = json.loads(self.question_order) if isinstance(self.question_order, str) else self.question_order
            except (TypeError, json.JSONDecodeError):
                question_ids = []

        # If no valid question_order, use the questions from answers
        if not question_ids:
            question_ids = [answer.question_id for answer in self.answers]

        total_questions = len(question_ids)
        if total_questions == 0:
            return 0

        # Count correct answers
        correct_answers = 0
        for answer in self.answers:
            question = Question.query.get(answer.question_id)
            if not question:
                continue

            # IMPORTANT FIX: Handle both option keys and direct values
            user_value = answer.user_answer
            correct_value = question.correct_answer

            # If user_answer is an option key, get the actual value
            if user_value in ['option1', 'option2', 'option3', 'option4']:
                user_value = getattr(question, user_value)

            # If correct_answer is an option key, get the actual value
            if correct_value in ['option1', 'option2', 'option3', 'option4']:
                correct_value = getattr(question, correct_value)

            # Compare the actual values
            if str(user_value).strip() == str(correct_value).strip():
                correct_answers += 1

        # Calculate score percentage
        return (correct_answers / total_questions) * 100
    
    def get_emotion_summary(self):
        """Get a summary of emotions across all answers"""
        import json
        emotions_summary = {}
        
        for answer in self.answers:
            if not hasattr(answer, 'emotions') or not answer.emotions:
                continue
                
            emotions_data = {}
            try:
                if isinstance(answer.emotions, str):
                    emotions_data = json.loads(answer.emotions)
                else:
                    emotions_data = answer.emotions
            except (TypeError, json.JSONDecodeError):
                continue
                
            for emotion, value in emotions_data.items():
                if emotion not in emotions_summary:
                    emotions_summary[emotion] = []
                emotions_summary[emotion].append(float(value))
        
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
    option_order = db.Column(db.JSON)  # Store the shuffled option order
    
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

class QuestionEmotionData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    attempt_id = db.Column(db.Integer, db.ForeignKey('attempt.id'), nullable=False)
    emotions = db.Column(db.JSON)  # Stores aggregated emotion data for this question
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    quiz = db.relationship('Quiz', backref='emotion_data')
    question = db.relationship('Question', backref='emotion_data')
    attempt = db.relationship('Attempt', backref='emotion_data')




def get_answer_emotion_summary(self):
    """Get a summary of emotions for this answer"""
    if not self.emotions:
        return "No emotion data recorded"
    
    emotions_data = json.loads(self.emotions) if isinstance(self.emotions, str) else self.emotions
    
    # Calculate satisfaction levels
    satisfied = (emotions_data.get('happy', 0) + emotions_data.get('surprise', 0) * 0.5)
    unsatisfied = (emotions_data.get('sad', 0) + emotions_data.get('angry', 0) + 
                   emotions_data.get('fear', 0) + emotions_data.get('disgust', 0))
    neutral = emotions_data.get('neutral', 0)
    
    # Normalize to ensure total is 100%
    total = satisfied + unsatisfied + neutral
    if total > 0:
        factor = 100 / total
        satisfied *= factor
        unsatisfied *= factor
        neutral *= factor
    
    # Determine dominant emotion
    dominant = "neutral"
    max_value = neutral
    
    if satisfied > max_value:
        dominant = "satisfied"
        max_value = satisfied
    
    if unsatisfied > max_value:
        dominant = "unsatisfied"
        max_value = unsatisfied
    
    return {
        'dominant': dominant,
        'satisfied': round(satisfied),
        'unsatisfied': round(unsatisfied),
        'neutral': round(neutral),
        'raw_data': emotions_data
    }



# ===== USER LOADER =====
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Create default admin function
# def create_default_admin():
#     # Check if admin role exists
#     admin_role = Role.query.filter_by(name='Admin').first()
#     if not admin_role:
#         admin_role = Role(name='Admin', description='Administrator with full access')
#         db.session.add(admin_role)
#         db.session.commit()
    
#     # Check if default admin exists
#     admin = User.query.filter_by(username='Admin').first()
#     if not admin:
#         admin = User(
#             unique_id=User.generate_unique_id('Admin', 'User'),
#             username='Admin',
#             email='admin@quizplatform.com',
#             first_name='Admin',
#             last_name='User',
#             role_id=admin_role.id,
#             is_admin=True
#         )
#         admin.set_password('20030909')
#         db.session.add(admin)
#         db.session.commit()




@app.route('/analyze_emotion', methods=['POST'])
def analyze_emotion():
    try:
        # Get image data from request
        image_data = request.json.get('image_data', '')
        if not image_data:
            return jsonify({'success': False, 'message': 'No image data provided'})
        
        # Remove the data URL prefix if present
        if 'base64,' in image_data:
            image_data = image_data.split('base64,')[1]
        
        # Decode the base64 image
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to OpenCV format
        opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Detect faces
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        
        if len(faces) == 0:
            return jsonify({
                'success': True,
                'face_detected': False,
                'message': 'No face detected'
            })
        
        # Get the largest face
        largest_face = max(faces, key=lambda rect: rect[2] * rect[3])
        x, y, w, h = largest_face
        
        # Crop face region
        face_region = opencv_image[y:y+h, x:x+w]
        
        # Convert back to RGB for DeepFace
        rgb_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2RGB)
        
        # Analyze emotions with DeepFace
        analysis = DeepFace.analyze(rgb_face, actions=['emotion'], enforce_detection=False)
        emotions = analysis[0]['emotion']
        
        # Calculate satisfaction levels
        satisfaction_levels = {
            'satisfied': emotions['happy'] / 100.0,
            'neutral': emotions['neutral'] / 100.0,
            'unsatisfied': (emotions['sad'] + emotions['angry'] + emotions['fear'] + emotions['disgust']) / 400.0
        }
        
        # Convert emotions to 0-1 scale
        normalized_emotions = {k: v/100.0 for k, v in emotions.items()}
        
        # Create face image preview
        cv2.rectangle(opencv_image, (x, y), (x+w, y+h), (0, 255, 0), 2)
        face_preview = opencv_image[max(0, y-20):min(opencv_image.shape[0], y+h+20), 
                                 max(0, x-20):min(opencv_image.shape[1], x+w+20)]
        
        # Convert face preview to base64 for response
        _, buffer = cv2.imencode('.jpg', face_preview)
        face_image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return jsonify({
            'success': True,
            'face_detected': True,
            'emotions': normalized_emotions,
            'satisfaction_levels': satisfaction_levels,
            'face_image': f'data:image/jpeg;base64,{face_image_base64}'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@emotion_api.route('/api/save-emotion-data', methods=['POST'])
def save_emotion_data():
    """Save aggregated emotion data for a question"""
    try:
        data = request.get_json()
        
        # Required fields
        required_fields = ['quiz_id', 'question_id', 'attempt_id', 'emotions']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'Missing required field: {field}'})
        
        # Get or create emotion record for this question attempt
        from models import QuestionEmotionData, db
        
        emotion_data = QuestionEmotionData.query.filter_by(
            quiz_id=data['quiz_id'],
            question_id=data['question_id'],
            attempt_id=data['attempt_id']
        ).first()
        
        if emotion_data:
            # Update existing record
            emotion_data.emotions = data['emotions']
        else:
            # Create new record
            emotion_data = QuestionEmotionData(
                quiz_id=data['quiz_id'],
                question_id=data['question_id'],
                attempt_id=data['attempt_id'],
                emotions=data['emotions']
            )
            db.session.add(emotion_data)
        
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error saving emotion data: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})
    


def ensure_haarcascade():
    """Ensure the haarcascade file is available"""
    haarcascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    if not os.path.exists(haarcascade_path):
        # If the file doesn't exist in the expected location, download it
        import urllib.request
        haarcascade_url = "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml"
        os.makedirs(os.path.dirname(haarcascade_path), exist_ok=True)
        urllib.request.urlretrieve(haarcascade_url, haarcascade_path)
    return haarcascade_path


def format_datetime(value):
    """Format datetime for display in templates."""
    if value is None:
        return ""
    return value.strftime("%B %d, %Y %I:%M %p") 


@app.route('/api/detect_emotion', methods=['POST'])
@login_required
def detect_emotion():
    """API endpoint to detect emotions from webcam image"""
    try:
        data = request.json
        image_data = data.get('image')
        
        if not image_data:
            return jsonify({'success': False, 'message': 'No image data provided'})
        
        # Remove the data URL prefix and decode base64
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        # Decode base64 to image file
        image_bytes = base64.b64decode(image_data)
        img_array = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        # Use DeepFace for emotion detection
        try:
            result = DeepFace.analyze(img, actions=['emotion'], enforce_detection=False)
            
            # Extract emotion data
            if isinstance(result, list):
                emotions = result[0]['emotion']
            else:
                emotions = result['emotion']
            
            # Normalize emotions to sum to 1.0
            total = sum(emotions.values())
            normalized_emotions = {k: v/total for k, v in emotions.items()}
            
            # Map emotions to simplified categories
            simplified_emotions = {
                'happy': normalized_emotions.get('happy', 0),
                'sad': normalized_emotions.get('sad', 0),
                'angry': normalized_emotions.get('angry', 0),
                'fear': normalized_emotions.get('fear', 0),
                'surprise': normalized_emotions.get('surprise', 0),
                'neutral': normalized_emotions.get('neutral', 0),
                'disgust': normalized_emotions.get('disgust', 0),
                'satisfied': normalized_emotions.get('happy', 0) + normalized_emotions.get('neutral', 0) * 0.5,
                'unsatisfied': normalized_emotions.get('sad', 0) + normalized_emotions.get('angry', 0) + normalized_emotions.get('disgust', 0)
            }
            
            return jsonify({
                'success': True,
                'emotions': simplified_emotions
            })
            
        except Exception as e:
            # Handle case where no face is detected
            app.logger.error(f"DeepFace error: {str(e)}")
            return jsonify({
                'success': False, 
                'message': 'No face detected or error in emotion analysis'
            })
    
    except Exception as e:
        app.logger.error(f"Error in detect_emotion: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})



# ===== ROUTES =====

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/features')
def features():
    return render_template('features.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        # Store message in database or send email
        flash('Message sent successfully!', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('choice'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Extract first and last name from the username (simplified)
        name_parts = username.split()
        first_name = name_parts[0] if name_parts else username
        last_name = name_parts[-1] if len(name_parts) > 1 else ""
        
        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('register.html')
        
        # Check if username exists
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('Username already exists!', 'danger')
            return render_template('register.html')
        
        # Check if email exists
        email_exists = User.query.filter_by(email=email).first()
        if email_exists:
            flash('Email already exists!', 'danger')
            return render_template('register.html')
        
        # Initially assign a default role (will be updated after choice)
        default_role = Role.query.filter_by(name='user').first()
        if not default_role:
            # Create default role if it doesn't exist
            default_role = Role(name='user')
            db.session.add(default_role)
            db.session.commit()
        
        # Generate unique ID
        unique_id = User.generate_unique_id(first_name, last_name)
        
        # Create new user
        new_user = User(
            unique_id=unique_id,
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role_id=default_role.id,
            created_at=datetime.now(),
            last_login=datetime.now()
        )
        new_user.set_password(password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
    
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('choice'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Find user by username or email
        user = User.query.filter((User.username == username) | (User.email == username)).first()
        
        # Check if user exists and password is correct
        if not user or not user.check_password(password):
            flash('Invalid username or password!', 'danger')
            return render_template('login.html')
        
        # Update last login time
        user.last_login = datetime.now()
        db.session.commit()
        
        # Log in user
        login_user(user)
        flash('Logged in successfully!', 'success')
        
        # If user is admin, redirect to admin dashboard
        if user.is_admin:
            return redirect(url_for('admin'))
        
        # Otherwise redirect to choice page
        return redirect(url_for('choice'))
    
    return render_template('login.html')


@app.route('/admin')
@login_required
def admin_dashboard():
    # Get basic statistics
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    total_quizzes = Quiz.query.count()
    active_quizzes = Quiz.query.filter_by(status='active').count()

    # Get user registration data for the last 30 days
    thirty_days_ago = datetime.now() - timedelta(days=30)
    reg_data = db.session.query(
        func.date(User.created_at).label('date'),
        func.count(User.id).label('count')
    ).filter(User.created_at >= thirty_days_ago)\
     .group_by(func.date(User.created_at))\
     .all()

    reg_dates = [str(data.date) for data in reg_data]
    reg_counts = [data.count for data in reg_data]

    # Get quiz creation data
    quiz_data = db.session.query(
        func.date(Quiz.created_at).label('date'),
        func.count(Quiz.id).label('count')
    ).filter(Quiz.created_at >= thirty_days_ago)\
     .group_by(func.date(Quiz.created_at))\
     .all()

    quiz_dates = [str(data.date) for data in quiz_data]
    quiz_counts = [data.count for data in quiz_data]

    return render_template('admin.html',
                         total_users=total_users,
                         active_users=active_users,
                         total_quizzes=total_quizzes,
                         active_quizzes=active_quizzes,
                         reg_dates=reg_dates,
                         reg_counts=reg_counts,
                         quiz_dates=quiz_dates,
                         quiz_counts=quiz_counts)

# @app.route('/admin/users')
# @login_required
# def admin_users():
#     page = request.args.get('page', 1, type=int)
#     users = User.query.paginate(page=page, per_page=10)
#     return render_template('admin/users.html', users=users)

# @app.route('/admin/quizzes')
# @login_required
# def admin_quizzes():
#     page = request.args.get('page', 1, type=int)
#     quizzes = Quiz.query.paginate(page=page, per_page=10)
#     return render_template('admin/quizzes.html', quizzes=quizzes)

# @app.route('/admin/roles')
# @login_required
# def admin_roles():
#     roles = Role.query.all()
#     return render_template('admin/roles.html', roles=roles)

# @app.route('/admin/settings')
# @login_required
# def admin_settings():
#     settings = SystemSetting.query.all()
#     emotion_configs = EmotionConfig.query.all()
#     return render_template('admin/settings.html',
#                          settings=settings,
#                          emotion_configs=emotion_configs)

# @app.route('/admin/user/<int:user_id>', methods=['GET', 'POST'])
# @login_required
# def admin_user_detail(user_id):
#     user = User.query.get_or_404(user_id)
#     if request.method == 'POST':
#         user.is_active = bool(request.form.get('is_active'))
#         user.is_admin = bool(request.form.get('is_admin'))
#         user.role_id = request.form.get('role_id', type=int)
        
#         db.session.commit()
#         flash('User updated successfully!', 'success')
#         return redirect(url_for('admin_users'))
    
#     roles = Role.query.all()
#     return render_template('admin/user_detail.html', user=user, roles=roles)

# @app.route('/admin/quiz/<int:quiz_id>')
# @login_required
# def admin_quiz_detail(quiz_id):
#     quiz = Quiz.query.get_or_404(quiz_id)
#     results = quiz.calculate_results()
#     return render_template('admin/quiz_detail.html', quiz=quiz, results=results)

# @app.route('/admin/analytics')
# @login_required
# def admin_analytics():
#     # Get overall system analytics
#     total_attempts = Attempt.query.count()
#     completion_rate = db.session.query(
#         func.count(Attempt.id) * 100.0 / func.count(distinct(Attempt.quiz_id))
#     ).filter(Attempt.completed_at.isnot(None)).scalar() or 0

#     # Get emotion analytics if available
#     emotion_data = db.session.query(
#         Question.id,
#         func.avg(Answer.emotions['satisfaction'].cast(Float)),
#         func.avg(Answer.emotions['confusion'].cast(Float))
#     ).join(Answer).group_by(Question.id).all()

#     return render_template('admin/analytics.html',
#                          total_attempts=total_attempts,
#                          completion_rate=completion_rate,
#                          emotion_data=emotion_data)

# @app.route('/admin/settings/update', methods=['POST'])
# @login_required
# def update_settings():
#     if request.method == 'POST':
#         for key, value in request.form.items():
#             if key.startswith('setting_'):
#                 setting_id = int(key.split('_')[1])
#                 setting = SystemSetting.query.get(setting_id)
#                 if setting:
#                     setting.setting_value = value
#                     setting.updated_by = current_user.id
        
#         db.session.commit()
#         flash('Settings updated successfully!', 'success')
#         return redirect(url_for('admin_settings'))




@app.route('/login/google')
def google_login():
    redirect_uri = url_for('google_authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/login/google/authorize')
def google_authorize():
    token = google.authorize_access_token()
    resp = google.get('userinfo')
    user_info = resp.json()
    
    # Check if user exists
    user = User.query.filter_by(email=user_info['email']).first()
    
    if not user:
        # Create a new user
        name_parts = user_info['name'].split()
        first_name = name_parts[0] if name_parts else user_info.get('given_name', '')
        last_name = name_parts[-1] if len(name_parts) > 1 else user_info.get('family_name', '')
        
        # Get default role
        default_role = Role.query.filter_by(name='user').first()
        if not default_role:
            default_role = Role(name='user')
            db.session.add(default_role)
            db.session.commit()
        
        # Generate unique ID
        unique_id = User.generate_unique_id(first_name, last_name)
        
        # Create new user with Google info
        user = User(
            unique_id=unique_id,
            username=user_info['email'].split('@')[0],  # Use part of email as username
            email=user_info['email'],
            first_name=first_name,
            last_name=last_name,
            profile_pic=user_info.get('picture', 'default.png'),
            role_id=default_role.id,
            is_active=True,
            password=None  # No password for Google users
        )
        
        db.session.add(user)
        db.session.commit()
    
    # Update last login time
    user.last_login = datetime.now()
    db.session.commit()
    
    # Log in the user
    login_user(user)
    flash('Successfully logged in with Google!', 'success')
    
    # Redirect to choice page
    return redirect(url_for('choice'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/choice')
@login_required
def choice():
    # Add your choice route logic here
    return render_template('choice.html')




@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard showing user's quizzes and attempts"""
    # Get quizzes created by the user
    created_quizzes = Quiz.query.filter_by(creator_id=current_user.id).all()
    for quiz in created_quizzes:
        quiz.update_status()  # Update quiz status before displaying
    
    # Get quizzes participated in by the user
    attempted_quizzes = db.session.query(Quiz).join(Attempt).filter(
        Attempt.user_id == current_user.id
    ).distinct().all()
    
    # Organize created quizzes by status
    active_quizzes = [q for q in created_quizzes if q.status == 'active']
    scheduled_quizzes = [q for q in created_quizzes if q.status == 'scheduled']
    ended_quizzes = [q for q in created_quizzes if q.status == 'ended']
    draft_quizzes = [q for q in created_quizzes if q.status == 'draft']

    def format_datetime(dt, format='%Y-%m-%d %H:%M'):
        """Format datetime objects"""
        if dt:
            return dt.strftime(format)
        return ''
    
    return render_template(
        'dashboard.html',
        active_quizzes=active_quizzes,
        scheduled_quizzes=scheduled_quizzes,
        ended_quizzes=ended_quizzes,
        draft_quizzes=draft_quizzes,
        format_datetime=format_datetime,
        attempted_quizzes=attempted_quizzes
    )




@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username')
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        # Update user details
        current_user.username = username
        current_user.email = email
        current_user.first_name = first_name
        current_user.last_name = last_name
        
        # Handle profile picture upload
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and file.filename != '' and allowed_file(file.filename):
                # Save the new profile picture
                filename = secure_filename(file.filename)
                # Add user ID to filename to make it unique
                filename = f"{current_user.id}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                
                # Update user's profile picture in the database
                current_user.profile_pic = filename
        
        # Save changes to database
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('edit_profile.html')

@app.route('/quiz/create', methods=['GET', 'POST'])
@login_required
def create_quiz():
    """Create a new quiz"""
    if request.method == 'POST':
        # Process form data
        title = request.form.get('title')
        description = request.form.get('description')
        duration = int(request.form.get('duration', 10))
        quiz_type = request.form.get('quiz_type')
        use_facial_analysis = 'use_facial_analysis' in request.form
        shuffle_questions = 'shuffle_questions' in request.form
        shuffle_options = 'shuffle_options' in request.form
        
        # Create new quiz
        new_quiz = Quiz(
            title=title,
            description=description,
            duration=duration,
            quiz_type=quiz_type,
            status='draft',
            access_code=Quiz.generate_access_code(),
            creator_id=current_user.id,
            use_facial_analysis=use_facial_analysis,
            shuffle_questions=shuffle_questions,
            shuffle_options=shuffle_options
        )
        
        # Handle scheduled time if it's a scheduled quiz
        if quiz_type == 'scheduled':
            scheduled_date = request.form.get('scheduled_date')
            scheduled_time = request.form.get('scheduled_time')
            if scheduled_date and scheduled_time:
                scheduled_datetime = datetime.strptime(f"{scheduled_date} {scheduled_time}", "%Y-%m-%d %H:%M")
                new_quiz.scheduled_time = scheduled_datetime
                
                # If scheduled time is in the future, mark as scheduled
                if scheduled_datetime > datetime.now():
                    new_quiz.status = 'scheduled'
        
        # Generate share link
        base_url = request.host_url.rstrip('/')
        new_quiz.share_link = f"{base_url}/quiz/join/{new_quiz.access_code}"
        
        db.session.add(new_quiz)
        db.session.commit()
        
        flash('Quiz created successfully!', 'success')
        return redirect(url_for('edit_quiz', quiz_id=new_quiz.id))
    
    return render_template('create_quiz.html')


@app.route('/api/question/<int:question_id>', methods=['GET'])
@login_required
def get_question(question_id):
    """API endpoint to get question data for editing"""
    question = Question.query.get_or_404(question_id)
    
    # Verify ownership through quiz
    quiz = Quiz.query.get(question.quiz_id)
    if quiz.creator_id != current_user.id:
        return jsonify({'error': 'Not authorized'}), 403
    
    # Return question data
    return jsonify({
        'id': question.id,
        'text': question.text,
        'image': question.image,
        'option1': question.option1,
        'option2': question.option2,
        'option3': question.option3,
        'option4': question.option4,
        'correct_answer': question.correct_answer,
        'time_limit': question.time_limit,
        'order': question.order
    })

# @app.route('/join_game', methods=['GET', 'POST'])
# @login_required
# def join_game():
#     if request.method == 'POST':
#         access_code = request.form.get('access_code')
        
#         # Find the quiz with the given access code
#         quiz = Quiz.query.filter_by(access_code=access_code).first()
        
#         if not quiz:
#             flash('Invalid access code. Please try again.', 'danger')
#             return redirect(url_for('join_game'))
        
#         # Check if quiz is active
#         quiz.update_status()
#         if quiz.current_status != 'active':
#             flash('This quiz is not currently active.', 'warning')
#             return redirect(url_for('join_game'))
        
#         # Check if user already has an attempt for this quiz
#         existing_attempt = Attempt.query.filter_by(
#             quiz_id=quiz.id,
#             user_id=current_user.id,
#             completed_at=None
#         ).first()
        
#         if existing_attempt:
#             # Continue existing attempt
#             return redirect(url_for('continue_quiz', attempt_id=existing_attempt.id))
        
#         # Create new attempt
#         new_attempt = Attempt(
#             quiz_id=quiz.id,
#             user_id=current_user.id
#         )
#         db.session.add(new_attempt)
#         db.session.commit()
        
#         return redirect(url_for('take_quiz', attempt_id=new_attempt.id))
    
#     return render_template('join_game.html')



def detect_emotions(base64_image: str) -> Dict[str, float]:
    """
    Detect emotions from base64 encoded image using DeepFace
    
    Args:
        base64_image: Base64 encoded image string
    
    Returns:
        Dictionary of emotion probabilities
    """
    try:
        start_time = time.time()
        # Decode base64 image
        if ',' in base64_image:
            image_data = base64_image.split(',')[1]
        else:
            image_data = base64_image
            
        image_bytes = base64.b64decode(image_data)
        
        # Convert to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None or img.size == 0:
            raise ValueError("Invalid image data")
            
        # Analyze emotions using DeepFace
        # Use silent=True to reduce terminal output
        result = DeepFace.analyze(img, actions=['emotion'], enforce_detection=False, silent=True)
        
        # Extract emotion data
        if isinstance(result, list):
            emotions = result[0]['emotion']
        else:
            emotions = result['emotion']
            
        # Convert to dictionary with float values
        emotions_dict = {k: float(v)/100.0 for k, v in emotions.items()}
        
        processing_time = time.time() - start_time
        print(f"Emotion detection completed in {processing_time:.2f} seconds")
        
        return emotions_dict
        
    except Exception as e:
        print(f"Error detecting emotions: {str(e)}")
        # Return default values if detection fails
        return {
            "angry": 0.0,
            "disgust": 0.0,
            "fear": 0.0,
            "happy": 0.0,
            "sad": 0.0,
            "surprise": 0.0,
            "neutral": 1.0  # Default to neutral if detection fails
        }

def map_to_satisfaction_levels(emotions: Dict[str, float]) -> Dict[str, float]:
    """
    Map raw emotion scores to satisfaction levels for quiz UI
    
    Args:
        emotions: Dictionary of emotion probabilities from DeepFace
    
    Returns:
        Dictionary with satisfied, neutral, and unsatisfied scores
    """
    # Calculate satisfaction based on positive emotions
    # Happy is the primary indicator, surprise is secondary
    satisfied = emotions.get('happy', 0) * 0.8 + emotions.get('surprise', 0) * 0.2
    
    # Use neutral directly
    neutral = emotions.get('neutral', 0)
    
    # Calculate unsatisfied based on negative emotions with weighted contribution
    unsatisfied = (
        emotions.get('sad', 0) * 0.4 + 
        emotions.get('angry', 0) * 0.3 + 
        emotions.get('fear', 0) * 0.15 + 
        emotions.get('disgust', 0) * 0.15
    )
    
    # Normalize to ensure the sum is approximately 1.0
    total = satisfied + neutral + unsatisfied
    if total > 0:
        satisfied /= total
        neutral /= total
        unsatisfied /= total
    
    return {
        'satisfied': round(satisfied, 4),
        'neutral': round(neutral, 4),
        'unsatisfied': round(unsatisfied, 4)
    }

@app.route('/quiz/result/<int:quiz_id>')
@login_required
def quiz_result(quiz_id):
    """View quiz results"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Get user's attempt
    attempt = Attempt.query.filter_by(quiz_id=quiz_id, user_id=current_user.id).order_by(Attempt.completed_at.desc()).first()
    
    # If no attempt or not completed, redirect to take the quiz
    if not attempt:
        flash('No attempt found for this quiz', 'warning')
        return redirect(url_for('dashboard'))
    
    if not attempt.completed_at:
        return redirect(url_for('take_quiz', quiz_id=quiz_id))
    
    # Get all questions with user answers
    questions_with_answers = []
    
    # Use the stored question order if available, otherwise use quiz questions order
    question_ids = []
    if attempt.question_order:
        try:
            # If question_order is stored as a JSON string
            import json
            question_ids = json.loads(attempt.question_order) if isinstance(attempt.question_order, str) else attempt.question_order
        except (TypeError, json.JSONDecodeError):
            # If it's already a list or couldn't be parsed
            question_ids = attempt.question_order
    
    # Fallback to all quiz questions if no valid question_order
    if not question_ids:
        question_ids = [q.id for q in quiz.questions]
    
    # Track correct answers
    correct_answers = 0
    
    # Process each question
    for question_id in question_ids:
        question = Question.query.get(question_id)
        if not question:
            continue
            
        answer = Answer.query.filter_by(attempt_id=attempt.id, question_id=question_id).first()
        
        # Default values if no answer found
        is_correct = False
        user_answer = None
        answer_time = None
        emotions = None
        
        # Process answer data if it exists
        if answer:
            user_answer = answer.user_answer
            answer_time = answer.answer_time
            
            # IMPORTANT FIX: Handling both option keys and direct answers
            user_value = user_answer
            correct_value = question.correct_answer
            
            # If user_answer is an option key, get the actual value
            if user_answer in ['option1', 'option2', 'option3', 'option4']:
                user_value = getattr(question, user_answer)
            
            # If correct_answer is an option key, get the actual value
            if correct_value in ['option1', 'option2', 'option3', 'option4']:
                correct_value = getattr(question, correct_value)
            
            # Log the comparison for debugging
            app.logger.debug(f"Answer comparison: User '{user_value}' vs Correct '{correct_value}'")
            
            # Check if answer is correct by comparing actual values
            if str(user_value).strip() == str(correct_value).strip():
                is_correct = True
                correct_answers += 1
            
            # Get emotions if available
            if hasattr(answer, 'emotions') and answer.emotions:
                try:
                    if isinstance(answer.emotions, str):
                        import json
                        emotions = json.loads(answer.emotions)
                    else:
                        emotions = answer.emotions
                except (TypeError, json.JSONDecodeError):
                    emotions = None
        
        # Add question with answer data to the list
        questions_with_answers.append({
            'question': question,
            'user_answer': user_answer,
            'is_correct': is_correct,
            'answer_time': answer_time,
            'emotions': emotions
        })
    
    # Calculate score as percentage
    total_questions = len(question_ids)
    score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
    
    # Log the score calculation for debugging
    app.logger.debug(f"Quiz {quiz_id} score calculation: {correct_answers}/{total_questions} = {score}%")
    
    # Get emotion summary if facial analysis was used
    emotion_summary = None
    if quiz.use_facial_analysis:
        if hasattr(attempt, 'get_emotion_summary'):
            emotion_summary = attempt.get_emotion_summary()
        elif hasattr(attempt, 'emotion_summary'):
            # Try to get directly from property if method doesn't exist
            emotion_summary = attempt.emotion_summary
    
    # Helper function for formatting datetime
    def format_datetime(dt):
        if dt:
            return dt.strftime('%B %d, %Y at %I:%M %p')
        return "N/A"
    
    return render_template(
        'quiz_result.html',
        quiz=quiz,
        attempt=attempt,
        score=score,
        questions_with_answers=questions_with_answers,
        format_datetime=format_datetime,
        getattr=getattr,
        emotion_summary=emotion_summary
    )





@app.route('/quiz/join/<access_code>')
def join_quiz_by_link(access_code):
    """Join a quiz directly using an access code from a link"""
    # Find quiz by access code
    quiz = Quiz.query.filter_by(access_code=access_code).first_or_404()
    
    # If user is not logged in, redirect to login
    if not current_user.is_authenticated:
        # Store the access code in session to redirect back after login
        session['joining_quiz_code'] = access_code
        flash('Please log in to join the quiz', 'info')
        return redirect(url_for('login'))
    
    # Update quiz status
    quiz.update_status()
    
    # Check if quiz is active
    if quiz.status != 'active':
        if quiz.status == 'scheduled':
            flash('This quiz has not started yet', 'warning')
        elif quiz.status == 'ended':
            flash('This quiz has already ended', 'warning')
        else:
            flash('This quiz is not available', 'warning')
        return redirect(url_for('dashboard'))
    
    # Check if user has already attempted this quiz
    existing_attempt = Attempt.query.filter_by(quiz_id=quiz.id, user_id=current_user.id).first()
    if existing_attempt and existing_attempt.completed_at:
        flash('You have already completed this quiz', 'info')
        return redirect(url_for('quiz_result', quiz_id=quiz.id))
    
    # Start new attempt or continue existing one
    if not existing_attempt:
        attempt = Attempt(quiz_id=quiz.id, user_id=current_user.id)
        db.session.add(attempt)
        db.session.commit()
    
    return redirect(url_for('take_quiz', quiz_id=quiz.id))

@app.route('/profile')
@login_required
def profile():
    """View and edit user profile"""
    return render_template('profile.html')



@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update user profile"""
    if request.method == 'POST':
        current_user.first_name = request.form.get('first_name')
        current_user.last_name = request.form.get('last_name')
        current_user.email = request.form.get('email')
        
        # Update password if provided
        new_password = request.form.get('new_password')
        if new_password:
            current_password = request.form.get('current_password')
            if not current_user.check_password(current_password):
                flash('Current password is incorrect', 'danger')
                return redirect(url_for('profile'))
            
            current_user.set_password(new_password)
        
        # Handle profile picture upload
        if 'profile_pic' in request.files:
            profile_pic = request.files['profile_pic']
            if profile_pic and profile_pic.filename:
                # Save profile picture
                filename = secure_filename(profile_pic.filename)
                pic_path = os.path.join(app.config['UPLOAD_FOLDER'], 'profiles', filename)
                profile_pic.save(pic_path)
                current_user.profile_pic = filename
        
        db.session.commit()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('profile'))


@app.route('/submit_feedback/<int:quiz_id>', methods=['POST'])
@login_required
def submit_feedback(quiz_id):
    quiz = db.session.get(Quiz, quiz_id)
    
    if not quiz:
        flash('Quiz not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get form data
    rating = request.form.get('rating')
    comment = request.form.get('comment')
    
    # Create new feedback
    feedback = QuizFeedback(
        quiz_id=quiz_id,
        user_id=current_user.id,
        rating=rating,
        comment=comment
    )
    
    db.session.add(feedback)
    db.session.commit()
    
    flash('Thank you for your feedback!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/attempt_details/<int:attempt_id>')
@login_required
def attempt_details(attempt_id):
    # Get the attempt object
    attempt = Attempt.query.get_or_404(attempt_id)
    
    # Security check - only allow the attempt creator or quiz creator to view details
    if current_user.id != attempt.user_id and current_user.id != attempt.quiz.creator_id and not current_user.is_admin:
        flash('You do not have permission to view this attempt.', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('attempt_details.html', attempt=attempt)

@app.route('/continue_quiz/<int:attempt_id>')
@login_required
def continue_quiz(attempt_id):
    attempt = Attempt.query.get_or_404(attempt_id)
    
    # Check if user is the owner of the attempt
    if attempt.user_id != current_user.id:
        abort(403)  # Forbidden
    
    # Check if attempt is already completed
    if attempt.completed_at:
        return redirect(url_for('attempt_details', attempt_id=attempt.id))
    
    return redirect(url_for('take_quiz', attempt_id=attempt.id))

@app.route('/quiz/take/<int:quiz_id>')
@login_required
def take_quiz(quiz_id):
    """Take a quiz"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Update quiz status
    quiz.update_status()
    
    # Check if quiz is active
    if quiz.status != 'active':
        flash('This quiz is not currently active', 'warning')
        return redirect(url_for('dashboard'))
    
    # Get or create attempt
    attempt = Attempt.query.filter_by(quiz_id=quiz_id, user_id=current_user.id).first()
    
    # Handle completed attempts
    if attempt and attempt.completed_at:
        flash('You have already completed this quiz', 'info')
        return redirect(url_for('quiz_result', quiz_id=quiz_id))
    
    # Get all questions for this quiz
    all_questions = Question.query.filter_by(quiz_id=quiz_id).order_by(Question.order).all()
    if not all_questions:
        flash('This quiz has no questions', 'warning')
        return redirect(url_for('dashboard'))
    
    # Create question order list
    question_order = []
    if attempt and attempt.question_order:
        try:
            # Try to use existing question order
            question_order = attempt.question_order
        except Exception:
            # If there's an error, we'll create a new order below
            question_order = []
    
    # If we don't have a valid question order, create one
    if not question_order:
        if quiz.shuffle_questions:
            # Shuffle questions
            question_ids = [q.id for q in all_questions]
            random.seed(current_user.id + quiz_id)
            random.shuffle(question_ids)
            question_order = question_ids
        else:
            # Use original order
            question_order = [q.id for q in all_questions]
            
        # Create or update attempt with new question order
        if not attempt:
            attempt = Attempt(
                quiz_id=quiz_id, 
                user_id=current_user.id,
                question_order=question_order
            )
            db.session.add(attempt)
        else:
            attempt.question_order = question_order
            
        db.session.commit()
    
    # Get answered questions
    answered_question_ids = []
    if attempt:
        answered_question_ids = [answer.question_id for answer in attempt.answers]
    
    # Find next unanswered question
    next_question_id = None
    # Use a safe check to handle potential issues with question_order
    for q_id in question_order:
        if q_id not in answered_question_ids:
            next_question_id = q_id
            break
    
    # Fallback: If we still don't have a next question, use the first unanswered question
    if next_question_id is None:
        for question in all_questions:
            if question.id not in answered_question_ids:
                next_question_id = question.id
                break
    
    # All questions answered - complete the attempt
    if next_question_id is None:
        if attempt:
            attempt.completed_at = datetime.now()
            db.session.commit()
        return redirect(url_for('quiz_result', quiz_id=quiz_id))
    
    next_question = Question.query.get(next_question_id)
    
    # Calculate remaining time for the quiz
    if quiz.quiz_type == 'live':
        end_time = quiz.started_at + timedelta(minutes=quiz.duration)
    else:
        end_time = quiz.scheduled_time + timedelta(minutes=quiz.duration)
    
    remaining_seconds = max(0, (end_time - datetime.now()).total_seconds())
    
    # Set up for facial analysis
    use_facial_analysis = quiz.use_facial_analysis
    
    # Determine question number (for display purposes)
    question_number = len(answered_question_ids) + 1
    
    # Prepare shuffled options if needed
    options = [
        {'key': 'option1', 'text': next_question.option1},
        {'key': 'option2', 'text': next_question.option2},
        {'key': 'option3', 'text': next_question.option3},
        {'key': 'option4', 'text': next_question.option4}
    ]
    
    # Shuffle options if enabled
    if quiz.shuffle_options:
        # Use a deterministic shuffle based on attempt id, question id, and user id
        seed_value = 0
        if attempt:
            seed_value = attempt.id
        seed_value += next_question.id + current_user.id
        random.seed(seed_value)
        random.shuffle(options)
    
    # Map shuffled options to A, B, C, D
    option_markers = ['A', 'B', 'C', 'D']
    for i, option in enumerate(options):
        option['marker'] = option_markers[i]
    
    return render_template(
        'take_quiz.html',
        quiz=quiz,
        question=next_question,
        attempt=attempt,
        question_number=question_number,
        total_questions=len(all_questions),
        remaining_seconds=remaining_seconds,
        use_facial_analysis=use_facial_analysis,
        options=options
    )







@app.route('/quiz/answer/<int:quiz_id>/<int:question_id>', methods=['POST'])
@login_required
def submit_answer(quiz_id, question_id):
    """Submit an answer for a quiz question with emotion data"""
    quiz = Quiz.query.get_or_404(quiz_id)
    question = Question.query.get_or_404(question_id)
    
    # Verify question belongs to quiz
    if question.quiz_id != quiz_id:
        return jsonify({'success': False, 'message': 'Question does not belong to this quiz'})
    
    # Update quiz status
    quiz.update_status()
    
    # Check if quiz is still active
    if quiz.status != 'active':
        return jsonify({'success': False, 'message': 'Quiz is no longer active'})
    
    # Get attempt
    attempt = Attempt.query.filter_by(quiz_id=quiz_id, user_id=current_user.id).first()
    if not attempt:
        return jsonify({'success': False, 'message': 'No active attempt found'})
    
    # Check if question already answered
    existing_answer = Answer.query.filter_by(attempt_id=attempt.id, question_id=question_id).first()
    if existing_answer:
        return jsonify({'success': False, 'message': 'Question already answered'})
    
    # Process answer - ensure consistent format
    user_answer = request.form.get('answer', '').strip()
    answer_time = float(request.form.get('answer_time', 0))
    
    # Log the captured answer for debugging
    app.logger.debug(f"Captured answer for question {question_id}: '{user_answer}'")
    
    # Get option order if shuffled
    option_order = None
    if quiz.shuffle_options:
        option_order_str = request.form.get('option_order')
        if option_order_str:
            try:
                import json
                option_order = json.loads(option_order_str)
            except json.JSONDecodeError:
                option_order = None
    
    # Process emotions data if available
    emotions_data = request.form.get('emotions_data')
    emotions_json = None
    
    if emotions_data:
        try:
            import json
            emotions_json = json.loads(emotions_data)
            # Validate emotions data
            if not isinstance(emotions_json, dict):
                emotions_json = {}
        except json.JSONDecodeError:
            emotions_json = {}
    
    # Create answer record
    answer = Answer(
        attempt_id=attempt.id,
        question_id=question_id,
        user_answer=user_answer,
        answer_time=answer_time,
        emotions=emotions_json,
        option_order=option_order
    )
    
    db.session.add(answer)
    db.session.commit()
    
    # Check if all questions answered
    answered_count = Answer.query.filter_by(attempt_id=attempt.id).count()
    total_questions = len(attempt.question_order) if attempt.question_order else len(quiz.questions)
    
    if answered_count >= total_questions:
        attempt.completed_at = datetime.now()
        db.session.commit()
        return jsonify({'success': True, 'completed': True, 'redirect': url_for('quiz_result', quiz_id=quiz_id)})
    
    return jsonify({'success': True, 'completed': False})


@app.route('/quiz/analytics/<int:quiz_id>')
@login_required
def quiz_analytics(quiz_id):
    """Show quiz analytics for quiz creator"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if user is the creator of the quiz
    if quiz.creator_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to view this quiz analytics', 'danger')
        return redirect(url_for('dashboard'))
    
    # Calculate results
    results = quiz.calculate_results()
    
    # Get emotion data by question
    emotion_analysis = {}
    for question in quiz.questions:
        # Get all emotions for this question across all attempts
        question_emotions = {}
        
        # Get answers for this question
        answers = Answer.query.join(Attempt).filter(
            Attempt.quiz_id == quiz_id,
            Answer.question_id == question.id,
            Answer.emotions.isnot(None)
        ).all()
        
        if not answers:
            continue
        
        # Initialize emotion counters
        emotion_counts = {
            'happy': 0,
            'sad': 0,
            'angry': 0,
            'fear': 0,
            'surprise': 0,
            'neutral': 0,
            'disgust': 0,
            'satisfied': 0,
            'unsatisfied': 0
        }
        
        # Count dominant emotions for each answer
        for answer in answers:
            if not answer.emotions:
                continue
            
            emotions = answer.emotions
            
            # Find dominant emotion
            dominant_emotion = max(
                (e for e in emotions.items() if e[0] not in ['satisfied', 'unsatisfied']),
                key=lambda x: x[1],
                default=(None, 0)
            )
            
            if dominant_emotion[0]:
                emotion_counts[dominant_emotion[0]] += 1
        
        # Calculate percentages
        total_answers = len(answers)
        emotion_percentages = {}
        
        for emotion, count in emotion_counts.items():
            emotion_percentages[emotion] = (count / total_answers) * 100 if total_answers > 0 else 0
        
        # Get correct/incorrect counts
        correct_count = sum(1 for answer in answers if answer.user_answer == question.correct_answer)
        incorrect_count = total_answers - correct_count
        
        # Calculate satisfaction metrics
        satisfied_count = sum(1 for answer in answers if answer.emotions and answer.emotions.get('satisfied', 0) > 0.5)
        unsatisfied_count = sum(1 for answer in answers if answer.emotions and answer.emotions.get('unsatisfied', 0) > 0.5)
        neutral_count = total_answers - satisfied_count - unsatisfied_count
        
        satisfaction = {
            'satisfied': (satisfied_count / total_answers) * 100 if total_answers > 0 else 0,
            'unsatisfied': (unsatisfied_count / total_answers) * 100 if total_answers > 0 else 0,
            'neutral': (neutral_count / total_answers) * 100 if total_answers > 0 else 0
        }
        
        # Store results for this question
        emotion_analysis[question.id] = {
            'emotions': emotion_percentages,
            'satisfaction': satisfaction,
            'correctness': {
                'correct': (correct_count / total_answers) * 100 if total_answers > 0 else 0,
                'incorrect': (incorrect_count / total_answers) * 100 if total_answers > 0 else 0
            }
        }
    
    return render_template(
        'quiz_analytics.html',
        quiz=quiz,
        results=results,
        emotion_analysis=emotion_analysis
    )


@app.route('/join_game', methods=['GET', 'POST'])
@login_required
def join_game():
    if request.method == 'POST':
        access_code = request.form.get('access_code')
        
        # Find the quiz with the given access code
        quiz = Quiz.query.filter_by(access_code=access_code).first()
        
        if not quiz:
            flash('Invalid access code. Please try again.', 'danger')
            return redirect(url_for('join_game'))
        
        # Check if quiz is active
        quiz.update_status()
        if quiz.current_status != 'active':
            flash('This quiz is not currently active.', 'warning')
            return redirect(url_for('join_game'))
        
        # Check if user already has an attempt for this quiz
        existing_attempt = Attempt.query.filter_by(
            quiz_id=quiz.id,
            user_id=current_user.id,
            completed_at=None
        ).first()
        
        if existing_attempt:
            # Continue existing attempt
            return redirect(url_for('continue_quiz', attempt_id=existing_attempt.id))
        
        # Create new attempt
        new_attempt = Attempt(
            quiz_id=quiz.id,
            user_id=current_user.id
        )
        db.session.add(new_attempt)
        db.session.commit()
        
        return redirect(url_for('take_quiz', attempt_id=new_attempt.id))
    
    # Get active public quizzes for the GET request
    active_quizzes = Quiz.query.filter_by(status='active').all()
    
    # Update quiz statuses to make sure they're current
    for quiz in active_quizzes:
        quiz.update_status()
    
    # Filter to only truly active quizzes
    active_quizzes = [quiz for quiz in active_quizzes if quiz.current_status == 'active']
    
    return render_template('join_game.html', active_quizzes=active_quizzes)

@app.route('/new_quiz', methods=['GET', 'POST'])
@login_required
def new_quiz():
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title')
        description = request.form.get('description')
        duration = int(request.form.get('duration'))
        quiz_type = request.form.get('quiz_type')
        scheduled_time = None
        status = request.form.get('status', 'scheduled')  # Default to 'scheduled' unless explicitly marked as 'draft'
        
        if quiz_type == 'scheduled':
            scheduled_time_str = request.form.get('scheduled_time')
            if scheduled_time_str:
                scheduled_time = datetime.strptime(scheduled_time_str, '%Y-%m-%dT%H:%M')
        
        # Generate access code and share link
        access_code = Quiz.generate_access_code()
        share_link = f"/join/{access_code}"
        
        # Create new quiz
        new_quiz = Quiz(
            title=title,
            description=description,
            duration=duration,
            quiz_type=quiz_type,
            status=status,
            access_code=access_code,
            share_link=share_link,
            creator_id=current_user.id,
            scheduled_time=scheduled_time
        )
        
        db.session.add(new_quiz)
        db.session.flush()  # Get the quiz ID before committing
        
        # Process questions
        questions_data = {}
        for key, value in request.form.items():
            if key.startswith('questions['):
                # Extract question index and field name
                parts = key.rstrip(']').split('[')
                if len(parts) == 3:
                    _, q_index, field = parts
                    # Fix: Remove any remaining brackets from q_index
                    q_index = q_index.rstrip(']')
                    
                    if q_index not in questions_data:
                        questions_data[q_index] = {}
                    questions_data[q_index][field] = value
        
        # Create question objects
        for q_index, q_data in questions_data.items():
            if len(set(['text', 'option1', 'option2', 'option3', 'option4', 'correct_answer', 'time_limit']) - set(q_data.keys())) > 0:
                # Skip incomplete questions
                continue
                
            # Handle image uploads
            image_filename = None
            if f'questions[{q_index}][image]' in request.files:
                image_file = request.files[f'questions[{q_index}][image]']
                if image_file and image_file.filename != '':
                    # Save the image
                    filename = secure_filename(image_file.filename)
                    # Add quiz ID and timestamp to make filename unique
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    image_filename = f"quiz_{new_quiz.id}_{q_index}_{timestamp}_{filename}"
                    image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
            
            try:
                # Create new question with clean q_index
                new_question = Question(
                    quiz_id=new_quiz.id,
                    text=q_data['text'],
                    image=image_filename,
                    option1=q_data['option1'],
                    option2=q_data['option2'],
                    option3=q_data['option3'],
                    option4=q_data['option4'],
                    correct_answer=q_data['correct_answer'],
                    time_limit=int(q_data['time_limit']),
                    order=int(q_index)  # q_index should now be clean of brackets
                )
                
                db.session.add(new_question)
            except ValueError as e:
                # Add logging for debugging
                print(f"Error processing question index '{q_index}': {str(e)}")
                flash(f"Error with question {q_index}: {str(e)}", 'danger')
                db.session.rollback()
                return redirect(url_for('new_quiz'))
        
        try:
            db.session.commit()
            flash(f"Quiz '{title}' created successfully!", 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating quiz: {str(e)}", 'danger')
            return redirect(url_for('new_quiz'))
    
    return render_template('create_quiz.html')

@app.route('/quiz/edit/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def edit_quiz(quiz_id):
    """Edit an existing quiz"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Verify ownership
    if quiz.creator_id != current_user.id:
        flash('You do not have permission to edit this quiz', 'danger')
        return redirect(url_for('dashboard'))
    
    # Check if quiz is editable (not active or ended)
    if quiz.status in ['active', 'ended']:
        flash('Cannot edit an active or ended quiz', 'warning')
        return redirect(url_for('quiz_detail', quiz_id=quiz_id))
    
    if request.method == 'POST':
        action = request.form.get('action', '')
        
        if action == 'update_details':
            # Update quiz details
            quiz.title = request.form.get('title')
            quiz.description = request.form.get('description')
            quiz.duration = int(request.form.get('duration', 10))
            quiz.use_facial_analysis = 'use_facial_analysis' in request.form
            
            if quiz.quiz_type == 'scheduled':
                scheduled_date = request.form.get('scheduled_date')
                scheduled_time = request.form.get('scheduled_time')
                if scheduled_date and scheduled_time:
                    quiz.scheduled_time = datetime.strptime(f"{scheduled_date} {scheduled_time}", "%Y-%m-%d %H:%M")
            
            db.session.commit()
            flash('Quiz details updated successfully!', 'success')
            
        elif action == 'add_question':
            # Add a new question
            question_text = request.form.get('question_text')
            option1 = request.form.get('option1')
            option2 = request.form.get('option2')
            option3 = request.form.get('option3')
            option4 = request.form.get('option4')
            correct_answer = request.form.get('correct_answer')
            time_limit = int(request.form.get('time_limit', 30))
            
            # Get the correct answer text based on the option selected
            if correct_answer == 'option1':
                correct_answer_text =  option1
            elif correct_answer == 'option2':
                correct_answer_text = option2
            elif correct_answer == 'option3':
                correct_answer_text = option3
            elif correct_answer == 'option4':
                correct_answer_text = option4
            else:
                correct_answer_text = ""
            
            # Get the order for the new question
            max_order = db.session.query(db.func.max(Question.order)).filter_by(quiz_id=quiz_id).scalar() or 0
            
            new_question = Question(
                quiz_id=quiz_id,
                text=question_text,
                option1=option1,
                option2=option2,
                option3=option3,
                option4=option4,
                correct_answer=correct_answer_text,
                time_limit=time_limit,
                order=max_order + 1
            )
            
            # Handle question image if uploaded
            if 'question_image' in request.files:
                image_file = request.files['question_image']
                if image_file and image_file.filename:
                    # Save image logic here
                    filename = secure_filename(image_file.filename)
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'questions', filename)
                    image_file.save(image_path)
                    new_question.image = filename
            
            db.session.add(new_question)
            db.session.commit()
            flash('Question added successfully!', 'success')
            
        elif action == 'delete_question':
            question_id = int(request.form.get('question_id'))
            question = Question.query.get_or_404(question_id)
            
            # Verify question belongs to this quiz
            if question.quiz_id != quiz_id:
                flash('Question does not belong to this quiz', 'danger')
                return redirect(url_for('edit_quiz', quiz_id=quiz_id))
            
            db.session.delete(question)
            db.session.commit()
            flash('Question deleted successfully!', 'success')
            
        elif action == 'update_question':
            question_id = int(request.form.get('question_id'))
            question = Question.query.get_or_404(question_id)
            
            # Verify question belongs to this quiz
            if question.quiz_id != quiz_id:
                flash('Question does not belong to this quiz', 'danger')
                return redirect(url_for('edit_quiz', quiz_id=quiz_id))
            
            question.text = request.form.get('question_text')
            question.option1 = request.form.get('option1')
            question.option2 = request.form.get('option2')
            question.option3 = request.form.get('option3')
            question.option4 = request.form.get('option4')
            
            # Get the correct answer text based on the option selected
            correct_answer = request.form.get('correct_answer')
            if correct_answer == 'option1':
                question.correct_answer = request.form.get('option1')
            elif correct_answer == 'option2':
                question.correct_answer = request.form.get('option2')
            elif correct_answer == 'option3':
                question.correct_answer = request.form.get('option3')
            elif correct_answer == 'option4':
                question.correct_answer = request.form.get('option4')
            
            question.time_limit = int(request.form.get('time_limit', 30))
            
            db.session.commit()
            flash('Question updated successfully!', 'success')
            
        elif action == 'finalize_quiz':
            # Ensure quiz has at least one question
            if not quiz.questions:
                flash('Please add at least one question before finalizing the quiz', 'warning')
                return redirect(url_for('edit_quiz', quiz_id=quiz_id))
            
            if quiz.quiz_type == 'scheduled' and quiz.scheduled_time:
                quiz.status = 'scheduled'
            else:
                quiz.status = 'scheduled'  # For live quizzes, they remain scheduled until started
                
            db.session.commit()
            flash('Quiz finalized and ready to use!', 'success')
            return redirect(url_for('quiz_detail', quiz_id=quiz_id))
    
    # For GET request, display the edit form
    return render_template('edit_quiz.html', quiz=quiz)

@app.route('/quiz/<int:quiz_id>')
@login_required
def quiz_detail(quiz_id):
    """View quiz details"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if user is the creator or has attempted this quiz
    is_creator = quiz.creator_id == current_user.id
    user_attempt = Attempt.query.filter_by(quiz_id=quiz_id, user_id=current_user.id).first()
    
    if not (is_creator or user_attempt):
        flash('You do not have access to this quiz', 'danger')
        return redirect(url_for('dashboard'))
    
    # Update quiz status
    quiz.update_status()
    
    # If viewing as participant and quiz is completed
    if user_attempt and user_attempt.completed_at and not is_creator:
        return render_template('quiz_result.html', quiz=quiz, attempt=user_attempt)
    
    # If viewing as creator
    if is_creator:
        # For CSRF protection
        csrf_token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        session['csrf_token'] = csrf_token
        return render_template('quiz_detail.html', quiz=quiz, csrf_token=csrf_token)
    
    # If participant but quiz not completed
    return redirect(url_for('take_quiz', quiz_id=quiz_id))



@app.route('/quiz/start/<int:quiz_id>', methods=['POST'])
@login_required
def start_quiz(quiz_id):
    """Start a live quiz"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Verify ownership and status
    if quiz.creator_id != current_user.id:
        return jsonify({'success': False, 'message': 'You do not have permission to start this quiz'})
    
    if quiz.status != 'scheduled':
        return jsonify({'success': False, 'message': 'This quiz cannot be started'})
    
    # Verify CSRF token
    csrf_token = request.headers.get('X-CSRFToken')
    if not csrf_token or csrf_token != session.get('csrf_token'):
        return jsonify({'success': False, 'message': 'Invalid CSRF token'})
    
    # Start the quiz
    quiz.status = 'active'
    quiz.started_at = datetime.now()
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/quiz/end/<int:quiz_id>', methods=['POST'])
@login_required
def end_quiz(quiz_id):
    """End an active quiz"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Verify ownership and status
    if quiz.creator_id != current_user.id:
        return jsonify({'success': False, 'message': 'You do not have permission to end this quiz'})
    
    if quiz.status != 'active':
        return jsonify({'success': False, 'message': 'This quiz is not active'})
    
    # Verify CSRF token
    csrf_token = request.headers.get('X-CSRFToken')
    if not csrf_token or csrf_token != session.get('csrf_token'):
        return jsonify({'success': False, 'message': 'Invalid CSRF token'})
    
    # End the quiz
    quiz.status = 'ended'
    quiz.ended_at = datetime.now()
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/quiz/delete/<int:quiz_id>')
@login_required
def delete_quiz(quiz_id):
    """Delete a quiz"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Verify ownership
    if quiz.creator_id != current_user.id:
        flash('You do not have permission to delete this quiz', 'danger')
        return redirect(url_for('dashboard'))
    
    db.session.delete(quiz)
    db.session.commit()
    
    flash('Quiz deleted successfully', 'success')
    return redirect(url_for('dashboard'))

@app.route('/quiz/join', methods=['GET', 'POST'])
@login_required
def join_quiz():
    """Join a quiz using access code"""
    if request.method == 'POST':
        access_code = request.form.get('access_code')
        
        # Find quiz by access code
        quiz = Quiz.query.filter_by(access_code=access_code).first()
        
        if not quiz:
            flash('Invalid access code', 'danger')
            return render_template('join_quiz.html')
        
        # Update quiz status
        quiz.update_status()
        
        # Check if quiz is active
        if quiz.status != 'active':
            if quiz.status == 'scheduled':
                flash('This quiz has not started yet', 'warning')
            elif quiz.status == 'ended':
                flash('This quiz has already ended', 'warning')
            else:
                flash('This quiz is not available', 'warning')
            return render_template('join_quiz.html')
        
        # Check if user has already attempted this quiz
        existing_attempt = Attempt.query.filter_by(quiz_id=quiz.id, user_id=current_user.id).first()
        if existing_attempt and existing_attempt.completed_at:
            flash('You have already completed this quiz', 'info')
            return redirect(url_for('quiz_result', quiz_id=quiz.id))
        
        # Start new attempt or continue existing one
        if not existing_attempt:
            attempt = Attempt(quiz_id=quiz.id, user_id=current_user.id)
            db.session.add(attempt)
            db.session.commit()
        else:
            attempt = existing_attempt
        
        return redirect(url_for('take_quiz', quiz_id=quiz.id))
    
    return render_template('join_quiz.html')

# @app.context_processor
# def utility_processor():
#     """Add utility functions to Jinja context"""
#     def format_datetime(dt, format='%Y-%m-%d %H:%M'):
#         """Format datetime objects"""
#         if dt:
#             return dt.strftime(format)
#         return ''
    
#     return {'format_datetime': format_datetime}

# @login_manager.user_loader
# def load_user(user_id):
#     """Load user by ID for Flask-Login"""
#     return User.query.get(int(user_id))

# # Initialize database and create default roles/admin
# @app.before_first_request
# def initialize_database():
#     db.create_all()
    
#     # Create default roles if they don't exist
#     admin_role = Role.query.filter_by(name='Admin').first()
#     if not admin_role:
#         admin_role = Role(name='Admin', description='Administrator with full access')
#         db.session.add(admin_role)
    
#     user_role = Role.query.filter_by(name='User').first()
#     if not user_role:
#         user_role = Role(name='User', description='Regular user')
#         db.session.add(user_role)
    
#     db.session.commit()
    
#     # Create default admin if it doesn't exist
#     admin = User.query.filter_by(username='admin').first()
#     if not admin:
#         admin = User(
#             unique_id=User.generate_unique_id('Admin', 'User'),
#             username='admin',
#             email='admin@quizplatform.com',
#             first_name='Admin',
#             last_name='User',
#             role_id=admin_role.id,
#             is_admin=True
#         )
#         admin.set_password('admin123')
#         db.session.add(admin)
#         db.session.commit()



# Create all tables and default admin
with app.app_context():
    db.create_all()
    # create_default_admin()

# Run the app
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(debug=True, host='0.0.0.0', port=port)