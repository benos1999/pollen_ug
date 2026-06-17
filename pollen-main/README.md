
# PyPollen — automating pollen-species identification from light-microscopy images


📄 **Full write-up:** [Final_Report.pdf](Final_Report.pdf) 


## Overview

The decline of insect pollinators threatens food security, and identifying which
plants pollinators forage from requires identifying pollen - traditionally a slow,
manual, expert task. **PyPollen** prototypes an automated alternative. Rather than
classifying species directly, it takes a novel approach: measure each grain's
**morphological features** (size, shape, texture) and work toward classifying those,
which generalises better across the 4,000+ species with described morphology.

The project covers the full data pipeline:

- **Data collection** — web scraping of pollen image and trait databases.
- **Image segmentation** — isolating individual grains from LM images.
- **Feature extraction** — geometric properties + grey-level co-occurrence matrix (GLCM) texture.
- **Machine learning** — error prediction (SVM), clustering (K-means), dimensionality reduction (PCA), and CNN experiments (U-Net, VGG16).

The SVM error-prediction model reached **81% accuracy** at
flagging mis-detected grains, trained on a dataset of **4,099 images**. Feature-classification
models were less reliable - see *Limitations* below.



---

## How it works

| Stage | Where | What it does |
| --- | --- | --- |
| Data collection | [Web Scraping/](Web%20Scraping/) | Scrapes PalDat and the Global Pollen Project for images + morphological traits. |
| Segmentation & features | [Scripts/PyPollen.py](Scripts/PyPollen.py) | Watershed + Canny segmentation, then geometric + GLCM texture features per grain. |
| Analysis & ML | [Analysis Notebooks/](Analysis%20Notebooks/) | PCA, K-means, SVM error prediction; U-Net and VGG16 deep-learning experiments. |

The core entry point is `get_props(path)` in `PyPollen.py`: it segments an image,
measures each candidate grain, and uses a trained SVM to discard erroneous detections.

---

## Repository structure

```
.
├── Scripts/
│   ├── PyPollen.py            # Core module: segmentation + feature extraction
│   ├── config.py              # File-path configuration (env-overridable)
│   ├── Magnification.ipynb    # Magnification-factor calibration
│   └── ...
├── Analysis Notebooks/
│   ├── Principal Component Analysis.ipynb
│   ├── K-Means and SVM.ipynb
│   ├── Pollen segmentation measures.ipynb
│   ├── Assessment of count and sizes.ipynb
│   └── Machine Learning/
│       ├── SVM_error_prediction_model.sav   # Trained error-prediction model
│       ├── U-Net_PollenSegmentation         # CNN segmentation experiment   (TODO: add .py/.ipynb extension)
│       └── VGG16PollenClassification        # CNN classification experiment (TODO: add .py/.ipynb extension)
├── Web Scraping/
│   ├── paldat_scraper.py
│   ├── GPP_scraper.py
│   └── scrape_utils/
├── Final_Report.pdf           # Full dissertation
├── requirements.txt
├── Pipfile / Pipfile.lock
└── .env.example
```

---

## Installation

Requires Python 3.14 (the pins are verified against it).

```bash
# Option A — pip
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Option B — pipenv
pipenv install
```

## Usage

```python
import sys
from pathlib import Path
sys.path.append("Scripts")      # PyPollen imports its sibling config module

from PyPollen import get_props

# Returns a DataFrame of per-grain geometric + texture measurements
features = get_props(Path("images/your_image.jpg"))
print(features)
```

Paths to the model and data files resolve automatically relative to the repo. To
point them elsewhere, set the environment variables in [.env.example](.env.example)
(`PYPOLLEN_MODEL_PATH`, `PYPOLLEN_TRUE_VALUES`, `PYPOLLEN_INPUT_FOLDER`).

> **Note on the model file:** `SVM_error_prediction_model.sav` was trained with
> scikit-learn 0.24.2. It loads under modern scikit-learn but emits an
> `InconsistentVersionWarning`; predictions are usable but for fully reproducible
> results the model should be retrained on the current version.

---

## Data

- **Included:** `paldat_out.json` (scraped PalDat traits) and the trained SVM model.
- **Not included**:
  `FINAL_measure_adj_atd.csv` (feature dataset), `PaldatNormalisedFinal.csv`
  (normalised morphological descriptions), and `true_values.csv` (manual grain
  counts/sizes for `optimise_segmentation_variables`, columns: `Image,count,size,mag`).
  These can be regenerated from the notebooks and scrapers.


---

## Tech stack

Python · scikit-image · scikit-learn · NumPy · pandas · SciPy · Matplotlib ·
TensorFlow/Keras (CNN experiments) · BeautifulSoup + Requests (scraping) · Jupyter

---

## Limitations & future work


- Feature-classification models were unreliable; more high-quality labelled data
  and more sophisticated architectures are needed.
- Segmentation parameters were hand-tuned; results vary with magnification and image quality.
- The error-prediction model should be retrained on current library versions.

---

## License & acknowledgements

Released under the MIT License — see [LICENSE](LICENSE).

Undergraduate dissertation project, BSc (Hons) Biological Sciences (Biotechnology).
Supervised by Prof. Maurice Gallagher and Dr. Chris Wood.
Data sourced from [PalDat](https://www.paldat.org) and the
[Global Pollen Project](https://globalpollenproject.org).
