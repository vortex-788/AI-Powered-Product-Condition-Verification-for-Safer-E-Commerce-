import os
import shutil
import random
from pathlib import Path

class DatasetManager:
    """Manages the creation and organization of the training dataset."""
    
    def __init__(self, base_dir: str = 'dataset'):
        self.base_dir = Path(base_dir)
        self.categories = [
            'scratch', 'crack', 'dent', 'discoloration', 'chip',
            'wear', 'stain', 'deformation', 'corrosion', 'missing_part', 'normal'
        ]
        self.splits = ['train', 'val', 'test']
        
    def create_structure(self):
        """Creates the directory structure for splits and categories."""
        for split in self.splits:
            for category in self.categories:
                dir_path = self.base_dir / split / category
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"Created {dir_path}")

    def split_data(self, source_dir: str, train_ratio=0.7, val_ratio=0.15):
        """
        Splits raw images from a source directory into train/val/test sets.
        Expects source_dir to have subdirectories named after categories.
        """
        source = Path(source_dir)
        if not source.exists():
            print(f"Source directory {source_dir} does not exist.")
            return

        for category in self.categories:
            cat_dir = source / category
            if not cat_dir.exists():
                continue
                
            files = list(cat_dir.glob('*.*'))
            random.shuffle(files)
            
            n_samples = len(files)
            n_train = int(n_samples * train_ratio)
            n_val = int(n_samples * val_ratio)
            
            train_files = files[:n_train]
            val_files = files[n_train:n_train + n_val]
            test_files = files[n_train + n_val:]
            
            self._copy_files(train_files, 'train', category)
            self._copy_files(val_files, 'val', category)
            self._copy_files(test_files, 'test', category)
            
            print(f"Category {category}: {len(train_files)} train, {len(val_files)} val, {len(test_files)} test")

    def _copy_files(self, files, split, category):
        """Helper to copy files to their respective split directories."""
        dest_dir = self.base_dir / split / category
        for f in files:
            shutil.copy2(f, dest_dir / f.name)

if __name__ == '__main__':
    manager = DatasetManager(base_dir='dataset')
    print("Initializing dataset structure...")
    manager.create_structure()
    print("\nTo populate data, place your raw categorized images in an 'images/raw' directory.")
    print("Then run: manager.split_data('images/raw')")
