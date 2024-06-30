document.querySelectorAll('[data-github]').forEach(function (element) {
  var repo = element.getAttribute('data-github');

  fetch('https://api.github.com/repos/' + repo).then(function (response) {
    return response.json();
  }).then(function (response) {
    element.querySelector('[data-forks]').textContent = response.forks;
    element.querySelector('[data-stars]').textContent = response.stargazers_count;
  });
});