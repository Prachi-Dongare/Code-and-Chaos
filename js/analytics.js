const ctx = document.getElementById('queriesChart');
new Chart(ctx, {
  type: 'bar',
  data: {
    labels: ['Wheat', 'Rice', 'Tomato', 'Potato'],
    datasets: [{
      label: 'Number of Queries',
      data: [12, 19, 7, 5],
      borderWidth: 1,
      backgroundColor: '#43a047'
    }]
  },
  options: {
    responsive: true,
    scales: {
      y: { beginAtZero: true }
    }
  }
});
