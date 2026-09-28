"""
generate_corpus.py

Builds a small synthetic corpus of Kaggle notebook logs in the same format
as real Kaggle console output, for the rarity-scoring step of the pipeline.

Composition (15 logs total):
  - 10 healthy runs (varying shapes, fold counts, accuracy — normal variation)
  - 3 CUDA-OOM failures (a *recurring* known failure type)
  - 2 novel one-off failures (a pandas KeyError, a network timeout) —
    these should score as most "rare" since the corpus has never seen them

Run: python3 generate_corpus.py
Writes logs to ./corpus/
"""

import random
from pathlib import Path

OUT_DIR = Path(__file__).parent / "corpus"
OUT_DIR.mkdir(exist_ok=True)

random.seed(7)


def healthy_log(run_id: int) -> str:
    n_folds = random.choice([5, 7, 10])
    n_train = random.choice([30000, 40000, 60000, 80000])
    n_test = n_train // 4
    n_features = random.choice([12, 15, 20, 42])
    acc = round(random.uniform(0.985, 0.9999), 5)
    t = 9.0
    lines = []

    def emit(msg, dash=True):
        nonlocal t
        t += random.uniform(0.5, 15)
        prefix = f"{t:.1f}s {len(lines)+1} 0.00s - " if dash else f"{t:.1f}s {len(lines)+1} "
        lines.append(prefix + msg)

    emit("Debugger warning: It seems that frozen modules are being used, which may")
    emit("make the debugger miss breakpoints. Please pass -Xfrozen_modules=off")
    emit("to python to disable frozen modules.")
    emit("Note: Debugging will proceed. Set PYDEVD_DISABLE_FILE_VALIDATION=1 to disable this validation.")
    lines.append("")
    emit(f"✅ Cell 1 executed successfully with an 80/20 train/test split!")
    emit(f"Train Features Shape: ({n_train}, {n_features}), Test Features Shape: ({n_test}, {n_features})")
    emit(f"🏋️‍♂️ Training models across {n_folds} folds...")
    for fold in range(1, n_folds + 1):
        emit(f"-> Processing Fold {fold}/{n_folds}", dash=False)
    emit("✅ Training complete!")
    lines.append("")
    emit("⚙️ Tuning ensemble weights and class thresholds...")
    emit("=" * 50, dash=False)
    emit(f"🏆 LOCAL IN-HOUSE BALANCED ACCURACY: {acc}")
    emit("=" * 50, dash=False)
    lines.append("")
    emit(f"🔮 UNSEEN HOLD-OUT TEST BALANCED ACCURACY: {round(acc + random.uniform(-0.001, 0.001), 5)}")
    emit("=" * 50, dash=False)
    emit("🧹 Cleaned directory!")
    emit(f"📁 Created 'submission.csv' with shape: ({n_test}, 2)")
    lines.append("")
    emit("Current output directory contents:")
    emit("['__notebook__.ipynb', 'submission.csv']", dash=False)
    return "\n".join(lines) + "\n"


def cuda_oom_log(run_id: int) -> str:
    n_folds = 5
    gib = round(random.uniform(1.5, 3.0), 2)
    t = 3.0
    lines = []

    def emit(msg, dash=True):
        nonlocal t
        t += random.uniform(0.5, 20)
        prefix = f"{t:.1f}s {len(lines)+1} 0.00s - " if dash else f"{t:.1f}s {len(lines)+1} "
        lines.append(prefix + msg)

    emit("✅ Cell 1 executed successfully with an 80/20 train/test split!")
    emit(f"Train Features Shape: (120000, 42), Test Features Shape: (30000, 42)")
    emit(f"🏋️‍♂️ Training models across {n_folds} folds...")
    for fold in range(1, 3):
        emit(f"-> Processing Fold {fold}/{n_folds}", dash=False)
    for fold in range(3, n_folds + 1):
        emit(f"-> Processing Fold {fold}/{n_folds}", dash=False)
        emit("-" * 71, dash=False)
        emit("RuntimeError                             Traceback (most recent call last)", dash=False)
        emit("Cell In[14], line 87", dash=False)
        emit(
            f"RuntimeError: CUDA out of memory. Tried to allocate {gib} GiB (GPU 0; 15.89 GiB total capacity; "
            f"14.02 GiB already allocated; 612.00 MiB free; 14.31 GiB reserved in total by PyTorch)",
            dash=False,
        )
    emit(f"❌ Training failed: {n_folds - 2}/{n_folds} folds raised RuntimeError")
    emit("⚠️ Falling back to last successful checkpoint (Fold 2)")
    emit("🧹 Cleaned directory!")
    emit(f"📁 Created 'submission.csv' with shape: (30000, 2)")
    return "\n".join(lines) + "\n"


def keyerror_log(run_id: int) -> str:
    """A novel, never-repeated failure type: a pandas merge KeyError."""
    lines = [
        "8.1s 1 0.00s - ✅ Cell 1 executed successfully with an 80/20 train/test split!",
        "12.4s 2 0.00s - Train Features Shape: (50000, 18), Test Features Shape: (12500, 18)",
        "13.0s 3 0.00s - 🔧 Merging external feature table on 'user_id'...",
        "13.4s 4 ---------------------------------------------------------------------",
        "13.4s 5 KeyError                                  Traceback (most recent call last)",
        "13.4s 6 Cell In[9], line 22",
        "13.4s 7 ----> 22 merged = train_df.merge(ext_features, on='user_id', how='left')",
        "13.4s 8 KeyError: 'user_id'",
        "13.5s 9 ❌ Feature merge failed: column 'user_id' not found in external_features.csv",
        "13.6s 10 🧹 Cleaned directory!",
    ]
    return "\n".join(lines) + "\n"


def timeout_log(run_id: int) -> str:
    """A novel, never-repeated failure type: a network timeout downloading external data."""
    lines = [
        "5.2s 1 0.00s - 🌐 Downloading external embeddings from remote cache...",
        "125.3s 2 0.00s - ---------------------------------------------------------------------",
        "125.3s 3 0.00s - ConnectionError                          Traceback (most recent call last)",
        "125.3s 4 0.00s - Cell In[3], line 6",
        "125.3s 5 0.00s - ----> 6 resp = requests.get(url, timeout=120)",
        "125.3s 6 0.00s - requests.exceptions.ReadTimeout: HTTPSConnectionPool(host='cache.example.com', port=443): Read timed out. (read timeout=120)",
        "125.4s 7 0.00s - ❌ Aborting: could not fetch external embeddings after 120s",
        "125.5s 8 0.00s - 🧹 Cleaned directory!",
    ]
    return "\n".join(lines) + "\n"


def valueerror_log(run_id: int) -> str:
    """A novel, never-repeated failure type: sklearn feature-count mismatch
    at inference time. Deliberately shares the same bare separator-line
    structure as keyerror_log/timeout_log, to test whether that line's
    rarity (and hallucination pattern) changes once precedent exists."""
    lines = [
        "6.4s 1 0.00s - ✅ Cell 1 executed successfully with an 80/20 train/test split!",
        "9.8s 2 0.00s - Train Features Shape: (45000, 21), Test Features Shape: (11250, 21)",
        "10.2s 3 0.00s - 📏 Scaling features with fitted StandardScaler...",
        "10.5s 4 ---------------------------------------------------------------------",
        "10.5s 5 ValueError                                Traceback (most recent call last)",
        "10.5s 6 Cell In[11], line 14",
        "10.5s 7 ----> 14 scaled = scaler.transform(test_df[feature_cols])",
        "10.5s 8 ValueError: X has 22 features, but StandardScaler is expecting 21 features as input.",
        "10.6s 9 ❌ Inference failed: feature count mismatch between test_df and fitted scaler",
        "10.7s 10 🧹 Cleaned directory!",
    ]
    return "\n".join(lines) + "\n"


def main():
    for i in range(1, 11):
        (OUT_DIR / f"healthy_{i:02d}.log").write_text(healthy_log(i))
    for i in range(1, 4):
        (OUT_DIR / f"cuda_oom_{i:02d}.log").write_text(cuda_oom_log(i))
    (OUT_DIR / "keyerror_novel_01.log").write_text(keyerror_log(1))
    (OUT_DIR / "timeout_novel_01.log").write_text(timeout_log(1))
    (OUT_DIR / "valueerror_novel_01.log").write_text(valueerror_log(1))
    print(f"Wrote {len(list(OUT_DIR.glob('*.log')))} logs to {OUT_DIR}")


if __name__ == "__main__":
    main()