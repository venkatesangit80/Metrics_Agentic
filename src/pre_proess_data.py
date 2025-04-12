import os
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import pickle
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.callbacks import EarlyStopping

base_dir = os.path.dirname(os.path.dirname(__file__))
file_path = os.path.join(base_dir, 'data', 'App3_Jan2023.csv')
backend_path = os.path.join(base_dir, 'data', 'backend_metrics_mapping.csv')
df_data = pd.read_csv(file_path)
df_backend = pd.read_csv(backend_path)
df_merged = pd.merge(df_data, df_backend, how='left')
df_merged.loc[df_merged['metric_description'].notnull(), 'metric_name'] = df_merged['metric_description']
df_merged.drop(columns=['metric_description'], inplace=True)

df_merged['timestamp'] = pd.to_datetime(df_merged['timestamp'], format='%Y-%m-%dT%H:%M:%S')

selected_metrics = [
    'Throughput',
    'Response Time (ms)',
    'Error Count',
    'CLR_CPU_Usage (%)'  # if App3 is .NET-based
]

df_filtered = df_merged[df_merged['metric_name'].isin(selected_metrics)]

cutoff_date = df_filtered['timestamp'].min() + pd.Timedelta(days=15)
df_train = df_filtered[df_filtered['timestamp'] < cutoff_date]
pivot_train = df_train.pivot_table(
    index='timestamp',
    columns='metric_name',
    values='metric_value',
    aggfunc='mean'  # or 'max', 'min', 'first'
).dropna()
pivot_train['hour'] = pivot_train.index.hour
pivot_train['dayofweek'] = pivot_train.index.dayofweek

#Scalar Execution
scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(pivot_train)

# Save the scaler for later use during testing
with open("../models/scaler.pkl", "wb") as f:
    pickle.dump(scaler, f)

#Auto Encoder
input_dim = X_scaled.shape[1]

model = Sequential([
    Dense(64, activation='relu', input_shape=(input_dim,)),
    Dense(32, activation='relu'),
    Dense(64, activation='relu'),
    Dense(input_dim, activation='linear')
])

model.compile(optimizer='adam', loss='mse')

# Optional early stopping to avoid overfitting
early_stop = EarlyStopping(monitor='loss', patience=5, restore_best_weights=True)

model.fit(X_scaled, X_scaled,
          epochs=50,
          batch_size=32,
          callbacks=[early_stop],
          verbose=1)

model.save("../models/autoencoder_model.h5")