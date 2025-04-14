// Wait for DOM to be fully loaded before initializing charts
document.addEventListener('DOMContentLoaded', function() {
    // Initialize overall emotion chart if it exists
    const emotionChartElement = document.getElementById('emotionChart');
    if (emotionChartElement) {
        const emotionCtx = emotionChartElement.getContext('2d');
        const emotionSummary = JSON.parse(emotionChartElement.getAttribute('data-emotions'));
        
        new Chart(emotionCtx, {
            type: 'radar',
            data: {
                labels: Object.keys(emotionSummary).map(emotion => emotion.charAt(0).toUpperCase() + emotion.slice(1)),
                datasets: [{
                    label: 'Emotional Response',
                    data: Object.values(emotionSummary),
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgba(54, 162, 235, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(54, 162, 235, 1)'
                }]
            },
            options: {
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 1
                    }
                }
            }
        });
    }
    
    // Initialize individual answer emotion charts
    const answerEmotionCharts = document.querySelectorAll('[id^="emotionChart"]:not(#emotionChart)');
    answerEmotionCharts.forEach(chartElement => {
        if (chartElement) {
            const ctx = chartElement.getContext('2d');
            const chartId = chartElement.id;
            const emotions = JSON.parse(chartElement.getAttribute('data-emotions'));
            
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: Object.keys(emotions),
                    datasets: [{
                        label: 'Emotion Intensity',
                        data: Object.values(emotions),
                        backgroundColor: [
                            'rgba(255, 99, 132, 0.5)',
                            'rgba(54, 162, 235, 0.5)',
                            'rgba(255, 206, 86, 0.5)',
                            'rgba(75, 192, 192, 0.5)',
                            'rgba(153, 102, 255, 0.5)',
                            'rgba(255, 159, 64, 0.5)'
                        ],
                        borderColor: [
                            'rgba(255, 99, 132, 1)',
                            'rgba(54, 162, 235, 1)',
                            'rgba(255, 206, 86, 1)',
                            'rgba(75, 192, 192, 1)',
                            'rgba(153, 102, 255, 1)',
                            'rgba(255, 159, 64, 1)'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 1
                        }
                    }
                }
            });
        }
    });
});