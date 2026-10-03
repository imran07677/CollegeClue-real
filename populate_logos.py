import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'collegeclue.settings')
django.setup()

from core.models import University, College

os.makedirs('media/logos', exist_ok=True)

COLLEGE_THEMES = {
    'svr': {
        'bg1': '#1e3c72', 'bg2': '#2a5298', 'accent': '#ffd700', 'initials': 'SVR',
        'symbol': 'M12 2L2 7l10 5 10-5-10-5zm0 9l-8-4v6l8 4 8-4v-6l-8 4zm0 6l-6-3v2l6 3 6-3v-2l-6 3z'
    },
    'alliance': {
        'bg1': '#8b0000', 'bg2': '#c0392b', 'accent': '#f1c40f', 'initials': 'ALU',
        'symbol': 'M12 3L2 12h3v8h6v-6h2v6h6v-8h3L12 3zm0 3.8l4 3.6v6.6h-2v-6H10v6H8v-6.6l4-3.6z'
    },
    'iit': {
        'bg1': '#0f2027', 'bg2': '#203a43', 'accent': '#00d2ff', 'initials': 'IIT',
        'symbol': 'M12 2a10 10 0 100 20 10 10 0 000-20zm1 14.5h-2v-5h2v5zm0-7h-2V7h2v2.5z'
    },
    'dtu': {
        'bg1': '#134e5e', 'bg2': '#71b280', 'accent': '#ffffff', 'initials': 'DTU',
        'symbol': 'M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 14l-5-5 1.41-1.41L12 14.17l7.59-7.59L21 8l-9 9z'
    },
    'bits': {
        'bg1': '#4b134f', 'bg2': '#c94b4b', 'accent': '#ffb347', 'initials': 'BITS',
        'symbol': 'M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z'
    },
    'iisc': {
        'bg1': '#00467f', 'bg2': '#a5cc82', 'accent': '#ffffff', 'initials': 'IISC',
        'symbol': 'M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zm0 12.5c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z'
    },
    'du': {
        'bg1': '#2c3e50', 'bg2': '#3498db', 'accent': '#e74c3c', 'initials': 'DU',
        'symbol': 'M18 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM9 4h2v5l-1-.75L9 9V4zm9 16H6V4h1v9l3-2.25L13 13V4h5v16z'
    },
    'anna': {
        'bg1': '#d35400', 'bg2': '#e67e22', 'accent': '#f39c12', 'initials': 'ANNA',
        'symbol': 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14.5v-9l6 4.5-6 4.5z'
    },
    'mumbai': {
        'bg1': '#1f4037', 'bg2': '#99f2c8', 'accent': '#0b486b', 'initials': 'UOM',
        'symbol': 'M12 2a10 10 0 100 20 10 10 0 000-20zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z'
    },
    'symbiosis': {
        'bg1': '#4a154b', 'bg2': '#611f69', 'accent': '#ecb22e', 'initials': 'SIU',
        'symbol': 'M12 2L1 21h22L12 2zm0 3.99L19.53 19H4.47L12 5.99zM11 16h2v2h-2zm0-6h2v4h-2z'
    },
    'bangalore': {
        'bg1': '#0052d4', 'bg2': '#4364f7', 'accent': '#6fb1fc', 'initials': 'BCU',
        'symbol': 'M12 3L2 12h3v8h6v-6h2v6h6v-8h3L12 3z'
    },
    'jadavpur': {
        'bg1': '#61045f', 'bg2': '#aa076b', 'accent': '#ffd700', 'initials': 'JU',
        'symbol': 'M12 2L4 5v6.09c0 5.05 3.41 9.76 8 10.91 4.59-1.15 8-5.86 8-10.91V5l-8-3z'
    },
    'mit': {
        'bg1': '#2b5876', 'bg2': '#4e4376', 'accent': '#f64f59', 'initials': 'MIT',
        'symbol': 'M12 2L2 7l10 5 10-5-10-5zm0 9l-8-4v6l8 4 8-4v-6l-8 4z'
    }
}

def generate_svg(theme, title):
    grad_id = 'grad_' + str(abs(hash(title)) % 100000)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="200" height="200">
  <defs>
    <linearGradient id="{grad_id}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{theme['bg1']};stop-opacity:1" />
      <stop offset="100%" style="stop-color:{theme['bg2']};stop-opacity:1" />
    </linearGradient>
    <filter id="shadow_{grad_id}" x="-10%" y="-10%" width="130%" height="130%">
      <feDropShadow dx="0" dy="4" stdDeviation="5" flood-opacity="0.25" />
    </filter>
  </defs>
  <rect width="190" height="190" x="5" y="5" rx="36" fill="url(#{grad_id})" filter="url(#shadow_{grad_id})" />
  <circle cx="100" cy="100" r="76" fill="none" stroke="{theme['accent']}" stroke-width="2.5" stroke-dasharray="6 4" opacity="0.6" />
  <g transform="translate(88, 38) scale(1.1)" fill="{theme['accent']}">
    <path d="{theme['symbol']}" />
  </g>
  <text x="100" y="126" font-family="'Segoe UI', -apple-system, system-ui, sans-serif" font-size="24" font-weight="800" fill="#ffffff" text-anchor="middle" letter-spacing="1.5">{theme['initials']}</text>
  <text x="100" y="152" font-family="'Segoe UI', -apple-system, system-ui, sans-serif" font-size="10" font-weight="600" fill="{theme['accent']}" text-anchor="middle" letter-spacing="1">CAMPUS DIRECTORY</text>
</svg>'''

for col in College.objects.all():
    name_lower = (col.name + ' ' + col.university.name).lower()
    selected_key = 'svr'
    for k in COLLEGE_THEMES:
        if k in name_lower:
            selected_key = k
            break
    theme = COLLEGE_THEMES[selected_key].copy()
    initials = ''.join([w[0] for w in col.name.split() if w[0].isalnum()][:4]).upper()
    if len(initials) >= 2:
        theme['initials'] = initials
    svg_content = generate_svg(theme, col.name)
    fname = f'logos/col_{col.slug}.svg'
    filepath = os.path.join('media', fname)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    col.logo = fname
    col.save(update_fields=['logo'])

for uni in University.objects.all():
    name_lower = uni.name.lower()
    selected_key = 'svr'
    for k in COLLEGE_THEMES:
        if k in name_lower:
            selected_key = k
            break
    theme = COLLEGE_THEMES[selected_key].copy()
    initials = ''.join([w[0] for w in uni.name.split() if w[0].isalnum()][:4]).upper()
    if len(initials) >= 2:
        theme['initials'] = initials
    svg_content = generate_svg(theme, uni.name)
    fname = f'logos/uni_{uni.slug}.svg'
    filepath = os.path.join('media', fname)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    uni.logo = fname
    uni.save(update_fields=['logo'])

print('Successfully generated and assigned logos to all colleges and universities!')
