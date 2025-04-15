import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, LSTM, Dense, Attention, RepeatVector, TimeDistributed, Concatenate, Lambda, Dropout
from tensorflow.keras.callbacks import EarlyStopping

# --- Helper to extract last timestep ---
def get_last_timestep(x):
    return x[:, -1, :]

# --- Create sequences for training ---
def create_forecast_sequences(data, window_size=60, forecast_size=30):
    X, y = [], []
    for i in range(len(data) - window_size - forecast_size):
        X.append(data[i:i + window_size])
        y.append(data[i + window_size:i + window_size + forecast_size])
    return np.array(X), np.array(y)

# --- Main training function ---
def train_atn_rnn_forecaster(csv_path, model_path, scaler_path):
    df = pd.read_csv(csv_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    selected_metrics = ['Throughput', 'Response Time (ms)', 'Error Count']
    df = df[selected_metrics].dropna()

    # Scale and save
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(df)

    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)

    # Prepare sequences
    X, y = create_forecast_sequences(scaled_data, window_size=60, forecast_size=30)
    print("Shape:", X.shape, y.shape)

    # Split data
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, shuffle=False)


    # --- Encoder ---
    encoder_inputs = Input(shape=(X.shape[1], X.shape[2]))
    x = LSTM(128, return_sequences=True)(encoder_inputs)
    x = Dropout(0.2)(x)
    x = LSTM(64, return_sequences=True)(x)
    encoder_output = LSTM(32, return_sequences=True)(x)

    # --- Decoder ---
    last_timestep = Lambda(get_last_timestep, name="get_last_timestep")(encoder_output)
    decoder_inputs = RepeatVector(y.shape[1])(last_timestep)
    d = LSTM(64, return_sequences=True)(decoder_inputs)
    d = Dropout(0.2)(d)
    decoder_lstm = LSTM(32, return_sequences=True)(d)

    # --- Attention & Output ---
    attention = Attention()([decoder_lstm, encoder_output])
    decoder_combined = Concatenate()([decoder_lstm, attention])
    outputs = TimeDistributed(Dense(X.shape[2]))(decoder_combined)

    model = Model(encoder_inputs, outputs)
    model.compile(optimizer='adam', loss='mse')

    early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=50,
        batch_size=32,
        callbacks=[early_stop],
        verbose=1
    )

    model.save(model_path)
    print("✅ ATN-RNN model saved successfully.")

    # Loss plot
    plt.figure(figsize=(10, 5))
    plt.plot(history.history['loss'], label='Training Loss')
    plt.plot(history.history['val_loss'], label='Validation Loss')
    plt.title("ATN-RNN Training vs Validation Loss")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("../outputs/atn_rnn_loss_plot.png")
    plt.show()

# --- Entry Point ---
if __name__ == "__main__":
    train_atn_rnn_forecaster(
        csv_path="../outputs/App3_inference_results_with_values.csv",
        model_path="../models/atn_rnn_forecast_model.h5",
        scaler_path="../models/atn_rnn_forecast_scaler.pkl"
    )