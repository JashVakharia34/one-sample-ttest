// ===================================================
//  One-Sample T-Test – Frontend Logic
// ===================================================

const form = document.getElementById('ttest-form');
const submitBtn = document.getElementById('submit-btn');
const errorMsg = document.getElementById('error-msg');
const resultsSection = document.getElementById('results-section');

// Load history on page load
document.addEventListener('DOMContentLoaded', loadHistory);

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
        loadHistory(); // Refresh history after new calculation
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


// ── History ────────────────────────────────────────────────────

async function loadHistory() {
    try {
        const res = await fetch('/history');
        const data = await res.json();

        const list = document.getElementById('history-list');
        const empty = document.getElementById('history-empty');
        const count = document.getElementById('history-count');

        if (data.length === 0) {
            empty.style.display = 'block';
            count.textContent = '';
            // Remove all history items but keep the empty message
            list.querySelectorAll('.history-item').forEach(el => el.remove());
            return;
        }

        empty.style.display = 'none';
        count.textContent = `${data.length} test${data.length > 1 ? 's' : ''}`;

        list.innerHTML = '';
        list.appendChild(empty); // Re-add hidden empty message
        empty.style.display = 'none';

        data.forEach((item, i) => {
            const card = document.createElement('div');
            card.className = 'history-item';
            card.style.animationDelay = `${i * 0.05}s`;

            const tailLabel = item.tail === 'two' ? 'Two-Tailed' : item.tail === 'left' ? 'Left-Tailed' : 'Right-Tailed';
            const verdictClass = item.reject_null ? 'reject' : 'accept';
            const verdictText = item.reject_null ? 'Rejected H₀' : 'Failed to Reject H₀';

            card.innerHTML = `
                <div class="history-item-top">
                    <div class="history-meta">
                        <span class="history-date">${item.created_at}</span>
                        <span class="history-badge ${verdictClass}">${verdictText}</span>
                        <span class="history-tail">${tailLabel}</span>
                    </div>
                    <button class="history-delete" onclick="deleteHistory(${item.id})" title="Delete this record">✕</button>
                </div>
                <div class="history-stats">
                    <div class="history-stat"><span>n</span><strong>${item.n}</strong></div>
                    <div class="history-stat"><span>x̄</span><strong>${item.sample_mean}</strong></div>
                    <div class="history-stat"><span>t</span><strong>${item.t_statistic}</strong></div>
                    <div class="history-stat"><span>p</span><strong>${item.p_value}</strong></div>
                    <div class="history-stat"><span>α</span><strong>${item.alpha}</strong></div>
                    <div class="history-stat"><span>μ₀</span><strong>${item.population_mean}</strong></div>
                </div>
            `;

            list.appendChild(card);
        });

    } catch (err) {
        console.error('Failed to load history:', err);
    }
}

async function deleteHistory(id) {
    try {
        const res = await fetch(`/history/${id}`, { method: 'DELETE' });
        if (res.ok) {
            loadHistory();
        }
    } catch (err) {
        console.error('Failed to delete:', err);
    }
}
