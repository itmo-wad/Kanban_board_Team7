from app import app, db, User, Dashboard, Column, Task, SummaryHistory
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from kanban_agent import KanbanAgent

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboards'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboards'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('signup'))
            
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('signup'))
            
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('dashboards'))
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and allowed_file(file.filename):
                if current_user.profile_picture != 'default-profile.png':  # Only delete if not the default
                    old_picture = os.path.join(app.config['UPLOAD_FOLDER'], current_user.profile_picture)
                    if os.path.exists(old_picture):
                        os.remove(old_picture)
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                current_user.profile_picture = filename
        
        current_user.username = request.form.get('username', current_user.username)
        current_user.email = request.form.get('email', current_user.email)
        
        if request.form.get('password'):
            current_user.password_hash = generate_password_hash(request.form.get('password'))
        
        db.session.commit()
        flash('Profile updated successfully')
        return redirect(url_for('profile'))
    
    return render_template('profile.html')

@app.route('/dashboards')
@login_required
def dashboards():
    return render_template('dashboards.html', dashboards=current_user.dashboards)

@app.route('/dashboard/new', methods=['POST'])
@login_required
def new_dashboard():
    name = request.form.get('name')
    dashboard = Dashboard(name=name, user_id=current_user.id)
    db.session.add(dashboard)
    db.session.commit()
    
    # Create default columns
    default_columns = ["To Do", "In Progress", "Done"]
    for position, title in enumerate(default_columns):
        column = Column(title=title, position=position, dashboard_id=dashboard.id)
        db.session.add(column)
    db.session.commit()
    
    return redirect(url_for('view_dashboard', dashboard_id=dashboard.id))

@app.route('/dashboard/<int:dashboard_id>')
@login_required
def view_dashboard(dashboard_id):
    dashboard = Dashboard.query.get_or_404(dashboard_id)
    if dashboard.user_id != current_user.id:
        return redirect(url_for('dashboards'))
    return render_template('dashboard.html', dashboard=dashboard)

@app.route('/api/column/new', methods=['POST'])
@login_required
def new_column():
    data = request.get_json()
    column = Column(
        title=data['title'],
        position=data['position'],
        dashboard_id=data['dashboard_id']
    )
    db.session.add(column)
    db.session.commit()
    return jsonify({'id': column.id, 'title': column.title})

@app.route('/api/column/<int:column_id>', methods=['PUT', 'DELETE'])
@login_required
def manage_column(column_id):
    column = Column.query.get_or_404(column_id)
    default_columns = ["To Do", "In Progress", "Done"]
    
    # Prevent operations on default columns
    if column.title in default_columns:
        return jsonify({'error': 'Cannot modify default columns'}), 403
    
    if request.method == 'DELETE':
        db.session.delete(column)
        db.session.commit()
        return '', 204
    
    data = request.get_json()
    column.title = data.get('title', column.title)
    column.position = data.get('position', column.position)
    db.session.commit()
    return jsonify({'id': column.id, 'title': column.title})

@app.route('/api/task/new', methods=['POST'])
@login_required
def new_task():
    data = request.get_json()
    due_date = None
    if data.get('due_date'):
        try:
            due_date = datetime.strptime(data['due_date'], '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
            
    task = Task(
        title=data['title'],
        description=data.get('description', ''),
        column_id=data['column_id'],
        position=data['position'],
        due_date=due_date
    )
    db.session.add(task)
    db.session.commit()
    return jsonify({
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else None
    })

@app.route('/api/task/<int:task_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def manage_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else None,
            'column_id': task.column_id
        })
    
    if request.method == 'DELETE':
        db.session.delete(task)
        db.session.commit()
        return '', 204
    
    data = request.get_json()
    task.title = data.get('title', task.title)
    task.description = data.get('description', task.description)
    task.column_id = data.get('column_id', task.column_id)
    task.position = data.get('position', task.position)
    
    if 'due_date' in data:
        try:
            task.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d') if data['due_date'] else None
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
    
    db.session.commit()
    return jsonify({
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else None,
        'column_id': task.column_id
    })

@app.route('/api/tasks/search', methods=['GET'])
@login_required
def search_tasks():
    query = request.args.get('q', '').lower()
    dashboard_id = request.args.get('dashboard_id')
    
    # Base query
    tasks_query = Task.query.join(Column).filter(Column.dashboard_id == dashboard_id)
    
    if query:
        # Search in title and description
        title_desc_filter = (Task.title.ilike(f'%{query}%') | Task.description.ilike(f'%{query}%'))
        
        # Try to parse the query as a date
        try:
            # Try different date formats
            date_formats = ['%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y']
            parsed_date = None
            
            for date_format in date_formats:
                try:
                    parsed_date = datetime.strptime(query, date_format)
                    break
                except ValueError:
                    continue
            
            if parsed_date:
                # If it's a valid date, add it to the search filter
                date_filter = Task.due_date == parsed_date
                tasks = tasks_query.filter(title_desc_filter | date_filter).all()
            else:
                tasks = tasks_query.filter(title_desc_filter).all()
        except ValueError:
            # If date parsing fails, just search in title and description
            tasks = tasks_query.filter(title_desc_filter).all()
    else:
        tasks = tasks_query.all()
    
    return jsonify([{
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'column_id': task.column_id,
        'due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else None
    } for task in tasks])

@app.route('/api/dashboard/<int:dashboard_id>', methods=['DELETE'])
@login_required
def delete_dashboard(dashboard_id):
    dashboard = Dashboard.query.get_or_404(dashboard_id)
    if dashboard.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(dashboard)
    db.session.commit()
    return jsonify({'message': 'Dashboard deleted successfully'}) 

@app.route('/generate_summary/<int:dashboard_id>', methods=['POST'])
@login_required
def generate_summary(dashboard_id):
    try:
        dashboard = Dashboard.query.filter_by(
            id=dashboard_id, 
            user_id=current_user.id
        ).first_or_404()
        
        agent = KanbanAgent(dashboard_id)
        
        summary = agent.generate_summary()
        
        new_summary = SummaryHistory(
            content=summary,
            dashboard_id=dashboard_id,
            user_id=current_user.id
        )
        db.session.add(new_summary)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "summary": summary,
            "memory": agent.memory.buffer
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
