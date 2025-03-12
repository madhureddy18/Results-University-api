from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:madhureddy18@localhost/results_university'
app.config['SECRET_KEY'] = '0248fd56fc0a4f4fc9b0e265ce56e049'  
db = SQLAlchemy(app)

# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    print(f"Loading user with ID: {user_id}")  # Debug statement
    if user_id is None:
        print("user_id is None!")  # Debug statement
        return None
    return User.query.get((user_id))

# Database Models
class User(UserMixin, db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=False)  # 'staff' or 'student'
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.subject_id'))  # Only for staff

    # Relationship to Subject (only for staff)
    subject = db.relationship('Subject', backref='staff')

    # Method to set password (hash the password)
    def set_password(self, password):
        self.password = generate_password_hash(password)

    # Method to check password
    def check_password(self, password):
        return check_password_hash(self.password, password)

    # Override get_id to return user_id instead of id
    def get_id(self):
        return str(self.user_id)  # Flask-Login requires the ID to be a string
    
class Subject(db.Model):
    subject_id = db.Column(db.Integer, primary_key=True)
    subject_name = db.Column(db.String, nullable=False)

class Marks(db.Model):
    student_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.subject_id'), primary_key=True)
    marks = db.Column(db.Integer, nullable=False)

    # Define a relationship to the Subject model
    subject = db.relationship('Subject', backref='marks')

class Results(db.Model):
    student_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), primary_key=True)
    overall_status = db.Column(db.String, nullable=False)

# Create tables in the database

with app.app_context():
    db.drop_all()  # Drop all tables
    db.create_all()  # Recreate tables based on the updated models
    print("Database schema updated successfully!")

with app.app_context():
    try:
        db.create_all()
        print("Database connected and tables created successfully!")
    except Exception as e:
        print(f"Database connection error: {e}")

with app.app_context():
    subjects = ['English', 'Hindi', 'Maths', 'Physics', 'Telugu', 'Social']
    for subject_name in subjects:
        subject = Subject(subject_name=subject_name)
        db.session.add(subject)
    db.session.commit()
    print("Subjects added successfully!")

with app.app_context():
    students = [
        {'username': 'student1', 'password': 'student123', 'role': 'student'},
        {'username': 'student2', 'password': 'student456', 'role': 'student'},
        {'username': 'student3', 'password': 'student789', 'role': 'student'},
        {'username': 'student4', 'password': 'student101', 'role': 'student'},
        {'username': 'student5', 'password': 'student112', 'role': 'student'},
    ]
    for student in students:
        user = User(username=student['username'], role=student['role'])
        user.set_password(student['password'])  # Hash the password
        db.session.add(user)
    db.session.commit()
    print("Students added successfully!")

with app.app_context():
    staff_members = [
        {'username': 'staff_english', 'password': 'staff123', 'role': 'staff', 'subject_id': 1},  # English
        {'username': 'staff_hindi', 'password': 'staff456', 'role': 'staff', 'subject_id': 2},    # Hindi
        {'username': 'staff_maths', 'password': 'staff789', 'role': 'staff', 'subject_id': 3},    # Maths
        {'username': 'staff_physics', 'password': 'staff101', 'role': 'staff', 'subject_id': 4},  # Physics
        {'username': 'staff_telugu', 'password': 'staff112', 'role': 'staff', 'subject_id': 5},   # Telugu
        {'username': 'staff_social', 'password': 'staff131', 'role': 'staff', 'subject_id': 6},   # Social
    ]
    for staff in staff_members:
        user = User(username=staff['username'], role=staff['role'], subject_id=staff['subject_id'])
        user.set_password(staff['password'])
        db.session.add(user)
    db.session.commit()
    print("Staff members added successfully!")

# Routes
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        print(f"Attempting login for: {username}, Role: {role}")  # Debug statement

        user = User.query.filter_by(username=username, role=role).first()
        if user:
            print(f"User found: {user.username}, ID: {user.get_id()}")  # Debug statement
            if user.check_password(password):  # Verify hashed password
                login_user(user)
                print(f"User {user.username} logged in successfully!")  # Debug statement
                if user.role == 'staff':
                    return redirect(url_for('staff_dashboard'))
                else:
                    return redirect(url_for('student_dashboard'))
            else:
                print("Invalid password")  # Debug statement
        else:
            print("User not found")  # Debug statement
        flash('Invalid credentials')
    return render_template('login.html')

from flask import session

from flask import Flask, render_template, request, redirect, url_for, flash

@app.route('/staff_dashboard', methods=['GET', 'POST'])
@login_required
def staff_dashboard():
    if current_user.role != 'staff':
        return "Unauthorized", 403

    # Get the subject assigned to the staff member
    assigned_subject = Subject.query.get(current_user.subject_id)
    if not assigned_subject:
        return "No subject assigned to this staff member.", 403

    # Fetch all students
    students = User.query.filter_by(role='student').all()

    # Fetch marks for all students in the assigned subject
    student_marks = []
    for student in students:
        marks_entry = Marks.query.filter_by(student_id=student.user_id, subject_id=assigned_subject.subject_id).first()
        student_marks.append({
            'student': student,
            'marks': marks_entry.marks if marks_entry else None  # If no marks exist, set to None
        })

    if request.method == 'POST':
        # Handle form submission to update marks
        for student in students:
            marks = request.form.get(f'marks_{student.user_id}')
            if marks:  # If marks are provided for this student
                try:
                    marks = int(marks)  # Convert marks to integer
                    # Check if marks already exist for this student and subject
                    marks_entry = Marks.query.filter_by(student_id=student.user_id, subject_id=assigned_subject.subject_id).first()
                    if marks_entry:
                        # Update existing marks
                        marks_entry.marks = marks
                    else:
                        # Create new marks entry
                        marks_entry = Marks(student_id=student.user_id, subject_id=assigned_subject.subject_id, marks=marks)
                        db.session.add(marks_entry)
                    print(f"Updated marks for {student.username}: {marks}")  # Debug statement
                except ValueError:
                    flash(f'Invalid marks for student {student.username}.', 'error')
                except Exception as e:
                    print(f"Error: {e}")  # Debug statement
                    flash(f'An error occurred while updating marks for {student.username}.', 'error')

        db.session.commit()
        flash('Marks updated successfully!', 'success')  # Success message
        return redirect(url_for('staff_dashboard'))

    return render_template('staff_dashboard.html', assigned_subject=assigned_subject, student_marks=student_marks)

@app.route('/enter_marks', methods=['POST'])
@login_required
def enter_marks():
    if current_user.role != 'staff':
        return "Unauthorized", 403

    try:
        student_id = request.form['student_id']
        print(f"Student ID: {student_id}")  # Debug statement

        # Save or update marks for each subject
        subjects = ['maths', 'science', 'english', 'telugu', 'hindi']
        for subject_name in subjects:
            marks = request.form.get(subject_name)
            if marks:
                subject = Subject.query.filter_by(subject_name=subject_name.capitalize()).first()
                if subject:
                    # Check if marks already exist for this student and subject
                    marks_entry = Marks.query.filter_by(student_id=student_id, subject_id=subject.subject_id).first()
                    if marks_entry:
                        # Update existing marks
                        marks_entry.marks = marks
                    else:
                        # Create new marks entry
                        marks_entry = Marks(student_id=student_id, subject_id=subject.subject_id, marks=marks)
                        db.session.add(marks_entry)
                    print(f"Updated marks for {subject_name}: {marks}")  # Debug statement

        db.session.commit()
        print("Marks submitted successfully!")  # Debug statement

        # Clear temporary marks from session
        session.pop('temporary_marks', None)
        session.pop('selected_student_id', None)

        flash('Marks saved permanently.')
    except KeyError as e:
        print(f"Missing key in form data: {e}")  # Debug statement
        flash('Invalid form submission')
    except Exception as e:
        print(f"Error: {e}")  # Debug statement
        flash('An error occurred while submitting marks')

    return redirect(url_for('staff_dashboard'))

def calculate_overall_status(student_id):
    marks = Marks.query.filter_by(student_id=student_id).all()
    overall_status = "Pass"
    for mark in marks:
        if mark.marks < 35:  # Assuming pass marks are 35
            overall_status = "Fail"
            break

    # Update or create the result entry
    result = Results.query.filter_by(student_id=student_id).first()
    if result:
        result.overall_status = overall_status
    else:
        result = Results(student_id=student_id, overall_status=overall_status)
        db.session.add(result)
    db.session.commit()

@app.route('/student_dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        return "Unauthorized", 403

    # Retrieve marks for the logged-in student with subject details
    marks = db.session.query(Marks, Subject).join(Subject).filter(Marks.student_id == current_user.user_id).all()
    
    # Calculate overall status
    for mark, subject in marks:
        if mark.marks < 35:  # Assuming pass marks are 35
            overall_status = "Fail"
            break
    else:
        overall_status="Pass"

    return render_template('student_dashboard.html', marks=marks, overall_status=overall_status)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Run the app
if __name__ == '__main__':
    app.run(debug=True)


