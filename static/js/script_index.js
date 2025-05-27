const array = ["img/cat.png", "img/black-white.png", "img/dog.png", "img/dog2.png", "img/poodle.png"];
const randomNumber = Math.floor(Math.random() * 5);
console.log(randomNumber)
console.log(array[randomNumber])
const img = document.getElementById('img');

img.setAttribute('src', array[randomNumber]);