import kagglehub
from pathlib import Path
import shutil
from src.config.settings import DATA_DIR

def fetch_kaggle_dataset():
    print("Downloading dataset from Kaggle...")
    path = kagglehub.dataset_download("lakshmi25npathi/online-retail-dataset")
    path = Path(path)

    # Check if cache is empty (files were moved previously)
    if not any(path.iterdir()):
        print("Cached dataset is empty. Re-downloading...")
        shutil.rmtree(path)
        path = kagglehub.dataset_download("lakshmi25npathi/online-retail-dataset")
        path = Path(path)

    target_folder = DATA_DIR

    target_folder.mkdir(parents=True, exist_ok=True)

    print(f"Dataset found at: {path}")
    for file_path in path.glob("*"):
        if file_path.is_file():
            target_file = target_folder / file_path.name
            if not target_file.exists():
                print(f"Copying {file_path.name} to {target_folder}...")
                shutil.copy2(str(file_path), str(target_file))
            else:
                print(f"{file_path.name} already exists in target.")

if __name__ == "__main__":
    fetch_kaggle_dataset()