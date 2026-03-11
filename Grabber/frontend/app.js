window.API_BASE = '/api/v1_7b82';
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
let DEFAULT_AVATAR = 'https://files.catbox.moe/2hsawz.jpg';

let haremPage = 1, galleryPage = 1;
let haremLoading = false, galleryLoading = false;
let haremHasMore = true, galleryHasMore = true;

// Harem logic now integrated into main container scroll

// DOM Elements
const pages = ['profile', 'gallery', 'quests', 'leaderboard'];
const containers = {
    profile: document.getElementById('page-profile'),
    gallery: document.getElementById('page-gallery'),
    quests: document.getElementById('page-quests'),
    leaderboard: document.getElementById('page-leaderboard')
};

const modal = document.getElementById('char-detail-modal');

// --- Initialization ---

async function fetchRarities() {
    const cached = sessionStorage.getItem('rarities');
    if (cached) {
        populateRaritySelects(JSON.parse(cached));
        return;
    }
    try {
        const response = await fetch(`${window.API_BASE}/rarities`);
        if (response.ok) {
            const rarities = await response.json();
            sessionStorage.setItem('rarities', JSON.stringify(rarities));
            populateRaritySelects(rarities);
        }
    } catch (e) {
        console.error("Failed to fetch rarities", e);
    }
}

function populateRaritySelects(rarities) {
    const haremSelect = document.getElementById('harem-filter-rarity');
    const gallerySelect = document.getElementById('gallery-filter-rarity');
    const options = rarities.map(r => `<option value="${r}">${r}</option>`).join('');
    haremSelect.innerHTML = '<option value="">All Rarities</option>' + options;
    gallerySelect.innerHTML = '<option value="">All Rarities</option>' + options;
}

async function loadBotInfo() {
    const cached = sessionStorage.getItem('botInfo');
    if (cached) return JSON.parse(cached);
    try {
        const response = await fetch(`${window.API_BASE}/bot/info`);
        if (response.ok) {
            const bot = await response.json();
            sessionStorage.setItem('botInfo', JSON.stringify(bot));
            return bot;
        }
    } catch (e) {
        console.warn("Could not fetch bot info", e);
    }
    return null;
}

async function init() {
    // 1. Start loading bot info immediately
    const botPromise = loadBotInfo();

    try {
        // 2. Authenticate
        const authResponse = await fetch(`${window.API_BASE}/secure_init`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ initData: tg.initData })
        });

        if (authResponse.ok) {
            const authData = await authResponse.json();
            sessionToken = authData.token;

            // 3. Setup and load initial data
            setupControls();
            fetchRarities();
            document.querySelector('.loading-status').innerText = 'LOADING PROFILE...';
            await loadProfile();
            await loadHarem(false);

            // 4. Finalize
            const bot = await botPromise; 
            if (bot) {
                document.getElementById('loading-bot-name').innerText = bot.name;
                if (bot.avatar) {
                    document.getElementById('loading-logo').style.backgroundImage = `url('${bot.avatar}')`;
                    DEFAULT_AVATAR = bot.avatar;
                }
            }
            
            // Set Telegram Header Color to match the app's dark theme
            if (tg && tg.setHeaderColor) {
                try {
                    tg.setHeaderColor(tg.themeParams.bg_color || '#1c1c1d');
                    tg.setBackgroundColor(tg.themeParams.bg_color || '#1c1c1d');
                } catch(e) { }
            }
            document.querySelector('.loading-status').innerText = 'READY!';

            setTimeout(() => {
                document.getElementById('loading-overlay').classList.add('hidden');
                document.getElementById('app-container').style.opacity = '1';
            }, 800);
        } else {
            tg.showAlert("Authentication failed. Please restart the app.");
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
    window.onscroll = (e) => {
        // Handle infinite scroll for the profile (harem) and others if they use window scroll
        const { scrollTop, scrollHeight, clientHeight } = document.documentElement;
        const activePage = document.querySelector('.page.active').id;
        
        if (scrollHeight - scrollTop <= clientHeight + 100) {
            if (activePage === 'page-profile') loadHarem(true);
            if (activePage === 'page-gallery') loadGallery(true);
        }
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
    const navPages = ['profile', 'gallery', 'quests', 'leaderboard'];
    document.querySelectorAll('.tab-item').forEach((item, idx) => {
        item.classList.toggle('active', navPages[idx] === pageId);
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
        case 'profile': 
            loadProfile(); 
            loadHarem(false);
            break;
        case 'gallery': loadGallery(false); break;
        case 'quests': loadQuests(); break;
        case 'leaderboard': loadLeaderboard(); break;
    }
}

// --- Data Fetching & Rendering ---

async function apiFetch(endpoint) {
    const res = await fetch(`${window.API_BASE}${endpoint}`, {
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
    document.getElementById('user-avatar').style.backgroundImage = `url('${data.avatar || DEFAULT_AVATAR}')`;

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
                <span class="professional-badge">${ach.icon || '✦'}</span>
            </div>
        `).join('');
    } else {
        badgeList.innerHTML = '<div style="color:var(--hint-color); font-size:12px; padding:10px; font-weight:500;">No achievements earned.</div>';
    }

    // Render Pet & Eggs
    renderPet(data.current_pet);
    renderEggs(data.eggs);
}

function renderPet(pet) {
    const section = document.getElementById('pet-section');
    const container = document.getElementById('active-pet-card');
    if (!pet) {
        section.style.display = 'none';
        return;
    }
    section.style.display = 'block';
    container.innerHTML = `
        <div class="pet-img-container" style="background-image: url('${pet.img || DEFAULT_AVATAR}')"></div>
        <div class="pet-info-mini">
            <div class="pet-name-line">${pet.name} <span style="font-size:10px; color:var(--hint-color)">Lvl ${pet.level}</span></div>
            <div class="pet-ability-line">✨ ${pet.ability}</div>
            <div class="pet-stats-line">HP: ${pet.hp} | ATK: ${pet.atk} | SPD: ${pet.spd} | Luck: ${Math.round(pet.luck * 100)}%</div>
            <div class="xp-track" style="height:4px; margin-top:8px">
                <div class="xp-fill-glow" style="width:${(pet.xp / pet.xp_needed) * 100}%"></div>
            </div>
        </div>
    `;
}

function renderEggs(eggs) {
    const section = document.getElementById('eggs-section');
    const list = document.getElementById('eggs-list');
    if (!eggs || eggs.length === 0) {
        section.style.display = 'none';
        return;
    }
    section.style.display = 'block';
    list.innerHTML = eggs.map(egg => `
        <div class="egg-item">
            <div class="egg-icon-large">🥚</div>
            <div class="egg-name-tiny">${egg.name}</div>
            <div class="egg-status-pill">${egg.status}</div>
            ${egg.status === 'fresh' ? `
                <button class="egg-btn-action" onclick="incubateEgg('${egg.id}', event)">Incubate</button>
            ` : ''}
            ${egg.status === 'incubating' && egg.remaining_mins <= 0 ? `
                <button class="egg-btn-action" style="background:var(--success-color)" onclick="hatchEgg('${egg.id}', event)">Hatch!</button>
            ` : ''}
            ${egg.status === 'incubating' && egg.remaining_mins > 0 ? `
                <div style="font-size:9px; margin-top:8px; color:var(--button-color)">${egg.remaining_mins}m left</div>
            ` : ''}
        </div>
    `).join('');
}

async function incubateEgg(eggId, event) {
    if (event && event.target) {
        event.target.disabled = true;
        event.target.innerText = "Processing...";
    }
    if (tg) tg.HapticFeedback.impactOccurred('medium');
    const res = await fetch(`${window.API_BASE}/eggs/incubate/${eggId}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${sessionToken}` }
    });
    if (res.ok) {
        tg?.showAlert("Incubation started!");
        loadProfile();
    } else {
        if (event && event.target) {
            event.target.disabled = false;
            event.target.innerText = "Incubate";
        }
        const err = await res.json();
        tg?.showAlert(err.detail || "Failed to start incubation");
    }
}

async function hatchEgg(eggId, event) {
    if (event && event.target) {
        event.target.disabled = true;
        event.target.innerText = "Hatching...";
    }
    if (tg) tg.HapticFeedback.notificationOccurred('success');
    const res = await fetch(`${window.API_BASE}/eggs/hatch/${eggId}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${sessionToken}` }
    });
    if (res.ok) {
        const result = await res.json();
        if (result.status === 'success') {
            showCharDetails(result.character.id);
            loadProfile();
            loadHarem(false);
        } else if (result.status === 'exploded') {
            tg?.showAlert("💥 " + result.message);
            loadProfile();
        }
    } else {
        if (event && event.target) {
            event.target.disabled = false;
            event.target.innerText = "Hatch!";
        }
        const err = await res.json();
        tg?.showAlert(err.detail || "Failed to hatch egg");
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

    const data = await apiFetch(`/harem?page=${haremPage}&search=${encodeURIComponent(search)}&rarity=${encodeURIComponent(rarity)}`);
    haremLoading = false;
    loader.style.display = 'none';

    if (!data) return;

    const grid = document.getElementById('harem-grid');
    if (!append && data.items.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📇</div>
                <div class="empty-title">Collection Empty</div>
                <div class="empty-desc">You haven't captured any characters yet that match your search.</div>
            </div>
        `;
        return;
    }


    const html = data.items.map((char, index) => renderCharCard(char, true, index)).join('');

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

    const data = await apiFetch(`/gallery?page=${galleryPage}&search=${encodeURIComponent(search)}&rarity=${encodeURIComponent(rarity)}`);
    galleryLoading = false;
    loader.style.display = 'none';

    if (!data) return;

    const grid = document.getElementById('gallery-grid');
    if (!append && data.items.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🖼️</div>
                <div class="empty-title">Gallery Empty</div>
                <div class="empty-desc">No characters found matching your filters.</div>
            </div>
        `;
        return;
    }

    const html = data.items.map((char, index) => renderCharCard(char, false, index)).join('');

    if (append) grid.innerHTML += html;
    else grid.innerHTML = html;

    galleryHasMore = data.items.length === 24;
    if (galleryHasMore) galleryPage++;
}

function renderCharCard(char, isHarem, index = 0) {
    const rarityColor = `var(--rarity-${char.rarity.toLowerCase()})`;
    const glowColor = `var(--rarity-glow-${char.rarity.toLowerCase()})`;
    // Calculate stagger delay based on index for smooth sequential rendering
    const staggerDelay = (index % 25) * 0.04; 
    
    return `
        <div class="char-card anim-stagger" style="border-bottom: 2px solid ${rarityColor}; --card-glow: ${glowColor}; animation-delay: ${staggerDelay}s" onclick="showCharDetails('${char.id}')">
            <div class="char-img-wrapper skeleton">
                <img src="${char.img_url}" class="char-img" loading="lazy" onload="this.style.opacity=1; this.parentElement.classList.remove('skeleton')">
            </div>
            <span class="rarity-pill" style="background:${rarityColor}">${char.rarity}</span>
            ${isHarem ? `<span class="count-badge">x${char.count}</span>` : ''}
            ${!isHarem && char.owned ? '<span class="count-badge" style="background:var(--button-color); font-size:8px; letter-spacing:0.5px;">COLLECTED</span>' : ''}
            ${!isHarem && !char.owned ? '<div class="lock-overlay"><svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg></div>' : ''}
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
            <div class="quest-icon" style="font-size:24px; color:var(--button-color)">
                ${q.symbol || '✦'}
            </div>
            <div class="quest-details">
                <div class="quest-title">${q.name || 'Unknown Quest'}</div>
                <div class="quest-desc">${q.description || 'No description available.'}</div>
                <div style="font-size:10px; color:var(--button-color); margin-top:4px">
                    ${q.progress || 0}/${q.target || 1} | +${q.reward_xp || 0} XP
                </div>
            </div>
            ${(q.progress || 0) >= (q.target || 1) && !q.claimed ?
            `<button onclick="claimQuest('${q.id}', event)" style="width:auto; padding:6px 12px; margin:0">Claim</button>` :
            (q.claimed ? '<span style="color:var(--success-color)">COMPLETED</span>' : '')}
    `;

    if (!data.daily?.length && !data.weekly?.length) {
        document.getElementById('page-quests').innerHTML += `
             <div class="empty-state">
                <div class="empty-icon">📜</div>
                <div class="empty-title">No Quests</div>
                <div class="empty-desc">Check back later for new missions!</div>
            </div>
        `;
    }

    document.getElementById('daily-quests-list').innerHTML = '<h4>Daily</h4>' + (data.daily || []).map(renderQuest).join('');
    document.getElementById('weekly-quests-list').innerHTML = '<h4>Weekly</h4>' + (data.weekly || []).map(renderQuest).join('');
}

async function claimQuest(qid, event) {
    if (event && event.target) {
        event.target.disabled = true;
        event.target.innerText = "...";
    }
    const res = await fetch(`${window.API_BASE}/quests/claim/${qid}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${sessionToken}` }
    });
    if (res.ok) {
        tg.HapticFeedback.notificationOccurred('success');
        loadQuests();
        loadProfile();
    } else {
        if (event && event.target) {
            event.target.disabled = false;
            event.target.innerText = "Claim";
        }
    }
}

async function loadLeaderboard(metric = 'level') {
    const data = await apiFetch(`/leaderboard?metric=${metric}`);
    const list = document.getElementById('leaderboard-list');
    const podiumEl = document.getElementById('leaderboard-podium');

    if (!data || data.length === 0) {
        podiumEl.innerHTML = '';
        list.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🏆</div>
                <div class="empty-title">No Rankings</div>
                <div class="empty-desc">The leaderboard is currently empty for this metric.</div>
            </div>
        `;
        return;
    }

    // Top 3 for Podium
    const top3 = data.slice(0, 3);
    const renderPodiumItem = (user, rank) => `
        <div class="podium-item rank-${rank}">
            <div class="podium-avatar" style="background-image:url('${user?.avatar || DEFAULT_AVATAR}'); background-size:cover"></div>
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
            <div class="list-item-avatar" style="background-image:url('${entry.avatar || DEFAULT_AVATAR}')"></div>
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

// --- Detail Modal ---

async function showCharDetails(charId) {
    if (tg && tg.HapticFeedback) tg.HapticFeedback.impactOccurred('medium');

    // Show modal
    modal.classList.remove('hidden');
    // Force reflow for CSS animation
    void modal.offsetWidth; 
    modal.classList.add('active');
    
    document.getElementById('modal-char-name').innerText = "Loading...";
    document.getElementById('modal-char-anime').innerText = "";
    document.getElementById('modal-char-rarity').innerText = "???";
    document.getElementById('modal-char-img').style.backgroundImage = 'none';

    try {
        const response = await fetch(`${window.API_BASE}/character/${charId}`);
        if (response.ok) {
            const char = await response.json();
            document.getElementById('modal-char-name').innerText = char.name;
            document.getElementById('modal-char-anime').innerText = char.anime;
            document.getElementById('modal-char-rarity').innerText = char.rarity;
            document.getElementById('modal-char-img').style.backgroundImage = `url('${char.img_url}')`;
            document.getElementById('modal-char-id').innerText = `ID: ${char.id}`;
        }
    } catch (e) {
        console.error("Error loading character details", e);
        closeModal();
    }
}

function closeModal(e) {
    // Prevent closing if we clicked inside the content, UNLESS it's the close button
    if (e && e.target !== modal && !e.target.classList.contains('modal-close-btn') && e.type !== 'touchend') return;
    
    modal.classList.remove('active');
    if (tg && tg.HapticFeedback) tg.HapticFeedback.impactOccurred('light');
    
    setTimeout(() => {
        modal.classList.add('hidden');
    }, 400); // Matches CSS transition time
}

// Swipe-to-Close Gesture Logic for Modal
let touchStartY = 0;
const modalContent = document.querySelector('.modal-content-glass');

modalContent.addEventListener('touchstart', (e) => {
    touchStartY = e.touches[0].clientY;
}, {passive: true});

modalContent.addEventListener('touchmove', (e) => {
    const currentY = e.touches[0].clientY;
    const diff = currentY - touchStartY;
    // Only allow pull-down if scrolled to top
    if (diff > 0 && modalContent.scrollTop <= 0) {
        modalContent.style.transform = `translateY(${diff}px)`;
    }
}, {passive: false});

modalContent.addEventListener('touchend', (e) => {
    const diff = e.changedTouches[0].clientY - touchStartY;
    modalContent.style.transform = ''; // Reset inline transform so CSS takes over
    if (diff > 120 && modalContent.scrollTop <= 0) {
        closeModal({type: 'touchend'});
    }
});

// Start
if (typeof tg !== 'undefined') {
    init();
} else {
    console.error("Telegram WebApp script not loaded");
}
