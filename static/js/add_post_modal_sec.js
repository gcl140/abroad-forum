function toggleAttachment(type) {
    const attachmentTypes = ['image', 'video', 'docs', 'link'];

    attachmentTypes.forEach(t => {
        const section = document.getElementById(`${t}-attachment`);
        const hasValue =
            (t === 'image' && (document.getElementById('image-upload').files.length > 0 || document.getElementById('image2-upload').files.length > 0)) ||
            (t === 'video' && document.getElementById('video-upload').files.length > 0) ||
            (t === 'docs' && document.getElementById('docs-upload').files.length > 0) ||
            (t === 'link' && document.querySelector('input[name="link"]').value.trim() !== '');

        // Only hide if it doesn't have a value AND it's not the selected type
        if (!hasValue && t !== type) {
            section.classList.add('hidden');
        } else {
            section.classList.remove('hidden');
        }
    });
}

// When page loads, check if any inputs are pre-filled and show the relevant section(s)
document.addEventListener('DOMContentLoaded', function () {
    toggleAttachment(null); // null forces the function to evaluate all and show any non-empty
});

document.addEventListener("DOMContentLoaded", function () {
    const fileInputs = [
        { inputId: "image-upload", labelId: "image-filename" },
        { inputId: "image2-upload", labelId: "image2-filename" },
        { inputId: "video-upload", labelId: "video-filename" },
        { inputId: "docs-upload", labelId: "docs-filename" },
    ];

    fileInputs.forEach(({ inputId, labelId }) => {
        const input = document.getElementById(inputId);
        const label = document.getElementById(labelId);

        if (input && label) {
            input.addEventListener("change", function () {
                const file = input.files[0];
                label.textContent = file ? file.name : "No file selected";
            });
        }
    });
});
