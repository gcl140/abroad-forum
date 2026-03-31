let currentImageIndex = 0;

function lonnextImage() {
  const images = document.querySelectorAll("#image-container .carousel-img");
  if (images.length < 2) return;

  images[currentImageIndex].classList.add("hidden");
  currentImageIndex = (currentImageIndex + 1) % images.length;
  images[currentImageIndex].classList.remove("hidden");
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

function toggleRepliesContainer(postId) {
  const btn = document.querySelector(`[data-target="replies-container-${postId}"]`);
  if (!btn) return;
  const container = document.getElementById(`replies-container-${postId}`);
  if (!container) return;
  const label = btn.querySelector('.label');
  const icon = btn.querySelector('i.fas');

  const opening = container.classList.contains('hidden');
  container.classList.toggle('hidden');

  if (opening) {
    if (label) label.classList.add('text-maroon');
    if (icon) { icon.classList.remove('fa-chevron-down'); icon.classList.add('fa-chevron-up'); }
  } else {
    if (icon) { icon.classList.remove('fa-chevron-up'); icon.classList.add('fa-chevron-down'); }
  }
}
