import os
import re
import logging
from collections import defaultdict

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sqlalchemy.ext.asyncio import AsyncSession

import mlflow
import mlflow.sklearn

from app.training import repository as training_repository

logger = logging.getLogger(__name__)

BACKEND_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
MODEL_DIR = os.path.join(BACKEND_ROOT, "ml_models")
MODEL_PATH = os.path.join(MODEL_DIR, "model.pkl")

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "]+",
    flags=re.UNICODE,
)


def extract_features(messages: list[dict]) -> dict:
    """Extract per-player features from a list of training messages.

    Each message dict must contain: user_id, role, phase, content.
    Returns a dict mapping user_id -> feature dict.
    """
    player_messages: dict[int, list[dict]] = defaultdict(list)
    for msg in messages:
        player_messages[msg["user_id"]].append(msg)

    features: dict[int, dict] = {}

    for user_id, msgs in player_messages.items():
        total = len(msgs)
        if total == 0:
            continue

        messages_by_phase: dict[str, int] = defaultdict(int)
        lengths: list[int] = []
        word_counts: list[int] = []
        question_count = 0
        caps_count = 0
        emoji_count = 0
        phases_active: set[str] = set()
        interaction_count = 0
        discussion_count = 0
        voting_count = 0

        for msg in msgs:
            content = msg["content"]
            phase = msg["phase"]

            messages_by_phase[phase] += 1
            phases_active.add(phase)

            content_len = len(content)
            lengths.append(content_len)
            word_counts.append(len(content.split()))

            if "?" in content:
                question_count += 1

            words = content.split()
            if words and all(w.isupper() and len(w) > 1 for w in words):
                caps_count += 1

            if EMOJI_PATTERN.search(content):
                emoji_count += 1

            if phase == "interaction":
                interaction_count += 1
            elif phase == "discussion":
                discussion_count += 1
            elif phase == "voting":
                voting_count += 1

        features[user_id] = {
            "total_messages": total,
            "messages_by_phase": dict(messages_by_phase),
            "avg_message_length": float(np.mean(lengths)),
            "question_ratio": question_count / total,
            "caps_ratio": caps_count / total,
            "emoji_ratio": emoji_count / total,
            "unique_phases_active_in": len(phases_active),
            "interaction_message_ratio": interaction_count / total,
            "discussion_message_ratio": discussion_count / total,
            "voting_message_ratio": voting_count / total,
            "avg_words_per_message": float(np.mean(word_counts)),
        }

    return features


def _features_to_vector(features: dict) -> np.ndarray:
    """Convert a single player's feature dict to a numeric numpy array.

    Drops messages_by_phase (dict) and keeps only scalar features
    in a fixed order.
    """
    return np.array([
        features["total_messages"],
        features["avg_message_length"],
        features["question_ratio"],
        features["caps_ratio"],
        features["emoji_ratio"],
        features["unique_phases_active_in"],
        features["interaction_message_ratio"],
        features["discussion_message_ratio"],
        features["voting_message_ratio"],
        features["avg_words_per_message"],
    ])


FEATURE_NAMES = [
    "total_messages",
    "avg_message_length",
    "question_ratio",
    "caps_ratio",
    "emoji_ratio",
    "unique_phases_active_in",
    "interaction_message_ratio",
    "discussion_message_ratio",
    "voting_message_ratio",
    "avg_words_per_message",
]


async def train_model(db: AsyncSession) -> dict:
    """Train the coordinator detection model.

    Returns dict with accuracy, model_path, and samples_used,
    or an error dict if training cannot proceed.
    """
    all_messages = await training_repository.get_all_training_data(db)

    if not all_messages:
        return {"error": "No training data available"}

    grouped: dict[tuple[int, int], list[dict]] = defaultdict(list)
    role_map: dict[tuple[int, int], str] = {}

    for msg in all_messages:
        key = (msg.game_id, msg.user_id)
        grouped[key].append({
            "user_id": msg.user_id,
            "role": msg.role,
            "phase": msg.phase,
            "content": msg.content,
        })
        role_map[key] = msg.role

    X_list: list[np.ndarray] = []
    y_list: list[int] = []

    for key, msgs in grouped.items():
        player_features = extract_features(msgs)
        if key[1] not in player_features:
            continue
        vec = _features_to_vector(player_features[key[1]])
        label = 1 if role_map[key] == "coordinator" else 0
        X_list.append(vec)
        y_list.append(label)

    X = np.array(X_list)
    y = np.array(y_list)

    if len(X) < 10:
        return {
            "error": f"Not enough samples for training: {len(X)} (minimum 10 required)"
        }

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y if len(np.unique(y)) > 1 else None,
    )

    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    accuracy = float(accuracy_score(y_test, y_pred))

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(clf, MODEL_PATH)

    mlflow.set_experiment("secret_signal_coordinator_detection")
    with mlflow.start_run():
        mlflow.log_param("n_estimators", 100)
        mlflow.log_param("random_state", 42)
        mlflow.log_param("samples", len(X))
        mlflow.log_param("features", len(FEATURE_NAMES))
        mlflow.log_metric("accuracy", accuracy)
        mlflow.sklearn.log_model(clf, "model")

    logger.info(
        "Model trained with accuracy=%.4f on %d samples",
        accuracy,
        len(X),
    )

    return {
        "accuracy": accuracy,
        "model_path": MODEL_PATH,
        "samples_used": len(X),
    }


def load_model() -> RandomForestClassifier:
    """Load the trained model from disk.

    Raises FileNotFoundError if the model does not exist.
    """
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Model not found at {MODEL_PATH}. Train the model first."
        )

    model = joblib.load(MODEL_PATH)
    logger.info("Model loaded from %s", MODEL_PATH)
    return model


async def predict_coordinator(db: AsyncSession, game_id: int) -> dict:
    """Predict the probability of each player being the coordinator.

    Returns dict mapping user_id -> {"probability": float, "prediction": str}.
    """
    model = load_model()

    messages = await training_repository.get_game_training_data(db, game_id)

    if not messages:
        return {"error": f"No training data found for game {game_id}"}

    grouped: dict[int, list[dict]] = defaultdict(list)
    for msg in messages:
        grouped[msg.user_id].append({
            "user_id": msg.user_id,
            "role": msg.role,
            "phase": msg.phase,
            "content": msg.content,
        })

    player_features = extract_features(
        [
            msg
            for user_msgs in grouped.values()
            for msg in user_msgs
        ]
    )

    results: dict[int, dict] = {}

    for user_id, feats in player_features.items():
        vec = _features_to_vector(feats).reshape(1, -1)
        prob = float(model.predict_proba(vec)[0][1])
        label = "coordinator" if prob >= 0.5 else "not_coordinator"
        results[user_id] = {
            "probability": round(prob, 4),
            "prediction": label,
        }

    return results
