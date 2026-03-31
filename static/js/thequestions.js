const imageIndices = {}; // track index per post

function nextImage(postId) {
  const container = document.getElementById(`image-${postId}-container`);
  const images = container.querySelectorAll(".carousel-img");

  if (images.length < 2) return;

  // init if undefined
  if (!(postId in imageIndices)) imageIndices[postId] = 0;

  // hide current
  images[imageIndices[postId]].classList.add("hidden");

  // next index
  imageIndices[postId] = (imageIndices[postId] + 1) % images.length;

  // show next
  images[imageIndices[postId]].classList.remove("hidden");
}

function sharePost(postId) {
  const shareUrl = `${window.location.origin}/post/${postId}/`;

  if (navigator.share) {
    navigator
      .share({
        title: "Check out this post",
        text: "Thought you might find this interesting.",
        url: shareUrl,
      })
      .catch((error) => {
        console.error("Sharing failed:", error);
        fallbackCopyLink(shareUrl);
      });
  } else if (navigator.clipboard) {
    fallbackCopyLink(shareUrl);
  } else {
    Toastify({
      text: `Sharing not supported. Copy this link:\n${shareUrl}`,
      duration: 4000,
      gravity: "top",
      position: "right",
      close: true,
      backgroundColor: "#f44336",
    }).showToast();
  }
}

function fallbackCopyLink(url) {
  navigator.clipboard
    .writeText(url)
    .then(() => {
      Toastify({
        text: "Link copied to clipboard! You can now share it.",
        duration: 3000,
        gravity: "top",
        position: "right",
        close: true,
        backgroundColor: "#4CAF50",
      }).showToast();
    })
    .catch(() => {
      Toastify({
        text: `Failed to copy automatically. Please copy this link manually:\n${url}`,
        duration: 4000,
        gravity: "top",
        position: "right",
        close: true,
        backgroundColor: "#f44336",
      }).showToast();
    });
}

function scrollAndFlash(hash) {
  const target = document.querySelector(hash);
  if (target) {
    const elementRect = target.getBoundingClientRect();
    const absoluteElementTop = elementRect.top + window.scrollY;

    // Scroll so it's near the bottom of the viewport
    const position = absoluteElementTop - window.innerHeight * 0.3;

    window.scrollTo({
      top: position,
      behavior: "smooth",
    });

    // Flash effect
    target.classList.add("flash-once");
    setTimeout(() => {
      target.classList.remove("flash-once");
    }, 1000);
  }
}

// On initial page load with hash
document.addEventListener("DOMContentLoaded", function () {
  if (window.location.hash) {
    scrollAndFlash(window.location.hash);
  }
});

// When clicking same-page links
document.addEventListener("click", function (e) {
  const link = e.target.closest('a[href^="#"]');
  if (link && link.getAttribute("href").length > 1) {
    e.preventDefault(); // stop default jump
    const hash = link.getAttribute("href");
    history.pushState(null, null, hash); // update URL hash
    scrollAndFlash(hash);
  }
});

document.addEventListener("click", function (e) {
  const btn = e.target.closest(".toggle-replies");
  if (!btn) return;

  const targetId = btn.getAttribute("data-target");
  const container = document.getElementById(targetId);
  const label = btn.querySelector(".label");
  const icon = btn.querySelector("i.fas");

  if (container.classList.contains("hidden")) {
    // Open
    container.classList.remove("hidden");
    if (label) label.classList.add("text-maroon");
    if (icon) {
      icon.classList.remove("fa-chevron-down");
      icon.classList.add("fa-chevron-up");
    }
  } else {
    // Close
    container.classList.add("hidden");
    if (icon) {
      icon.classList.remove("fa-chevron-up");
      icon.classList.add("fa-chevron-down");
    }
  }
});

// Delegated handlers for share and next-image
document.addEventListener('click', function(e) {
  const shareBtn = e.target.closest('[data-share-post]');
  if (shareBtn) {
    const id = parseInt(shareBtn.getAttribute('data-share-post'), 10);
    if (!isNaN(id)) sharePost(id);
    return;
  }

  const nextImgBtn = e.target.closest('[data-next-image]');
  if (nextImgBtn) {
    const id = nextImgBtn.getAttribute('data-next-image');
    nextImage(id);
    return;
  }
});
