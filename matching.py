from flask import Flask, request, jsonify, abort
import cv2
import numpy as np
from werkzeug import secure_filename
import os
from datetime import datetime
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from ImageItem import ImageItem
import matcher as match


# configuration
DEBUG = True
SECRET_KEY = 'secret'
USERNAME = 'admin'
PASSWORD = 'password'
# Set root folder and application name
ROOT = os.path.abspath(os.path.dirname(__file__))
# assuming application name is same as folder
APP_NAME = os.path.basename(ROOT)
DATABASE_NAME = "images.db"
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(ROOT, "tmp/" + DATABASE_NAME)

# Set up App
app = Flask(__name__)
app.config.from_object(__name__)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)

list_images = []

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Category %r>' % self.name

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    origin = db.Column(db.String(50))
    rating = db.Column(db.Float)
    description = db.Column(db.String(500))
    ingredients = db.Column(db.String(500))
    url = db.Column(db.String(80), unique=True)
    date_added = db.Column(db.DateTime)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category',
        backref=db.backref('items', lazy='dynamic'))

    def __init__(self, title, origin, category, url, description, ingredients, rating= None, date_added = None):
        id = db.Column(db.Integer, primary_key=True)
        self.title = title
        self.origin = origin
        if rating is None:
            rating = 0.0
        self.rating = rating
        self.url =  url
        self.category = category
        self.description = description
        self.ingredients = ingredients
        if date_added is None:
            date_added = datetime.utcnow()
        self.date_added = date_added

        def __repr__(self):
            return '<item %r>' % self.title

@app.route('/upload', methods=['POST', 'GET'])
def hello():
    #Handle POST request
    if request.method == 'POST':
        start = datetime.now()
        #Check if the database has been proccesed
        if not list_images:
            calc_calculate_sift()
        img = request.files['pic']
        #TODO, SAVE IMAGE TO FOLDER.
        name = secure_filename(img.filename)
        img.save(os.path.join(ROOT, "tmp/" + name))
        query = ImageItem("tmp/"+name, name)
        matcher = match.Matcher()

        r = matcher.search(query, list_images)
        if not r :
            end = datetime.now()
            delta = end-start
            print delta
            return abort(404)

        name = str(r[0][1])
        img_item = Item.query.filter_by(url=name).first()



        if img_item is None:
            return abort(404)

        t = {"title": img_item.title, "origin": img_item.origin, "category": img_item.category.name,
                "description": img_item.description, "ingredients": img_item.ingredients}

        end = datetime.now()
        delta = end-start
        print delta
        return jsonify(t)

    #Handle GET request
    elif request.method == 'GET':
        return '''
            <form action="" method="post" enctype="multipart/form-data">
                <input type="file" name="pic" accept="image/*">
                <input type="submit">
            </form>
        '''

@app.route('/add-image', methods=['POST', 'GET'])
def add_image():
    """
    Method to add an image to the db
    """
    #Handle POST request
    if request.method == 'POST':
        img = request.files['pic']
        img_title = request.form['name']
        img_origin = request.form['origin']
        img_category = request.form['category']
        img_desc = request.form['desc']
        img_ingredients = request.form['ingredients']
        img_ingredients = img_ingredients.replace('\r\n','')
        #name = secure_filename(img.filename)

        category = Category.query.filter_by(name=img_category).first()

        if category is None:
            return "Category not found"
        #Check if there is items in the category
        items = Item.query.all()
        if not items:
            num_of_items = 0
        else:
            num_of_items = Item.query.all()[-1].id

        name_img_db = img_category + "_" + str(num_of_items + 1) + ".jpg"
        item = Item(img_title, img_origin, category, name_img_db, img_desc, img_ingredients)
        db.session.add(item)
        db.session.commit()
        img.save("images/%s" % name_img_db)
        return "Added"

    #Handle GET request
    elif request.method == 'GET':
        return '''
            <form action="" method="post" enctype="multipart/form-data">
                <input type="file" name="pic" accept="image/*"><br>
                Title:<br>
                <input type="text" name="name"><br>
                Origin:<br>
                <input type="text" name="origin"><br>
                Category:<br>
                <input type="text" name="category"><br>
                Description:<br>
                <textarea name="desc"></textarea><br>
                Ingredients:<br>
                <textarea name="ingredients"></textarea><br>
                <input type="submit">
            '''

"""
IMAGE PROCESSING METHODS
"""

def calc_calculate_sift():
    """
    Method to calculate the descriptors of each image  in the dataset.
    """
    global list_images
    for f in os.listdir("images"):
        if f == ".DS_Store":
            continue
        image = ImageItem("images/"+f, f)
        list_images.append(image)
        print "FINISHING", f

@app.route('/load_db')
def load_db():
    calc_calculate_sift()
    return "DONE"
if __name__ == '__main__':
    manager.run()
