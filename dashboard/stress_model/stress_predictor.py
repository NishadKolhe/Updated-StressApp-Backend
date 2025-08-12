import os
import pandas as pd
import numpy as np
import pickle
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import empath
from textblob import TextBlob
import spacy
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Initialize all models once
lexicon = empath.Empath()
nlp = spacy.load("en_core_web_sm")
vader = SentimentIntensityAnalyzer()

BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "stress_level_xgb_model.pkl")
FEATURES_PATH = os.path.join(BASE_DIR, "stress_features.pkl")
CSV_PATH = os.path.join(os.path.dirname(__file__), "stress.csv")

def extract_features_from_text(text):
    empath_features = lexicon.analyze(text, normalize=True)
    tb = TextBlob(text)
    tb_sentiment = tb.sentiment.polarity  # -1 to 1

    vader_scores = vader.polarity_scores(text)
    vader_neg = vader_scores["neg"]
    vader_pos = vader_scores["pos"]
    vader_compound = vader_scores["compound"]

    doc = nlp(text)
    pronoun_count = sum(1 for token in doc if token.pos_ == "PRON")
    verb_count = sum(1 for token in doc if token.pos_ == "VERB")

    # Scaled feature values
    features = {
        "lex_liwc_negemo": empath_features.get("negative_emotion", 0) * 100 + vader_neg * 100,
        "lex_liwc_anx": empath_features.get("anxiety", 0) * 100 + vader_neg * 60,
        "lex_liwc_anger": empath_features.get("anger", 0) * 100,
        "lex_liwc_sad": empath_features.get("sadness", 0) * 100,
        "lex_liwc_affect": tb_sentiment * 50,  # sentiment in [-1, 1], scale up
        "lex_liwc_posemo": empath_features.get("positive_emotion", 0) * 100 + vader_pos * 100,
        "lex_liwc_social": empath_features.get("social_media", 0) * 100,
        "lex_dal_avg_activation": 0,
        "lex_dal_avg_imagery": 0,
        "lex_dal_avg_pleasantness": vader_compound * 50,
        "confidence": 1.0
    }

    # Keyword-based boost (amplified)
    lower_text = text.lower()
    if "stress" in lower_text or "stressed" in lower_text:
        features["lex_liwc_anx"] += 8.0
        features["lex_liwc_negemo"] += 8.0
    if "angry" in lower_text:
        features["lex_liwc_anger"] += 5.0
    if "tired" in lower_text or "exhausted" in lower_text:
        features["lex_liwc_sad"] += 5.0
    if "cry" in lower_text or "cried" in lower_text:
        features["lex_liwc_sad"] += 10.0
        features["lex_liwc_negemo"] += 5.0

    return features


def train_and_save_model():
    df = pd.read_csv(CSV_PATH)
    df = df.dropna()

    features = [
        "lex_liwc_negemo",
        "lex_liwc_anx",
        "lex_liwc_anger",
        "lex_liwc_sad",
        "lex_liwc_affect",
        "lex_liwc_posemo",
        "lex_liwc_social",
        "lex_dal_avg_activation",
        "lex_dal_avg_imagery",
        "lex_dal_avg_pleasantness",
        "confidence"
    ]

    df["stress_level"] = (
        df["lex_liwc_negemo"] * 0.4 +
        df["lex_liwc_anx"] * 0.3 +
        df["lex_liwc_sad"] * 0.1 +
        df["confidence"] * 10 * 0.2
    )
    df["stress_level"] = df["stress_level"].clip(0, 10)

    X = df[features]
    y = df["stress_level"]

    xtrain, xtest, ytrain, ytest = train_test_split(X, y, test_size=0.3, random_state=42)

    model = XGBRegressor(n_estimators=100, random_state=42, objective='reg:squarederror')
    model.fit(xtrain, ytrain)

    ypred = model.predict(xtest)
    mse = mean_squared_error(ytest, ypred)
    r2 = r2_score(ytest, ypred)
    print(f"Model trained. Test MSE: {mse:.2f}, R2: {r2:.2f}")

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    with open(FEATURES_PATH, "wb") as f:
        pickle.dump(features, f)

if not os.path.exists(MODEL_PATH) or not os.path.exists(FEATURES_PATH):
    print("Training model since saved model not found...")
    train_and_save_model()

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)
with open(FEATURES_PATH, "rb") as f:
    features = pickle.load(f)

def predict_stress_from_text(text):
    

    features_dict = extract_features_from_text(text)
    input_df = pd.DataFrame([{feat: features_dict.get(feat, 0) for feat in features}])

    prediction = model.predict(input_df)[0]
    prediction = max(0, min(10, prediction))  # clip between 0 and 10
    return prediction

def main():
    import os
    if not os.path.exists("stress_level_xgb_model.pkl"):
        print("Training model since saved model not found...")
        train_and_save_model()

    print("Stress Level Predictor (0–10 scale)")
    print("Type a description of your day (type 'exit' to quit):")

    while True:
        user_input = input("\nYour description: ")
        if user_input.strip().lower() in ("exit", "quit"):
            print("Goodbye.")
            break
        score = predict_stress_from_text(user_input)
        print(f"Predicted stress level: {score:.2f} / 10")

if __name__ == "__main__":
    main()
