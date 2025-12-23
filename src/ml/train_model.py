import pandas as pd
import logging
import mlflow
import mlflow.sklearn
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from src.ml.data_preparation import load_and_prepare_data
from src.config.settings import MLRUNS_DIR, MODELS_DIR, TRAINED_MODEL_PATH

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def train_sales_forecast_model(n_estimators, max_depth):
    df = load_and_prepare_data()

    logger.info("Splitting data into training and testing sets...")
    
    features = ['month', 'year', 'prev_month_sales']
    X = df[features]
    y = df['y']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=42)

    
    
    mlflow.set_tracking_uri(MLRUNS_DIR.as_uri())
    mlflow.set_experiment("Smart_Inventory_Sales_Forecast")

    run_name = f"RF_n{n_estimators}_d{max_depth}"

    with mlflow.start_run(run_name=run_name):
        params = {
            'n_estimators': n_estimators,
            'max_depth': max_depth,
            'random_state': 42
        }

        model = RandomForestRegressor(**params)
        model.fit(X_train, y_train)

        predictions = model.predict(X_test)

        metrics = {
            'mae': mean_absolute_error(y_test, predictions),
            'mse': mean_squared_error(y_test, predictions),
            'r2': r2_score(y_test, predictions)
        }

        MODELS_DIR.mkdir(exist_ok=True)
        joblib.dump(model, TRAINED_MODEL_PATH)
        logger.info(f"Model saved explicitly for deployment at {TRAINED_MODEL_PATH}")

        mlflow.log_params(params)
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(model, "random_forest_model")

        logger.info("Model Trained and Logged")

if __name__ == "__main__":
    train_sales_forecast_model(n_estimators=200, max_depth=20)