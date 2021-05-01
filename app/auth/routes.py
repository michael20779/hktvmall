from flask import Flask, redirect, url_for, flash, request, render_template, abort, Response
from flask_babel import _
from flask_login import current_user, login_user, logout_user
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
import os
import urllib.request
from app import db
from app.auth import bp
from app.auth.email import send_password_reset_email
from app.auth.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from app.models import User, Img
from datetime import datetime



@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash(_('Invalid username or password'))
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('auth/login.html', title=_('Sign In'), form=form)


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, phonenumber=form.phonenumber.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(_('Congratulations, you are now a registered user!'))
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title=_('Register'), form=form)


@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash(
            _('Check your email for the instructions to reset your password'))
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html',
                           title=_('Reset Password'), form=form)


@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash(_('Your password has been reset.'))
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)


@bp.route('/upload', methods=['POST'])
def upload():
    pic = request.files['pic']

    if not pic:
        return 'No pic uploaded'

    filename = secure_filename(pic.filename)
    mimetype = pic.mimetype

    img = Img(img=pic.read(), mimetype=mimetype, name=filename)
    db.session.add(img)
    db.session.commit()

    return 'Img has been uploaded!'

    return render_template('index.html', title=_('Image'))


bp = Flask(__name__)

bp.secret_key = "caircocoders-ednalan"

bp.config['MYSQL_HOST'] = 'localhost'
bp.config['MYSQL_USER'] = 'root'
bp.config['MYSQL_PASSWORD'] = ''
bp.config['MYSQL_DB'] = 'testingdb'
bp.config['MYSQL_CURSORCLASS'] = 'DictCursor'



UPLOAD_FOLDER = 'static/uploads'
bp.config['UPLOAD_FOLADER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

def allowed_file(filename):
    return '.' in filename and filename.rsplist('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route("/upload",methods=["POST","GET"])
def upload():
    cursor = mysql.connection.cursor()
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    now = datetime.now()
    if request.method == 'POST':
        files = request.files.getlist('files[]')
        print(files)
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                cur.execute("INSERT INTO images (file_name, uploaded_on) VALUES (%s, %s)",[filename, now])
                mysql.connection.commit()
            print(file)
        cur.close()
        flash('File(s) successfully uploaded')
    return redirect('/')