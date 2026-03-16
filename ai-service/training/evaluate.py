import os
import json
import numpy as np
import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
from train import DamageModelTrainer

def evaluate_model(model_path='best_damage_model.h5', test_dir='dataset/test', output_dir='metrics'):
    """Evaluates a trained model and generates performance metrics."""
    
    if not os.path.exists(model_path):
        print(f"Model {model_path} not found. Train the model first.")
        return
        
    os.makedirs(output_dir, exist_ok=True)
    
    # Load model
    print("Loading model...")
    model = tf.keras.models.load_model(model_path)
    
    # Setup trainer to reuse data generator logic
    trainer = DamageModelTrainer(base_dir=os.path.dirname(test_dir))
    
    print("Evaluating on test set...")
    test_gen = trainer._data_generator('test')
    
    # Get predictions
    test_gen.reset()
    predictions = model.predict(test_gen, steps=len(test_gen))
    y_pred = np.argmax(predictions, axis=1)
    y_true = test_gen.classes
    
    class_names = list(test_gen.class_indices.keys())
    
    # 1. Classification Report (Precision, Recall, F1)
    report = classification_report(y_true, y_pred, target_names=class_names, output_dict=True)
    
    metrics_file = os.path.join(output_dir, 'evaluation_metrics.json')
    with open(metrics_file, 'w') as f:
        json.dump(report, f, indent=4)
    print(f"Metrics saved to {metrics_file}")
    
    # Print a summary to console
    print("\n--- Model Performance ---")
    print(f"Overall Accuracy: {report['accuracy']:.2%}")
    for category in class_names:
        if category in report:
            print(f"{category.capitalize()}: F1-Score = {report[category]['f1-score']:.2f}")

    # 2. Confusion Matrix
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(12, 10))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=class_names, yticklabels=class_names)
    plt.title('Damage Classification Confusion Matrix')
    plt.ylabel('True Category')
    plt.xlabel('Predicted Category')
    
    cm_file = os.path.join(output_dir, 'confusion_matrix.png')
    plt.savefig(cm_file, bbox_inches='tight')
    plt.close()
    print(f"Confusion matrix visualization saved to {cm_file}")

if __name__ == '__main__':
    evaluate_model()
