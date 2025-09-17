// Dark mode toggle
const darkToggle = document.getElementById("darkToggle");
darkToggle.addEventListener("click", () => {
  document.body.classList.toggle("dark");
  if (document.body.classList.contains("dark")) {
    darkToggle.textContent = "☀️";
  } else {
    darkToggle.textContent = "🌙";
  }
});

// Login redirect
document.getElementById("loginBtn").addEventListener("click", () => {
  const role = document.getElementById("role").value;
  if (role === "farmer") window.location.href = "farmer.html";
  if (role === "expert") window.location.href = "expert.html";
  if (role === "policy") window.location.href = "analytics.html";
});
