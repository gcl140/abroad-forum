function toggleReplyForm(groupId) {
    const container = document.getElementById(`reply-form-container-${groupId}`);
    const button = document.getElementById(`reply-button-${groupId}`);

    const isHidden = container.classList.contains('hidden');
    container.classList.toggle('hidden');

    if (isHidden) {
        button.classList.add('text-maroon');
    } else {
        button.classList.remove('text-maroon');
    }
}
