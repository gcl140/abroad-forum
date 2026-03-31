function toggleReplyParentForm(groupId) {
    const container = document.getElementById(`reply-to-parent-form-container-${groupId}`);
    const button = document.getElementById(`reply-parent-button-${groupId}`);

    const isHidden = container.classList.contains('hidden');
    container.classList.toggle('hidden');

    if (isHidden) {
        button.classList.add('text-maroon');
    } else {
        button.classList.remove('text-maroon');
    }
}
