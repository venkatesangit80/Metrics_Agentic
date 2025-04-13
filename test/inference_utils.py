import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import load_model


def generate_windows(df, window_size=30):
    """
    Generates 30-minute sequences and stores the original values for analysis.
    """
    scaler = load_scaler()
    df_scaled = scaler.transform(df)

    sequences = []
    timestamps = []
    original_windows = []

    for i in range(len(df_scaled) - window_size):
        seq = df_scaled[i:i + window_size]
        raw = df.iloc[i + window_size]  # use last point in the window
        sequences.append(seq)
        original_windows.append(raw.values)
        timestamps.append(df.index[i + window_size])

    return np.array(sequences), timestamps, original_windows


def detect_anomalies(model, sequences, timestamps, raw_data, metric_names, dynamic=True, threshold_value=0.01):
    """
    Detect anomalies using LSTM AutoEncoder. Uses MAD-based threshold if dynamic=True.
    """
    preds = model.predict(sequences)
    errors = np.mean(np.square(sequences - preds), axis=(1, 2))

    # === Dynamic Thresholding (Median Absolute Deviation) ===
    if dynamic:
        median = np.median(errors)
        mad = np.median(np.abs(errors - median))
        threshold = median + 3 * mad
        print(f"[Dynamic] Threshold derived using MAD: {threshold:.5f}")
    else:
        threshold = threshold_value
        print(f"[Static] Threshold used: {threshold:.5f}")

    anomaly_flags = (errors > threshold).astype(int)

    # Explanation (top deviated metric in last timestep)
    explanations = []
    for i in range(len(sequences)):
        actual = sequences[i][-1]
        predicted = preds[i][-1]
        diffs = np.abs(actual - predicted)
        top_metric = metric_names[np.argmax(diffs)]
        explanations.append(f"High deviation in '{top_metric}'")

    # Raw metric values at window end
    raw_df = pd.DataFrame(raw_data, columns=metric_names)

    result_df = pd.DataFrame({
        'timestamp': timestamps,
        'reconstruction_error': errors,
        'anomaly': anomaly_flags,
        'explanation': explanations
    })

    return pd.concat([result_df, raw_df], axis=1)


def load_scaler(path="../models/lstm_scaler.pkl"):
    import pickle
    with open(path, "rb") as f:
        return pickle.load(f)