import pandas as pd
import numpy as np
import pickle
from tensorflow.keras.models import load_model
from sklearn.metrics import mean_squared_error
from datetime import timedelta

# === Step 1: Load Test Data ===
df = pd.read_csv("../data/App3_Jan2023.csv")
df['timestamp'] = pd.to_datetime(df['timestamp'])

# === Step 2: Filter next 15 days ===
cutoff = df['timestamp'].min() + pd.Timedelta(days=15)
df_test = df[df['timestamp'] >= cutoff]

selected_metrics = ['Throughput', 'Response Time (ms)', 'Error Count', 'CLR_CPU_Usage (%)']
df_test = df_test[df_test['metric_name'].isin(selected_metrics)]

# === Step 3: Pivot ===
pivot_test = df_test.pivot_table(index='timestamp', columns='metric_name', values='metric_value', aggfunc='mean').dropna()

# === Step 4: Load Scaler ===
with open("../models/lstm_scaler.pkl", "rb") as f:
    scaler = pickle.load(f)

X_scaled = scaler.transform(pivot_test)

# === Step 5: Create Sliding Windows ===
def create_sequences(data, window_size):
    X = []
    for i in range(len(data) - window_size):
        seq = data[i:i + window_size]
        X.append(seq)
    return np.array(X)

window_size = 30
X_seq = create_sequences(X_scaled, window_size)

# === Step 6: Load LSTM AutoEncoder ===
model = load_model("../models/lstm_autoencoder_model.h5", compile=False)

# === Step 7: Predict & Compute Reconstruction Error ===
X_pred = model.predict(X_seq)
errors = np.mean(np.square(X_seq - X_pred), axis=(1, 2))

# === Step 8: Assign Errors Back to Timestamps ===
timestamps = pivot_test.index[window_size:]
df_result = pd.DataFrame({
    "timestamp": timestamps,
    "reconstruction_error": errors,
    "anomaly": (errors > 0.01).astype(int)  # static threshold; can be tuned
})

# === Step 9: Save Results ===
df_result.to_csv("../outputs/App3_inference_results.csv", index=False)

print("✅ Inference completed. Results saved to outputs folder.")