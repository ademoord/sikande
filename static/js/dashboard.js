document.addEventListener('DOMContentLoaded', function() {
    const rootStyles = getComputedStyle(document.documentElement);
    const textColor = rootStyles.getPropertyValue('--text').trim() || '#2a2722';
    const range = window.SIKANDE_DASHBOARD_RANGE || 'month';

    const categoryColors = {
        'needs': 'forestgreen',
        'liabilities': 'mediumpurple',
        'saving': 'lightskyblue',
        'charity': 'mediumseagreen',
        'fun': 'lightsalmon',
        'urgent': 'indianred',
        'legacy': '#8a8170'
    };

    const rangeTitle = range === 'all' ? 'All Time' : 'Current Month';

    // Spending doughnut (respects range selector)
    const doughnutEl = document.getElementById('doughnutChart');
    if (doughnutEl) {
        fetch('/api/doughnut_chart_data?range=' + encodeURIComponent(range))
            .then(response => response.json())
            .then(data => {
                new Chart(doughnutEl.getContext('2d'), {
                    type: 'doughnut',
                    data: {
                        labels: data.categories,
                        datasets: [{
                            data: data.counts,
                            backgroundColor: data.categories.map(c => categoryColors[c] || '#c9a227')
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'top',
                                labels: { color: textColor }
                            },
                            title: {
                                display: true,
                                text: 'Distribusi Pengeluaran — ' + rangeTitle,
                                color: textColor
                            }
                        }
                    }
                });
            });
    }

    // Monthly spending bar chart (All Time + archive only)
    const monthlyEl = document.getElementById('spendingMonthlyChart');
    if (monthlyEl) {
        fetch('/api/spending_monthly_chart?range=' + encodeURIComponent(range))
            .then(response => response.json())
            .then(data => {
                if (!data.labels || !data.labels.length) return;
                new Chart(monthlyEl.getContext('2d'), {
                    type: 'bar',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: 'Total (Rp)',
                            data: data.totals,
                            backgroundColor: 'rgba(201, 162, 39, 0.35)',
                            borderColor: 'rgba(201, 162, 39, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false },
                            title: {
                                display: true,
                                text: 'Monthly spending (last 24 months)',
                                color: textColor
                            }
                        },
                        scales: {
                            y: {
                                ticks: { color: textColor },
                                grid: { color: 'rgba(138, 129, 112, 0.2)' }
                            },
                            x: {
                                ticks: { color: textColor, maxRotation: 45 },
                                grid: { display: false }
                            }
                        }
                    }
                });
            });
    }

    // Investment distribution doughnut
    const investmentEl = document.getElementById('investmentChart');
    if (investmentEl) {
        fetch('/api/investment_chart_data')
            .then(response => response.json())
            .then(data => {
                new Chart(investmentEl.getContext('2d'), {
                    type: 'doughnut',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            data: data.values,
                            backgroundColor: data.colors
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'top',
                                labels: { color: textColor }
                            },
                            title: {
                                display: true,
                                text: 'Portfolio Allocation (Current Value)',
                                color: textColor
                            }
                        }
                    }
                });
            });
    }
});
