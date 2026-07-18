document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.getElementById('sidebar');
    const menu = document.getElementById('menu-toggle');
    const close = document.getElementById('close-sidebar');

    menu.addEventListener('click', () => {
        sidebar.classList.add('active');
        document.body.classList.add('sidebar-open');
    });

    close.addEventListener('click', () => {
        sidebar.classList.remove('active');
        document.body.classList.remove('sidebar-open');
    });

    document.addEventListener('click', (e) => {
        if (
            sidebar.classList.contains('active') &&
            !sidebar.contains(e.target) &&
            !menu.contains(e.target)
        ) {
            sidebar.classList.remove('active');
            document.body.classList.remove('sidebar-open');
        }
    });
});

// APRI MODAL
document.querySelectorAll(".book-image").forEach(img => {
  img.addEventListener("click", () => {
    const modal = document.getElementById("imageModal");
    const modalImg = modal.querySelector("img");

    modalImg.src = img.src;
    modal.style.display = "flex";
  });
});

// CHIUDI MODAL cliccando sulla X
document.querySelector(".close-image-modal").addEventListener("click", () => {
  document.getElementById("imageModal").style.display = "none";
});

// CHIUDI MODAL cliccando fuori dall'immagine
document.getElementById("imageModal").addEventListener("click", (e) => {
  if (e.target.id === "imageModal") {
    e.currentTarget.style.display = "none";
  }
});

// Overlay di conferma per modifica profilo
const form = document.querySelector('form[action*="salva_profilo"]');
const overlay = document.getElementById('confirmOverlay');
const cancelBtn = document.getElementById('cancelConfirm');
const confirmForm = document.getElementById('confirmForm');

if (form && overlay) {
  form.addEventListener('submit', function (e) {
    e.preventDefault();

    // Copia i valori nel form di conferma
    document.getElementById('confirmNome').value = document.getElementById('nome').value;
    document.getElementById('confirmEmail').value = document.getElementById('email').value;
    document.getElementById('confirmPassword').value = document.getElementById('password').value;

    overlay.style.display = 'flex';
  });

  cancelBtn.addEventListener('click', function () {
    overlay.style.display = 'none';
  });
}
// Occhietto mostra/nascondi password
const togglePassword = document.getElementById('togglePassword');
const passwordInput = document.getElementById('password');

if (togglePassword) {
  togglePassword.addEventListener('click', () => {
    const isPassword = passwordInput.type === "password";
    passwordInput.type = isPassword ? "text" : "password";
    togglePassword.textContent = isPassword ? "🙈" : "👁️";
  });
}
