document.addEventListener('DOMContentLoaded', function () {
  var map = L.map('maparea').setView([39.7837304, -100.445882], 3);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap'
  }).addTo(map);

  fetch('/static/json/places.json')
    .then(response => response.json())
    .then(data => {
      data.places.forEach(place => {
        var marker = L.marker([place.lat, place.lng]).addTo(map);
        marker.bindPopup(`<h2 style='color:black;'>${place.name}</h2><h3 style='color:black;'>${place.description}</h3>`);
      });
    })
    .catch(error => console.error('Error loading places:', error));
});