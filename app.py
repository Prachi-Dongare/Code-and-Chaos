from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get", methods=["POST"])
def chatbot_response():
    user_msg = request.json.get("msg").lower()
    
    # Simple rule-based logic (later replace with ML)
    if "yellow leaves" in user_msg:
        reply = "This looks like nitrogen deficiency. Suggest urea spray."
    elif "pest" in user_msg:
        reply = "Upload a leaf image for better diagnosis (coming soon!)."
    elif "water" in user_msg:
        reply = "Water your crop early morning or late evening to reduce evaporation."
    else:
        reply = "Sorry, I didn’t understand. Please ask about pest, water, or leaves."

    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True)
