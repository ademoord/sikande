function confirmDelete(itemID) {
    if (confirm("Are you sure you want to delete this record?")) {
      window.location.href = "/item/del/" + itemID;
    }
}

function toggleNavbar() {
    const hamburger = document.querySelector('.navbar-hamburger');
    hamburger.classList.toggle('open');
}

window.onload = function() {
    window.scrollTo(0, document.body.scrollHeight);
};

function scrollToTop() {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
}