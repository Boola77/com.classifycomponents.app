# coding:utf-8

import os
import numpy as np
import streamlit as st
import torch
import joblib

from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification
)


# =====================================================
# LOAD MODEL (cached ⚡)
# =====================================================
@st.cache_resource
def load_model_and_tokenizer(path):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = AutoModelForSequenceClassification.from_pretrained(path)
    tokenizer = AutoTokenizer.from_pretrained(path)

    model.to(device)
    model.eval()

    return model, tokenizer, device


@st.cache_resource
def load_label_encoder(path):
    return joblib.load(path)


# ---- paths ----
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

path_trainer_predict = BASE_DIR / "data" / "model"
label_path = path_trainer_predict / "label_encoder.pkl"


# ---- load once ----
model, tokenizer, device = load_model_and_tokenizer(path_trainer_predict)
label_encoder = load_label_encoder(label_path)


# =====================================================
# 🚀 BATCH PREDICT (FAST)
# =====================================================
def predict_batch(df, columns, batch_size=64):
    """
    Predict Description CAT for a dataframe (vectorized ⚡)
    """

    results = []

    # ---- loop by batch ----
    for i in range(0, len(df), batch_size):
        chunk = df.iloc[i:i+batch_size]

        texts = (
            chunk[columns]
            .fillna("")
            .astype(str)
            .agg(" | ".join, axis=1)
            .tolist()
        )

        inputs = tokenizer(
            texts,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=256
        ).to(device)

        with torch.no_grad():
            outputs = model(**inputs)

        preds = torch.argmax(outputs.logits, dim=1).cpu().numpy()

        decoded = label_encoder.inverse_transform(preds)
        results.extend(decoded)

    return results


# =====================================================
# SAFE FILL FUNCTION (used in your app)
# =====================================================
def fill_description_cat(df, columns):
    df = df[columns].copy()

    if 'CAT Description' not in df.columns:
        df["CAT Description"] = np.nan

    mask = df['CAT Description'].isna()

    df["CAT Description"] = df["CAT Description"].astype("string")

    if mask.any():
        df.loc[mask, 'CAT Description'] = predict_batch(df.loc[mask], columns)

    return df