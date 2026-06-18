/* AVYRA-LIVE — Admin JS */

// Sidebar toggle on mobile
function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
}

// Fetch prospect stats on dashboard
if (document.getElementById('stat-prospects')) {
  fetch('/api/prospects/stats')
    .then(r => r.json())
    .then(d => {
      if (d.total) document.getElementById('stat-prospects').textContent = d.total;
    })
    .catch(() => {});
}
