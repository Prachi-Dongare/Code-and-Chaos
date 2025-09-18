from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_cors import CORS
import os
from model_utils import predict_image
from nlp_utils import get_answer

app = Flask(__name__)
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---------------- Database Models ----------------
class Query(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100))
    query_text = db.Column(db.String(500), nullable=True)
    image_path = db.Column(db.String(200), nullable=True)
    crop_type = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(50), default='pending_ai')
    ai_confidence = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.DateTime, default=db.func.now())

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    query_id = db.Column(db.Integer, db.ForeignKey('query.id'), nullable=False)
    responder_type = db.Column(db.String(20), default='AI')
    response_text = db.Column(db.String(1000), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now())

# ---------------- Upload Config ----------------
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}

# ---------------- HTML Page Routes ----------------
@app.route('/')
def home():
    return render_template('dashboard.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/roles')
def roles_page():
    return render_template('roles.html')

@app.route('/farmer')
def farmer_page():
    return render_template('farmer.html')

@app.route('/expert')
def expert_page():
    return render_template('expert.html')

@app.route('/policy')
def policy_page():
    return render_template('policy.html')

# ---------------- API Routes ----------------

# Submit text query
@app.route('/api/query/text', methods=['POST'])
def query_text():
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({"error": "Missing query"}), 400

    query_text = data['query']
    region = data.get('region', "Unknown")
    user_id = data.get('user_id', "anonymous")

    # Save query
    new_query = Query(user_id=user_id, query_text=query_text, location=region, status="pending_ai")
    db.session.add(new_query)
    db.session.commit()

    # AI tries to answer
    ai_result = get_answer(query_text)
    ai_conf = ai_result.get('confidence', 0)
    ai_answer_text = ai_result.get('answer', '')

    if ai_conf >= 0.6 and "Unknown" not in ai_answer_text:
        # AI answered
        new_query.status = 'ai_answered'
        new_query.ai_confidence = ai_conf
        db.session.commit()
        answer = Answer(query_id=new_query.id, responder_type='AI', response_text=ai_answer_text)
        db.session.add(answer)
        db.session.commit()
        return jsonify({
            "message": "AI answered the query",
            "query_id": new_query.id,
            "answer": ai_answer_text,
            "confidence": ai_conf,
            "status": new_query.status
        }), 200
    else:
        # Escalate to expert
        new_query.status = 'escalated'
        new_query.ai_confidence = ai_conf
        db.session.commit()
        return jsonify({
            "message": "Query escalated to expert",
            "query_id": new_query.id,
            "status": new_query.status
        }), 200

# Submit image query
@app.route('/api/query/image', methods=['POST'])
def query_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files['image']
    region = request.form.get('region', "Unknown")
    user_id = request.form.get('user_id', "anonymous")

    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({"error": "Invalid image"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Save query
    new_query = Query(user_id=user_id, image_path=filepath, location=region, status="pending_ai")
    db.session.add(new_query)
    db.session.commit()

    # AI prediction from image
    ai_result = predict_image(filepath)
    ai_conf = ai_result.get('confidence', 0)
    ai_answer_text = ai_result.get('answer', '')

    if ai_conf >= 0.6 and "Unknown" not in ai_answer_text:
        new_query.status = 'ai_answered'
        new_query.ai_confidence = ai_conf
        db.session.commit()
        answer = Answer(query_id=new_query.id, responder_type='AI', response_text=ai_answer_text)
        db.session.add(answer)
        db.session.commit()
        return jsonify({
            "message": "AI answered the image query",
            "query_id": new_query.id,
            "answer": ai_answer_text,
            "confidence": ai_conf,
            "status": new_query.status
        }), 200
    else:
        new_query.status = 'escalated'
        new_query.ai_confidence = ai_conf
        db.session.commit()
        return jsonify({
            "message": "Image query escalated to expert",
            "query_id": new_query.id,
            "status": new_query.status
        }), 200

# Expert reply
@app.route('/api/expert/reply', methods=['POST'])
def expert_reply():
    data = request.get_json()
    if not data or 'query_id' not in data or 'response_text' not in data:
        return jsonify({"error": "Missing fields"}), 400

    query_id = data['query_id']
    response_text = data['response_text']

    query = Query.query.get(query_id)
    if not query:
        return jsonify({"error": "Query not found"}), 404

    query.status = 'expert_answered'
    db.session.commit()
    answer = Answer(query_id=query_id, responder_type='Expert', response_text=response_text)
    db.session.add(answer)
    db.session.commit()

    return jsonify({"message": "Expert replied successfully", "query_id": query_id}), 200

# Get escalated queries for expert page
@app.route('/api/dashboard/escalated', methods=['GET'])
def get_escalated_queries():
    queries = Query.query.filter_by(status="escalated").order_by(Query.timestamp.desc()).all()
    return jsonify([
        {
            "id": q.id,
            "query_text": q.query_text,
            "image_path": q.image_path,
            "timestamp": q.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "location": q.location,
            "user_id": q.user_id
        } for q in queries
    ]), 200

# Get answered queries for farmer page
@app.route('/api/farmer/answers', methods=['GET'])
def get_answers():
    answers = Answer.query.join(Query, Answer.query_id==Query.id)\
        .filter(Query.user_id=="anonymous")\
        .order_by(Answer.timestamp.desc()).all()
    return jsonify([
        {
            "query_id": a.query_id,
            "response_text": a.response_text,
            "responder_type": a.responder_type,
            "timestamp": a.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        } for a in answers
    ]), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
