/* =====================================================
   🌸 Emotional Planner · BASE JS
   - Dark Mode Toggle (cu persistenta)
   - UX mic polish
===================================================== */

document.addEventListener("DOMContentLoaded", () => {

    /* ------------------------------
       🌙 DARK MODE
    ------------------------------ */

    const darkToggle = document.querySelector(".dark-toggle");
    const body = document.body;

    if (darkToggle) {
        // Aplică tema la încărcare
        const savedTheme = localStorage.getItem("theme");
        if (savedTheme === "dark") {
            body.classList.add("dark-mode");
            darkToggle.textContent = "☀️";
        }

        // Toggle la click
        darkToggle.addEventListener("click", () => {
            body.classList.toggle("dark-mode");

            const isDark = body.classList.contains("dark-mode");
            darkToggle.textContent = isDark ? "☀️" : "🌙";
            localStorage.setItem("theme", isDark ? "dark" : "light");
        });
    }

    /* ------------------------------
       ✨ UX: remove focus after click
    ------------------------------ */
    document.addEventListener("click", (e) => {
        if (e.target.matches("button, a")) {
            e.target.blur();
        }
    });

});







