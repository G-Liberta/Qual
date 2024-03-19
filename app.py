from flask import Flask, render_template, request, redirect, url_for
from flask import session
import psycopg2
import json
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate a random secret key

# Load quiz questions from JSON file
with open('questions.json', 'r') as file:
    quiz_questions = json.load(file)

# Connect to your PostgreSQL database
connection = psycopg2.connect(
    dbname='QA',
    user='postgres',
    password='.',
    host='localhost',
    port='8080'
)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/quiz')
def quiz():
    session['quiz_questions'] = quiz_questions  # Store quiz questions in session
    return render_template('quiz.html', quiz_questions=quiz_questions)


@app.route('/submit', methods=['POST'])
def submit():
    quiz_questions = session.get('quiz_questions')  # Retrieve quiz questions from session
    if not quiz_questions:
        return redirect(url_for('quiz'))  # Redirect if session doesn't contain quiz questions

    total_questions = len(quiz_questions)
    correct_answers = 0

    for index, question in enumerate(quiz_questions):
        user_answers = request.form.getlist(f'answer_{index}')
        if set(user_answers) == set(question['correct_answer']):
            correct_answers += 1

    incorrect_answers = total_questions - correct_answers
    session.pop('quiz_questions')  # Clear quiz questions from session

    return redirect(url_for('result', total_questions=total_questions, correct_answers=correct_answers, incorrect_answers=incorrect_answers))


@app.route('/result')
def result():
    total_questions = request.args.get('total_questions')
    correct_answers = request.args.get('correct_answers')
    incorrect_answers = request.args.get('incorrect_answers')
    return render_template('result.html', total_questions=total_questions, correct_answers=correct_answers, incorrect_answers=incorrect_answers)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        hashed_password = request.form['password']
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s AND hashed_password = %s", (username, hashed_password))
        user = cursor.fetchone()
        cursor.close()
        if user:
            return redirect(url_for('quiz'))
        else:
            return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        hashed_password = request.form['password']
        cursor = connection.cursor()
        try:
            cursor.execute("INSERT INTO users (username, hashed_password) VALUES (%s, %s)", (username, hashed_password))
            connection.commit()
            return redirect(url_for('login'))
        except psycopg2.IntegrityError:
            connection.rollback()
            return render_template('register.html', error='Username already exists')
        finally:
            cursor.close()
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
