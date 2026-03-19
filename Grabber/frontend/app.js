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

// Fix #2: XSS sanitizer — use for all user-facing text in innerHTML
function sanitize(str) {
    const d = document.createElement('div');
    d.textContent = str ?? '';
    return d.innerHTML;
}

// Harem logic now integrated into main container scroll
function safeImg(url) {
    if (!url || url === 'undefined' || url === 'null') return `url('${DEFAULT_AVATAR}')`;
    // Returns a multiple-background shorthand where the primary URL is tried first, 
    // and the default avatar is the local fallback.
    return `url('${url}'), url('${DEFAULT_AVATAR}')`;
}

function handleImgError(el) {
    el.onerror = null; // Prevent infinite loop
    el.src = DEFAULT_AVATAR;
    el.parentElement.classList.remove('skeleton');
}

// DOM Elements
const pages = ['profile', 'gallery', 'quests', 'leaderboard'];
const containers = {
    profile: document.getElementById('page-profile'),
    gallery: document.getElementById('page-gallery'),
    quests: document.getElementById('page-quests'),
    leaderboard: document.getElementById('page-leaderboard'),
    shop: document.getElementById('page-shop')
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
        // Use apiFetch which includes the auth header (B4 fix)
        const rarities = await apiFetch('/rarities');
        if (rarities) {
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
    if (!haremSelect || !gallerySelect) return;

    const options = rarities.map(r => `<option value="${r}">${r}</option>`).join('');
    haremSelect.innerHTML = '<option value="">Rarity (All)</option>' + options;
    gallerySelect.innerHTML = '<option value="">Rarity (All)</option>' + options;
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

async function loadModules() {
    const modules = ['profile', 'gallery', 'quests', 'leaderboard', 'shop'];
    const version = '2.8'; // Cache busting
    
    const loadPromises = modules.map(async (name) => {
        try {
            const response = await fetch(`templates/${name}.html?v=${version}`);
            if (response.ok) {
                return { name, html: await response.text() };
            }
        } catch (e) {
            console.error(`Failed to load module ${name}`, e);
        }
        return { name, html: '' };
    });

    const loaded = await Promise.all(loadPromises);
    loaded.forEach(mod => {
        const container = document.getElementById(`page-${mod.name}`);
        if (container) {
            if (mod.html) {
                container.innerHTML = mod.html;
            } else {
                // Fix #15: Show error instead of silent blank page on template load failure
                container.innerHTML = `<div class="empty-state" style="padding:40px 0">
                    <div class="empty-icon">⚠️</div>
                    <div class="empty-title">Failed to Load</div>
                    <div class="empty-desc">Could not load the ${mod.name} section. Please restart the app.</div>
                </div>`;
            }
        }
    });
}

async function init() {
    // 1. Load HTML Modules first
    document.querySelector('.loading-status').innerText = 'LOADING MODULES...';
    await loadModules();

    // 2. Start loading bot info
    const botPromise = loadBotInfo();

    try {
        // 2. Authenticate
        const userPhoto = tg?.initDataUnsafe?.user?.photo_url || null;
        const storedToken = localStorage.getItem('sessionToken');
        
        const authResponse = await fetch(`${window.API_BASE}/secure_init`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                initData: tg?.initData || null,
                token: storedToken,
                avatar: userPhoto 
            })
        });

        if (authResponse.ok) {
            const authData = await authResponse.json();
            sessionToken = authData.token;
            localStorage.setItem('sessionToken', sessionToken);

            // 4. Setup controls (now that modules are in DOM)
            setupControls();
            
            // 5. Load initial data
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
            // Fix #9: use optional chaining so this doesn't crash outside Telegram
            tg?.showAlert("Authentication failed. Please restart the app.");
        }
    } catch (e) {
        tg?.showAlert("Server connection error: " + e.message);  // Fix #9
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
        const card = e.target.closest('.char-card, .quest-card, .list-item, .tab-item, button, .egg-btn-action, .quest-claim-btn');
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
    // L1 fix: separate debounce timers so harem and gallery don't cancel each other
    let haremSearchTimeout, gallerySearchTimeout;
    const onFilterChange = (type) => {
        if (tg) tg.HapticFeedback.selectionChanged();
        if (type === 'harem') loadHarem(false);
        else loadGallery(false);
    };

    document.getElementById('harem-search').oninput = () => {
        clearTimeout(haremSearchTimeout);
        haremSearchTimeout = setTimeout(() => onFilterChange('harem'), 500);
    };
    document.getElementById('harem-filter-rarity').onchange = () => onFilterChange('harem');

    document.getElementById('gallery-search').oninput = () => {
        clearTimeout(gallerySearchTimeout);
        gallerySearchTimeout = setTimeout(() => onFilterChange('gallery'), 500);
    };
    document.getElementById('gallery-filter-rarity').onchange = () => onFilterChange('gallery');

    // Leaderboard Metric Switcher
    document.getElementById('lb-metric-select').onchange = (e) => loadLeaderboard(e.target.value);
}

// --- Navigation ---

function navigate(pageId) {
    const navPages = ['profile', 'gallery', 'quests', 'leaderboard', 'shop'];
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
        case 'shop': loadShop(); break;
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
    
    // Identity & Avatar
    document.getElementById('user-name').innerText = sanitize(data.first_name || 'User');
    document.getElementById('user-title').innerText = sanitize(data.titles?.current || 'Rookie');
    document.getElementById('user-avatar').style.backgroundImage = safeImg(data.avatar);
    document.getElementById('user-level-badge').innerText = data.stats.level || 1;
    document.getElementById('streak-val').innerText = data.stats.streak || 0;

    // Progression (XP)
    document.getElementById('user-xp-val').innerText = `${data.stats.xp_current.toLocaleString()} / ${data.stats.xp_needed.toLocaleString()} XP`;
    const xpPercent = Math.min(100, (data.stats.xp_current / data.stats.xp_needed) * 100);
    document.getElementById('xp-bar-fill').style.width = `${xpPercent}%`;

    // Stat Strip Tiles — Fix #16: rank now comes from /me directly
    document.getElementById('stat-rank').innerText = data.stats.rank ? `#${data.stats.rank}` : '#?';
    document.getElementById('stat-balance').innerText = data.stats.points.toLocaleString();
    document.getElementById('stat-zenith').innerText = data.stats.zenith.toLocaleString();
    document.getElementById('stat-collection').innerText = data.stats.total_characters.toLocaleString();

    // Specialized Renderers
    if (data.current_pet) renderPet(data.current_pet);
    if (data.eggs) renderEggs(data.eggs);
    if (data.achievements) renderAchievements(data.achievements);
}

function renderAchievements(achievements) {
    const list = document.getElementById('achievements-list');
    if (!achievements || achievements.length === 0) {
        list.innerHTML = '<div style="color:var(--hint-color); font-size:11px; padding:10px;">No achievements yet.</div>';
        return;
    }
    list.innerHTML = achievements.map(ach => `
        <div class="badge-item" title="${sanitize(ach.name)}">
            <div style="font-size:24px">${sanitize(ach.icon || '✦')}</div>
        </div>
    `).join('');
}

function renderPet(pet) {
    const section = document.getElementById('pet-section');
    const container = document.getElementById('active-pet-card');
    if (!pet) {
        section.style.display = 'none';
        return;
    }
    section.style.display = 'block';
    
    // Check if user has other pets to show a switcher
    const hasMorePets = currentUser?.owned_pets?.length > 1;
    
    container.innerHTML = `
        <div class="pet-img-container" style="background-image: url('${pet.img || DEFAULT_AVATAR}')"></div>
        <div class="pet-info-mini">
            <div class="pet-name-line">${sanitize(pet.name)} <span style="font-size:10px; color:var(--hint-color)">Lvl ${pet.level}</span></div>
            <div class="pet-ability-line">✨ ${sanitize(pet.ability)}</div>
            <div class="pet-stats-line">HP: ${pet.hp} | ATK: ${pet.atk} | SPD: ${pet.spd} | Luck: ${Math.round(pet.luck * 100)}%</div>
            <div class="xp-track" style="height:4px; margin-top:8px">
                <div class="xp-fill-glow" style="width:${(pet.xp / pet.xp_needed) * 100}%"></div>
            </div>
            ${hasMorePets ? `<button class="pet-switch-btn" onclick="togglePetList()">SWITCH PET</button>` : ''}
        </div>
    `;

    // Render the hidden pet list for selection
    if (hasMorePets) {
        const listContainer = document.createElement('div');
        listContainer.id = 'owned-pets-list';
        listContainer.className = 'owned-pets-popup hidden';
        listContainer.innerHTML = `
            <div class="popup-header">SELECT PET</div>
            <div class="popup-grid">
                ${currentUser.owned_pets.map(p => `
                    <div class="pet-select-item ${p.is_active ? 'active' : ''}" onclick="switchPet('${p.name}')">
                        <div class="pet-select-img" style="background-image: url('${p.img || DEFAULT_AVATAR}')"></div>
                        <div class="pet-select-name">${p.name}</div>
                    </div>
                `).join('')}
            </div>
        `;
        // Append or replace
        const oldList = document.getElementById('owned-pets-list');
        if (oldList) oldList.remove();
        section.appendChild(listContainer);
    }
}

function togglePetList() {
    const list = document.getElementById('owned-pets-list');
    if (list) {
        list.classList.toggle('hidden');
        if (tg) tg.HapticFeedback.impactOccurred('light');
    }
}

async function switchPet(name) {
    if (tg) {
        tg.HapticFeedback.selectionChanged();
        togglePetList();
    }
    const res = await fetch(`${window.API_BASE}/pets/set_active/${encodeURIComponent(name)}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${sessionToken}` }
    });
    if (res.ok) {
        // Optimistic refresh instead of full profile DOM rebuild
        apiFetch('/me').then(data => {
            if(data) {
                currentUser = data;
                if(data.current_pet) renderPet(data.current_pet);
            }
        });
    }
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
        // Optimistic DOM update
        const item = event?.target?.closest('.egg-item');
        if (item && event.target) {
            event.target.remove();
            item.querySelector('.egg-status-pill').innerText = 'incubating';
        }
    } else {
        if (event && event.target) {
            event.target.classList.remove('loading');
            event.target.disabled = false;
        }
        const err = await res.json();
        tg?.showAlert(err.detail || "Failed to start incubation");
    }
}

async function hatchEgg(eggId, event) {
    if (event && event.target) {
        event.target.classList.add('loading');
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
            // Optimistic: remove egg card, background sync
            const item = event?.target?.closest('.egg-item');
            if (item) item.remove();
            apiFetch('/me').then(d => {
                if(d) {
                    currentUser = d;
                    document.getElementById('stat-zenith').innerText = d.stats.zenith.toLocaleString();
                    document.getElementById('stat-collection').innerText = d.stats.total_characters.toLocaleString();
                }
            });
        } else if (result.status === 'exploded') {
            tg?.showAlert("💥 " + result.message);
            const item = event?.target?.closest('.egg-item');
            if (item) item.remove();
        }
    } else {
        if (event && event.target) {
            event.target.classList.remove('loading');
            event.target.disabled = false;
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
    
    // Fix #2: Sanitize user-facing text from DB to prevent XSS
    const safeName = sanitize(char.name);
    const safeAnime = sanitize(char.anime);
    const safeRarity = sanitize(char.rarity);
    
    return `
        <div class="char-card anim-stagger" style="border-bottom: 2px solid ${rarityColor}; --card-glow: ${glowColor}; animation-delay: ${staggerDelay}s" onclick="showCharDetails('${char.id}')">
            <div class="char-img-wrapper skeleton">
                <img src="${char.img_url}" class="char-img" loading="lazy" 
                     onerror="handleImgError(this)"
                     onload="this.style.opacity=1; this.parentElement.classList.remove('skeleton')">
            </div>
            <span class="rarity-pill" style="background:${rarityColor}">${safeRarity}</span>
            ${isHarem ? `<span class="count-badge">x${char.count}</span>` : ''}
            ${!isHarem && char.owned ? '<span class="count-badge" style="background:var(--button-color); font-size:8px; letter-spacing:0.5px;">COLLECTED</span>' : ''}
            ${!isHarem && !char.owned ? '<div class="lock-overlay"><svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg></div>' : ''}
            <div class="char-info">
                <div class="char-name">${safeName}</div>
                <div style="font-size:9px; color:var(--hint-color)">${safeAnime}</div>
            </div>
        </div>
    `;
}

async function loadQuests() {
    const data = await apiFetch('/quests');
    if (!data) return;

    const renderQuest = (q) => {
        const progress = q.progress || 0;
        const target = q.target || 1;
        const percent = Math.min(100, (progress / target) * 100);
        const isCompleted = progress >= target;
        // Fix #2: sanitize quest text
        const safeName = sanitize(q.name || 'Unknown Quest');
        const safeDesc = sanitize(q.description || 'No description available.');

        return `
            <div class="quest-card ${q.claimed ? 'completed' : ''}">
                <div class="quest-icon">
                    ${sanitize(q.symbol || '✦')}
                </div>
                <div class="quest-details">
                    <div class="quest-title">${safeName}</div>
                    <p class="quest-desc">${safeDesc}</p>
                    
                    <div class="quest-progress-track">
                        <div class="quest-progress-fill" style="width: ${percent}%"></div>
                    </div>
                    
                    <div class="quest-footer">
                        <span class="quest-reward">💰 +${q.reward_xp || 0} XP</span>
                        <span style="color:var(--hint-color)">${progress}/${target}</span>
                    </div>
                </div>
                
                <div class="quest-action">
                    ${isCompleted && !q.claimed ?
                `<button class="quest-claim-btn" onclick="claimQuest('${q.id}', event)">CLAIM</button>` :
                (q.claimed ? '<span class="quest-status-text">DONE ✔</span>' : '')}
                </div>
            </div>
        `;
    };

    const dailyList = document.getElementById('daily-quests-list');
    const weeklyList = document.getElementById('weekly-quests-list');

    if (!data.daily?.length && !data.weekly?.length) {
        // L2 fix: use = instead of += to avoid stacking empty states
        document.getElementById('page-quests').querySelector('.quest-lists-container')?.remove();
        document.getElementById('page-quests').innerHTML += `
             <div class="empty-state">
                <div class="empty-icon">📜</div>
                <div class="empty-title">No Quests</div>
                <div class="empty-desc">Check back later for new missions!</div>
            </div>
        `;
        return;
    }

    dailyList.innerHTML = (data.daily || []).map(renderQuest).join('');
    weeklyList.innerHTML = (data.weekly || []).map(renderQuest).join('');
}

async function claimQuest(qid, event) {
    if (event && event.target) {
        event.target.classList.add('loading');
    }
    const res = await fetch(`${window.API_BASE}/quests/claim/${qid}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${sessionToken}` }
    });
    if (res.ok) {
        tg?.HapticFeedback?.notificationOccurred('success');
        
        // Optimistic DOM update: mark as done without full reload
        if (event && event.target) {
            const btn = event.target;
            const container = btn.closest('.quest-action');
            if (container) container.innerHTML = '<span class="quest-status-text">DONE ✔</span>';
            const card = btn.closest('.quest-card');
            if (card) card.classList.add('completed');
        }

        // Silent background sync
        apiFetch('/me').then(d => {
            if(d) {
                currentUser = d;
                document.getElementById('stat-balance').innerText = d.stats.points.toLocaleString();
                document.getElementById('user-xp-val').innerText = `${d.stats.xp_current.toLocaleString()} / ${d.stats.xp_needed.toLocaleString()} XP`;
                const xpPercent = Math.min(100, (d.stats.xp_current / d.stats.xp_needed) * 100);
                document.getElementById('xp-bar-fill').style.width = `${xpPercent}%`;
                document.getElementById('user-level-badge').innerText = d.stats.level || 1;
            }
        });
    } else {
        if (event && event.target) {
            event.target.classList.remove('loading');
            event.target.disabled = false;
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
            <div class="podium-avatar" style="background-image:${safeImg(user?.avatar)}; background-size:cover"></div>
            <div style="font-size:${rank === 1 ? '14px' : '12px'}; font-weight:${rank === 1 ? 'bold' : 'normal'}">
                ${sanitize(user?.name || 'TBA')}
            </div>
            <div style="font-size:10px; color:var(--button-color)">
                ${metric === 'level' ? `Lvl ${user?.level || 0}` : (user?.value?.toLocaleString() || '0')}
            </div>
        </div>
    `;

    // L3 fix: guard podium rendering for < 3 users
    const p2 = top3.length > 1 ? renderPodiumItem(top3[1], 2) : '';
    const p1 = top3.length > 0 ? renderPodiumItem(top3[0], 1) : '';
    const p3 = top3.length > 2 ? renderPodiumItem(top3[2], 3) : '';
    podiumEl.innerHTML = p2 + p1 + p3;

    list.innerHTML = data.slice(3).map(entry => `
        <div class="list-item">
            <span style="color:var(--hint-color); width:24px; font-size:11px">#${entry.rank}</span>
            <div class="list-item-avatar" style="background-image:${safeImg(entry.avatar)}"></div>
            <span style="flex:1; font-weight:700">${sanitize(entry.name)}</span>
            <span style="font-weight:900; color:var(--button-color)">
                ${metric === 'level' ? `Lvl ${entry.level || 0}` : entry.value.toLocaleString()}
            </span>
        </div>
    `).join('');
}

// Fix #5: Removed duplicate updateBackButton definition that was here (lines 718-725)
// The canonical definition is above in setupControls section.

// --- Shop Logic ---

function switchShopTab(tab) {
    document.querySelectorAll('.shop-view').forEach(v => v.classList.remove('active'));
    document.querySelectorAll('.shop-subtab').forEach(t => t.classList.remove('active'));
    
    document.getElementById(`shop-content-${tab}`).classList.add('active');
    const tabs = document.querySelectorAll('.shop-subtab');
    if (tab === 'chars') tabs[0].classList.add('active');
    if (tab === 'pets') tabs[1].classList.add('active');
    if (tab === 'upgrades') tabs[2].classList.add('active');
    
    if (tg) tg.HapticFeedback.selectionChanged();
}

async function loadShop() {
    const hub = await apiFetch('/shop/hub');
    if (!hub) return;
    
    document.getElementById('shop-shards-val').innerText = hub.balance.toLocaleString();
    document.getElementById('shop-zenith-val').innerText = hub.zenith.toLocaleString();
    document.getElementById('shop-rarity-title').innerText = `DAILY STOCK (${hub.characters_rarity.toUpperCase()})`;
    
    // Load sub-sections (can be parallelized)
    loadShopCharacters();
    loadShopPets();
    loadShopPass();
}

async function loadShopCharacters() {
    const chars = await apiFetch('/shop/characters');
    const grid = document.getElementById('shop-chars-grid');
    if (!chars || chars.length === 0) {
        grid.innerHTML = '<div class="empty-state">No stock today.</div>';
        return;
    }
    
    grid.innerHTML = chars.map(char => {
        // Fix #2: sanitize DB text fields
        const safeName = sanitize(char.name);
        const safeAnime = sanitize(char.anime);
        return `
        <div class="char-card shop-item ${char.owned ? 'owned' : ''}">
            <div class="char-img-wrapper" onclick="showCharDetails('${char.id}')">
                <div class="char-img" style="background-image: ${safeImg(char.img_url)}"></div>
                <div class="preview-overlay">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                    PREVIEW
                </div>
            </div>
            
            <div class="char-info">
                <div class="char-name">${safeName}</div>
                <div class="char-anime-sub">${safeAnime}</div>
            </div>

            ${char.owned ? '<div class="owned-overlay">OWNED</div>' : `
                <button class="shop-buy-btn merged-buy" onclick="confirmShopBuy('${char.id}', '${char.name.replace(/'/g, "\\'").replace(/</g, '&lt;')}', ${char.zenith_price || 5}, event)">
                    <span class="buy-price">⧫ ${char.zenith_price || 5}</span>
                    <span class="buy-text">BUY NOW</span>
                </button>
            `}
        </div>
        `;
    }).join('');
}

async function loadShopPets() {
    const data = await apiFetch('/shop/pets');
    const list = document.getElementById('shop-pets-list');
    if (!data) return;
    
    list.innerHTML = data.pets.map((pet, index) => {
        const isOwned = data.owned.includes(pet.name);
        const isLocked = data.current_level < pet.req_level;
        
        return `
            <div class="pet-shop-card ${isOwned ? 'owned' : (isLocked ? 'locked' : '')}">
                <div class="pet-shop-img" style="background-image: url('${pet.img}')"></div>
                <div class="pet-shop-info">
                    <div class="pet-shop-name">${pet.name}</div>
                    <div class="pet-shop-ability">✨ ${pet.ability}</div>
                    <div class="pet-shop-desc">${pet.desc}</div>
                    ${isLocked ? `<div class="unlock-condition">🔒 UNLOCKS AT LEVEL ${pet.req_level}</div>` : ''}
                    <div class="pet-shop-stats">❤️ ${pet.hp} | ⚔️ ${pet.atk} | ⚡ ${pet.spd} | 🍀 ${Math.round(pet.luck*100)}%</div>
                </div>
                <div class="pet-shop-action">
                    ${isOwned ? '<span class="owned-btn">OWNED</span>' : 
                      (isLocked ? `<span class="locked-btn">LOCKED</span>` : 
                      `<button class="buy-btn" onclick="buyPet(${index}, '${pet.name.replace(/'/g, "\\'")}', ${pet.zenith_price})">⧫ ${pet.zenith_price}</button>`)}
                </div>
            </div>
        `;
    }).join('');
}

async function loadShopPass() {
    const data = await apiFetch('/shop/battlepass');
    const container = document.getElementById('shop-pass-container');
    if (!data) return;
    
    const renderCard = (tier, price, color) => `
        <div class="pass-upgrade-card ${data.current_tier === tier ? 'active' : ''}" style="border-left: 4px solid ${color}">
            <div class="pass-info">
                <div class="pass-tier-name">${tier.toUpperCase()} PASS</div>
                <div class="pass-tier-status">${data.current_tier === tier ? 'CURRENTLY ACTIVE' : 'UPGRADE AVAILABLE'}</div>
            </div>
            <div class="pass-action">
                ${data.current_tier === tier ? '✅' : 
                  (data.current_tier === 'premium' && tier === 'premium' ? '✅' : 
                  `<button class="buy-btn" onclick="upgradePass('${tier}', ${price})">⧫ ${price}</button>`)}
            </div>
        </div>
    `;

    container.innerHTML = `
        ${renderCard('premium', data.prices.premium, '#ffd700')}
        ${renderCard('elite', data.prices.elite, '#00f2ff')}
    `;
}

// --- Purchase Logic ---

// Fix #18: Added event param so the button can be disabled during the async confirm flow
async function confirmShopBuy(charId, name, price, event) {
    const btn = event?.target?.closest('button');
    if (btn) btn.disabled = true;
    if (tg) tg.showConfirm(`Buy ${name} for ${price} Zenith?`, async (ok) => {
        if (ok) {
            const res = await fetch(`${window.API_BASE}/shop/buy/character/${charId}`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${sessionToken}` }
            });
            if (res.ok) {
                tg.HapticFeedback.notificationOccurred('success');
                tg.showAlert(`Successfully purchased ${name}!`);
                loadShop(); // Need to update shop grid to say 'OWNED'
                
                // Optimistic currency update
                if (currentUser && currentUser.stats) {
                    currentUser.stats.zenith -= price;
                    document.getElementById('stat-zenith').innerText = currentUser.stats.zenith.toLocaleString();
                }
            } else {
                if (btn) btn.disabled = false;
                const err = await res.json();
                tg.showAlert(err.detail || "Purchase failed.");
            }
        } else {
            if (btn) btn.disabled = false;
        }
    });
}

async function buyPet(index, name, price) {
    if (tg) tg.showConfirm(`Purchase ${name} for ${price} Zenith?`, async (ok) => {
        if (ok) {
            const res = await fetch(`${window.API_BASE}/shop/buy/pet/${index}`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${sessionToken}` }
            });
            if (res.ok) {
                tg.HapticFeedback.notificationOccurred('success');
                tg.showAlert(`Successfully purchased ${name}!`);
                loadShopPets();
                
                // Optimistic currency update
                if (currentUser && currentUser.stats) {
                    currentUser.stats.zenith -= price;
                    document.getElementById('stat-zenith').innerText = currentUser.stats.zenith.toLocaleString();
                }
            } else {
                const err = await res.json();
                tg.showAlert(err.detail || "Purchase failed.");
            }
        }
    });
}

async function upgradePass(tier, price) {
    if (tg) tg.showConfirm(`Upgrade to ${tier.toUpperCase()} Pass for ${price} Zenith?`, async (ok) => {
        if (ok) {
            const res = await fetch(`${window.API_BASE}/shop/upgrade_pass/${tier}`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${sessionToken}` }
            });
            if (res.ok) {
                tg.HapticFeedback.notificationOccurred('success');
                tg.showAlert(`Battle Pass upgraded to ${tier.toUpperCase()}!`);
                loadShopPass();
                
                // Optimistic currency update
                if (currentUser && currentUser.stats) {
                    currentUser.stats.zenith -= price;
                    document.getElementById('stat-zenith').innerText = currentUser.stats.zenith.toLocaleString();
                }
            } else {
                const err = await res.json();
                tg.showAlert(err.detail || "Upgrade failed.");
            }
        }
    });
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
        // Fix #3/#7: Pass Authorization header so character endpoint is properly authenticated
        const response = await fetch(`${window.API_BASE}/character/${charId}`, {
            headers: { 'Authorization': `Bearer ${sessionToken}` }
        });
        if (response.ok) {
            const char = await response.json();
            document.getElementById('modal-char-name').innerText = sanitize(char.name);
            document.getElementById('modal-char-anime').innerText = sanitize(char.anime);
            document.getElementById('modal-char-rarity').innerText = sanitize(char.rarity);
            document.getElementById('modal-char-img').style.backgroundImage = safeImg(char.img_url);
            document.getElementById('modal-char-id').innerText = `ID: ${sanitize(char.id)}`;
        }
    } catch (e) {
        console.error("Error loading character details", e);
        closeModal();
    }
}

function closeModal(e) {
    // Prevent closing if we clicked inside the content, UNLESS it's the close button
    if (e && e.target && e.target !== modal && !e.target.classList.contains('modal-close-btn') && e.type !== 'touchend') return;
    
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
