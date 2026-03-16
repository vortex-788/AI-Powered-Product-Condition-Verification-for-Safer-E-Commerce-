# AI Model Training Pipeline Guide

This directory contains the necessary scripts to train a custom deep learning model for the VeriShield AI Service using transfer learning on top of MobileNetV2.

## New Dependencies Required
To run the training pipeline, you must install the following additional packages. 
*(Note: These are separated from the main `requirements.txt` to keep the production inference container lightweight).*

```bash
pip install tensorflow==2.15.0 scikit-learn==1.3.2 matplotlib==3.8.2 seaborn==0.13.0
```

## Pipeline Execution Steps

### 1. Prepare the Dataset
Collect images of products and place them into folders categorized by damage type inside `ai-service/training/dataset/raw/`.

Example structure:
```
dataset/
└── raw/
    ├── scratch/
    ├── crack/
    ├── dent/
    └── normal/
```

Then, run the dataset manager to automatically shuffle and split them into Train (70%), Validation (15%), and Test (15%) sets:
```bash
python dataset_manager.py
```

### 2. Train the Model
The `train.py` script automatically utilizes the `preprocessor.py` to apply Contrast Limited Adaptive Histogram Equalization (CLAHE) to all training images on-the-fly, simulating various lighting conditions via data augmentation.

To start training:
```bash
python train.py
```
This will perform a two-phase training loop (frozen base first, then fine-tuning) and output a `best_damage_model.h5` file.

### 3. Evaluate the Model
To generate Precision, Recall, F1-Scores, and a visualized Confusion Matrix:
```bash
python evaluate.py
```
This will output `evaluation_metrics.json` and a `confusion_matrix.png` file into a new `metrics/` directory.

### 4. Deployment
Once satisfied with the evaluation metrics, move `best_damage_model.h5` into `ai-service/models/` and toggle `self.model_trained = True` inside `damage_detector.py`.
