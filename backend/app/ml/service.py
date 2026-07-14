import os
import re
import logging
from collections import defaultdict

import joblib
import numpy as np
from sklearn.ensemble import (
    RandomForestClassifier,
    GradientBoostingClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, f1_score
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
BEST_MODEL_META_PATH = os.path.join(MODEL_DIR, "best_model.json")

EMOJI_PATTERN = re.compile(
    "["
    "\U0001f600-\U0001f64f"
    "\U0001f300-\U0001f5ff"
    "\U0001f680-\U0001f6ff"
    "\U0001f1e0-\U0001f1ff"
    "\U00002702-\U000027b0"
    "\U000024c2-\U0001f251"
    "]+",
    flags=re.UNICODE,
)


MODEL_REGISTRY = {
    "random_forest": RandomForestClassifier(n_estimators=100, random_state=42),
    "logistic_regression": LogisticRegression(
        max_iter=1000, random_state=42, class_weight="balanced"
    ),
    "gradient_boosting": GradientBoostingClassifier(n_estimators=100, random_state=42),
    "svm": SVC(
        kernel="rbf",
        probability=True,
        random_state=42,
        class_weight="balanced",
    ),
}


def extract_features(messages: list[dict]) -> dict:
    """Extract per-player features from a list of training messages.

    Each message dict must contain: user_id, role, phase, content.
    Optional keys: has_reply (bool), reply_to_role (str|None).
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

        # Social / reply / reaction features
        reply_count = 0
        reply_to_coordinator = 0
        reply_to_detective = 0
        reply_to_citizen = 0
        reaction_events = 0
        unique_reaction_emojis: set[str] = set()
        text_message_count = 0

        for msg in msgs:
            content = msg["content"]
            phase = msg["phase"]
            is_reaction = content.startswith("[reaction:")

            if is_reaction:
                reaction_events += 1
                emoji_val = content[len("[reaction:") : -1]
                unique_reaction_emojis.add(emoji_val)
                continue

            text_message_count += 1
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

            if msg.get("has_reply"):
                reply_count += 1
                reply_role = msg.get("reply_to_role")
                if reply_role == "coordinator":
                    reply_to_coordinator += 1
                elif reply_role == "detective":
                    reply_to_detective += 1
                elif reply_role in ("citizen", "operative"):
                    reply_to_citizen += 1

        effective_total = max(total, 1)

        features[user_id] = {
            "total_messages": total,
            "messages_by_phase": dict(messages_by_phase),
            "avg_message_length": (float(np.mean(lengths)) if lengths else 0.0),
            "question_ratio": (
                question_count / text_message_count if text_message_count > 0 else 0.0
            ),
            "caps_ratio": (
                caps_count / text_message_count if text_message_count > 0 else 0.0
            ),
            "emoji_ratio": (
                emoji_count / text_message_count if text_message_count > 0 else 0.0
            ),
            "unique_phases_active_in": len(phases_active),
            "interaction_message_ratio": (
                interaction_count / text_message_count
                if text_message_count > 0
                else 0.0
            ),
            "discussion_message_ratio": (
                discussion_count / text_message_count if text_message_count > 0 else 0.0
            ),
            "voting_message_ratio": (
                voting_count / text_message_count if text_message_count > 0 else 0.0
            ),
            "avg_words_per_message": (
                float(np.mean(word_counts)) if word_counts else 0.0
            ),
            # Social / reply features
            "reply_ratio": reply_count / effective_total,
            "reply_to_coordinator_ratio": (reply_to_coordinator / effective_total),
            "reply_to_detective_ratio": (reply_to_detective / effective_total),
            "reply_to_citizen_ratio": (reply_to_citizen / effective_total),
            # Reaction features
            "reaction_event_ratio": reaction_events / effective_total,
            "unique_reaction_emoji_count": len(unique_reaction_emojis),
            # Text-only message count for reference
            "text_message_ratio": text_message_count / effective_total,
        }

    return features


def _features_to_vector(features: dict) -> np.ndarray:
    """Convert a single player's feature dict to a numeric numpy array.

    Drops messages_by_phase (dict) and keeps only scalar features
    in a fixed order.
    """
    return np.array(
        [
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
            features["reply_ratio"],
            features["reply_to_coordinator_ratio"],
            features["reply_to_detective_ratio"],
            features["reply_to_citizen_ratio"],
            features["reaction_event_ratio"],
            features["unique_reaction_emoji_count"],
            features["text_message_ratio"],
        ]
    )


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
    "reply_ratio",
    "reply_to_coordinator_ratio",
    "reply_to_detective_ratio",
    "reply_to_citizen_ratio",
    "reaction_event_ratio",
    "unique_reaction_emoji_count",
    "text_message_ratio",
]


async def train_model(db: AsyncSession) -> dict:
    """Train multiple models, compare performance, and keep the best one.

    Returns dict with best_model_name, accuracy, model_path, and samples_used,
    or an error dict if training cannot proceed.
    """
    all_messages = await training_repository.get_all_training_data(db)

    if not all_messages:
        return {"error": "No training data available"}

    grouped: dict[tuple[int, int], list[dict]] = defaultdict(list)
    role_map: dict[tuple[int, int], str] = {}

    for msg in all_messages:
        key = (msg.game_id, msg.user_id)
        grouped[key].append(
            {
                "user_id": msg.user_id,
                "role": msg.role,
                "phase": msg.phase,
                "content": msg.content,
                "has_reply": getattr(msg, "has_reply", False),
                "reply_to_role": getattr(msg, "reply_to_role", None),
            }
        )
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
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y if len(np.unique(y)) > 1 else None,
    )

    os.makedirs(MODEL_DIR, exist_ok=True)

    best_score = -1.0
    best_model = None
    best_name = None
    best_accuracy = 0.0
    best_f1 = 0.0
    all_results: list[dict] = []

    mlflow.set_experiment("secret_signal_coordinator_detection")

    for name, model in MODEL_REGISTRY.items():
        try:
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            accuracy = float(accuracy_score(y_test, y_pred))
            f1 = float(f1_score(y_test, y_pred, zero_division=0))

            cv_scores = cross_val_score(
                model,
                X_train,
                y_train,
                cv=min(3, len(np.unique(y_train))),
                scoring="accuracy",
            )
            cv_mean = float(cv_scores.mean())

            score = (accuracy + f1 + cv_mean) / 3

            all_results.append(
                {
                    "model": name,
                    "accuracy": round(accuracy, 4),
                    "f1_score": round(f1, 4),
                    "cv_accuracy": round(cv_mean, 4),
                    "combined_score": round(score, 4),
                }
            )

            with mlflow.start_run(run_name=name):
                mlflow.log_param("model", name)
                mlflow.log_param("samples", len(X))
                mlflow.log_param("features", len(FEATURE_NAMES))
                mlflow.log_metric("accuracy", accuracy)
                mlflow.log_metric("f1_score", f1)
                mlflow.log_metric("cv_accuracy", cv_mean)
                mlflow.log_metric("combined_score", score)
                mlflow.sklearn.log_model(model, name)

            if score > best_score:
                best_score = score
                best_model = model
                best_name = name
                best_accuracy = accuracy
                best_f1 = f1

        except Exception as e:
            logger.warning("Model %s failed: %s", name, e)
            all_results.append(
                {
                    "model": name,
                    "error": str(e),
                }
            )

    if best_model is None:
        return {"error": "All models failed during training"}

    joblib.dump(best_model, MODEL_PATH)

    best_meta = {
        "best_model": best_name,
        "accuracy": round(best_accuracy, 4),
        "f1_score": round(best_f1, 4),
        "samples": len(X),
        "all_results": all_results,
    }
    with open(BEST_MODEL_META_PATH, "w") as f:
        import json

        json.dump(best_meta, f, indent=2)

    with mlflow.start_run(run_name=f"best_{best_name}"):
        mlflow.log_param("best_model", best_name)
        mlflow.log_param("samples", len(X))
        mlflow.log_param("features", len(FEATURE_NAMES))
        mlflow.log_metric("accuracy", best_accuracy)
        mlflow.log_metric("f1_score", best_f1)
        mlflow.sklearn.log_model(best_model, "best_model")

    logger.info(
        "Best model: %s with accuracy=%.4f, f1=%.4f on %d samples",
        best_name,
        best_accuracy,
        best_f1,
        len(X),
    )

    return {
        "best_model": best_name,
        "accuracy": best_accuracy,
        "model_path": MODEL_PATH,
        "samples_used": len(X),
        "all_results": [
            {k: v for k, v in r.items() if k != "model"} for r in all_results
        ],
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
        grouped[msg.user_id].append(
            {
                "user_id": msg.user_id,
                "role": msg.role,
                "phase": msg.phase,
                "content": msg.content,
                "has_reply": getattr(msg, "has_reply", False),
                "reply_to_role": getattr(msg, "reply_to_role", None),
            }
        )

    player_features = extract_features(
        [msg for user_msgs in grouped.values() for msg in user_msgs]
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
