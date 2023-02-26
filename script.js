//alert("my launched script.js file");
console.log("my launched script.js file");

//change colour of header.. need to insert window.parent at the brginning to be accepted the style
window.parent.document.querySelector('#cash-flow > div > span').style.background = '#fafafa';

//reload button onClick to reload page
window.parent.document.querySelector('.css-1offfwp a').addEventListener("click", () => {
    window.parent.location.reload();
});