# ML Development Guide

## 🤖 ML Directory Structure

```text
services/
├── ml/                           # 🤖 ML & Academic Library Code
│   ├── pyrightconfig.json        # Relaxed type checking for ML libs
│   ├── crank_email_classifier.py
│   ├── crank_image_classifier.py
│   └── [future ML modules]
├── platform/                     # 🏛️ Platform services (strict checking)
├── security/                     # 🔒 Security services (strict checking)
├── api/                          # 🌐 API services (strict checking)
└── [other service categories]

```

## 🎯 **When to Put Code in `services/ml/`**

### ✅ **BELONGS in `services/ml/`**

- **ML Model Training/Inference**: sklearn, PyTorch, TensorFlow code

- **Academic Libraries**: NLTK, spaCy, academic research packages

- **Data Science Pipelines**: Heavy pandas/numpy with dynamic typing

- **Computer Vision**: OpenCV, PIL processing with runtime-determined types

- **NLP Processing**: Text analysis, language models, sentiment analysis

- **Recommendation Engines**: Collaborative filtering, content-based systems

### ❌ **Does NOT belong in `services/ml/`**

- **Platform Services**: Authentication, load balancing, service discovery

- **Security Code**: Certificate management, encryption, access control

- **API Gateways**: Request routing, rate limiting, validation

- **Database Services**: ORM models, migrations, data access layers

- **Configuration Management**: Settings, environment handling

## 🔧 **Type Checking Behavior**

### **ML Directory (`services/ml/`)**

- **Type Checking Mode**: `basic` (relaxed)

- **ML Library Issues**: Suppressed (sklearn attribute access, NLTK types)

- **Real Errors**: Still caught (syntax, logic, security patterns)

### **Other Directories**

- **Type Checking Mode**: `strict`

- **Full Type Safety**: All Pylance diagnostics enabled

- **Security Focus**: Maximum error detection for critical code

## 🚀 **Development Workflow**

### **Adding New ML Module**

1. **Create file**: `services/ml/your_ml_module.py`

2. **Automatic configuration**: Inherits relaxed type checking

3. **Import ML libraries freely**: sklearn, nltk, torch, etc.

4. **Focus on functionality**: Type noise automatically suppressed

### **Adding New Platform Module**

1. **Create file**: `services/platform/your_platform_module.py`

2. **Strict type checking**: Full Pylance validation

3. **Professional standards**: Complete type annotations required

4. **Security focus**: Maximum error detection enabled

## 📋 **ML Development Best Practices**

### **File Organization**

```python
# services/ml/my_classifier.py

import sklearn  # ✅ Academic library - type issues suppressed
import nltk     # ✅ Academic library - type issues suppressed
import numpy    # ✅ Scientific computing - dynamic typing ok

# Professional practices still apply

def train_model(data: pd.DataFrame) -> sklearn.base.BaseEstimator:
    """Train classifier model."""  # ✅ Clear documentation
    # Implementation with relaxed type checking

```

### **What's Still Required**

- **Function documentation**: Clear docstrings

- **Return type hints**: When reasonably possible

- **Error handling**: Proper exception management

- **Security practices**: Safe file handling, input validation

### **What's Relaxed**

- **ML Library Attributes**: `model.predict_proba()` after `model = None`

- **Runtime Type Determination**: Dynamic numpy array shapes

- **Academic Library Gaps**: Missing type stubs for research code

- **Complex Generic Types**: Nested ML pipeline types

## 🔄 **Review & Maintenance**

### **Quarterly Review** (Every 3 months)

- **Check ML ecosystem improvements**: New type stubs available?

- **Evaluate suppressions**: Can any be removed?

- **Update documentation**: Reflect current best practices

### **Adding Future ML Categories**

```text
services/ml/
├── nlp/              # Natural Language Processing
├── vision/           # Computer Vision
├── recommenders/     # Recommendation Systems
├── forecasting/      # Time Series & Prediction
└── research/         # Experimental/Research Code

```

## 🎉 **Benefits**

- **🎯 Focused Development**: ML developers don't fight type checker noise

- **🔒 Security Preserved**: Platform code maintains strict type safety

- **📈 Scalable**: Easy to categorize new R&D modules

- **📚 Clear Boundaries**: Obvious separation between ML and platform code

- **🚀 R&D Friendly**: Academic libraries work out-of-the-box

---
*Updated: November 8, 2025*
*Part of Email Classifier Cleanup & ML Architecture Project*
