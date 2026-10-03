/**
 * College Clue - Live Auto-Suggest Search Bar
 * Provides instant live suggestions for Universities, Colleges, and Courses as the user types.
 */
document.addEventListener('DOMContentLoaded', function () {
    const searchInputs = document.querySelectorAll('input[name="search"], #navCollegeSearchInput, [data-suggest-search]');
    if (!searchInputs.length) return;

    searchInputs.forEach(input => {
        setupAutoSuggest(input);
    });

    function setupAutoSuggest(input) {
        // Create container wrapper if needed
        const parent = input.parentElement;
        if (getComputedStyle(parent).position === 'static') {
            parent.style.position = 'relative';
        }

        // Create dropdown container
        const dropdown = document.createElement('div');
        dropdown.className = 'search-suggestions-dropdown shadow-lg rounded-4 p-2 bg-white border border-light-subtle';
        dropdown.style.position = 'absolute';
        dropdown.style.top = '100%';
        dropdown.style.left = '0';
        dropdown.style.right = '0';
        dropdown.style.zIndex = '1060';
        dropdown.style.display = 'none';
        dropdown.style.marginTop = '6px';
        dropdown.style.maxHeight = '380px';
        dropdown.style.overflowY = 'auto';
        dropdown.style.minWidth = '320px';

        parent.appendChild(dropdown);

        let debounceTimer = null;
        let activeIndex = -1;

        input.addEventListener('input', function () {
            const query = input.value.trim();
            clearTimeout(debounceTimer);

            if (query.length < 1) {
                hideDropdown();
                return;
            }

            debounceTimer = setTimeout(() => {
                fetchSuggestions(query);
            }, 200);
        });

        input.addEventListener('focus', function () {
            if (input.value.trim().length >= 1 && dropdown.innerHTML.trim().length > 0) {
                dropdown.style.display = 'block';
            }
        });

        // Keyboard navigation
        input.addEventListener('keydown', function (e) {
            const items = dropdown.querySelectorAll('.suggest-item');
            if (!items.length || dropdown.style.display === 'none') return;

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                activeIndex = (activeIndex + 1) % items.length;
                updateActiveItem(items);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                activeIndex = (activeIndex - 1 + items.length) % items.length;
                updateActiveItem(items);
            } else if (e.key === 'Enter') {
                if (activeIndex >= 0 && items[activeIndex]) {
                    e.preventDefault();
                    items[activeIndex].click();
                }
            } else if (e.key === 'Escape') {
                hideDropdown();
            }
        });

        function updateActiveItem(items) {
            items.forEach((item, idx) => {
                if (idx === activeIndex) {
                    item.classList.add('active-suggest', 'bg-primary-subtle');
                    item.scrollIntoView({ block: 'nearest' });
                } else {
                    item.classList.remove('active-suggest', 'bg-primary-subtle');
                }
            });
        }

        // Close on click outside
        document.addEventListener('click', function (e) {
            if (!parent.contains(e.target)) {
                hideDropdown();
            }
        });

        function hideDropdown() {
            dropdown.style.display = 'none';
            activeIndex = -1;
        }

        function fetchSuggestions(query) {
            fetch(`/api/search-suggest/?q=${encodeURIComponent(query)}`)
                .then(res => res.json())
                .then(data => {
                    renderDropdown(data.results, query);
                })
                .catch(err => {
                    console.error('Search suggest error:', err);
                });
        }

        function renderDropdown(results, query) {
            const { universities = [], colleges = [], courses = [] } = results;
            const totalMatches = universities.length + colleges.length + courses.length;

            if (totalMatches === 0) {
                dropdown.innerHTML = `
                    <div class="p-3 text-center text-muted small">
                        <i class="bi bi-search text-secondary d-block mb-1 fs-5"></i>
                        No institutes found matching "<strong>${escapeHtml(query)}</strong>"
                    </div>
                `;
                dropdown.style.display = 'block';
                return;
            }

            let html = '';

            // 1. Universities
            if (universities.length > 0) {
                html += `
                    <div class="px-2 pt-2 pb-1 text-uppercase text-secondary fw-bold" style="font-size: 0.72rem; letter-spacing: 0.5px;">
                        <i class="bi bi-mortarboard-fill text-primary me-1"></i>Universities
                    </div>
                `;
                universities.forEach(u => {
                    const logoHtml = u.logo_url 
                        ? `<img src="${u.logo_url}" alt="${escapeHtml(u.name)}" class="rounded-2 border flex-shrink-0" style="width: 28px; height: 28px; object-fit: contain;">`
                        : `<div class="bg-primary text-white rounded-2 d-flex align-items-center justify-content-center fw-bold small flex-shrink-0" style="width: 28px; height: 28px; font-size: 0.75rem;">${escapeHtml(u.name.charAt(0))}</div>`;

                    html += `
                        <a href="${u.url}" class="suggest-item d-flex justify-content-between align-items-center text-decoration-none p-2 rounded-3 text-dark mb-1">
                            <div class="d-flex align-items-center gap-2 overflow-hidden">
                                ${logoHtml}
                                <div class="overflow-hidden">
                                    <div class="fw-semibold small text-truncate" style="max-width: 200px;">${highlightMatch(u.name, query)}</div>
                                    <div class="text-muted" style="font-size: 0.75rem;"><i class="bi bi-geo-alt me-1"></i>${u.city}, ${u.state}</div>
                                </div>
                            </div>
                            <span class="badge bg-warning-subtle text-warning-emphasis rounded-pill small flex-shrink-0">★ ${u.rating}</span>
                        </a>
                    `;
                });
            }

            // 2. Colleges & Faculties
            if (colleges.length > 0) {
                html += `
                    <div class="px-2 pt-2 pb-1 text-uppercase text-secondary fw-bold mt-1 border-top" style="font-size: 0.72rem; letter-spacing: 0.5px;">
                        <i class="bi bi-building text-info me-1"></i>Colleges & Campuses
                    </div>
                `;
                colleges.forEach(c => {
                    const logoHtml = c.logo_url 
                        ? `<img src="${c.logo_url}" alt="${escapeHtml(c.name)}" class="rounded-2 border flex-shrink-0" style="width: 32px; height: 32px; object-fit: contain;">`
                        : `<div class="bg-primary text-white rounded-2 d-flex align-items-center justify-content-center fw-bold small flex-shrink-0" style="width: 32px; height: 32px; font-size: 0.8rem;">${escapeHtml(c.name.charAt(0))}</div>`;

                    const registeredBadge = c.is_registered 
                        ? `<span class="badge bg-success-subtle text-success border border-success-subtle rounded-pill py-0 px-1" style="font-size: 0.65rem;"><i class="bi bi-patch-check-fill me-1"></i>Open</span>`
                        : `<span class="badge bg-light text-muted border rounded-pill py-0 px-1" style="font-size: 0.65rem;">Directory</span>`;

                    html += `
                        <a href="${c.url}" class="suggest-item d-flex justify-content-between align-items-center text-decoration-none p-2 rounded-3 text-dark mb-1">
                            <div class="d-flex align-items-center gap-2 overflow-hidden">
                                ${logoHtml}
                                <div class="overflow-hidden">
                                    <div class="d-flex align-items-center gap-1">
                                        <span class="fw-semibold small text-truncate" style="max-width: 175px;">${highlightMatch(c.name, query)}</span>
                                        ${registeredBadge}
                                    </div>
                                    <div class="text-muted" style="font-size: 0.72rem;">${escapeHtml(c.university)} &bull; ${escapeHtml(c.city)}</div>
                                </div>
                            </div>
                            <div class="text-end flex-shrink-0">
                                <span class="badge bg-primary-subtle text-primary rounded-pill small">₹${c.fees}</span>
                            </div>
                        </a>
                    `;
                });
            }

            // 3. Academic Courses
            if (courses.length > 0) {
                html += `
                    <div class="px-2 pt-2 pb-1 text-uppercase text-secondary fw-bold mt-1 border-top" style="font-size: 0.72rem; letter-spacing: 0.5px;">
                        <i class="bi bi-journal-bookmark text-success me-1"></i>Academic Courses
                    </div>
                `;
                courses.forEach(cr => {
                    html += `
                        <a href="${cr.url}" class="suggest-item d-flex justify-content-between align-items-center text-decoration-none p-2 rounded-3 text-dark mb-1">
                            <span class="small fw-medium">${highlightMatch(cr.name, query)}</span>
                            <span class="text-muted small"><i class="bi bi-arrow-right-short fs-5"></i></span>
                        </a>
                    `;
                });
            }

            // Bottom prompt
            html += `
                <div class="pt-2 mt-1 border-top text-center">
                    <a href="/colleges/?search=${encodeURIComponent(query)}" class="small text-primary text-decoration-none fw-semibold">
                        Press Enter to see all results for "${escapeHtml(query)}" &rarr;
                    </a>
                </div>
            `;

            dropdown.innerHTML = html;
            dropdown.style.display = 'block';
            activeIndex = -1;
        }

        function highlightMatch(text, query) {
            if (!query) return escapeHtml(text);
            const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
            return escapeHtml(text).replace(regex, '<span class="text-primary fw-bold">$1</span>');
        }

        function escapeHtml(string) {
            return String(string)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#039;');
        }
    }
});
