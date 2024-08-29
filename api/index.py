from flask import Flask, render_template, request, jsonify, redirect, session, flash
from supabase import create_client
import random
import os


app = Flask("goodnight v1")
app.secret_key = os.urandom(24)

data = {
    "database_password": os.environ.get("DATABASE_PASSWORD"),
    "public_api_key": os.environ.get("PUBLIC_API_KEY"),
    "service_role": os.environ.get("SERVICE_ROLE"),
    "db_url": os.environ.get("DB_URL"),
    "jwt_secret": os.environ.get("JWT_SECRET"),
}

url = data["db_url"]
key = data["service_role"]
supabase = create_client(str(url), str(key))
local_uid = ""

@app.route('/')
def index():
    if 'user' in session:
        return redirect('/dash')
    return render_template('index.html')

@app.route('/links')
def edit_links():
    global local_uid
    if 'user' in session:
        data = supabase.from_("users").select("*").eq("email", local_uid).execute().data
        return render_template('links.html', links=data[0]['links'])
    else:
        return redirect('/login')

@app.route('/links/add')
def add_link():
    global local_uid
    data = supabase.from_("users").select("*").eq("email", local_uid).execute().data

    return render_template('add_link.html')

@app.route('/links/add/value', methods=['POST'])
def link_add():
    global local_uid
    data = supabase.from_("users").select("*").eq("email", local_uid).execute().data
    links_save = data[0]["links"]
    key = request.form["key"]
    value = request.form["value"]
    links_save.update({ key: value })
    print(links_save)
    supabase.from_("users").update({ "links": links_save }).eq("email", local_uid).execute()

    return redirect('/links')

@app.route('/links/update/value', methods=['POST'])
def update_link():
    global local_uid
    data = supabase.from_("users").select("*").eq("email", local_uid).execute().data

    save_json = data[0]['links']
    save_json[request.form['key']] = request.form['value']
    supabase.from_("users").update({"links": save_json}).eq("email", local_uid).execute()
    return redirect('/links')

@app.route('/links/delete', methods=['POST'])
def delete_link():
    global local_uid
    data = supabase.from_("users").select("*").eq("email", local_uid).execute().data

    save_json = data[0]['links']
    save_json.pop(request.form['key'])
    supabase.from_("users").update({"links": save_json}).eq("email", local_uid).execute()
    return redirect('/links')

@app.route('/links/edit/<num>')
def edit_link(num):
    global local_uid
    data = supabase.from_("users").select("*").eq("email", local_uid).execute().data
    if 'user' in session:
        name = list(data[0]['links'].keys())[int(num)]
        value = data[0]['links'][name]

        return render_template("change_link.html",
                               name=name,
                               value=value)
    else:
        return redirect('/login')

@app.route('/dashboard')
def dashboard():
    global local_uid
    data = supabase.from_("users").select("*").eq("email", local_uid).execute().data
    if 'user' in session:
        try:
            name = str(data[0]["vanity"])
            name_ = str(data[0]["name"])
            quote = str(data[0]["quote"])
        except Exception as e:
            flash(str(e))
            session.pop('user', None)
            return redirect('/login')
        return render_template('dash.html', vanity=name, name=name_, quote=quote)
    else:
        return redirect('/login')

@app.route('/<vanity>')
def user(vanity):
    data = supabase.from_("users").select("*").eq("vanity", vanity).execute().data
    meme = data[0]['meme']
    links = data[0]['links']
    badges = data[0]['badges']
    icon = data[0]['icon']
    quote = data[0]['quote']
    premium = data[0]['premium']
    name = data[0]['name']

    return render_template("user.html",
                           meme=meme,
                           links=links,
                           badges=badges,
                           icon=icon,
                           quote=quote,
                           name=name,
                           premium=premium,
                           vanity=vanity)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect('/dash')
    global local_uid
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            response = supabase.auth.sign_in_with_password({
                'email': email,
                'password': password
            })
        except Exception as e:
            flash(str(e))  # Flash the exception message
            app.logger.error(f"Error during login: {str(e)}")  # Log the error
            return redirect('/login')

        if response:
            try:
                local_uid = str(email)
                session['user'] = True
                return redirect('/dashboard')
            except Exception as e:
                flash(str(e))
                app.logger.error(f"Error setting session: {str(e)}")
                return redirect('/login')
        else:
            try:
                error_message = response['error']['message']
                flash(error_message)
                return jsonify({'error': error_message}), 401
            except Exception as e:
                flash(str(e))
                app.logger.error(f"Error handling response: {str(e)}")
                return redirect('/')
    else:
        return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    global local_uid
    if 'user' in session:
       return redirect('/dash')
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        credentials = {
            'email': email,
            'password': password,
        }

        response = supabase.auth.sign_up(credentials)
        table_name = 'users'
        vanity = ''.join(random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890') for _ in range(6))
        local_uid = str(email)
        print(email)
        print(local_uid)
        new_row = {
            'vanity': vanity,
            'name': 'New User',
            'views': 0,
            'links': {'Join Me on Goodnight': '/'},
            'premium': False,
            'meme': '',
            'quote': 'im new here',
            'icon': 'https://epoecigquyjkfvqldkus.supabase.co/storage/v1/object/public/memes/default_icon/Default_PFP.png',
            'audio': '',
            'badges': ["email"],
            'email': email
        }
        supabase.from_(table_name).insert(new_row).execute()

        if response:
            return 'Check your email for a sign up link.'
        else:
            return jsonify({'error': response['error']['message']}), 400
    else:
        return render_template('signup.html')

@app.route('/logout')
def logout():
    global local_uid
    session.pop('user', None)
    return redirect('/')

@app.route('/settings', methods=['POST'])
def settings():
    global local_uid
    if 'user' in session:
        flash('Succesfully changed settings!')
        vanity = request.form["username"]
        name = request.form["name"]
        quote = request.form["quote"]
        response = supabase.from_('users').update({ "vanity": vanity, "name": name, "quote": quote }).eq("email", local_uid).execute()
        return redirect('/dashboard')
    else:
        return redirect('/login')

@app.route('/upload', methods=['POST'])
def upload():
    global local_uid
    if 'user' in session:
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        if file.filename == '':
            return 'No selected file'
        if file:
            file_path = "img/" + ''.join(random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890') for _ in range(16)) + '.png'
            url = f'https://epoecigquyjkfvqldkus.supabase.co/storage/v1/object/public/memes/{file_path}'
            try:
                response = supabase.storage.from_("memes").upload(file_path, file.read(), {
                    'content-type': 'image/png'
                })
                response = supabase.from_('users').update({ "meme": url }).eq("email", local_uid).execute()
                flash('Successfully changed meme!')
                return redirect('/dashboard')
            except Exception as e:
                return str(e)
    else:
        return redirect('/login')

if __name__ == '__main__':
    app.run('0.0.0.0', port=3000)
