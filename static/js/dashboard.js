document.addEventListener('DOMContentLoaded', function() {
    // Theme-aware text color for chart labels/titles
    const rootStyles = getComputedStyle(document.documentElement);
    const textColor = rootStyles.getPropertyValue('--text').trim() || '#2a2722';

    // Get the current month and year
    const currentDate = new Date();
    const monthNames = ["January", "February", "March", "April", "May", "June",
                        "July", "August", "September", "October", "November", "December"];
    const currentMonth = monthNames[currentDate.getMonth()];
    const currentYear = currentDate.getFullYear();

    // Fetch data for the bar chart (only if the bar chart canvas is present)
    const barChartEl = document.getElementById('barChart');
    if (barChartEl) {
    fetch('/api/bar_chart_data')
        .then(response => response.json())
        .then(data => {
            const ctxBar = barChartEl.getContext('2d');
            new Chart(ctxBar, {
                type: 'bar',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Item Data',
                        data: data.values,
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                        title: {
                            display: true,
                            text: `Item Data Bar Chart for ${currentMonth} ${currentYear}`
                        }
                    }
                }
            });
        });
    }

    // Fetch data for the doughnut chart
    fetch('/api/doughnut_chart_data')
        .then(response => response.json())
        .then(data => {
            const ctxDoughnut = document.getElementById('doughnutChart').getContext('2d');

            const categoryColors = {
                'needs': 'forestgreen',
                'liabilities': 'mediumpurple',
                'saving': 'lightskyblue',
                'charity': 'mediumseagreen',
                'fun': 'lightsalmon',
                'urgent': 'indianred'
            };

            const chartData = {
                labels: data.categories,
                datasets: [{
                    data: data.counts,
                    backgroundColor: data.categories.map(category => categoryColors[category])
                }]
            };

            new Chart(ctxDoughnut, {
                type: 'doughnut',
                data: chartData,
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
                            text: `Distribusi Pengeluaran di Bulan: ${currentMonth} ${currentYear}`,
                            color: textColor
                        }
                    }
                }
            });
        });

    // Investment distribution doughnut (only if its canvas is present)
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
