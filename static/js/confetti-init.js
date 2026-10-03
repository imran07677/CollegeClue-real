/**
 * College Clue - Confetti Animation Trigger
 * Detects if the body tag has data-confetti="true" and triggers a celebration burst.
 */
document.addEventListener('DOMContentLoaded', function () {
    const isConfettiEnabled = document.body.getAttribute('data-confetti');

    if (isConfettiEnabled === 'true' && typeof confetti === 'function') {
        // First burst from center
        confetti({
            particleCount: 100,
            spread: 70,
            origin: { y: 0.6 }
        });

        // Left cannon after 250ms
        setTimeout(function () {
            confetti({
                particleCount: 60,
                angle: 60,
                spread: 55,
                origin: { x: 0 }
            });
        }, 250);

        // Right cannon after 400ms
        setTimeout(function () {
            confetti({
                particleCount: 60,
                angle: 120,
                spread: 55,
                origin: { x: 1 }
            });
        }, 400);
    }
});
