console.clear();

const loginBtn = document.getElementById('login');
const signupBtn = document.getElementById('signup');

loginBtn.addEventListener('click', (e) => {
	let parent = e.target.parentNode.parentNode;
	Array.from(e.target.parentNode.parentNode.classList).find((element) => {
		if(element !== "slide-up") {
			parent.classList.add('slide-up')
		}else{
			signupBtn.parentNode.classList.add('slide-up')
			parent.classList.remove('slide-up')
		}
	});
});

signupBtn.addEventListener('click', (e) => {
	let parent = e.target.parentNode;
	Array.from(e.target.parentNode.classList).find((element) => {
		if(element !== "slide-up") {
			parent.classList.add('slide-up')
		}else{
			loginBtn.parentNode.parentNode.classList.add('slide-up')
			parent.classList.remove('slide-up')
		}
	});
});

// ============================================

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