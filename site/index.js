function myFunction() {
  var link = "https://discord.com/api/v8/invites/Umw5NxcVSP?with_counts=true"; 
  var res = fetch(link).json()
  document.getElementById("demo").innerHTML = res;
}
