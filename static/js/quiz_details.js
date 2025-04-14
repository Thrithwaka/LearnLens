document.addEventListener('DOMContentLoaded', function() {
    // Initialize clipboard.js
    if (typeof ClipboardJS !== 'undefined') {
        new ClipboardJS('.copy-btn');
    }
    
    // Copy button feedback
    const copyLinkBtn = document.getElementById('copy-link-btn');
    if (copyLinkBtn) {
        copyLinkBtn.addEventListener('click', function() {
            const originalText = this.innerHTML;
            this.innerHTML = '<i class="fas fa-check"></i> Copied!';
            setTimeout(() => {
                this.innerHTML = originalText;
            }, 2000);
        });
    }
    
    // Quiz control buttons
    const startQuizBtn = document.getElementById('start-quiz-btn');
    const endQuizBtn = document.getElementById('end-quiz-btn');
    
    if (startQuizBtn) {
        startQuizBtn.addEventListener('click', function() {
            if (confirm('Are you sure you want to start this quiz? Participants will be able to join.')) {
                startQuiz();
            }
        });
    }
    
    if (endQuizBtn) {
        endQuizBtn.addEventListener('click', function() {
            if (confirm('Are you sure you want to end this quiz? No more responses will be accepted.')) {
                endQuiz();
            }
        });
    }
    
    function startQuiz() {
        // Get values from data attributes
        const url = startQuizBtn.getAttribute('data-url');
        const csrf = startQuizBtn.getAttribute('data-csrf');
        
        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrf,
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.reload();
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while starting the quiz.');
        });
    }
    
    function endQuiz() {
        // Get values from data attributes
        const url = endQuizBtn.getAttribute('data-url');
        const csrf = endQuizBtn.getAttribute('data-csrf');
        
        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrf,
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.reload();
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while ending the quiz.');
        });
    }
    
    // Chart rendering for ended quizzes
    renderQuizCharts();
    
    function renderQuizCharts() {
        const questionChartEl = document.getElementById('questionChart');
        const emotionChartEl = document.getElementById('emotionChart');
        
        // Only proceed if we have charts on the page
        if (!questionChartEl) return;
        
        // Question performance chart
        if (window.quizData && window.quizData.questionStats) {
            const stats = window.quizData.questionStats;
            const labels = stats.map((stat, index) => `Q${index + 1}`);
            const correctData = stats.map(stat => stat.correct_answers);
            const incorrectData = stats.map(stat => stat.incorrect_answers);
            
            const ctx = questionChartEl.getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Correct Answers',
                            data: correctData,
                            backgroundColor: '#4CAF50',
                            borderColor: '#388E3C',
                            borderWidth: 1
                        },
                        {
                            label: 'Incorrect Answers',
                            data: incorrectData,
                            backgroundColor: '#F44336',
                            borderColor: '#D32F2F',
                            borderWidth: 1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    },
                    plugins: {
                        title: {
                            display: true,
                            text: 'Question Performance'
                        }
                    }
                }
            });
        }
        
        // Emotion analysis chart
        if (emotionChartEl && window.quizData && window.quizData.emotionData) {
            const emotionData = window.quizData.emotionData;
            const questionIds = Object.keys(emotionData);
            
            // Calculate average emotions across all questions
            const avgEmotions = {
                satisfied: 0,
                neutral: 0,
                unsatisfied: 0
            };
            
            let count = 0;
            questionIds.forEach(id => {
                const emotions = emotionData[id];
                if (emotions) {
                    avgEmotions.satisfied += emotions.happy || 0;
                    avgEmotions.neutral += emotions.neutral || 0;
                    
                    // Calculate unsatisfied as average of negative emotions
                    const unsatisfied = (
                        (emotions.sad || 0) + 
                        (emotions.angry || 0) + 
                        (emotions.fear || 0) + 
                        (emotions.disgust || 0)
                    ) / 4;
                    
                    avgEmotions.unsatisfied += unsatisfied;
                    count++;
                }
            });
            
            if (count > 0) {
                avgEmotions.satisfied /= count;
                avgEmotions.neutral /= count;
                avgEmotions.unsatisfied /= count;
            }
            
            const emotionCtx = emotionChartEl.getContext('2d');
            new Chart(emotionCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Satisfied', 'Neutral', 'Unsatisfied'],
                    datasets: [{
                        data: [
                            avgEmotions.satisfied * 100,
                            avgEmotions.neutral * 100,
                            avgEmotions.unsatisfied * 100
                        ],
                        backgroundColor: ['#4CAF50', '#FFC107', '#F44336'],
                        borderColor: ['#388E3C', '#FFA000', '#D32F2F'],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Overall Emotional Response'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    let label = context.label || '';
                                    if (label) {
                                        label += ': ';
                                    }
                                    label += context.raw.toFixed(1) + '%';
                                    return label;
                                }
                            }
                        }
                    }
                }
            });
        }
    }
});