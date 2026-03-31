// Toggle reply attachments for specific post
function toggleReplyAttachment(type, postId) {
    const attachmentTypes = ['image', 'video', 'docs', 'link'];

    attachmentTypes.forEach(t => {
        const section = document.getElementById(`reply-${t}-attachment-${postId}`);
        if (!section) return;

        const hasValue =
            (t === 'image' && document.getElementById(`reply-image-upload-${postId}`)?.files.length > 0) ||
            (t === 'video' && document.getElementById(`reply-video-upload-${postId}`)?.files.length > 0) ||
            (t === 'docs' && document.getElementById(`reply-docs-upload-${postId}`)?.files.length > 0) ||
            (t === 'link' && document.getElementById(`reply-link-input-${postId}`)?.value.trim() !== '');

        if (!hasValue && t !== type) {
            section.classList.add('hidden');
        } else {
            section.classList.remove('hidden');
        }
    });
}

// Initialize all reply forms
document.addEventListener("DOMContentLoaded", function() {
    // Find all reply forms (by common attribute)
    document.querySelectorAll('[id^="reply-form-"]').forEach(form => {
        const postId = form.id.split('-').pop();

        // File input handlers
        const setupFileInput = (inputId, labelId, type) => {
            const input = document.getElementById(`${inputId}-${postId}`);
            const label = document.getElementById(`${labelId}-${postId}`);

            if (input && label) {
                input.addEventListener("change", function() {
                    const file = input.files[0];
                    label.textContent = file ? file.name : "No file selected";
                    if (file) toggleReplyAttachment(type, postId);
                });
            }
        };

        // Setup file inputs
        setupFileInput('reply-image-upload', 'reply-image-filename', 'image');
        setupFileInput('reply-image2-upload', 'reply-image2-filename', 'image');
        setupFileInput('reply-video-upload', 'reply-video-filename', 'video');
        setupFileInput('reply-docs-upload', 'reply-docs-filename', 'docs');

        // Link input handler
        const linkInput = document.getElementById(`reply-link-input-${postId}`);
        if (linkInput) {
            linkInput.addEventListener('input', function() {
                toggleReplyAttachment('link', postId);
            });
        }
    });
});

function toggleReplies(postId) {
  const btn = document.querySelector(`[data-target="replies-container-${postId}"]`);
  if (!btn) return;

  const container = document.getElementById(`replies-container-${postId}`);
  const label = btn.querySelector(".label");
  const icon = btn.querySelector("i.fas");

  if (container.classList.contains("hidden")) {
    container.classList.remove("hidden");
    if (label) label.classList.add("text-maroon");
    if (icon) {
      icon.classList.remove("fa-chevron-down");
      icon.classList.add("fa-chevron-up");
    }
  }
}
