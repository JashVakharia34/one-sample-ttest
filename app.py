import os
from datetime import datetime, timezone
from flask import Flask, render_template, request, jsonify  # type: ignore[import-not-found]
import numpy as np  # type: ignore[import-not-found]
from scipy import stats  # type: ignore[import-not-found]
from flask_sqlalchemy import SQLAlchemy  # type: ignore[import-not-found]

app = Flask(__name__)

# Database configuration — uses DATABASE_URL env var on Render, falls back to local SQLite
database_url = os.environ.get('DATABASE_URL', 'sqlite:///local.db')
# Render provides postgres:// but SQLAlchemy needs postgresql://
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# ── Database Model ──────────────────────────────────────────────
class TestResult(db.Model):  # type: ignore[name-defined]
    __tablename__ = 'test_results'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    sample_data = db.Column(db.Text, nullable=False)
    population_mean = db.Column(db.Float, nullable=False)
    alpha = db.Column(db.Float, nullable=False)
    tail = db.Column(db.String(10), nullable=False)
    n = db.Column(db.Integer, nullable=False)
    sample_mean = db.Column(db.Float, nullable=False)
    sample_std = db.Column(db.Float, nullable=False)
    standard_error = db.Column(db.Float, nullable=False)
    t_statistic = db.Column(db.Float, nullable=False)
    degrees_of_freedom = db.Column(db.Integer, nullable=False)
    p_value = db.Column(db.Float, nullable=False)
    ci_lower = db.Column(db.Float, nullable=False)
    ci_upper = db.Column(db.Float, nullable=False)
    reject_null = db.Column(db.Boolean, nullable=False)
    conclusion = db.Column(db.Text, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'sample_data': self.sample_data,
            'population_mean': self.population_mean,
            'alpha': self.alpha,
            'tail': self.tail,
            'n': self.n,
            'sample_mean': self.sample_mean,
            'sample_std': self.sample_std,
            'standard_error': self.standard_error,
            't_statistic': self.t_statistic,
            'degrees_of_freedom': self.degrees_of_freedom,
            'p_value': self.p_value,
            'ci_lower': self.ci_lower,
            'ci_upper': self.ci_upper,
            'reject_null': self.reject_null,
            'conclusion': self.conclusion,
        }


# Auto-create tables on startup
with app.app_context():
    db.create_all()


# ── Routes ──────────────────────────────────────────────────────
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

        # Build conclusion text
        if reject:
            conclusion = (
                f"Reject the null hypothesis (p = {round(p_val, 4)} < α = {alpha}). "  # type: ignore[call-overload]
                f"There is significant evidence that the population mean differs from {pop_mean}."
            )
        else:
            conclusion = (
                f"Fail to reject the null hypothesis (p = {round(p_val, 4)} ≥ α = {alpha}). "  # type: ignore[call-overload]
                f"There is not enough evidence to conclude that the population mean differs from {pop_mean}."
            )

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
            'conclusion': conclusion,
        }

        # Save to database
        record = TestResult(**{  # type: ignore[call-arg]
            'sample_data': sample_str,
            'population_mean': pop_mean,
            'alpha': alpha,
            'tail': tail,
            'n': result['n'],
            'sample_mean': result['sample_mean'],
            'sample_std': result['sample_std'],
            'standard_error': result['standard_error'],
            't_statistic': result['t_statistic'],
            'degrees_of_freedom': df,
            'p_value': result['p_value'],
            'ci_lower': result['ci_lower'],
            'ci_upper': result['ci_upper'],
            'reject_null': reject,
            'conclusion': conclusion,
        })
        db.session.add(record)
        db.session.commit()

        result['id'] = record.id
        result['created_at'] = record.created_at.strftime('%Y-%m-%d %H:%M:%S') if record.created_at else None

        return jsonify(result)

    except ValueError:
        return jsonify({'error': 'Invalid input. Please enter numeric values separated by commas.'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/history')
def history():
    """Return the last 50 test results, newest first."""
    results = TestResult.query.order_by(TestResult.created_at.desc()).limit(50).all()
    return jsonify([r.to_dict() for r in results])


@app.route('/history/<int:record_id>', methods=['DELETE'])
def delete_history(record_id):
    """Delete a single test result by ID."""
    record = TestResult.query.get_or_404(record_id)
    db.session.delete(record)
    db.session.commit()
    return jsonify({'success': True})


if __name__ == '__main__':
    app.run(debug=True)
