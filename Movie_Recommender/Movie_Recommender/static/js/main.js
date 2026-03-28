// Netflix-Style JavaScript for MovieFlux

// ============================================
// Utility Functions
// ============================================

function getLikedMovies() {
    try {
        const liked = localStorage.getItem('likedMovies');
        return liked ? JSON.parse(liked) : [];
    } catch (e) {
        return [];
    }
}

function saveLikedMovie(movieTitle) {
    const liked = getLikedMovies();
    if (!liked.includes(movieTitle)) {
        liked.push(movieTitle);
        localStorage.setItem('likedMovies', JSON.stringify(liked));
    }
}

function isMovieLiked(movieTitle) {
    return getLikedMovies().includes(movieTitle);
}

// ============================================
// Watchlist Functions
// ============================================
function toggleWatchlist(movieTitle) {
    const formData = new FormData();
    formData.append('movie_title', movieTitle);

    fetch('/toggle_watchlist', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `movie_title=${encodeURIComponent(movieTitle)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Find the *specific* button and its SVG icon in the card
            const card = document.querySelector(`[data-movie-title="${movieTitle}"]`);
            const svgIcon = card ? card.querySelector('.watchlist-btn .watchlist-icon') : null;

            if (svgIcon) {
                // Determine if we are adding (filled icon) or removing (outline icon)
                if (data.action === 'added') {
                    // SVG for a FILLED STAR (example of 'liked' state)
                    svgIcon.innerHTML = '<path fill="currentColor" d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>';
                    svgIcon.setAttribute('stroke', 'none'); // Remove stroke if using fill
                    svgIcon.setAttribute('fill', 'currentColor'); // Ensure it's filled
                } else {
                    // SVG for PLUS SIGN (original 'add to list' state)
                    svgIcon.innerHTML = '<path d="M12 5v14M5 12h14"/>';
                    svgIcon.setAttribute('stroke', 'currentColor'); // Restore stroke for outline
                    svgIcon.setAttribute('fill', 'none'); // Ensure it's not filled
                }
            }
            // showNotification(data.message, 'success'); // Assuming you have this function
            alert(data.message); // Fallback notification
        } else {
            // showNotification(data.error || 'Operation failed', 'error');
            alert(data.error || 'Operation failed'); // Fallback notification
        }
    })
    .catch(error => {
        console.error('Error:', error);
        // showNotification('Failed to update watchlist', 'error');
        alert('Failed to update watchlist'); // Fallback notification
    });
}

// ============================================
// Navbar Scroll Effect
// ============================================

window.addEventListener('scroll', function() {
    const navbar = document.getElementById('navbar');
    if (navbar) {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    }
});

// ============================================
// Initialize on DOM Load
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    initializeNavigation();
    initializeProfileDropdown();
    initializeSearchButton();
    initializeContentRows();
    initializeWatchlistButtons();
    initializeSearchForm();
    initializeImageErrorHandling();
    initializeCardInteractions();
});

// ============================================
// Navigation
// ============================================

function initializeNavigation() {
    // Set active nav link based on current page
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath || (currentPath === '/' && href === '/')) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

// ============================================
// Profile Dropdown
// ============================================

function initializeProfileDropdown() {
    const profileBtn = document.getElementById('profileBtn');
    const profileMenu = document.getElementById('profileMenu');
    
    if (profileBtn && profileMenu) {
        profileBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            profileMenu.classList.toggle('show');
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!profileBtn.contains(e.target) && !profileMenu.contains(e.target)) {
                profileMenu.classList.remove('show');
            }
        });
    }
}

// ============================================
// Search Button
// ============================================

function initializeSearchButton() {
    const searchBtn = document.getElementById('searchBtn');
    
    if (searchBtn) {
        searchBtn.addEventListener('click', function() {
            window.location.href = '/search';
        });
    }
}

// ============================================
// Content Rows - Horizontal Scrolling
// ============================================

function initializeContentRows() {
    const rows = document.querySelectorAll('.row-content');
    
    rows.forEach(row => {
        let isDown = false;
        let startX;
        let scrollLeft;
        
        // Mouse drag
        row.addEventListener('mousedown', (e) => {
            isDown = true;
            row.style.cursor = 'grabbing';
            startX = e.pageX - row.offsetLeft;
            scrollLeft = row.scrollLeft;
        });
        
        row.addEventListener('mouseleave', () => {
            isDown = false;
            row.style.cursor = 'grab';
        });
        
        row.addEventListener('mouseup', () => {
            isDown = false;
            row.style.cursor = 'grab';
        });
        
        row.addEventListener('mousemove', (e) => {
            if (!isDown) return;
            e.preventDefault();
            const x = e.pageX - row.offsetLeft;
            const walk = (x - startX) * 2;
            row.scrollLeft = scrollLeft - walk;
        });
        
        // Touch support
        let touchStartX = 0;
        let touchScrollLeft = 0;
        
        row.addEventListener('touchstart', (e) => {
            touchStartX = e.touches[0].pageX;
            touchScrollLeft = row.scrollLeft;
        });
        
        row.addEventListener('touchmove', (e) => {
            if (!touchStartX) return;
            const x = e.touches[0].pageX;
            const walk = (x - touchStartX) * 2;
            row.scrollLeft = touchScrollLeft - walk;
        });
        
        row.addEventListener('touchend', () => {
            touchStartX = 0;
        });
        
        row.style.cursor = 'grab';
        
        // Navigation arrows
        const container = row.closest('.row-container');
        if (container) {
            const leftBtn = container.querySelector('.row-nav-left');
            const rightBtn = container.querySelector('.row-nav-right');
            
            // Left arrow
            if (leftBtn) {
                leftBtn.addEventListener('click', () => {
                    row.scrollBy({
                        left: -600,
                        behavior: 'smooth'
                    });
                });
            }
            
            // Right arrow
            if (rightBtn) {
                rightBtn.addEventListener('click', () => {
                    row.scrollBy({
                        left: 600,
                        behavior: 'smooth'
                    });
                });
            }
            
            // Update arrow visibility based on scroll position
            const updateArrows = () => {
                if (leftBtn && rightBtn) {
                    const isAtStart = row.scrollLeft <= 0;
                    const isAtEnd = row.scrollLeft >= row.scrollWidth - row.clientWidth - 10;
                    
                    leftBtn.style.opacity = isAtStart ? '0.3' : '1';
                    leftBtn.style.pointerEvents = isAtStart ? 'none' : 'auto';
                    
                    rightBtn.style.opacity = isAtEnd ? '0.3' : '1';
                    rightBtn.style.pointerEvents = isAtEnd ? 'none' : 'auto';
                }
            };
            
            row.addEventListener('scroll', updateArrows);
            updateArrows(); // Initial check
        }
    });
}

// ============================================
// Watchlist Button Functionality
// ============================================

// ============================================
// Watchlist Button Functionality (FIXED)
// ============================================

function initializeWatchlistButtons() {
    const watchlistBtns = document.querySelectorAll('.watchlist-btn');
    
    watchlistBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            
            // Look up the hierarchy to find the main movie card container
            // The card container should have the data-movie-title attribute
            const movieCard = this.closest('.netflix-card');
            
            if (movieCard) {
                const movieTitle = movieCard.getAttribute('data-movie-title');
                console.log("Toggling watchlist for:", movieTitle); // Check the title here!
                toggleWatchlist(movieTitle);
            } else {
                console.error("Could not find parent card with movie title attribute.");
            }
        });
    });
}

// ============================================
// Card Interactions
// ============================================

function initializeCardInteractions() {
    const cards = document.querySelectorAll('.netflix-card');
    
    cards.forEach(card => {
        const playBtn = card.querySelector('.play-btn');
        const infoBtn = card.querySelector('.info-btn');
        
        if (playBtn) {
            playBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                showNotification('Play feature coming soon!', 'info');
            });
        }
        
        if (infoBtn) {
            infoBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                const overview = card.getAttribute('data-movie-overview');
                showNotification(`More info about ${overview}`, 'info');
            });
        }
    });
}

// ============================================
// Search Form
// ============================================

function initializeSearchForm() {
    const searchForm = document.getElementById('searchForm');
    const searchInput = document.getElementById('searchInput');
    const searchButton = document.getElementById('searchButton');
    const searchResults = document.getElementById('searchResults');
    
    if (searchForm && searchButton && searchResults) {
        searchForm.addEventListener('submit', function(e) {
            const query = searchInput.value.trim();
            
            if (!query) {
                e.preventDefault();
                return;
            }
            
            searchButton.disabled = true;
            const buttonText = searchButton.querySelector('.button-text');
            const buttonLoading = searchButton.querySelector('.button-loading');
            
            if (buttonText && buttonLoading) {
                buttonText.style.display = 'none';
                buttonLoading.style.display = 'inline-flex';
            }
            
            searchResults.classList.add('loading');
        });
    }
}

// ============================================
// Image Error Handling
// ============================================

function initializeImageErrorHandling() {
    const images = document.querySelectorAll('img');
    const placeholder = 'https://via.placeholder.com/300x450?text=No+Image';
    
    images.forEach(img => {
        img.addEventListener('error', function() {
            if (this.src !== placeholder) {
                this.src = placeholder;
            }
        });
    });
}

// ============================================
// Notification System
// ============================================

function showNotification(message, type = 'info') {
    const existing = document.querySelector('.notification');
    if (existing) {
        existing.remove();
    }
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    if (!document.querySelector('#notification-styles')) {
        const style = document.createElement('style');
        style.id = 'notification-styles';
        style.textContent = `
            .notification {
                position: fixed;
                top: 90px;
                right: 20px;
                background: rgba(20, 20, 20, 0.95);
                color: var(--netflix-white);
                padding: 16px 24px;
                border-radius: 4px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.5);
                z-index: 10000;
                animation: slideIn 0.3s ease;
                max-width: 300px;
                border-left: 4px solid var(--accent-color);
            }
            .notification-error {
                border-left-color: var(--netflix-red);
            }
            .notification-success {
                border-left-color: #4caf50;
            }
            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// ============================================
// Hero Section Interactions
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    const playBtn = document.querySelector('.btn-play');
    const moreInfoBtn = document.querySelector('.btn-more-info');
    
    if (playBtn) {
        playBtn.addEventListener('click', function() {
            showNotification('Play feature coming soon!', 'info');
        });
    }
    
    if (moreInfoBtn) {
        moreInfoBtn.addEventListener('click', function() {
            const heroSection = document.getElementById('heroSection');
            if (heroSection) {
                const movieTitle = heroSection.querySelector('.hero-title')?.textContent;
                if (movieTitle) {
                    showNotification(`More information about "${movieTitle}"`, 'info');
                }
            }
        });
    }
});

function toggleLike(btn, movieId) {
  if (!movieId) {
        alert("Cannot like this movie (missing ID)");
        return;
    }

  fetch("/toggle_like", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ movie_id: movieId })
  })
  .then(res => res.json())
  .then(data => {
    if (data.liked) btn.classList.add("liked");
    else btn.classList.remove("liked");
  })
  .catch(err => console.error("Error liking movie:", err));
}


