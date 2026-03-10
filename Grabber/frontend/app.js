const tg = window.Telegram?.WebApp;

// Global Error Handler for Android Debugging
window.onerror = function (msg, url, lineNo, columnNo, error) {
    const string = msg.toLowerCase();
    const substring = "script error";
    if (string.indexOf(substring) > -1) {
        tg?.showAlert('Script Error: See Browser Console for Detail');
    } else {
        const message = [
            'Message: ' + msg,
            'URL: ' + url,
            'Line: ' + lineNo,
            'Column: ' + columnNo,
            'Error object: ' + JSON.stringify(error)
        ].join(' - ');
        tg?.showAlert(message);
    }
    return false;
};

if (tg) {
    tg.expand();
    tg.ready();
}

let sessionToken = null;
let currentUser = null;

let haremPage = 1, galleryPage = 1;
let haremLoading = false, galleryLoading = false;
let haremHasMore = true, galleryHasMore = true;

// DOM Elements
const pages = ['profile', 'harem', 'gallery', 'quests', 'leaderboard'];
const containers = {
    profile: document.getElementById('page-profile'),
    harem: document.getElementById('page-harem'),
    gallery: document.getElementById('page-gallery'),
    quests: document.getElementById('page-quests'),
    leaderboard: document.getElementById('page-leaderboard')
};

// --- Initialization ---

async function init() {
    try {
        const response = await fetch('/api/v1_7b82/secure_init', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ initData: tg.initData })
        });

        if (response.ok) {
            const data = await response.json();
            sessionToken = data.token;
            refreshData('profile');
            setupControls();

            // Hide loading screen
            setTimeout(() => {
                document.getElementById('loading-overlay').classList.add('hidden');
            }, 500);
        } else {
            tg.showAlert("Auth failed. Please restart.");
        }
    } catch (e) {
        tg.showAlert("Server connection error: " + e.message);
    }
}

function setupControls() {
    // Back Button Global Listener
    if (tg && tg.BackButton) {
        tg.BackButton.onClick(() => {
            if (tg) tg.HapticFeedback.impactOccurred('light');
            navigate('profile');
        });
    }

    // Glass Card Interaction (Haptics)
    document.getElementById('app-container').addEventListener('click', (e) => {
        const card = e.target.closest('.char-card, .quest-card, .list-item');
        if (card && tg) {
            tg.HapticFeedback.impactOccurred('light');
        }
    });

    // Scroll Listeners
    document.getElementById('harem-scroll-container').onscroll = (e) => {
        const { scrollTop, scrollHeight, clientHeight } = e.target;
        if (scrollHeight - scrollTop <= clientHeight + 100) loadHarem(true);
    };
    document.getElementById('gallery-scroll-container').onscroll = (e) => {
        const { scrollTop, scrollHeight, clientHeight } = e.target;
        if (scrollHeight - scrollTop <= clientHeight + 100) loadGallery(true);
    };

    // Filter Listeners (with debounce for search)
    let searchTimeout;
    const onFilterChange = (type) => {
        if (tg) tg.HapticFeedback.selectionChanged();
        if (type === 'harem') loadHarem(false);
        else loadGallery(false);
    };

    document.getElementById('harem-search').oninput = () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => onFilterChange('harem'), 500);
    };
    document.getElementById('harem-filter-rarity').onchange = () => onFilterChange('harem');

    document.getElementById('gallery-search').oninput = () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => onFilterChange('gallery'), 500);
    };
    document.getElementById('gallery-filter-rarity').onchange = () => onFilterChange('gallery');

    // Leaderboard Metric Switcher
    document.getElementById('lb-metric-select').onchange = (e) => loadLeaderboard(e.target.value);
}

// --- Navigation ---

function navigate(pageId) {
    document.querySelectorAll('.tab-item').forEach((item, idx) => {
        const pages = ['profile', 'harem', 'gallery', 'quests', 'leaderboard'];
        item.classList.toggle('active', pages[idx] === pageId);
    });

    document.querySelectorAll('.page').forEach(el => {
        el.classList.toggle('active', el.id === `page-${pageId}`);
    });

    refreshData(pageId);
    updateBackButton(pageId);
    if (tg) tg.HapticFeedback.impactOccurred('light');
}

function updateBackButton(pageId) {
    if (!tg) return;
    if (pageId === 'profile') {
        tg.BackButton.hide();
    } else {
        tg.BackButton.show();
    }
}

function refreshData(pageId) {
    if (!sessionToken) return;
    switch (pageId) {
        case 'profile': loadProfile(); break;
        case 'harem': loadHarem(false); break;
        case 'gallery': loadGallery(false); break;
        case 'quests': loadQuests(); break;
        case 'leaderboard': loadLeaderboard(); break;
    }
}

// --- Data Fetching & Rendering ---

async function apiFetch(endpoint) {
    const res = await fetch(`/api/v1_7b82${endpoint}`, {
        headers: { 'Authorization': `Bearer ${sessionToken}` }
    });
    if (res.status === 401) { init(); return null; }
    return res.ok ? await res.json() : null;
}

async function loadProfile() {
    const data = await apiFetch('/me');
    if (!data) return;

    currentUser = data;
    document.getElementById('user-name').innerText = data.first_name;
    document.getElementById('user-title').innerText = data.titles.current;
    document.getElementById('user-avatar').style.backgroundImage = `url('${data.avatar || 'https://files.catbox.moe/2hsawz.jpg'}')`;

    // Level & XP
    document.getElementById('user-level-badge').innerText = data.stats.level || 1;
    document.getElementById('user-xp-val').innerText = `${data.stats.xp_current.toLocaleString()} / ${data.stats.xp_needed.toLocaleString()}`;
    const xpPercent = Math.min(100, (data.stats.xp_current / data.stats.xp_needed) * 100);
    document.getElementById('xp-bar-fill').style.width = `${xpPercent}%`;

    // Luxury Stats
    document.getElementById('streak-val').innerText = data.stats.streak || 0;
    document.getElementById('stat-rank').innerText = `#${data.stats.rank || '?'}`;
    document.getElementById('stat-balance').innerText = data.stats.points.toLocaleString();
    document.getElementById('stat-zenith').innerText = data.stats.zenith.toLocaleString();
    document.getElementById('stat-collection').innerText = data.stats.total_characters.toLocaleString();

    // Badges/Achievements
    const badgeList = document.getElementById('achievements-list');
    if (data.achievements && data.achievements.length > 0) {
        badgeList.innerHTML = data.achievements.map(ach => `
            <div class="badge-item" title="${ach.name}">
                ${ach.icon || '🏅'}
            </div>
        `).join('');
    } else {
        badgeList.innerHTML = '<div style="color:var(--hint-color); font-size:12px; padding:10px">No badges yet.</div>';
    }
}

async function loadHarem(append = false) {
    if (haremLoading || (append && !haremHasMore)) return;
    if (!append) { haremPage = 1; haremHasMore = true; }

    haremLoading = true;
    const loader = document.getElementById('harem-loading');
    loader.style.display = 'block';

    const search = document.getElementById('harem-search').value;
    const rarity = document.getElementById('harem-filter-rarity').value;

    const data = await apiFetch(`/harem?page=${haremPage}&search=${search}&rarity=${rarity}`);
    haremLoading = false;
    loader.style.display = 'none';

    if (!data) return;

    const grid = document.getElementById('harem-grid');
    const html = data.items.map(char => renderCharCard(char, true)).join('');

    if (append) grid.innerHTML += html;
    else grid.innerHTML = html;

    haremHasMore = data.items.length === 20;
    if (haremHasMore) haremPage++;
}

async function loadGallery(append = false) {
    if (galleryLoading || (append && !galleryHasMore)) return;
    if (!append) { galleryPage = 1; galleryHasMore = true; }

    galleryLoading = true;
    const loader = document.getElementById('gallery-loading');
    loader.style.display = 'block';

    const search = document.getElementById('gallery-search').value;
    const rarity = document.getElementById('gallery-filter-rarity').value;

    const data = await apiFetch(`/gallery?page=${galleryPage}&search=${search}&rarity=${rarity}`);
    galleryLoading = false;
    loader.style.display = 'none';

    if (!data) return;

    const grid = document.getElementById('gallery-grid');
    const html = data.items.map(char => renderCharCard(char, false)).join('');

    if (append) grid.innerHTML += html;
    else grid.innerHTML = html;

    galleryHasMore = data.items.length === 24;
    if (galleryHasMore) galleryPage++;
}

function renderCharCard(char, isHarem) {
    const rarityColor = `var(--rarity-${char.rarity.toLowerCase()})`;
    return `
        <div class="char-card" style="border-bottom: 2px solid ${rarityColor}">
            <img src="${char.img_url}" class="char-img" loading="lazy">
            <span class="rarity-pill" style="background:${rarityColor}">${char.rarity}</span>
            ${isHarem ? `<span class="count-badge">x${char.count}</span>` : ''}
            ${!isHarem && char.owned ? '<span class="count-badge" style="background:var(--button-color)">Owned</span>' : ''}
            <div class="char-info">
                <div class="char-name">${char.name}</div>
                <div style="font-size:9px; color:var(--hint-color)">${char.anime}</div>
            </div>
        </div>
    `;
}

async function loadQuests() {
    const data = await apiFetch('/quests');
    if (!data) return;
    const renderQuest = (q) => `
        <div class="quest-card">
            <div class="quest-icon">${q.icon || '❔'}</div>
            <div class="quest-details">
                <div class="quest-title">${q.name || 'Unknown Quest'}</div>
                <div class="quest-desc">${q.description || 'No description available.'}</div>
                <div style="font-size:10px; color:var(--button-color); margin-top:4px">
                    ${q.progress || 0}/${q.target || 1} | +${q.reward_xp || 0} XP
                </div>
            </div>
            ${(q.progress || 0) >= (q.target || 1) && !q.claimed ?
            `<button onclick="claimQuest('${q.id}')" style="width:auto; padding:6px 12px; margin:0">Claim</button>` :
            (q.claimed ? '✅' : '')}
        </div>
    `;

    document.getElementById('daily-quests-list').innerHTML = '<h4>Daily</h4>' + (data.daily || []).map(renderQuest).join('');
    document.getElementById('weekly-quests-list').innerHTML = '<h4>Weekly</h4>' + (data.weekly || []).map(renderQuest).join('');
}

async function claimQuest(qid) {
    const res = await fetch(`/api/v1_7b82/quests/claim/${qid}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${sessionToken}` }
    });
    if (res.ok) {
        tg.HapticFeedback.notificationOccurred('success');
        loadQuests();
        loadProfile();
    }
}

async function loadLeaderboard(metric = 'level') {
    const data = await apiFetch(`/leaderboard?metric=${metric}`);
    const list = document.getElementById('leaderboard-list');
    const podiumEl = document.getElementById('leaderboard-podium');

    if (!data || data.length === 0) {
        podiumEl.innerHTML = '';
        list.innerHTML = '<div style="text-align:center; padding:20px; color:var(--hint-color)">No rankings available yet.</div>';
        return;
    }

    // Top 3 for Podium
    const top3 = data.slice(0, 3);
    const renderPodiumItem = (user, rank) => `
        <div class="podium-item rank-${rank}">
            <div class="podium-avatar" style="background-image:url('${user?.avatar || 'https://files.catbox.moe/2hsawz.jpg'}'); background-size:cover"></div>
            <div style="font-size:${rank === 1 ? '14px' : '12px'}; font-weight:${rank === 1 ? 'bold' : 'normal'}">
                ${user?.name || 'TBA'}
            </div>
            <div style="font-size:10px; color:var(--button-color)">
                ${metric === 'level' ? `Lvl ${user?.level || 0}` : (user?.value?.toLocaleString() || '0')}
            </div>
        </div>
    `;

    podiumEl.innerHTML = renderPodiumItem(top3[1], 2) + renderPodiumItem(top3[0], 1) + renderPodiumItem(top3[2], 3);

    list.innerHTML = data.slice(3).map(entry => `
        <div class="list-item">
            <span style="color:var(--hint-color); width:24px; font-size:11px">#${entry.rank}</span>
            <div class="list-item-avatar" style="background-image:url('${entry.avatar || 'https://files.catbox.moe/2hsawz.jpg'}')"></div>
            <span style="flex:1; font-weight:700">${entry.name}</span>
            <span style="font-weight:900; color:var(--button-color)">
                ${metric === 'level' ? `Lvl ${entry.level || 0}` : entry.value.toLocaleString()}
            </span>
        </div>
    `).join('');
}

function updateBackButton(pageId) {
    if (!tg) return;
    if (pageId === 'profile') {
        tg.BackButton.hide();
    } else {
        tg.BackButton.show();
    }
}

// Start
if (typeof tg !== 'undefined') {
    init();
} else {
    console.error("Telegram WebApp script not loaded");
}
