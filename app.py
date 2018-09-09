from flask import Flask, render_template, request,make_response,session,redirect
import flask_hashing as hasher
import database_functions as db
import json
from flask_recaptcha import ReCaptcha
app = Flask(__name__)
app.secret_key="marios-ioanna"
hashing =hasher.Hashing(app)

app.config.update(dict(
    RECAPTCHA_ENABLED = True,
    RECAPTCHA_SITE_KEY = "6LfVnW0UAAAAAOIZWk2TeYhhOpvj_kEDKs_5Vy9H",
    RECAPTCHA_SECRET_KEY = "6LfVnW0UAAAAAAblnAAAnZmqbw3bk9dJScnE-PHl",
    RECAPTCHA_SIZE = "compact"
))

recaptcha = ReCaptcha()
recaptcha.init_app(app)


@app.route('/')
@app.route('/home')
def load_home():
    return  render_template('/index.html')

@app.route('/result',methods = ['POST', 'GET'])
def result():
     if request.method == 'POST':  
        form=request.form
        rooms=db.load_available_rooms(form)
        resp = make_response( render_template('reservation.html',rooms=rooms) )
        resp.set_cookie('Check-in',form["Check-in"] )
        resp.set_cookie('Check-out',form["Check-out"] )
        return resp



@app.route('/photos')
def load_photos():
    return  render_template('photos.html')

@app.route('/reservation')
def load_reservation():
    return  render_template('reservation.html')


@app.route('/login')
def load_login(message=None):
    return  render_template('login.html',comment=message)

@app.route('/signUp')
@app.route('/sign_up')
def load_sign_up():
    return  render_template('signUp.html')

@app.route('/modal_details/<room_id>')
def modal_details(room_id):
    return json.dumps( db.get_modal_details(room_id) )#return json with all details for the modal

@app.route('/start_reservation/<room_id>')
def start_reservation(room_id):
    session['room_ID']=room_id
    session['redirect']=None
    check_in = request.cookies.get('Check-in')
    check_out = request.cookies.get('Check-out')
    available=db.avaiability_check(room_id,check_in,check_out)
    if not available==True:
        return available

    if not session.get('logged_in'): #requires login?
        session['redirect']="/start_reservation/"+str(room_id)

        return  load_login("You are not logged in.Please login to procceed!")
    
    
    
    print("Room-ID:"+str(room_id)+"Check-in:"+str(check_in)+"Check-out:"+str(check_out))
    details=db.get_modal_details(room_id)
    details.pop('Photos')
    details['Check-in']=check_in
    details['Check-out']=check_out
    user_details=db.load_user_details(session['user'])
    session['user_details']=user_details
    details.update(user_details)
    print(details)
    return render_template('reserve_details.html',details=details)

@app.route('/login_check',methods = ['POST', 'GET'])
def login_check():
    if request.method == 'POST':
        form=request.form
        username=form["email"]
        password=hashing.hash_value(form["password"], salt='123456789')#hash password
        if not recaptcha.verify():
            return load_login("You fucking robot...!!!")
        if not db.check_credentials(username,password):
            return load_login("Invalid username/password.Please try again")            
        #Login succesfull
        session['logged_in']=True
        session['user']=username
        if not session.get("redirect")==None:
            print(session.get("redirect"))
            return redirect(session.get("redirect"))
        return redirect('/home')
@app.route('/logout')
def logout():
    session['logged_in']=False
    return redirect("/")

@app.route('/finish_reservation',methods = ['POST', 'GET'])
def finish_reservation():
    if request.method == 'POST':
        form=request.form
        print("heyy(old first,then new)")
        print(session['user_details'])
        print(form)
        db.check_diffs_and_update(session['user_details'],form,session['user'])
        room_ID=session.get("room_ID")
        db.make_reservation(room_ID,request.cookies.get('Check-in'),request.cookies.get('Check-out'),session['user'])
        
        return "Geia sou ore malaka"
    
    return redirect('/home')

def require_login():
    pass
    
if __name__ == '__main__':
    app.run(port='5005',debug=True)