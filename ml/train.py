import os
import joblib
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

# Import preprocessing functions
from ml.preprocessing import load_data, preprocess_data, split_data, scale_features


def train_and_evaluate(
    model,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    model_name: str
) -> dict:
 
    print(f"\n==========================================")
    print(f" TRAINING & EVALUATING: {model_name}")
    print(f"==========================================")

    # Train model
    model.fit(X_train, y_train)

    # Predictions
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)

    # Metrics
    train_acc = accuracy_score(y_train, y_pred_train)
    test_acc = accuracy_score(y_test, y_pred_test)

    acc = accuracy_score(y_test, y_pred_test)
    prec = precision_score(y_test, y_pred_test, zero_division=0)
    rec = recall_score(y_test, y_pred_test, zero_division=0)
    f1 = f1_score(y_test, y_pred_test, zero_division=0)

    cm = confusion_matrix(y_test, y_pred_test)
    cr = classification_report(y_test, y_pred_test, digits=4)

    print(f"Training Accuracy: {train_acc:.4f}")
    print(f"Testing Accuracy: {test_acc:.4f}\n")
    print("Evaluation:")
    print(f"Accuracy : {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall   : {rec:.4f}")
    print(f"F1 Score : {f1:.4f}\n")
    print("Confusion Matrix:")
    print(cm)
    print("\nClassification Report:")
    print(cr)

    return {
        'model': model,
        'Accuracy': acc,
        'Precision': prec,
        'Recall': rec,
        'F1 Score': f1,
        'Training Accuracy': train_acc,
        'Testing Accuracy': test_acc,
        'Confusion Matrix': cm,
        'Classification Report': cr
    }


def tune_decision_tree(X_train: pd.DataFrame, y_train: pd.Series) -> DecisionTreeClassifier:
    print("\nRunning hyperparameter tuning for Decision Tree using GridSearchCV...")
    param_grid = {
        'max_depth': [4, 6, 8, 10],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4]
    }
    dt = DecisionTreeClassifier(random_state=42)
    grid_search = GridSearchCV(
        estimator=dt,
        param_grid=param_grid,
        scoring='f1',
        cv=3,
        n_jobs=-1,
        verbose=0
    )
    grid_search.fit(X_train, y_train)
    print(f"Best CV F1-score: {grid_search.best_score_:.4f}")
    print(f"Best hyperparameters: {grid_search.best_params_}")
    return grid_search.best_estimator_


def tune_random_forest(X_train: pd.DataFrame, y_train: pd.Series) -> RandomForestClassifier:
    print("\nRunning hyperparameter tuning for Random Forest using GridSearchCV...")
    param_grid = {
        'n_estimators': [50, 100, 150],
        'max_depth': [8, 12, None],
        'min_samples_split': [2, 5],
        'min_samples_leaf': [1, 2]
    }
    rf = RandomForestClassifier(random_state=42)
    grid_search = GridSearchCV(
        estimator=rf,
        param_grid=param_grid,
        scoring='f1',
        cv=3,
        n_jobs=-1,
        verbose=0
    )
    grid_search.fit(X_train, y_train)
    print(f"Best CV F1-score: {grid_search.best_score_:.4f}")
    print(f"Best hyperparameters: {grid_search.best_params_}")
    return grid_search.best_estimator_


def tune_gradient_boosting(X_train: pd.DataFrame, y_train: pd.Series) -> GradientBoostingClassifier:
    print("\nRunning hyperparameter tuning for Gradient Boosting using GridSearchCV...")
    param_grid = {
        'n_estimators': [100, 150],
        'learning_rate': [0.01, 0.05, 0.1],
        'max_depth': [3, 4, 5]
    }
    gb = GradientBoostingClassifier(random_state=42)
    grid_search = GridSearchCV(
        estimator=gb,
        param_grid=param_grid,
        scoring='f1',
        cv=3,
        n_jobs=-1,
        verbose=0
    )
    grid_search.fit(X_train, y_train)
    print(f"Best CV F1-score: {grid_search.best_score_:.4f}")
    print(f"Best hyperparameters: {grid_search.best_params_}")
    return grid_search.best_estimator_


def print_comparison_table(results: dict):
    print("\n==========================================================================================")
    print("                              MODEL COMPARISON TABLE")
    print("==========================================================================================")
    header = f"| {'Model':<30} | {'Accuracy':<8} | {'Precision':<9} | {'Recall':<8} | {'F1 Score':<8} | {'Train Acc':<9} | {'Test Acc':<8} |"
    separator = f"|{'-'*32}|{'-'*10}|{'-'*11}|{'-'*10}|{'-'*10}|{'-'*11}|{'-'*10}|"
    print(header)
    print(separator)

    for model_name, metrics in results.items():
        row = (
            f"| {model_name:<30} | "
            f"{metrics['Accuracy']:<8.4f} | "
            f"{metrics['Precision']:<9.4f} | "
            f"{metrics['Recall']:<8.4f} | "
            f"{metrics['F1 Score']:<8.4f} | "
            f"{metrics['Training Accuracy']:<9.4f} | "
            f"{metrics['Testing Accuracy']:<8.4f} |"
        )
        print(row)
    print("==========================================================================================\n")


def print_decision_tree_comparison(dt_orig: dict, dt_pruned: dict):
    print("\n==================================================")
    print("         DECISION TREE GENERALIZATION COMPARISON")
    print("==================================================")
    header = f"| {'Metric':<20} | {'Original DT':<12} | {'Pruned DT':<12} |"
    separator = f"|{'-'*22}|{'-'*14}|{'-'*14}|"
    print(header)
    print(separator)

    metrics_list = ['Training Accuracy', 'Testing Accuracy', 'Precision', 'Recall', 'F1 Score']
    for m in metrics_list:
        row = f"| {m:<20} | {dt_orig[m]:<12.4f} | {dt_pruned[m]:<12.4f} |"
        print(row)
    print("==================================================\n")


def main():
    # 1. Load and Preprocess Data
    data_path = os.path.join('data', 'raw', 'ai4i2020.csv')
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Dataset not found at {data_path}")

    df = load_data(data_path)
    X, y = preprocess_data(df)

    # 2. Train-Test Split (Stratified, random_state=123)
    X_train, X_test, y_train, y_test = split_data(X, y, test_size=0.2, random_state=123)

    # 3. Create Scaled Sets (For Logistic Regression models)
    X_train_scaled, X_test_scaled, scaler = scale_features(X_train, X_test)

    # Dictionary to collect results
    all_results = {}

    # --- Model 1: Logistic Regression ---
    lr_model = LogisticRegression(random_state=42, max_iter=1000)
    all_results['Logistic Regression'] = train_and_evaluate(
        lr_model, X_train_scaled, y_train, X_test_scaled, y_test, "Logistic Regression"
    )

    # --- Model 2: Balanced Logistic Regression ---
    lr_bal_model = LogisticRegression(random_state=42, class_weight='balanced', max_iter=1000)
    all_results['Balanced Logistic Regression'] = train_and_evaluate(
        lr_bal_model, X_train_scaled, y_train, X_test_scaled, y_test, "Balanced Logistic Regression"
    )

    # --- Model 3: Decision Tree (Baseline) ---
    dt_baseline = DecisionTreeClassifier(random_state=42)
    all_results['Decision Tree'] = train_and_evaluate(
        dt_baseline, X_train, y_train, X_test, y_test, "Decision Tree (Baseline)"
    )

    # --- Model 4: Pruned Decision Tree ---
    # We prune the decision tree using hyperparameter tuning values we searched:
    # max_depth=6, min_samples_split=2, min_samples_leaf=1
    dt_pruned = DecisionTreeClassifier(
        max_depth=6,
        min_samples_split=2,
        min_samples_leaf=1,
        random_state=42
    )
    all_results['Pruned Decision Tree'] = train_and_evaluate(
        dt_pruned, X_train, y_train, X_test, y_test, "Pruned Decision Tree"
    )

    # Compare Decision Tree Generalization
    print_decision_tree_comparison(all_results['Decision Tree'], all_results['Pruned Decision Tree'])

    # Explain generalization improvement
    print("Generalization Analysis:")
    orig_gap = all_results['Decision Tree']['Training Accuracy'] - all_results['Decision Tree']['Testing Accuracy']
    pruned_gap = all_results['Pruned Decision Tree']['Training Accuracy'] - all_results['Pruned Decision Tree']['Testing Accuracy']
    print(f"- Original Decision Tree Overfitting Gap (Train Acc - Test Acc): {orig_gap:.4f}")
    print(f"- Pruned Decision Tree Overfitting Gap (Train Acc - Test Acc): {pruned_gap:.4f}")
    if pruned_gap < orig_gap:
        print("-> SUCCESS: Pruning reduced the generalization gap and Alleviated overfitting.")
        print(f"   Pruned DT test F1-score improved from {all_results['Decision Tree']['F1 Score']:.4f} to {all_results['Pruned Decision Tree']['F1 Score']:.4f}.")

    # --- Model 5: Tuned Decision Tree (Auto Search) ---
    tuned_dt_estimator = tune_decision_tree(X_train, y_train)
    all_results['Tuned Decision Tree'] = train_and_evaluate(
        tuned_dt_estimator, X_train, y_train, X_test, y_test, "Tuned Decision Tree"
    )

    # --- Model 6: Random Forest (Baseline) ---
    rf_baseline = RandomForestClassifier(random_state=42)
    all_results['Random Forest'] = train_and_evaluate(
        rf_baseline, X_train, y_train, X_test, y_test, "Random Forest (Baseline)"
    )

    # --- Model 7: Random Forest (Tuned) ---
    best_rf_estimator = tune_random_forest(X_train, y_train)
    all_results['Tuned Random Forest'] = train_and_evaluate(
        best_rf_estimator, X_train, y_train, X_test, y_test, "Tuned Random Forest"
    )

    # --- Model 8: Gradient Boosting (Baseline) ---
    gb_baseline = GradientBoostingClassifier(random_state=42)
    all_results['Gradient Boosting'] = train_and_evaluate(
        gb_baseline, X_train, y_train, X_test, y_test, "Gradient Boosting (Baseline)"
    )

    # --- Model 9: Gradient Boosting (Tuned) ---
    best_gb_estimator = tune_gradient_boosting(X_train, y_train)
    all_results['Tuned Gradient Boosting'] = train_and_evaluate(
        best_gb_estimator, X_train, y_train, X_test, y_test, "Tuned Gradient Boosting"
    )

    # 4. Print Overall Comparison Table
    print_comparison_table(all_results)

    # 5. Automatically determine the best model
    best_model_name = None
    best_composite_score = -1.0

    print("Composite Scoring (0.5 * F1 + 0.5 * Recall) for Predictive Maintenance:")
    for model_name, metrics in all_results.items():
        comp_score = 0.5 * metrics['F1 Score'] + 0.5 * metrics['Recall']
        print(
            f"- {model_name:<30}: Composite Score = {comp_score:.4f} "
            f"(F1 = {metrics['F1 Score']:.4f}, Recall = {metrics['Recall']:.4f})"
        )
        if comp_score > best_composite_score:
            best_composite_score = comp_score
            best_model_name = model_name

    if best_model_name is None:
        raise RuntimeError("No best model was selected.")

    print(
        f"\n--> BEST MODEL DETERMINED: {best_model_name} "
        f"with Composite Score of {best_composite_score:.4f}"
    )

    # 6. Save the Best Model
    requires_scaling = "Logistic Regression" in best_model_name

    saved_model_path = "saved_models"
    os.makedirs(saved_model_path, exist_ok=True)

    best_model_dict = {
        "model": all_results[best_model_name]["model"],
        "scaler": scaler if requires_scaling else None,
        "features": X.columns.tolist(),
        "model_name": best_model_name,
        "metrics": {
            "Accuracy": all_results[best_model_name]["Accuracy"],
            "Precision": all_results[best_model_name]["Precision"],
            "Recall": all_results[best_model_name]["Recall"],
            "F1 Score": all_results[best_model_name]["F1 Score"],
            "Training Accuracy": all_results[best_model_name]["Training Accuracy"],
            "Testing Accuracy": all_results[best_model_name]["Testing Accuracy"],
        },
    }

    model_filepath = os.path.join(saved_model_path, "best_model.joblib")
    joblib.dump(best_model_dict, model_filepath)

    print(f"Successfully saved the best model details to: {model_filepath}")


if __name__ == "__main__":
    main()
