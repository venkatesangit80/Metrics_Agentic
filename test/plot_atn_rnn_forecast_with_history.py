
import pandas as pd
import matplotlib.pyplot as plt

def plot_history_forecast(history_csv, forecast_csv):
    df_hist = pd.read_csv(history_csv, index_col='timestamp')
    df_hist.index = pd.to_datetime(df_hist.index)

    df_forecast = pd.read_csv(forecast_csv)
    df_forecast['timestamp'] = pd.to_datetime(df_forecast['timestamp'])
    df_forecast.set_index('timestamp', inplace=True)

    metrics = ['Throughput', 'Response Time (ms)', 'Error Count']
    sla_thresholds = {'Response Time (ms)': 200, 'Error Count': 2}

    fig, axes = plt.subplots(len(metrics), 1, figsize=(15, 10), sharex=True)

    for i, metric in enumerate(metrics):
        # Plot last 60 mins history
        axes[i].plot(df_hist.index[-60:], df_hist[metric].tail(60), label=f'History: {metric}', color='gray')

        # Plot forecast
        axes[i].plot(df_forecast.index, df_forecast[metric], label=f'Forecast: {metric}', color='blue')

        # SLA line (if defined)
        if metric in sla_thresholds:
            axes[i].axhline(sla_thresholds[metric], color='red', linestyle='--', label='SLA Threshold')

        axes[i].set_title(f"{metric} - Last 60 Min History + 30 Min Forecast")
        axes[i].legend()
        axes[i].grid(True)

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    plot_history_forecast(
        "../outputs/App3_inference_results_with_values.csv",
        "../outputs/App3_forecast_next_30min_atn_rnn.csv"
    )
