"""File paths used by PyPollen.

Defaults can be overridden with environment variables (or a .env file loaded by
the caller) so the module runs without editing source. See .env.example.
"""

import os
from pathlib import Path

# Directory containing this file (the Scripts folder).
BASE_DIR = Path(__file__).resolve().parent

# Repository root (one level up from Scripts).
REPO_DIR = BASE_DIR.parent

# Trained SVM model used to flag erroneous grain detections.
MODEL_PATH = Path(
    os.environ.get(
        "PYPOLLEN_MODEL_PATH",
        REPO_DIR / "Analysis Notebooks" / "Machine Learning" / "SVM_error_prediction_model.sav",
    )
)

# CSV of manually recorded grain counts/sizes, required by
# optimise_segmentation_variables (see README for its columns).
TRUE_VALUES_PATH = Path(
    os.environ.get("PYPOLLEN_TRUE_VALUES", REPO_DIR / "true_values.csv")
)

# Folder of input microscopy images for the __main__ demo run.
INPUT_FOLDER = Path(
    os.environ.get("PYPOLLEN_INPUT_FOLDER", REPO_DIR / "images")
)
