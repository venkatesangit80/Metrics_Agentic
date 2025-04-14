import yaml

class RuleEngine:
    def __init__(self, rules_path):
        with open(rules_path, 'r') as f:
            self.rules = yaml.safe_load(f)['rules']

    def evaluate_row(self, row):
        violated = []
        for rule in self.rules:
            try:
                if eval(rule['condition']):
                    violated.append({
                        "id": rule['id'],
                        "description": rule['description'],
                        "severity": rule.get('severity', 'Medium')
                    })
            except Exception as e:
                print(f"Rule '{rule['id']}' failed to evaluate: {e}")
        return violated

    def apply_rules(self, df):
        # Optionally compute period_type before applying rules
        df['hour'] = df['timestamp'].dt.hour
        df['period_type'] = df['hour'].apply(self.classify_period)

        # Apply rules row-wise
        df['violated_rules'] = df.apply(lambda row: self.evaluate_row(row), axis=1)
        df['violated_rule_ids'] = df['violated_rules'].apply(lambda r: [v['id'] for v in r])
        df['violated_descriptions'] = df['violated_rules'].apply(lambda r: [v['description'] for v in r])
        df['violated_severities'] = df['violated_rules'].apply(lambda r: [v['severity'] for v in r])
        return df

    @staticmethod
    def classify_period(hour):
        if 9 <= hour < 18:
            return 'Business Hours'
        elif 2 <= hour < 4:
            return 'Batch Window'
        else:
            return 'Off Hours'