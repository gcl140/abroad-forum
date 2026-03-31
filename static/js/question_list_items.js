const imageIndices = {};

function nextImage(postId) {
  const container = document.getElementById(`image-${postId}-container`);
  const images = container.querySelectorAll(".carousel-img");

  if (images.length < 2) return;

  if (!(postId in imageIndices)) imageIndices[postId] = 0;

  images[imageIndices[postId]].classList.add("hidden");
  imageIndices[postId] = (imageIndices[postId] + 1) % images.length;
  images[imageIndices[postId]].classList.remove("hidden");
}

function sharePost(postId) {
  const shareUrl = `${window.location.origin}/post/${postId}/`;

  if (navigator.share) {
    navigator.share({
      title: "Check out this post",
      text: "Thought you might find this interesting.",
      url: shareUrl,
    }).catch((error) => {
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
  navigator.clipboard.writeText(url).then(() => {
    Toastify({
      text: "Link copied to clipboard! You can now share it.",
      duration: 3000,
      gravity: "top",
      position: "right",
      close: true,
      backgroundColor: "#4CAF50",
    }).showToast();
  }).catch(() => {
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
    const position = absoluteElementTop - window.innerHeight * 0.3;

    window.scrollTo({ top: position, behavior: "smooth" });

    target.classList.add("flash-once");
    setTimeout(() => {
      target.classList.remove("flash-once");
    }, 1000);
  }
}

document.addEventListener("DOMContentLoaded", function () {
  if (window.location.hash) {
    scrollAndFlash(window.location.hash);
  }
});

document.addEventListener("click", function (e) {
  const link = e.target.closest('a[href^="#"]');
  if (link && link.getAttribute("href").length > 1) {
    e.preventDefault();
    const hash = link.getAttribute("href");
    history.pushState(null, null, hash);
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
    container.classList.remove("hidden");
    label.classList.add("text-maroon");
    icon.classList.remove("fa-chevron-down");
    icon.classList.add("fa-chevron-up");
  } else {
    container.classList.add("hidden");
    icon.classList.remove("fa-chevron-up");
    icon.classList.add("fa-chevron-down");
  }
});
