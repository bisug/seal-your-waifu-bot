const tg = window.Telegram.WebApp;
tg.expand();

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
        const response = await fetch('/api/auth', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ initData: tg.initData })
        });

        if (response.ok) {
            const data = await response.json();
            sessionToken = data.token;
            refreshData('profile');
            setupControls();
        } else {
            tg.showAlert("Auth failed. Please restart.");
        }
    } catch (e) {
        tg.showAlert("Server connection error.");
    }
}

function setupControls() {
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
    const res = await fetch(`/api${endpoint}`, {
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
    document.getElementById('user-xp-val').innerText = `${data.stats.xp_current} / ${data.stats.xp_needed}`;

    const xpPercent = (data.stats.xp_current / data.stats.xp_needed) * 100;
    document.getElementById('xp-bar-fill').style.width = `${xpPercent}%`;

    document.getElementById('stat-rank').innerText = `#${data.stats.rank || '?'}`;
    document.getElementById('stat-balance').innerText = data.stats.points.toLocaleString();
    document.getElementById('stat-zenith').innerText = data.stats.zenith.toLocaleString();
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
    const renderQuest = (q) => `
        <div class="quest-card">
            <div class="quest-icon">${q.icon}</div>
            <div class="quest-details">
                <div class="quest-title">${q.name}</div>
                <div class="quest-desc">${q.description}</div>
                <div style="font-size:10px; color:var(--button-color); margin-top:4px">
                    ${q.progress}/${q.target} | +${q.reward_xp} XP
                </div>
            </div>
            ${q.progress >= q.target && !q.claimed ?
            `<button onclick="claimQuest('${q.id}')" style="width:auto; padding:6px 12px; margin:0">Claim</button>` :
            (q.claimed ? '✅' : '')}
        </div>
    `;

    document.getElementById('daily-quests-list').innerHTML = '<h4>Daily</h4>' + data.daily.map(renderQuest).join('');
    document.getElementById('weekly-quests-list').innerHTML = '<h4>Weekly</h4>' + data.weekly.map(renderQuest).join('');
}

async function claimQuest(qid) {
    const res = await fetch(`/api/quests/claim/${qid}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${sessionToken}` }
    });
    if (res.ok) {
        tg.HapticFeedback.notificationOccurred('success');
        loadQuests();
        loadProfile();
    }
}

async function loadLeaderboard() {
    const data = await apiFetch('/leaderboard?metric=level');
    const list = document.getElementById('leaderboard-list');

    // Top 3 for Podium
    const top3 = data.slice(0, 3);
    const podiumHtml = `
        <div class="podium-item rank-2">
            <div class="podium-avatar" style="background-image:url('${top3[1]?.avatar || ''}'); background-size:cover"></div>
            <div style="font-size:12px">${top3[1]?.name || ''}</div>
        </div>
        <div class="podium-item rank-1">
            <div class="podium-avatar" style="background-image:url('${top3[0]?.avatar || ''}'); background-size:cover"></div>
            <div style="font-size:14px; font-weight:bold">${top3[0]?.name || ''}</div>
        </div>
        <div class="podium-item rank-3">
            <div class="podium-avatar" style="background-image:url('${top3[2]?.avatar || ''}'); background-size:cover"></div>
            <div style="font-size:12px">${top3[2]?.name || ''}</div>
        </div>
    `;
    document.getElementById('leaderboard-podium').innerHTML = podiumHtml;

    list.innerHTML = data.slice(3).map(entry => `
        <div class="list-item">
            <span style="color:var(--hint-color); width:20px">#${entry.rank}</span>
            <span style="flex:1; margin-left:12px">${entry.name}</span>
            <span style="font-weight:bold">Lvl ${entry.level || 0}</span>
        </div>
    `).join('');
}

// Start
init();
