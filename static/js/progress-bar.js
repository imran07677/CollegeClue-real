/**
 * College Clue - Form Submission Progress Bar
 * Displays an animated Bootstrap progress bar when student registration form is submitted.
 */
document.addEventListener('DOMContentLoaded', function () {
    const registrationForm = document.getElementById('student-registration-form');
    const progressWrapper = document.getElementById('submission-progress-wrapper');
    const progressBar = document.getElementById('submission-progress-bar');
    const progressPercentage = document.getElementById('submission-progress-percentage');
    const submitBtn = document.getElementById('submit-registration-btn');

    if (!registrationForm || !progressWrapper || !progressBar || !submitBtn) {
        return;
    }

    registrationForm.addEventListener('submit', function (event) {
        // Basic check if form is valid before initiating submission animation
        if (!registrationForm.checkValidity()) {
            return;
        }

        // Show progress bar container
        progressWrapper.classList.remove('d-none');

        // Disable submit button to prevent double submissions
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Processing Admission...';

        let currentProgress = 15;
        progressBar.style.width = currentProgress + '%';
        progressBar.setAttribute('aria-valuenow', currentProgress);
        if (progressPercentage) progressPercentage.textContent = currentProgress + '%';

        const interval = setInterval(function () {
            if (currentProgress < 90) {
                currentProgress += Math.floor(Math.random() * 15) + 10;
                if (currentProgress > 90) currentProgress = 90;
                progressBar.style.width = currentProgress + '%';
                progressBar.setAttribute('aria-valuenow', currentProgress);
                if (progressPercentage) progressPercentage.textContent = currentProgress + '%';
            } else {
                clearInterval(interval);
            }
        }, 250);
    });
});
