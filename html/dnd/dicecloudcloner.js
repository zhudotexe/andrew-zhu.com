const urlParams = new URLSearchParams(window.location.search);
const success = urlParams.get('success');
if (success === '0') {
    document.getElementById("error").style.visibility = "visible";
}
