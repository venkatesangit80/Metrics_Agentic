from inference_utils import generate_windows, detect_anomalies
import pandas as pd
from tensorflow.keras.models import load_model

# Load and preprocess
df = pd.read_csv("../data/App3_Jan2023.csv")
df['timestamp'] = pd.to_datetime(df['timestamp'])
cutoff = df['timestamp'].min() + pd.Timedelta(days=15)
df = df[df['timestamp'] >= cutoff]

selected_metrics = ['Throughput', 'Response Time (ms)', 'Error Count', 'CLR_CPU_Usage (%)']
df = df[df['metric_name'].isin(selected_metrics)]

pivot_df = df.pivot_table(index='timestamp', columns='metric_name', values='metric_value', aggfunc='mean').dropna()

# Run inference
sequences, timestamps, raw_data = generate_windows(pivot_df, window_size=30)
model = load_model("../models/lstm_autoencoder_model.h5", compile=False)
results = detect_anomalies(
    model=model,
    sequences=sequences,
    timestamps=timestamps,
    raw_data=raw_data,
    metric_names=pivot_df.columns.tolist(),
    dynamic=True  # <- enable MAD-based thresholding
)

# Save
results.to_csv("../outputs/App3_inference_results_with_values.csv", index=False)
print("✅ Inference + metrics saved.")