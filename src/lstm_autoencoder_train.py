import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import pickle
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, LSTM, RepeatVector, TimeDistributed, Dense
from tensorflow.keras.callbacks import EarlyStopping

# Load your merged CSV with real metric names
df = pd.read_csv("../data/App3_Jan2023.csv")
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Filter only the metrics you want
selected_metrics = ['Throughput', 'Response Time (ms)', 'Error Count', 'CLR_CPU_Usage (%)']
df = df[df['metric_name'].isin(selected_metrics)]

# First 15 days of data
cutoff = df['timestamp'].min() + pd.Timedelta(days=15)
df_train = df[df['timestamp'] < cutoff]

# Pivot to wide format
pivot_train = df_train.pivot_table(
    index='timestamp',
    columns='metric_name',
    values='metric_value',
    aggfunc='mean'  # just in case of duplicates
).dropna()



def create_sequences(data, window_size):
    X = []
    for i in range(len(data) - window_size):
        seq = data[i:i+window_size]
        X.append(seq)
    return np.array(X)

# Example: 30-minute sequences (assuming 1 row = 1 min)
window_size = 30

scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(pivot_train)

# Save the scaler
with open("../models/lstm_scaler.pkl", "wb") as f:
    pickle.dump(scaler, f)

# Create sequences
X_seq = create_sequences(X_scaled, window_size)
print("Training shape:", X_seq.shape)  # Should be (num_windows, 30, num_metrics)

timesteps = X_seq.shape[1]
n_features = X_seq.shape[2]

# Encoder
inputs = Input(shape=(timesteps, n_features))
encoded = LSTM(64, activation='relu')(inputs)
encoded = RepeatVector(timesteps)(encoded)

# Decoder
decoded = LSTM(64, activation='relu', return_sequences=True)(encoded)
decoded = TimeDistributed(Dense(n_features))(decoded)

# Model
model = Model(inputs, decoded)
model.compile(optimizer='adam', loss='mse')
model.summary()


early_stop = EarlyStopping(monitor='loss', patience=5, restore_best_weights=True)

history = model.fit(
    X_seq, X_seq,
    epochs=50,
    batch_size=32,
    callbacks=[early_stop],
    verbose=1
)

# Save model
model.save("../models/lstm_autoencoder_model.h5")