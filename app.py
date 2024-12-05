from flask import Flask, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import pandas as pd
import uuid
import openai

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///feedback.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bootstrap = Bootstrap(app)

client = openai.OpenAI(
    api_key="7f5AQ030gyWL6Cbgu1GNO-fTRvLAyKgQ8Lcu10bMZnvz6UgH3fXxJgooGCP60ToYx6z3PQAc2HUo72fk2GOVMeg",  
    base_url="https://api.openai.iniad.org/api/v1",
)

# Feedback model
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    playlist_id = db.Column(db.String(100), nullable=False)
    track_name = db.Column(db.String(200), nullable=False)
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)
    track_id = db.Column(db.String(100), nullable=False)

# Create the database tables
def create_tables():
    with app.app_context():
        db.create_all()

def map_emotion_to_playlist(output):
    output = output.lower().strip()
    if output in ['dance', 'positive', 'study', 'driving', 'relax', 'workout', 'focus', 'chill']:
        return output
    else:
        return 'positive' 

# Home route
@app.route('/')
def index():
    options = ['dance', 'positive', 'study', 'driving', 'relax', 'workout', 'focus', 'chill']
    return render_template('index.html', options=options, title="Music App")

# Result route
@app.route('/result.html', methods=["GET", "POST"])
def result():
    selected_value = request.args.get('select')
    data = pd.read_csv('spotify.csv')
    df = data[['artist', 'name', 'album', 'release_date', 'feels']]
    selected_data = df[df['feels'] == selected_value]
    
    if not selected_data.empty:
        sample_size = min(len(selected_data), 20)
        random_data = selected_data.sample(n=sample_size)
        tables = [random_data.to_html(classes='data', header="true", index=False)]
    else:
        tables = ['<p>選択されたカテゴリーにデータがありません。</p>']

    playlist_id = str(uuid.uuid4())
    return render_template('result.html', tables=tables, titles=random_data.columns.values if not selected_data.empty else [], title="卒業制作", playlist_id=playlist_id)

# Feedback route
@app.route('/feedback/<playlist_id>', methods=['POST'])
def feedback(playlist_id):
    track_id = request.form.get('track_id')  # フォームから曲IDを受け取る
    track_name = request.form.get('track_name')  # 曲名を受け取る
    vote = request.form.get('vote')  # いいねか悪いねかを受け取る

    feedback = Feedback.query.filter_by(playlist_id=playlist_id, track_id=track_id).first()

    # 存在しないフィードバックの場合、新しいレコードを作成
    if not feedback:
        feedback = Feedback(playlist_id=playlist_id, track_name=track_name, track_id=track_id, upvotes=0, downvotes=0)
        db.session.add(feedback)

    # いいね・悪いねのカウント
    if vote == 'upvote':
        feedback.upvotes += 1
    elif vote == 'downvote':
        feedback.downvotes += 1

    db.session.commit()
    return redirect(url_for('show_feedback', playlist_id=playlist_id))

@app.route('/show_feedback/<playlist_id>')
def show_feedback(playlist_id):
    feedback_data = Feedback.query.filter_by(playlist_id=playlist_id).all()  # プレイリストの全てのフィードバックを取得
    return render_template('feedback_result.html', feedback_data=feedback_data)  # ここでfeedback_dataを渡す

@app.route('/reset_feedback/<playlist_id>', methods=['POST'])
def reset_feedback(playlist_id):
    feedback = Feedback.query.filter_by(playlist_id=playlist_id).first()
    if feedback:
        feedback.upvotes = 0
        feedback.downvotes = 0
        db.session.commit()
    return redirect(url_for('show_feedback', playlist_id=playlist_id))

# Chat with OpenAI API
@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        user_input = request.form.get('emotion_input')
        
        # Prompt OpenAI API to respond with one of the categories
        response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
            "role": "user", 
            "content": (
                "I am building a music recommendation app. Based on the user's current emotion, "
                "please select one of the following categories: dance, positive, study, driving, "
                "relax, workout, focus, or chill. Consider the emotion as described by the user and "
                "map it to the most fitting category. If the user's emotion is ambiguous or doesn't "
                "fit clearly, default to 'positive'.\n"
                f"Emotion description: {user_input}"
                )
            }
        ]
)
        
        output = response.choices[0].message.content.strip()
        playlist_option = map_emotion_to_playlist(output)
        
        return redirect(url_for('result', select=playlist_option))
    
    return render_template('index.html')

# Create the database tables when the app starts
if __name__ == '__main__':
    create_tables()
    app.run(host='localhost', port=8080, debug=True)
