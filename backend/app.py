from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from gtts import gTTS
import os

app = Flask(__name__)
CORS(app)

# ==============================
# Database Configuration
# ==============================
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///translations.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ==============================
# Database Model
# ==============================
class Translation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_text = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(10), nullable=False)
    translated_text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# Create database tables
with app.app_context():
    db.create_all()


# ==============================
# Translation Model Loader
# ==============================
loaded_models = {}

def load_translation_model(lang_code):
    if lang_code not in loaded_models:
        model_name = f"Helsinki-NLP/opus-mt-en-{lang_code}"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        loaded_models[lang_code] = (tokenizer, model)
    return loaded_models[lang_code]


# ==============================
# Translate Route
# ==============================
@app.route("/translate", methods=["POST"])
def translate():
    data = request.json
    text_en = data.get("text")
    lang_code = data.get("language")

    if not text_en or not lang_code:
        return jsonify({"error": "Missing text or language"}), 400

    # Translate
    tokenizer, model = load_translation_model(lang_code)
    inputs = tokenizer(text_en, return_tensors="pt", padding=True)
    outputs = model.generate(**inputs)
    translated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Save to database
    new_record = Translation(
        original_text=text_en,
        language=lang_code,
        translated_text=translated_text
    )
    db.session.add(new_record)
    db.session.commit()

    # Generate audio
    audio_path = "output.mp3"
    tts = gTTS(text=translated_text, lang=lang_code)
    tts.save(audio_path)

    return jsonify({
        "translated_text": translated_text,
        "audio_url": "http://127.0.0.1:5000/audio"
    })


# ==============================
# Audio Route
# ==============================
@app.route("/audio")
def get_audio():
    return send_file("output.mp3", mimetype="audio/mpeg")


# ==============================
# History Route
# ==============================
@app.route("/history", methods=["GET"])
def get_history():
    records = Translation.query.order_by(
        Translation.timestamp.desc()
    ).limit(10).all()

    history = []
    for r in records:
        history.append({
            "id": r.id,
            "original_text": r.original_text,
            "language": r.language,
            "translated_text": r.translated_text,
            "timestamp": r.timestamp.strftime("%Y-%m-%d %H:%M")
        })

    return jsonify(history)


@app.route("/delete/<int:id>", methods=["DELETE"])
def delete_translation(id):
    record = Translation.query.get(id)

    if not record:
        return jsonify({"error": "Record not found"}), 404

    db.session.delete(record)
    db.session.commit()

    return jsonify({"message": "Deleted successfully"})

# ==============================
# Run App
# ==============================
if __name__ == "__main__":
    app.run(debug=True)