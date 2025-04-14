from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import json
import os
import random
import string
from sqlalchemy import or_
from models import db, User, Quiz, Question, Attempt, Answer, QuizFeedback, Role, EmotionConfig

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz_platform.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


@app.route('/dashboard')
@login_required
def dashboard():
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
    
    return render_template(
        'dashboard.html',
        active_quizzes=active_quizzes,
        scheduled_quizzes=scheduled_quizzes,
        ended_quizzes=ended_quizzes,
        draft_quizzes=draft_quizzes,
        attempted_quizzes=attempted_quizzes
    )

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

@app.route('/quiz/create', methods=['GET', 'POST'])
@login_required
def create_quiz():
    if request.method == 'POST':
        # Process form data
        title = request.form.get('title')
        description = request.form.get('description')
        duration = int(request.form.get('duration', 10))
        quiz_type = request.form.get('quiz_type')
        use_facial_analysis = 'use_facial_analysis' in request.form
        
        # Create new quiz
        new_quiz = Quiz(
            title=title,
            description=description,
            duration=duration,
            quiz_type=quiz_type,
            status='draft',
            access_code=Quiz.generate_access_code(),
            creator_id=current_user.id,
            use_facial_analysis=use_facial_analysis
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

@app.route('/quiz/<int:quiz_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if current user is the creator
    if quiz.user_id != current_user.id:
        flash('You do not have permission to edit this quiz.', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        # Update quiz details
        if action == 'update_details':
            quiz.title = request.form.get('title')
            quiz.description = request.form.get('description')
            quiz.duration = int(request.form.get('duration', 30))
            quiz.use_facial_analysis = 'use_facial_analysis' in request.form
            
            if quiz.quiz_type == 'scheduled':
                scheduled_date = request.form.get('scheduled_date')
                scheduled_time_str = request.form.get('scheduled_time')
                if scheduled_date and scheduled_time_str:
                    quiz.scheduled_time = datetime.strptime(f"{scheduled_date} {scheduled_time_str}", '%Y-%m-%d %H:%M')
            
            db.session.commit()
            flash('Quiz details updated successfully!', 'success')
            
        # Add a question
        elif action == 'add_question':
            question_text = request.form.get('question_text')
            time_limit = int(request.form.get('time_limit', 30))
            option1 = request.form.get('option1')
            option2 = request.form.get('option2')
            option3 = request.form.get('option3')
            option4 = request.form.get('option4')
            correct_option = request.form.get('correct_answer')
            
            # Determine correct answer based on selected option
            correct_answer = option1
            if correct_option == 'option2':
                correct_answer = option2
            elif correct_option == 'option3':
                correct_answer = option3
            elif correct_option == 'option4':
                correct_answer = option4
            
            new_question = Question(
                quiz_id=quiz.id,
                text=question_text,
                option1=option1,
                option2=option2,
                option3=option3,
                option4=option4,
                correct_answer=correct_answer,
                time_limit=time_limit
            )
            
            db.session.add(new_question)
            db.session.commit()
            flash('Question added successfully!', 'success')
            
        # Update a question
        elif action == 'update_question':
            question_id = request.form.get('question_id')
            question = Question.query.get(question_id)
            
            if question and question.quiz_id == quiz.id:
                question.text = request.form.get('question_text')
                question.time_limit = int(request.form.get('time_limit', 30))
                question.option1 = request.form.get('option1')
                question.option2 = request.form.get('option2')
                question.option3 = request.form.get('option3')
                question.option4 = request.form.get('option4')
                
                correct_option = request.form.get('correct_answer')
                if correct_option == 'option1':
                    question.correct_answer = question.option1
                elif correct_option == 'option2':
                    question.correct_answer = question.option2
                elif correct_option == 'option3':
                    question.correct_answer = question.option3
                elif correct_option == 'option4':
                    question.correct_answer = question.option4
                
                db.session.commit()
                flash('Question updated successfully!', 'success')
            
        # Delete a question
        elif action == 'delete_question':
            question_id = request.form.get('question_id')
            question = Question.query.get(question_id)
            
            if question and question.quiz_id == quiz.id:
                db.session.delete(question)
                db.session.commit()
                flash('Question deleted successfully!', 'success')
                
        # Finalize the quiz
        elif action == 'finalize_quiz':
            # Only finalize if there's at least one question
            if quiz.questions.count() > 0:
                quiz.is_finalized = True
                db.session.commit()
                flash('Quiz has been finalized and is ready to be shared!', 'success')
                return redirect(url_for('quiz_detail', quiz_id=quiz.id))
            else:
                flash('Cannot finalize a quiz with no questions. Please add at least one question.', 'danger')
                
        return redirect(url_for('edit_quiz', quiz_id=quiz.id))
        
    return render_template('edit_quiz.html', quiz=quiz)


@app.route('/quiz/start/<int:quiz_id>', methods=['POST'])
@login_required
def start_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Verify ownership and status
    if quiz.creator_id != current_user.id:
        return jsonify({'success': False, 'message': 'You do not have permission to start this quiz'})
    
    if quiz.status != 'scheduled' or quiz.quiz_type != 'live':
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
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Verify ownership
    if quiz.creator_id != current_user.id:
        flash('You do not have permission to delete this quiz', 'danger')
        return redirect(url_for('dashboard'))
    
    db.session.delete(quiz)
    db.session.commit()
    
    flash('Quiz deleted successfully', 'success')
    return redirect(url_for('dashboard'))

@app.route('/join-quiz', methods=['GET', 'POST'])
@login_required
def join_quiz():
    if request.method == 'POST':
        access_code = request.form.get('access_code')
        
        quiz = Quiz.query.filter_by(access_code=access_code).first()
        
        if not quiz:
            flash('Invalid quiz code. Please try again.', 'danger')
            return redirect(url_for('join_quiz'))
            
        if not quiz.is_finalized:
            flash('This quiz is not yet ready to be taken.', 'danger')
            return redirect(url_for('join_quiz'))
            
        # Check if the quiz is scheduled and not yet available
        if quiz.quiz_type == 'scheduled' and quiz.scheduled_time > datetime.now():
            flash(f'This quiz is scheduled for {format_datetime(quiz.scheduled_time)}. Please come back then.', 'info')
            return redirect(url_for('join_quiz'))
            
        # Check if user has already attempted this quiz
        existing_attempt = QuizAttempt.query.filter_by(
            user_id=current_user.id,
            quiz_id=quiz.id
        ).first()
        
        if existing_attempt and existing_attempt.is_completed:
            flash('You have already completed this quiz.', 'info')
            return redirect(url_for('quiz_result', quiz_id=quiz.id))
            
        # Create a new attempt or use existing one
        if not existing_attempt:
            attempt = QuizAttempt(
                user_id=current_user.id,
                quiz_id=quiz.id,
                started_at=datetime.now()
            )
            db.session.add(attempt)
            db.session.commit()
            
        return redirect(url_for('take_quiz', quiz_id=quiz.id))
        
    # Get user's completed attempts to show in history
    attempted_quizzes = QuizAttempt.query.filter_by(
        user_id=current_user.id,
        is_completed=True
    ).order_by(QuizAttempt.completed_at.desc()).limit(5).all()
    
    return render_template('join_quiz.html', attempted_quizzes=attempted_quizzes)

@app.route('/quiz/<int:quiz_id>/take', methods=['GET', 'POST'])
@login_required
def take_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Find or create quiz attempt
    attempt = QuizAttempt.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz.id
    ).first()
    
    if not attempt:
        # Create new attempt
        attempt = QuizAttempt(
            user_id=current_user.id,
            quiz_id=quiz.id,
            started_at=datetime.now()
        )
        db.session.add(attempt)
        db.session.commit()
        
    if attempt.is_completed:
        flash('You have already completed this quiz.', 'info')
        return redirect(url_for('quiz_result', quiz_id=quiz.id))
        
    # Check if time limit is exceeded
    time_elapsed = datetime.now() - attempt.started_at
    time_limit_minutes = quiz.duration
    if time_elapsed.total_seconds() > time_limit_minutes * 60:
        attempt.is_completed = True
        attempt.completed_at = datetime.now()
        db.session.commit()
        flash('Time limit exceeded. Your quiz has been submitted.', 'info')
        return redirect(url_for('quiz_result', quiz_id=quiz.id))
    
    if request.method == 'POST':
        # Process quiz submission
        questions = quiz.questions.all()
        for question in questions:
            answer_key = f'question_{question.id}'
            selected_option = request.form.get(answer_key)
            
            # Record user answer
            user_answer = UserAnswer(
                quiz_attempt_id=attempt.id,
                question_id=question.id,
                selected_answer=selected_option,
                is_correct=selected_option == question.correct_answer
            )
            db.session.add(user_answer)
        
        # Process emotion data if facial analysis was used
        if quiz.use_facial_analysis:
            emotion_data = request.form.get('emotion_data')
            if emotion_data:
                try:
                    emotion_json = json.loads(emotion_data)
                    for question_id, emotions in emotion_json.items():
                        emotion_record = EmotionData(
                            quiz_attempt_id=attempt.id,
                            question_id=int(question_id),
                            emotion_data=json.dumps(emotions)
                        )
                        db.session.add(emotion_record)
                except Exception as e:
                    app.logger.error(f"Error processing emotion data: {e}")
        
        # Complete the attempt
        attempt.is_completed = True
        attempt.completed_at = datetime.now()
        db.session.commit()
        
        flash('Quiz completed! Here are your results.', 'success')
        return redirect(url_for('quiz_result', quiz_id=quiz.id))
        
    questions = quiz.questions.all()
    
    # Calculate time remaining
    time_elapsed_seconds = time_elapsed.total_seconds()
    time_remaining_seconds = (time_limit_minutes * 60) - time_elapsed_seconds
    time_remaining_minutes = max(0, int(time_remaining_seconds // 60))
    time_remaining_seconds = max(0, int(time_remaining_seconds % 60))
    
    return render_template(
        'take_quiz.html',
        quiz=quiz,
        questions=questions,
        attempt=attempt,
        time_remaining_minutes=time_remaining_minutes,
        time_remaining_seconds=time_remaining_seconds
    )

@app.route('/quiz/answer/<int:quiz_id>/<int:question_id>', methods=['POST'])
@login_required
def submit_answer(quiz_id, question_id):
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
    
    # Process answer
    user_answer = request.form.get('answer')
    answer_time = float(request.form.get('answer_time', 0))
    emotions_data = request.form.get('emotions_data', '{}')
    
    # Create answer record
    answer = Answer(
        attempt_id=attempt.id,
        question_id=question_id,
        user_answer=user_answer,
        answer_time=answer_time,
        emotions=json.loads(emotions_data) if emotions_data else {}
    )
    
    db.session.add(answer)
    db.session.commit()
    
    # Check if all questions answered
    answered_count = Answer.query.filter_by(attempt_id=attempt.id).count()
    total_questions = Question.query.filter_by(quiz_id=quiz_id).count()
    
    if answered_count >= total_questions:
        attempt.completed_at = datetime.now()
        db.session.commit()
        return jsonify({'success': True, 'completed': True, 'redirect': url_for('quiz_result', quiz_id=quiz_id, attempt_id=attempt.id)})
    
    return jsonify({'success': True, 'completed': False})

@app.route('/quiz/<int:quiz_id>/result')
@login_required
def quiz_result(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Get the attempt for this user
    attempt = QuizAttempt.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz.id,
        is_completed=True
    ).first_or_404()
    
    # Get user answers for this attempt
    user_answers = UserAnswer.query.filter_by(quiz_attempt_id=attempt.id).all()
    
    # Calculate score
    total_questions = len(quiz.questions.all())
    correct_answers = sum(1 for answer in user_answers if answer.is_correct)
    
    score_percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0
    
    # Get emotion data if applicable
    emotion_data = None
    if quiz.use_facial_analysis:
        emotion_records = EmotionData.query.filter_by(quiz_attempt_id=attempt.id).all()
        if emotion_records:
            emotion_data = {}
            for record in emotion_records:
                emotion_data[record.question_id] = json.loads(record.emotion_data)
    
    return render_template(
        'quiz_result.html',
        quiz=quiz,
        attempt=attempt,
        user_answers=user_answers,
        score_percentage=round(score_percentage, 1),
        correct_answers=correct_answers,
        total_questions=total_questions,
        emotion_data=emotion_data
    )

# Ajax route to save emotion data during quiz
@app.route('/api/save-emotions', methods=['POST'])
@login_required
def save_emotions():
    if not request.is_json:
        return jsonify({'error': 'Invalid request format'}), 400
        
    data = request.json
    attempt_id = data.get('attempt_id')
    question_id = data.get('question_id')
    emotions = data.get('emotions')
    
    if not all([attempt_id, question_id, emotions]):
        return jsonify({'error': 'Missing required data'}), 400
        
    # Verify the attempt belongs to current user
    attempt = QuizAttempt.query.get(attempt_id)
    if not attempt or attempt.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    # Save emotion data
    emotion_data = EmotionData(
        quiz_attempt_id=attempt_id,
        question_id=question_id,
        emotion_data=json.dumps(emotions)
    )
    
    db.session.add(emotion_data)
    db.session.commit()
    
    return jsonify({'success': True})


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
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
                # Save profile picture logic here
                filename = secure_filename(profile_pic.filename)
                pic_path = os.path.join(app.config['UPLOAD_FOLDER'], 'profiles', filename)
                profile_pic.save(pic_path)
                current_user.profile_pic = filename
        
        db.session.commit()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('profile'))

@app.context_processor
def utility_processor():
    """Add utility functions to Jinja context"""
    def format_datetime(dt, format='%Y-%m-%d %H:%M'):
        """Format datetime objects"""
        if dt:
            return dt.strftime(format)
        return ''
    
    return {'format_datetime': format_datetime}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create default roles if they don't exist
        admin_role = Role.query.filter_by(name='Admin').first()
        if not admin_role:
            admin_role = Role(name='Admin', description='Administrator with full access')
            db.session.add(admin_role)
        
        user_role = Role.query.filter_by(name='User').first()
        if not user_role:
            user_role = Role(name='User', description='Regular user')
            db.session.add(user_role)
        
        db.session.commit()
        
    app.run(debug=True)