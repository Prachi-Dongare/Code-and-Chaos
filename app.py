from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

# Your image model function is in a separate file, so you import it here.
from model_utils import predict_image
# Your text model function is in a separate file, so you import it here.
from nlp_utils import get_answer

# Create the Flask application instance
app = Flask(__name__)

# Configure the SQLite database
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database object
db = SQLAlchemy(app)

# Define your database models (tables)
class Query(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100))
    query_text = db.Column(db.String(500), nullable=True)
    image_path = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(50), default='pending_ai')
    ai_confidence = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.DateTime, default=db.func.now())

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    query_id = db.Column(db.Integer, db.ForeignKey('query.id'), nullable=False)
    responder_type = db.Column(db.String(20), default='AI')
    response_text = db.Column(db.String(1000), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now())

class Expert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    specialty = db.Column(db.String(100))

class KnowledgeBase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(5000), nullable=False)
    tags = db.Column(db.String(500))
    embeddings = db.Column(db.PickleType, nullable=True)

# A function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}

# Set the upload folder for images
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Placeholder endpoint for the root URL
@app.route('/')
def home():
    return "<h1>Agri-AI Backend is Running!</h1>"

# API Endpoint for image queries
@app.route('/api/query/image', methods=['POST'])
def query_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Call the real model and use its prediction
        prediction_result = predict_image(file_path)
        ai_confidence = prediction_result['confidence']
        ai_response = {
            "prediction": prediction_result['prediction'],
            "confidence": ai_confidence,
            "solution": "Placeholder: This will be a real solution in the final version."
        }

        new_query = Query(user_id="anonymous", image_path=file_path, status="pending_ai", ai_confidence=ai_confidence)
        db.session.add(new_query)
        db.session.commit()

        return jsonify({"message": "Image received and is being processed", "result": ai_response}), 200
    else:
        return jsonify({"error": "File type not allowed"}), 400

# API Endpoint for text queries
@app.route('/api/query/text', methods=['POST'])
def query_text():
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({"error": "Missing 'query' in request body"}), 400
    query_text = data.get('query')
    
    if not data or 'query' not in data:
        return jsonify({"error": "Missing 'query' in request body"}), 400

    query_text = data.get('query')
    # Add a line to get the region from the request
    region = data.get('region')
    # ... (rest of the function)

    # Call the real NLP model and use its prediction
    prediction_result = get_answer(query_text)
    ai_confidence = prediction_result['confidence']
    ai_response = {
        "answer": prediction_result['answer'],
        "confidence": ai_confidence,
        "recommendations": prediction_result['recommendations']
    }
    
    new_query = Query(user_id="anonymous", query_text=query_text, status="pending_ai", ai_confidence=ai_confidence)
    db.session.add(new_query)
    db.session.commit()

    return jsonify({"message": "Query received and is being processed", "result": ai_response}), 200

@app.route('/api/expert/reply', methods=['POST'])
def expert_reply():
    data = request.get_json()
    if not data or 'query_id' not in data or 'response_text' not in data:
        return jsonify({"error": "Missing required fields"}), 400

    query_id = data.get('query_id')
    response_text = data.get('response_text')
    
    # Update the original query's status
    query = Query.query.get(query_id)
    if not query:
        return jsonify({"error": "Query not found"}), 404

    query.status = 'expert_answered'

    # Save the expert's answer
    new_answer = Answer(
        query_id=query_id,
        responder_type='Expert',
        response_text=response_text
    )
    db.session.add(new_answer)
    db.session.commit()

    # The KnowledgeBase model will be populated with this answer later
    # For now, just a placeholder.
    
    return jsonify({"message": "Expert reply saved successfully", "query_id": query_id}), 200

# API Endpoint to get overall query trends
@app.route('/api/dashboard/metrics', methods=['GET'])
def get_dashboard_metrics():
    # Get total number of queries
    total_queries = Query.query.count()
    
    # Get queries answered by AI vs. Expert
    ai_answered = Query.query.filter_by(status='ai_answered').count()
    expert_answered = Query.query.filter_by(status='expert_answered').count()
    
    # Calculate automation rate
    automation_rate = (ai_answered / total_queries) * 100 if total_queries > 0 else 0
    
    # Get the most common queries (based on keywords)
    # This is a simple placeholder to show a query trend.
    top_issues = ["Yellowing Leaves", "Aphids", "Overwatering"]

    return jsonify({
        "total_queries": total_queries,
        "ai_answered": ai_answered,
        "expert_answered": expert_answered,
        "automation_rate": round(automation_rate, 2),
        "top_issues": top_issues
    }), 200

# API Endpoint to get a list of all queries for expert review
@app.route('/api/dashboard/queries', methods=['GET'])
def get_all_queries():
    queries = Query.query.order_by(Query.timestamp.desc()).all()
    queries_list = []
    for query in queries:
        queries_list.append({
            "id": query.id,
            "query_text": query.query_text,
            "image_path": query.image_path,
            "status": query.status,
            "ai_confidence": query.ai_confidence,
            "timestamp": query.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        })
    return jsonify(queries_list), 200

# Run the application
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
