
import pandas as pd
import numpy as np
import pickle
from tensorflow.keras.models import load_model
from tensorflow.keras.utils import get_custom_objects
from tensorflow.keras.layers import Lambda

def get_last_timestep(x):
    return x[:, -1, :]

def prepare_input_sequence(csv_path, window_size=60):
    df = pd.read_csv(csv_path, index_col='timestamp')
    df.index = pd.to_datetime(df.index)

    selected_metrics = ['Throughput', 'Response Time (ms)', 'Error Count']
    df = df[selected_metrics].dropna()

    scaler = pickle.load(open("../models/atn_rnn_forecast_scaler.pkl", "rb"))
    scaled_data = scaler.transform(df)

    input_seq = np.expand_dims(scaled_data[-window_size:], axis=0)
    return input_seq, scaler, df.index[-1]

def predict_with_atn_rnn(model_path, input_seq, scaler, last_timestamp):
    get_custom_objects().update({'get_last_timestep': Lambda(get_last_timestep)})
    model = load_model(model_path, compile=False)
    forecast = model.predict(input_seq)[0]

    forecast_inverted = scaler.inverse_transform(forecast)

    future_timestamps = pd.date_range(start=last_timestamp + pd.Timedelta(minutes=1), periods=forecast.shape[0], freq='T')
    df_forecast = pd.DataFrame(forecast_inverted, columns=['Throughput', 'Response Time (ms)', 'Error Count'])
    df_forecast['timestamp'] = future_timestamps

    df_forecast['breach_response_time'] = df_forecast['Response Time (ms)'] > 200
    df_forecast['breach_error_count'] = df_forecast['Error Count'] > 2

    return df_forecast

if __name__ == "__main__":
    input_seq, scaler, last_ts = prepare_input_sequence("../outputs/App3_inference_results_with_values.csv")
    df_forecast = predict_with_atn_rnn("../models/atn_rnn_forecast_model.h5", input_seq, scaler, last_ts)
    df_forecast.to_csv("../outputs/App3_forecast_next_30min_atn_rnn.csv", index=False)
    print("✅ ATN-RNN forecast for next 30 minutes saved.")
