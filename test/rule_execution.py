from rule_engine import RuleEngine
import pandas as pd

# Load your post-inference results
df = pd.read_csv("../outputs/App3_inference_results_with_values.csv")
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Load and apply rule engine
engine = RuleEngine("../config/rules.yaml")
df_with_violations = engine.apply_rules(df)

# Save the enhanced file
df_with_violations.to_csv("../outputs/App3_results_with_rule_violations.csv", index=False)
print("✅ Rule evaluation completed.")