from lib2to3.pgen2.token import LBRACE
from tkinter import Label
from wsgiref.validate import validator
from flask import Flask, render_template, request, jsonify
import os
import sqlite3 as sql
from flask_wtf import FlaskForm
from matplotlib.pyplot import flag
from wtforms import  IntegerField, validators, StringField, SelectField



# app - The flask application where all the magical things are configured.
app = Flask(__name__)
app.config['SECRET_KEY']='LongAndRandomSecretKey'

# Constants - Stuff that we need to know that won't ever change!
DATABASE_FILE = "database.db"
DEFAULT_BUGGY_ID = "1"
BUGGY_RACE_SERVER_URL = "https://rhul.buggyrace.net"

#------------------------------------------------------------
# the index page
#------------------------------------------------------------
colours = [("1","Red"),("2","Green"),("3","Blue"),("4","Purple"),("5","Yellow")]
patterns = [("1","plain"),("2","vstripe"),("3","hstripe"),("4","dstripe"),("5","checker"),("6","spot")]
tyreType = [("1","knobbly"), ("2","slick"), ("3","steelband"), ("4","reactive"), ("5","maglev")]
armourType = [("1","none"), ("2","wood"), ("3","aluminium"), ("4","thinsteel"), ("5","thicksteel"), ("6","titanium")]
powerType = [("1","petrol"), ("2","fusion"), ("3","steam"), ("4","bio"), ("5","electric"), ("6","rocket"), ("7","hamster"), ("8","thermo"), ("9","solar"), ("10","wind")]
weaponType = [("1","none"), ("2","spike"), ("3","flame"), ("4","charge"), ("5","biohazard")]
algoType = [("1","defensive"), ("2","steady"), ("3","offensive"), ("4","titfortat"), ("5","random")]


partCosts = {
    "none": 0,
    "petrol": 4,
    "fusion": 400,
    "steam": 3,
    "bio": 5,
    "electric": 20,
    "rocket": 16,
    "hamster": 3,
    "thermo" : 300,
    "solar": 40,
    "wind": 20,
    "knobbly": 15,
    "slick": 10,
    "steelband": 20,
    "reactive": 40,
    "maglev": 50,
    "wood": 40,
    "aluminium": 200,
    "thinsteel": 100,
    "thicksteel": 200,
    "titanium": 290,
    "spike": 5,
    "flame": 20,
    "charge": 28,
    "biohazard": 30,
    "fireproof": 70,
    "insulated": 100,
    "antibiotic": 90,
    "banging": 42,
    "hamster_booster": 5
}

#the form which is used to design a buggy 
class makeBuggyForm(FlaskForm):
    wheels = SelectField(("Select which type of wheels you would like on your buggy: "), choices=tyreType)
    qty_wheels = IntegerField(("Enter number of wheels for your buggy: "), validators=[validators.NumberRange(min=4, max=12, message="Please make sure the number of Wheels is between 4 and 12")])
    flag_color = SelectField(("Enter a Primary Flag Colour for your Buggy: "), choices=colours)
    secondary_flag_color = SelectField(("Enter a Secondary Flag Colour for your buggy(Not Required): "),choices=colours)
    flag_pattern = SelectField(("Select the pattern for your flag: "),choices=patterns)
    power_type = SelectField(("Select your primary power type: "), choices=powerType)
    power_units = IntegerField(("Enter number of primary power units: "), validators=[validators.NumberRange(min=1, max=100)])
    aux_power_type = SelectField(("Select Auxilary Power Type(Not Required): "), choices=powerType)
    aux_power_units = IntegerField(("Enter number of Auxilary Power Units: "), validators=[validators.NumberRange(min=1, max=100)])
    armour = SelectField(("Select Armour Type for your buggy(Not Required): "), choices=armourType)
    attack = SelectField(("Select Weapons you would like to add to your buggy: "), choices=weaponType)
    qty_attacks = IntegerField(("Enter number of attacks you would like to use: "), validators=[validators.NumberRange(min=0,max=100)])
    algo = SelectField(("Select the Race Computer Algorithm you would like to use for your buggy: "), choices=algoType)
    fireproof = IntegerField(("Would you like your buggy to be fireproof 0 for false, 1 for true: "), validators=[validators.NumberRange(min=0, max=1)])
    insulated = IntegerField(("Would you like your buggy to have rubber insulation 0 for false, 1 for true: "), validators=[validators.NumberRange(min=0, max=1)])
    antibiotic = IntegerField(("Would you like your buggy to be antibiotic 0 for false, 1 for true: "), validators=[validators.NumberRange(min=0, max=1)])
    banging = IntegerField(("Would you like a banging sound system in your buggy 0 for false, 1 for true: "), validators=[validators.NumberRange(min=0, max=1)])
    hamster_booster = IntegerField(("would you like any hamster boosters"), validators=[validators.NumberRange(min=0, max=100)])
#function to calculate the cost of the buggy and do some data validation
def buggyCost(wheels, qty_wheels, power_type, power_units, aux_power_type, aux_power_units, armour, attack, qty_attacks, fireproof, insulated, antibiotic, banging, hamster_booster):
    #making sure if the power type is non consumable the units are only 1
    if power_type == "fusion" or power_type == "thermo" or power_type == "solar" or power_type == "wind":
        power_units = 1
    if aux_power_type == "fusion" or aux_power_type == "thermo" or aux_power_type == "solar" or aux_power_type == "wind":
        aux_power_units = 1
    #making sure wheels can only be even
    if qty_wheels%2 != 0:
        qty_wheels += 1

    cost = (partCosts[wheels]*qty_wheels)+(partCosts[power_type]*power_units)+(partCosts[aux_power_type]*aux_power_units)+partCosts[armour]+(partCosts[attack]*qty_attacks)+(partCosts["hamster_booster"]*hamster_booster)
    if fireproof==1:
        cost += partCosts["fireproof"]
    elif insulated==1:
        cost+= partCosts["insulated"]
    elif antibiotic==1:
        cost+= partCosts["antibiotic"]
    elif banging==1:
        cost += partCosts["banging"]
    return cost 





@app.route('/')
def home():
    return render_template('index.html', server_url=BUGGY_RACE_SERVER_URL)

#------------------------------------------------------------
# creating a new buggy:
#  if it's a POST request process the submitted data
#  but if it's a GET request, just show the form
#------------------------------------------------------------
@app.route('/new', methods = ['POST', 'GET'])
def create_buggy():
    form = makeBuggyForm(wheels=4)
    if request.method == 'GET':
        return render_template("buggy-form.html", form=form)
    elif request.method == 'POST' and form.validate():
        #gets the data from the form and stores it in variables
        wheels = dict(form.wheels.choices).get(form.wheels.data)
        qty_wheels = form.qty_wheels.data
        flag_color = dict(form.flag_color.choices).get(form.flag_color.data)
        secondary_flag_color = dict(form.secondary_flag_color.choices).get(form.secondary_flag_color.data)
        flag_pattern = dict(form.flag_pattern.choices).get(form.flag_pattern.data)
        power_type = dict(form.power_type.choices).get(form.power_type.data)
        power_units = form.power_units.data
        aux_power_type = dict(form.aux_power_type.choices).get(form.aux_power_type.data)
        aux_power_units = form.aux_power_units.data
        armour = dict(form.armour.choices).get(form.armour.data)
        attack = dict(form.attack.choices).get(form.attack.data)
        qty_attacks = form.qty_attacks.data
        algo = dict(form.algo.choices).get(form.algo.data)
        fireproof = form.fireproof.data
        insulated = form.insulated.data
        antibiotic = form.antibiotic.data
        banging = form.banging.data
        hamster_booster = form.hamster_booster.data
        cost = buggyCost(wheels, qty_wheels, power_type, power_units, aux_power_type, aux_power_units, armour, attack, qty_attacks, fireproof, insulated, antibiotic, banging, hamster_booster )
        #updates the database with the new data
        try:
            with sql.connect(DATABASE_FILE) as con:
                cur = con.cursor()
                sql_update_query = """UPDATE buggies SET wheels=?, qty_wheels=?, flag_color=?, flag_color_secondary=?, flag_pattern=?, power_type=?, power_units=?,  aux_power_type=?, aux_power_units=?, armour=?, attack=?, qty_attacks=?, algo=?, fireproof=?, insulate=?, antibiotic=?, banging=? ,hamster_booster=?, total_cost=?  WHERE id=?"""
                data = (wheels, qty_wheels, flag_color, secondary_flag_color, flag_pattern, power_type, power_units,  aux_power_type, aux_power_units, armour, attack, qty_attacks, algo, fireproof, insulated, antibiotic, banging ,hamster_booster, cost, DEFAULT_BUGGY_ID)
                cur.execute(sql_update_query, data)
                con.commit()
                msg = "Record successfully saved cost: %s"%cost
        except Exception as error:
            print(error)
            con.rollback()
            msg = "error in update operation"
        finally:
            con.close()
        return render_template("updated.html", msg = msg)

#------------------------------------------------------------
# a page for displaying the buggy
#------------------------------------------------------------
@app.route('/buggy')
def show_buggies():
    con = sql.connect(DATABASE_FILE)
    con.row_factory = sql.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM buggies")
    record = cur.fetchone(); 
    return render_template("buggy.html", buggy = record)

#------------------------------------------------------------
# a placeholder page for editing the buggy: you'll need
# to change this when you tackle task 2-EDIT
#------------------------------------------------------------
@app.route('/edit')
def edit_buggy():
    con = sql.connect(DATABASE_FILE)
    con.row_factory = sql.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM buggies")
    rows = cur.fetchall()
    for row in rows:
        form = makeBuggyForm(qty_wheels=row[1],flag_color=row[2],secondary_flag_color=row[3],flag_pattern=row[4],power_type=row[5],power_units=row[6],aux_power_type=row[7],aux_power_units=row[8],hamster_booster=row[9],wheels=row[10],armour=row[11],attack=row[12],qty_attacks=row[13],fireproof=row[14],insulated=row[15],antibiotic=row[16],banging=row[17],algo=row[18])
    return render_template("edit.html", form=form)

#------------------------------------------------------------
# You probably don't need to edit this... unless you want to ;)
#
# get JSON from current record
#  This reads the buggy record from the database, turns it
#  into JSON format (excluding any empty values), and returns
#  it. There's no .html template here because it's *only* returning
#  the data, so in effect jsonify() is rendering the data.
#------------------------------------------------------------
@app.route('/json')
def summary():
    con = sql.connect(DATABASE_FILE)
    con.row_factory = sql.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM buggies WHERE id=? LIMIT 1", (DEFAULT_BUGGY_ID))

    buggies = dict(zip([column[0] for column in cur.description], cur.fetchone())).items() 
    return jsonify({ key: val for key, val in buggies if (val != "" and val is not None) })

@app.route('/poster')
def poster():
   return render_template('poster.html')

@app.route('/info')
def info():
    return render_template("info.html")
# You shouldn't need to add anything below this!
if __name__ == '__main__':
    alloc_port = os.environ['CS1999_PORT']
    app.run(debug=True, host="0.0.0.0", port=alloc_port)

