# Streamline: AI Movie Recommender

An undergraduate AI project for NUST featuring Semantic Search and Hybrid Recommendation logic.

## 🚀 Features
* **Semantic Search:** Find movies by describing plots using NLP (Sentence-Transformers).
* **Hybrid Recommendations:** Combines Content-Based and Collaborative filtering.
* **Multi-Profile:** Support for up to 5 user profiles with personalized watchlists.

## 📸 Screenshots
![Homepage](./docs/images/homepage.png)
![Search Results](./docs/images/search_results.png)

## 🛠️ Quick Start 

1. **Install Dependencies:**
   ```bash
   pip install flask pandas numpy scikit-learn sentence-transformers torch
   ```
2. **Initialize DB:**
   ```bash
   python api/db.py
   ```
3. **Run App:**
   ```bash
   python api/index.py
   ```

## 📂 Tech Stack
* **Backend:** Flask (Python)
* **Database:** SQLite
* **AI/ML:** PyTorch, Scikit-Learn
```
