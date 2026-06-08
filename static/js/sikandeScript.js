// Login page slider (only present on the login page in older layouts)
const loginBtn = document.getElementById('login');
const signupBtn = document.getElementById('signup');

if (loginBtn) {
  loginBtn.addEventListener('click', (e) => {
    let parent = e.target.parentNode.parentNode;
    Array.from(e.target.parentNode.parentNode.classList).find((element) => {
      if (element !== "slide-up") {
        parent.classList.add('slide-up');
      } else if (signupBtn) {
        signupBtn.parentNode.classList.add('slide-up');
        parent.classList.remove('slide-up');
      }
    });
  });
}

if (signupBtn) {
  signupBtn.addEventListener('click', (e) => {
    let parent = e.target.parentNode;
    Array.from(e.target.parentNode.classList).find((element) => {
      if (element !== "slide-up") {
        parent.classList.add('slide-up');
      } else if (loginBtn) {
        loginBtn.parentNode.parentNode.classList.add('slide-up');
        parent.classList.remove('slide-up');
      }
    });
  });
}

// ============================================

function confirmDelete(itemID) {
  if (confirm("Are you sure you want to delete this record?")) {
    window.location.href = "/item/del/" + itemID;
  }
}

function scrollToTop() {
  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  });
}
