// ===================================================
//  One-Sample T-Test – Frontend Logic
// ===================================================

const form = document.getElementById('ttest-form');
const submitBtn = document.getElementById('submit-btn');
const errorMsg = document.getElementById('error-msg');
const resultsSection = document.getElementById('results-section');

form.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Hide previous results / errors
    resultsSection.classList.add('hidden');
    errorMsg.classList.remove('show');
    submitBtn.classList.add('loading');

    const payload = {
        sample_data: document.getElementById('sample-data').value.trim(),
        population_mean: document.getElementById('pop-mean').value,
        alpha: document.getElementById('alpha').value,
        tail: document.getElementById('tail').value,
    };

    try {
        const res = await fetch('/calculate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.error || 'Something went wrong.');
        }

        renderResults(data);
    } catch (err) {
        errorMsg.textContent = err.message;
        errorMsg.classList.add('show');
    } finally {
        submitBtn.classList.remove('loading');
    }
});

function renderResults(d) {
    // Stat values
    document.getElementById('val-n').textContent = d.n;
    document.getElementById('val-mean').textContent = d.sample_mean;
    document.getElementById('val-std').textContent = d.sample_std;
    document.getElementById('val-se').textContent = d.standard_error;
    document.getElementById('val-t').textContent = d.t_statistic;
    document.getElementById('val-p').textContent = d.p_value;
    document.getElementById('val-df').textContent = d.degrees_of_freedom;
    document.getElementById('val-ci').textContent = `[${d.ci_lower}, ${d.ci_upper}]`;

    // Verdict banner
    const banner = document.getElementById('verdict-banner');
    const icon = document.getElementById('verdict-icon');
    const text = document.getElementById('verdict-text');

    banner.className = 'verdict-banner'; // reset
    if (d.reject_null) {
        banner.classList.add('reject');
        icon.textContent = '🔴';
    } else {
        banner.classList.add('fail-to-reject');
        icon.textContent = '🟢';
    }
    text.textContent = d.conclusion;

    // Hypotheses
    const mu0 = d.population_mean;
    document.getElementById('hyp-null').textContent = `μ = ${mu0}`;

    if (d.tail === 'two') {
        document.getElementById('hyp-alt').textContent = `μ ≠ ${mu0}`;
    } else if (d.tail === 'left') {
        document.getElementById('hyp-alt').textContent = `μ < ${mu0}`;
    } else {
        document.getElementById('hyp-alt').textContent = `μ > ${mu0}`;
    }

    // Show results
    resultsSection.classList.remove('hidden');

    // Scroll to results smoothly
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

    // Animate stat cards entry
    document.querySelectorAll('.stat-card').forEach((card, i) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(16px)';
        setTimeout(() => {
            card.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 80 * i);
    });
}
