from flask import Flask, render_template, request, jsonify  # type: ignore[import-not-found]
import numpy as np  # type: ignore[import-not-found]
from scipy import stats  # type: ignore[import-not-found]

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.get_json()

        # Parse sample data
        sample_str = data.get('sample_data', '')
        pop_mean = float(data.get('population_mean', 0))
        alpha = float(data.get('alpha', 0.05))
        tail = data.get('tail', 'two')  # 'two', 'left', 'right'

        # Convert comma/space/newline separated values to list of floats
        raw = sample_str.replace('\n', ',').replace(' ', ',')
        values = [float(v.strip()) for v in raw.split(',') if v.strip()]

        if len(values) < 2:
            return jsonify({'error': 'Please enter at least 2 data values.'}), 400

        sample = np.array(values)

        # Perform one-sample t-test
        t_stat, p_value_two = stats.ttest_1samp(sample, pop_mean)

        # Adjust p-value based on tail direction
        if tail == 'two':
            p_value = p_value_two
        elif tail == 'left':
            p_value = p_value_two / 2 if t_stat < 0 else 1 - p_value_two / 2
        elif tail == 'right':
            p_value = p_value_two / 2 if t_stat > 0 else 1 - p_value_two / 2
        else:
            p_value = p_value_two

        # Degrees of freedom
        df = len(sample) - 1

        # Confidence interval for the mean
        confidence = 1 - alpha
        se = stats.sem(sample)
        margin = se * stats.t.ppf((1 + confidence) / 2, df)
        ci_lower = float(np.mean(sample) - margin)
        ci_upper = float(np.mean(sample) + margin)

        # Decision
        reject = bool(p_value < alpha)

        # Convert to plain Python floats for JSON serialization & type safety
        mean_val = float(np.mean(sample))
        std_val = float(np.std(sample, ddof=1))
        se_val = float(se)
        t_val = float(t_stat)
        p_val = float(p_value)

        # Descriptive statistics
        result = {
            'n': len(sample),
            'sample_mean': round(mean_val, 6),  # type: ignore[call-overload]
            'sample_std': round(std_val, 6),  # type: ignore[call-overload]
            'standard_error': round(se_val, 6),  # type: ignore[call-overload]
            'population_mean': pop_mean,
            't_statistic': round(t_val, 6),  # type: ignore[call-overload]
            'degrees_of_freedom': df,
            'p_value': round(p_val, 6),  # type: ignore[call-overload]
            'alpha': alpha,
            'ci_lower': round(ci_lower, 6),  # type: ignore[call-overload]
            'ci_upper': round(ci_upper, 6),  # type: ignore[call-overload]
            'reject_null': reject,
            'tail': tail,
            'conclusion': (
                f"Reject the null hypothesis (p = {round(p_val, 4)} < α = {alpha}). "  # type: ignore[call-overload]
                f"There is significant evidence that the population mean differs from {pop_mean}."
                if reject else
                f"Fail to reject the null hypothesis (p = {round(p_val, 4)} ≥ α = {alpha}). "  # type: ignore[call-overload]
                f"There is not enough evidence to conclude that the population mean differs from {pop_mean}."
            ),
        }

        return jsonify(result)

    except ValueError:
        return jsonify({'error': 'Invalid input. Please enter numeric values separated by commas.'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
