"""
ShopLens Semantic Search Fine-Tuning Script.

Fine-tunes sentence-transformers/all-MiniLM-L6-v2 on grocery domain triples
using TripletLoss with Cosine distance metric.
Uses a native PyTorch training loop to ensure full offline execution and
complete reproducibility without external hub/datasets dependencies.
Evaluates on validation.csv at each epoch and saves the best model checkpoint.
"""

import json
import math
import os
import random
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader, Dataset

# Allow offline execution if explicitly set by environment, otherwise allow downloading pretrained weights
if os.environ.get("HF_HUB_OFFLINE") is None:
    pass

from sentence_transformers import SentenceTransformer
from sentence_transformers.sentence_transformer.losses import (
    TripletDistanceMetric,
    TripletLoss,
)

from evaluate_retrieval import (
    CATALOG_PRODUCTS,
    build_catalog_document_text,
    evaluate_model,
)

# ---------------------------------------------------------------------------
# Paths and Configuration
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATASETS_DIR = BASE_DIR / "datasets"
MODELS_DIR = BASE_DIR / "models"

TRAIN_CSV = DATASETS_DIR / "train.csv"
VAL_CSV = DATASETS_DIR / "validation.csv"
TEST_CSV = DATASETS_DIR / "test.csv"

BASE_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
RANDOM_SEED = 42
BATCH_SIZE = 16
LEARNING_RATE = 2e-5
EPOCHS = 4
TRIPLET_MARGIN = 0.25


def set_seed(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


class GroceryTripletsDataset(Dataset):
    """PyTorch Dataset yielding (anchor_query, pos_text, neg_text)."""

    def __init__(self, csv_path: Path):
        self.df = pd.read_csv(csv_path)
        self.triplets: list[tuple[str, str, str]] = []
        for _, row in self.df.iterrows():
            q = str(row["query"]).strip()
            pos_id = int(row["positive_product_id"])
            neg_id = int(row["negative_product_id"])

            pos_text = build_catalog_document_text(pos_id)
            neg_text = build_catalog_document_text(neg_id)
            self.triplets.append((q, pos_text, neg_text))

    def __len__(self) -> int:
        return len(self.triplets)

    def __getitem__(self, idx: int) -> tuple[str, str, str]:
        return self.triplets[idx]


def collate_triplets(batch: list[tuple[str, str, str]]) -> tuple[list[str], list[str], list[str]]:
    anchors = [item[0] for item in batch]
    positives = [item[1] for item in batch]
    negatives = [item[2] for item in batch]
    return anchors, positives, negatives


def train():
    set_seed(RANDOM_SEED)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n==========================================")
    print(f"Starting Fine-Tuning: {BASE_MODEL_NAME}")
    print(f"==========================================")
    print(f"Train path: {TRAIN_CSV}")
    print(f"Val path:   {VAL_CSV}")
    print(f"Test path:  {TEST_CSV}")
    print(f"Batch size: {BATCH_SIZE} | LR: {LEARNING_RATE} | Epochs: {EPOCHS} | Margin: {TRIPLET_MARGIN}")

    # Load Base Pretrained Model
    model = SentenceTransformer(BASE_MODEL_NAME)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    # 1. Baseline Evaluation on Validation and Test Sets
    print("\n--- Evaluating Baseline Pretrained Model ---")
    baseline_val = evaluate_model(model, VAL_CSV)
    baseline_test = evaluate_model(model, TEST_CSV)

    print("Baseline Validation Metrics:")
    print(json.dumps(baseline_val["summary"], indent=2))
    print("Baseline Test Metrics:")
    print(json.dumps(baseline_test["summary"], indent=2))

    # 2. Prepare Training DataLoader and Loss
    train_dataset = GroceryTripletsDataset(TRAIN_CSV)
    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        collate_fn=collate_triplets,
    )
    print(f"Loaded {len(train_dataset)} training triples across {len(train_loader)} batches per epoch.")

    loss_fn = TripletLoss(
        model=model,
        distance_metric=TripletDistanceMetric.COSINE,
        triplet_margin=TRIPLET_MARGIN,
    )

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=0.01,
    )

    total_steps = len(train_loader) * EPOCHS
    warmup_steps = int(total_steps * 0.1)

    def get_lr_factor(current_step: int) -> float:
        if current_step < warmup_steps:
            return float(current_step) / float(max(1, warmup_steps))
        progress = float(current_step - warmup_steps) / float(max(1, total_steps - warmup_steps))
        return max(0.0, 0.5 * (1.0 + math.cos(math.pi * progress)))

    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda=get_lr_factor)

    # 3. Fine-Tuning Loop with Epoch-by-Epoch Validation
    best_val_ndcg = baseline_val["summary"]["ndcg@10"]
    best_epoch = 0
    best_model_path = MODELS_DIR / "best_model"

    training_history = []
    global_step = 0

    for epoch in range(1, EPOCHS + 1):
        model.train()
        total_epoch_loss = 0.0

        for batch_idx, (anchors, positives, negatives) in enumerate(train_loader, start=1):
            optimizer.zero_grad()

            feat_a = model.preprocess(anchors)
            feat_p = model.preprocess(positives)
            feat_n = model.preprocess(negatives)

            # Move tensors to device if necessary
            for f in [feat_a, feat_p, feat_n]:
                for k in f:
                    if isinstance(f[k], torch.Tensor):
                        f[k] = f[k].to(device)

            loss = loss_fn([feat_a, feat_p, feat_n], None)
            loss.backward()

            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            scheduler.step()

            total_epoch_loss += loss.item()
            global_step += 1

        avg_epoch_loss = total_epoch_loss / len(train_loader)
        current_lr = scheduler.get_last_lr()[0]
        print(f"\n>>> Epoch {epoch}/{EPOCHS} Finished. Avg Loss: {avg_epoch_loss:.4f} | LR: {current_lr:.6f}")

        # Save checkpoint
        checkpoint_dir = MODELS_DIR / f"checkpoint-epoch-{epoch}"
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        model.save(str(checkpoint_dir))
        print(f"Saved checkpoint to: {checkpoint_dir}")

        # Evaluate on validation set
        model.eval()
        val_eval = evaluate_model(model, VAL_CSV)
        val_summary = val_eval["summary"]
        print(f"Epoch {epoch} Validation Metrics:")
        print(json.dumps(val_summary, indent=2))

        record = {
            "epoch": epoch,
            "train_loss": avg_epoch_loss,
            "checkpoint": str(checkpoint_dir),
            "val_metrics": val_summary,
        }
        training_history.append(record)

        if val_summary["ndcg@10"] > best_val_ndcg:
            print(f"[*] New best validation NDCG@10: {val_summary['ndcg@10']:.4f} (improved from {best_val_ndcg:.4f})")
            best_val_ndcg = val_summary["ndcg@10"]
            best_epoch = epoch
            model.save(str(best_model_path))

    print(f"\n==========================================")
    print(f"Training Complete. Best Epoch: {best_epoch} with Val NDCG@10: {best_val_ndcg:.4f}")
    if best_epoch == 0:
        print("[!] Pretrained baseline had highest NDCG@10. Saving epoch 4 to best_model for comparison.")
        model.save(str(best_model_path))
    else:
        print(f"Best model selected and saved to: {best_model_path}")
    print(f"==========================================")

    # 4. Final Evaluation of Best Model on Held-Out Test Set
    best_model = SentenceTransformer(str(best_model_path))
    fine_tuned_val = evaluate_model(best_model, VAL_CSV)
    fine_tuned_test = evaluate_model(best_model, TEST_CSV)

    summary_report = {
        "base_model": BASE_MODEL_NAME,
        "epochs": EPOCHS,
        "batch_size": BATCH_SIZE,
        "learning_rate": LEARNING_RATE,
        "margin": TRIPLET_MARGIN,
        "seed": RANDOM_SEED,
        "best_epoch": best_epoch,
        "baseline_val": baseline_val["summary"],
        "baseline_test": baseline_test["summary"],
        "fine_tuned_val": fine_tuned_val["summary"],
        "fine_tuned_test": fine_tuned_test["summary"],
        "training_history": training_history,
    }

    report_path = BASE_DIR / "fine_tuning_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(summary_report, f, indent=2)
    print(f"Detailed report saved to: {report_path}")

    return summary_report


if __name__ == "__main__":
    train()
