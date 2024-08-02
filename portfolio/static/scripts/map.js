document.addEventListener('DOMContentLoaded', function () {
  var map = L.map('maparea').setView([39.7837304, -100.445882], 3);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap'
  }).addTo(map);
  setTimeout(() => {
    if (typeof places !== 'undefined' && Array.isArray(places)) {
      places.forEach(place => {
        var marker = L.marker([parseFloat(place.lat), parseFloat(place.lng)]).addTo(map);
        marker.bindPopup(`<h2 style='color:black;'>${place.name}</h2><h3 style='color:black;'>${place.description}</h3>`);
      });
    }
  }, 1000);
});