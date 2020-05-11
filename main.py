from flask import Flask, render_template, request, session, redirect
from datetime import datetime
from flask_mail import Mail
from werkzeug.utils import secure_filename
import os
import  math
from flask_sqlalchemy import SQLAlchemy
import json


with open("config.json",'r') as c:
    params = json.load(c)["params"]

local_server =True

app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload-location']
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL ='True',
    MAIL_USERNAME =params['gmail_usr'],
    MAIL_PASSWORD =params['gmail_password']
)
mail = Mail(app)
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']
db = SQLAlchemy(app)


class posts(db.Model):
    serial = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.VARCHAR(40), nullable=False, unique=False)
    subtitle = db.Column(db.VARCHAR(20), nullable=True , unique=False)
    slug = db.Column(db.VARCHAR(20), nullable=False , unique=True)
    content = db.Column(db.VARCHAR(1000), unique=True , nullable=True)
    img_file = db.Column(db.VARCHAR(15), unique=False, nullable=False)
    date = db.Column(db.String(20), nullable=True)

class contact(db.Model):
    serial = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.VARCHAR(40), nullable=False, unique=False)
    email = db.Column(db.VARCHAR(20), nullable=False)
    phone = db.Column(db.VARCHAR(15), unique=True, nullable=True)
    msg = db.Column(db.VARCHAR(100), unique=False, nullable=False)
    date = db.Column(db.String(12))

@app.route('/')
def home():
    #pagination
    posting= posts.query.filter_by().all()
    last = math.ceil(len(posting)/params['no_of_posts'])
    #posts =post[]
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page =int(page)
    post = posting[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts'])+int(params['no_of_posts'])]

    if (page ==1):
        prev = "#"
        next ="/?page=" +str(page+1)
    elif(page ==last):
        next = "#"
        prev = "/?page=" +str(page-1)
    else:
        next = "/?page=" + str(page + 1)
        prev = "/?page=" + str(page - 1)

    return render_template('index.html' , params= params, posting=post , prev = prev, next = next)

@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route('/delete/<string:serial>', methods=['GET','POST'])
def delete(serial):
    if 'user' in session and session['user'] == params['admin_usr']:
        post = posts.query.filter_by(serial=serial).first()
        db.session.delete(post)
        db.session.commit()

    return redirect('/dashboard')




@app.route('/uploader', methods=['GET','POST'])
def uploader():
    if 'user' in session and session['user'] == params['admin_usr']:
        if request.method == 'POST':
            if request.files:

                file = request.files['file']
                file.save(os.path.join(app.config['UPLOAD_FOLDER']), secure_filename(file.filename))
                return "UPLOADED SUCCESSFULLY"


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' in session and session['user'] == params['admin_usr']:
        posting = posts.query.all()
        return  render_template('dashboard.html', params=params, posting = posting)

    if request.method == 'POST':
        username = request.form.get('uname')
        password = request.form['password']
        if (username == params['admin_usr']) and (password == params['admin_pass']):
            session['user'] = username
            posting = posts.query.all()
            return render_template('dashboard.html', params=params, posting= posting)

    return render_template('login.html', params=params)

@app.route('/post/<string:post_slug>', methods= ['GET'])
def post_route(post_slug):
    post = posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params , post=post)

@app.route('/contact' , methods = ['GET' , 'POST'])
def contact():
    if (request.method == 'POST'):
        '''add entry to the data base'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        entry = Contact(name=name , phone = phone ,date=datetime.now(), email=email , msg=message)
        db.session.add(entry)
        db.session.commit()
        mail.send_message( 'new message from thunder by' + name,
                           sender =email,
                           recipients =[params['gmail_usr']],
                           body =message + "\n" + phone

        )

    return render_template('contact.html', params= params)

@app.route('/edit/<string:serial>', methods= ['GET','POST'])
def edit(serial):
    if 'user' in session and session['user'] == params['admin_usr']:
        if request.method == 'POST':
            box_title = request.form.get('title')
            subtitle = request.form.get('subtitle')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date= datetime.now()

            if serial =='0':
                posting = posts(title= box_title, subtitle= subtitle, slug= slug, content = content, img_file= img_file,date=date)
                db.session.add(posting)
                db.session.commit()
            else:
                posting = posts.query.filter_by(serial=serial).first()
                posting.title = box_title
                posting.subtitle =subtitle
                posting.slug = slug
                posting.content = content
                posting.img_file = img_file
                posting.date= date
                db.session.commit()
                return redirect('/edit/' + serial)

        posting = posts.query.filter_by(serial=serial).first()
        return render_template('edit.html', params=params ,posting=posting)




@app.route('/about')
def about():
    return render_template('about.html', params= params)

app.run(debug=True)

