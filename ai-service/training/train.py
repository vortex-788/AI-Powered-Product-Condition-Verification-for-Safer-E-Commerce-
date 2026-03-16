import os
import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from preprocessor import preprocess_image

class DamageModelTrainer:
    """Trains a Deep Learning model for product damage classification."""
    
    def __init__(self, base_dir='dataset', img_size=(224, 224), batch_size=32):
        self.base_dir = base_dir
        self.img_size = img_size
        self.batch_size = batch_size
        self.classes = ['scratch', 'crack', 'dent', 'discoloration', 'chip', 
                        'wear', 'stain', 'deformation', 'corrosion', 'missing_part', 'normal']
        self.num_classes = len(self.classes)
        self.model = self._build_model()
        
    def _build_model(self):
        """Constructs a transfer-learning model on top of MobileNetV2."""
        base_model = MobileNetV2(
            weights='imagenet',
            include_top=False,
            input_shape=(*self.img_size, 3)
        )
        
        # Freeze base model layers initially
        base_model.trainable = False
        
        x = base_model.output
        x = GlobalAveragePooling2D()(x)
        x = Dense(256, activation='relu')(x)
        x = Dropout(0.5)(x)
        predictions = Dense(self.num_classes, activation='softmax')(x)
        
        model = Model(inputs=base_model.input, outputs=predictions)
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='categorical_crossentropy',
            metrics=['accuracy', tf.keras.metrics.Precision(), tf.keras.metrics.Recall()]
        )
        return model
        
    def _data_generator(self, split):
        """Yields batches of augmented preprocessed images."""
        split_dir = os.path.join(self.base_dir, split)
        datagen = tf.keras.preprocessing.image.ImageDataGenerator(
            rotation_range=20,
            width_shift_range=0.2,
            height_shift_range=0.2,
            horizontal_flip=True,
            zoom_range=0.2,
            brightness_range=[0.7, 1.3] # Simulate poor lighting conditions
        )
        
        # We define a custom preprocessing function to inject our OpenCV CLAHE logic
        def custom_preprocessing(img):
            # ImageDataGenerator gives float32 [0, 255]. Convert to uint8 for OpenCV.
            img_uint8 = img.astype('uint8')
            processed = preprocess_image(img_uint8, self.img_size)
            # MobileNetV2 expects inputs between [-1, 1]
            return tf.keras.applications.mobilenet_v2.preprocess_input(processed.astype('float32'))
            
        datagen.preprocessing_function = custom_preprocessing

        return datagen.flow_from_directory(
            split_dir,
            target_size=self.img_size,
            batch_size=self.batch_size,
            class_mode='categorical',
            classes=self.classes,
            shuffle=(split == 'train')
        )
        
    def train(self, epochs=20):
        """Executes the training loop."""
        print("Initializing data generators...")
        train_gen = self._data_generator('train')
        val_gen = self._data_generator('val')
        
        # Callbacks
        callbacks = [
            EarlyStopping(patience=5, restore_best_weights=True, monitor='val_loss'),
            ModelCheckpoint('best_damage_model.h5', save_best_only=True, monitor='val_accuracy')
        ]
        
        print("Starting training phase 1 (frozen base)...")
        history = self.model.fit(
            train_gen,
            validation_data=val_gen,
            epochs=epochs,
            callbacks=callbacks
        )
        
        # Fine-tuning phase
        print("Starting training phase 2 (fine-tuning)...")
        self.model.trainable = True
        # Freeze all but the last 30 layers
        for layer in self.model.layers[:-30]:
            layer.trainable = False
            
        self.model.compile(
            optimizer=Adam(learning_rate=1e-5), # Lower learning rate for fine tuning
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        history_fine = self.model.fit(
            train_gen,
            validation_data=val_gen,
            epochs=epochs // 2,
            callbacks=callbacks
        )
        
        return history, history_fine

if __name__ == '__main__':
    # Usage example
    trainer = DamageModelTrainer()
    # history = trainer.train(epochs=30)
    print("Model architecture built and ready for training once dataset is populated.")
