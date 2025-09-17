function submitQuery() {
  let q = document.getElementById("question").value;
  document.getElementById("response").innerText =
    "AI thinks your query was: " + q + " (dummy response)";
}

function feedback(type) {
  alert("Feedback: " + type);
}

function submitFeedback() {
  let c = document.getElementById("fbcomment").value;
  alert("Feedback submitted: " + c);
}
