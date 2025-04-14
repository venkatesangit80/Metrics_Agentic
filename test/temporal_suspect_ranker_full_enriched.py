
import pandas as pd
import numpy as np
from collections import defaultdict
from tensorflow.keras.models import load_model
import pickle

def temporal_suspect_trail(pivot_df, anomaly_timestamps, metric_names, lookbacks=[15, 30, 45]):
    result = []

    for ts in anomaly_timestamps:
        row = {'timestamp': ts}
        suspects = defaultdict(float)

        for mins in lookbacks:
            prior_ts = ts - pd.Timedelta(minutes=mins)
            if prior_ts in pivot_df.index and ts in pivot_df.index:
                before = pivot_df.loc[prior_ts].values
                after = pivot_df.loc[ts].values
                delta = np.abs(after - before)
                for i, m in enumerate(metric_names):
                    suspects[m] += delta[i]

        sorted_suspects = sorted(suspects.items(), key=lambda x: x[1], reverse=True)
        row['temporal_suspects'] = [s[0] for s in sorted_suspects]
        row['temporal_scores'] = [round(s[1], 3) for s in sorted_suspects]
        result.append(row)

    return pd.DataFrame(result)

def run_temporal_suspect_analysis():
    # Load inference results
    df_result = pd.read_csv("../outputs/App3_inference_results_with_values.csv")
    df_result['timestamp'] = pd.to_datetime(df_result['timestamp'])

    # Load raw full metrics
    df_metrics = pd.read_csv("../data/App3_Jan2023.csv")
    df_metrics['timestamp'] = pd.to_datetime(df_metrics['timestamp'])

    # Load backend metric mapping
    df_mapping = pd.read_csv("../data/backend_metrics_mapping.csv")

    # Merge mapping to original metrics
    df_metrics = pd.merge(df_metrics, df_mapping, how='left', on='metric_name')
    df_metrics['metric_final'] = df_metrics['metric_description'].fillna(df_metrics['metric_name'])

    # Pivot full metrics using final names
    pivot_all = df_metrics.pivot_table(index='timestamp', columns='metric_final', values='metric_value', aggfunc='mean')
    pivot_all = pivot_all.dropna()

    # Load scaler
    with open("../models/lstm_scaler.pkl", "rb") as f:
        scaler = pickle.load(f)

    # Scale for suspect analysis
    metric_names = pivot_all.columns.tolist()
    pivot_scaled = pd.DataFrame(scaler.fit_transform(pivot_all), columns=metric_names, index=pivot_all.index)

    # Anomaly timestamps
    anomaly_timestamps = df_result[df_result['anomaly'] == 1]['timestamp']

    # Temporal suspect trail
    df_suspects = temporal_suspect_trail(pivot_scaled, anomaly_timestamps, metric_names)

    # Merge and save
    df_final = pd.merge(df_result, df_suspects, on='timestamp', how='left')
    df_final.to_csv("../outputs/App3_results_with_full_temporal_suspects_enriched.csv", index=False)
    print("✅ Temporal suspect analysis with metric mapping complete.")

if __name__ == "__main__":
    run_temporal_suspect_analysis()
