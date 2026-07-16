"""
ML residual correction model.

Learns the error between physics simulation and real telemetry,
then corrects future physics predictions.

Two modes:
  1. XGBoostRegressor (best performance)
  2. Simple sklearn MLPRegressor fallback

Pipeline:
  physics_features → predict_residual → corrected = physics + residual_prediction
"""

import os
import sys
import json
import numpy as np

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.append(ROOT)

XGB_AVAILABLE = False
SKLEARN_AVAILABLE = False
try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    pass

try:
    from sklearn.neural_network import MLPRegressor
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    SKLEARN_AVAILABLE = True
except ImportError:
    pass

from simulator.calibrate_from_f1 import load_lap_file, extract_speed_trace, extract_throttle_brake_trace, run_simulated_lap
from utils.config_loader import load_yaml

CAR_CONFIG_PATH = os.path.join(ROOT, "configs", "car_simple.yaml")


class ResidualModel:
    """
    Learns and corrects physics model residuals using ML.

    Usage:
        model = ResidualModel()
        model.train(features, targets)     # features = physics states, targets = actual - physics
        correction = model.predict(features)
        corrected_speed = physics_speed + correction
    """

    def __init__(self, model_type: str = "auto"):
        """
        Parameters
        ----------
        model_type : str
            'xgboost', 'random_forest', 'mlp', or 'auto' (best available).
        """
        self.model_type = model_type
        self.model = None
        self.scaler = None
        self.feature_names = [
            "speed_kmh", "throttle", "brake", "yaw_deg",
            "track_curvature", "lap_progress",
            "tire_wear", "fuel_load_pct", "downforce",
        ]
        self._is_trained = False

    def _get_model(self):
        if self.model_type == "xgboost" and XGB_AVAILABLE:
            return xgb.XGBRegressor(
                n_estimators=200, max_depth=6, learning_rate=0.1,
                subsample=0.8, colsample_bytree=0.8,
                random_state=42,
            )
        elif self.model_type == "random_forest" and SKLEARN_AVAILABLE:
            return RandomForestRegressor(
                n_estimators=200, max_depth=10, random_state=42,
            )
        elif self.model_type == "mlp" and SKLEARN_AVAILABLE:
            return MLPRegressor(
                hidden_layer_sizes=(64, 32), activation="relu",
                max_iter=500, random_state=42,
            )
        elif self.model_type == "auto":
            if XGB_AVAILABLE:
                return xgb.XGBRegressor(n_estimators=200, max_depth=6, random_state=42)
            elif SKLEARN_AVAILABLE:
                return RandomForestRegressor(n_estimators=200, random_state=42)
        return None

    def extract_features(
        self,
        packets: list,
        tire_state: dict = None,
        fuel_state: dict = None,
        aero_state: dict = None,
    ) -> np.ndarray:
        """
        Extract feature matrix from session packets.

        Returns (n_samples, n_features) array.
        """
        n = len(packets)
        if n == 0:
            return np.zeros((0, len(self.feature_names)))

        features = np.zeros((n, len(self.feature_names)))

        track_indices = [p.get("track_index", 0) for p in packets]
        n_track_pts = max(track_indices) + 1 if track_indices else 1

        for i, p in enumerate(packets):
            true = p.get("true", {})
            features[i, 0] = true.get("speed_kmh", 0)
            features[i, 1] = true.get("throttle", 0)
            features[i, 2] = true.get("brake_cmd", 0)
            features[i, 3] = true.get("yaw_deg", 0)
            features[i, 4] = np.sin(track_indices[i] / max(n_track_pts, 1) * 2 * np.pi)  # curvature proxy
            features[i, 5] = (track_indices[i] / max(n_track_pts, 1)) if n_track_pts > 0 else 0.0

        # Tire, fuel, aero if provided
        if tire_state:
            features[:, 6] = tire_state.get("wear_pct", 0) / 100.0
        if fuel_state:
            features[:, 7] = fuel_state.get("fuel_pct", 100)
        if aero_state:
            features[:, 8] = aero_state.get("downforce_coeff", 1.2)

        return features

    def build_training_data(
        self,
        real_packets: list,
        car_params: dict = None,
        dt: float = 0.1,
    ) -> tuple:
        """
        Build (features, targets) from real telemetry.

        Features: physics state + control inputs.
        Targets: residual = real_speed - physics_speed.
        """
        if car_params is None:
            car_params = load_yaml(CAR_CONFIG_PATH)

        throttles, brakes = extract_throttle_brake_trace(real_packets)
        real_speeds = extract_speed_trace(real_packets)
        sim_speeds = run_simulated_lap(car_params, throttles, brakes, dt)

        n = min(len(real_speeds), len(sim_speeds))
        features = self.extract_features(real_packets[:n])
        targets = real_speeds[:n] - sim_speeds[:n]

        return features, targets

    def train(
        self,
        features: np.ndarray,
        targets: np.ndarray,
        test_size: float = 0.2,
    ) -> dict:
        """
        Train the residual model.

        Returns dict with training metrics.
        """
        if features.shape[0] == 0:
            return {"error": "No training data"}

        model = self._get_model()
        if model is None:
            return {"error": "No ML library available. Install xgboost or scikit-learn."}

        if SKLEARN_AVAILABLE:
            self.scaler = StandardScaler()
            features_scaled = self.scaler.fit_transform(features)
        else:
            features_scaled = features

        if test_size > 0 and features.shape[0] > 10:
            X_train, X_test, y_train, y_test = train_test_split(
                features_scaled, targets, test_size=test_size, random_state=42
            )
            model.fit(X_train, y_train)
            train_score = model.score(X_train, y_train)
            test_score = model.score(X_test, y_test)

            # Predict residuals for metrics
            preds = model.predict(X_test)
            mae = float(np.mean(np.abs(preds - y_test)))
            rmse = float(np.sqrt(np.mean((preds - y_test) ** 2)))
        else:
            model.fit(features_scaled, targets)
            train_score = model.score(features_scaled, targets)
            test_score = None
            preds = model.predict(features_scaled)
            mae = float(np.mean(np.abs(preds - targets)))
            rmse = float(np.sqrt(np.mean((preds - targets) ** 2)))

        self.model = model
        self._is_trained = True

        return {
            "model_type": type(model).__name__,
            "train_r2": round(train_score, 4),
            "test_r2": round(test_score, 4) if test_score is not None else None,
            "mae_kmh": round(mae, 3),
            "rmse_kmh": round(rmse, 3),
            "n_samples": features.shape[0],
            "n_features": features.shape[1],
        }

    def predict(self, features: np.ndarray) -> np.ndarray:
        """Predict speed residual correction."""
        if not self._is_trained or self.model is None:
            return np.zeros(features.shape[0])

        if self.scaler is not None and features.shape[1] == self.scaler.n_features_in_:
            features = self.scaler.transform(features)

        return self.model.predict(features)

    def correct_speed(
        self, physics_speed: float, feature_vector: np.ndarray
    ) -> float:
        """Apply residual correction to a single physics speed value."""
        if not self._is_trained:
            return physics_speed
        correction = self.predict(feature_vector.reshape(1, -1))[0]
        return physics_speed + correction

    def save(self, path: str):
        """Save trained model to disk."""
        import pickle
        data = {
            "model": self.model,
            "scaler": self.scaler,
            "feature_names": self.feature_names,
            "is_trained": self._is_trained,
        }
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(data, f)

    def load(self, path: str):
        """Load trained model from disk."""
        import pickle
        with open(path, "rb") as f:
            data = pickle.load(f)
        self.model = data["model"]
        self.scaler = data["scaler"]
        self.feature_names = data["feature_names"]
        self._is_trained = data["is_trained"]

    @property
    def is_trained(self) -> bool:
        return self._is_trained


# ---------------------------------------------------------------------------
#  CLI TRAINING UTILITY
# ---------------------------------------------------------------------------

def train_residual_from_logs(
    log_dir: str = None,
    car_params: dict = None,
    model_type: str = "auto",
    save_path: str = None,
    dt: float = 0.1,
) -> ResidualModel:
    """
    Train residual model from all session logs in a directory.

    Parameters
    ----------
    log_dir : str
        Directory containing session log JSONs.
    car_params : dict
        Car parameters for physics simulation.
    model_type : str
    save_path : str
        Path to save trained model.
    dt : float

    Returns
    -------
    ResidualModel
    """
    if log_dir is None:
        log_dir = os.path.join(ROOT, "data", "logs")

    if car_params is None:
        car_params = load_yaml(CAR_CONFIG_PATH)

    if save_path is None:
        save_path = os.path.join(ROOT, "data", "models", "residual_model.pkl")

    all_features = []
    all_targets = []

    json_files = [f for f in os.listdir(log_dir) if f.endswith(".json")]
    for fname in json_files:
        fpath = os.path.join(log_dir, fname)
        try:
            packets = load_lap_file(fpath)
            model = ResidualModel(model_type=model_type)
            features, targets = model.build_training_data(packets, car_params, dt)
            if len(features) > 0:
                all_features.append(features)
                all_targets.append(targets.reshape(-1, 1))
                print(f"  {fname}: {len(features)} samples")
        except Exception as e:
            print(f"  Skipping {fname}: {e}")

    if not all_features:
        print("No training data found.")
        return ResidualModel()

    X = np.vstack(all_features)
    y = np.vstack(all_targets).ravel()

    print(f"Training on {X.shape[0]} samples, {X.shape[1]} features")
    model = ResidualModel(model_type=model_type)
    metrics = model.train(X, y)
    print(f"Train metrics: {metrics}")

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        model.save(save_path)
        print(f"Model saved to {save_path}")

    return model


def cli():
    import argparse
    parser = argparse.ArgumentParser(description="Train residual correction model")
    parser.add_argument("--log-dir", type=str, default=None)
    parser.add_argument("--model-type", type=str, default="auto", choices=["auto", "xgboost", "random_forest", "mlp"])
    parser.add_argument("--save-path", type=str, default=None)
    args = parser.parse_args()

    train_residual_from_logs(
        log_dir=args.log_dir,
        model_type=args.model_type,
        save_path=args.save_path,
    )


if __name__ == "__main__":
    cli()
