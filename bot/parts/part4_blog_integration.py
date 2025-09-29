MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017/")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "kannada_entertainment")
BLOGGER_API_KEY = os.environ.get("BLOGGER_API_KEY", "")
BLOGGER_BLOG_ID = os.environ.get("BLOGGER_BLOG_ID", "")
BLOG_URL = os.environ.get("BLOG_URL", "")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "")

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kannada Entertainment Hub - Latest Movies, Series & Shows</title>
    
    <!-- SEO Meta Tags -->
    <meta name="description" content="Download latest Kannada movies, web series, TV shows and dubbed content. High quality downloads with multiple formats available.">
    <meta name="keywords" content="Kannada movies, Kannada web series, Kannada TV shows, Kannada dubbed movies, download, entertainment">
    <meta name="author" content="Kannada Entertainment Hub">
    
    <!-- Open Graph Tags -->
    <meta property="og:title" content="Kannada Entertainment Hub">
    <meta property="og:description" content="Your ultimate destination for Kannada entertainment content">
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://kannada-movies-rvasp.blogspot.com">
    
    <!-- Favicon -->
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🎬</text></svg>">
    
    <!-- Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --primary: #ff6b35;
            --primary-dark: #e55a2b;
            --secondary: #2c3e50;
            --accent: #3498db;
            --success: #27ae60;
            --warning: #f39c12;
            --danger: #e74c3c;
            --light: #ecf0f1;
            --dark: #2c3e50;
            --text: #2c3e50;
            --text-light: #7f8c8d;
            --bg: #ffffff;
            --bg-light: #f8f9fa;
            --gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --shadow: 0 10px 30px rgba(0,0,0,0.1);
            --border-radius: 12px;
        }

        body {
            font-family: 'Poppins', sans-serif;
            line-height: 1.6;
            color: var(--text);
            background: var(--bg-light);
            overflow-x: hidden;
        }

        /* Header */
        .header {
            background: var(--gradient);
            color: white;
            padding: 1rem 0;
            position: sticky;
            top: 0;
            z-index: 1000;
            backdrop-filter: blur(10px);
            box-shadow: var(--shadow);
        }

        .nav-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 1.5rem;
            font-weight: 700;
            text-decoration: none;
            color: white;
        }

        .nav-menu {
            display: flex;
            list-style: none;
            gap: 2rem;
            align-items: center;
        }

        .nav-link {
            color: white;
            text-decoration: none;
            font-weight: 500;
            transition: all 0.3s ease;
            padding: 0.5rem 1rem;
            border-radius: var(--border-radius);
        }

        .nav-link:hover {
            background: rgba(255,255,255,0.1);
            transform: translateY(-2px);
        }

        .mobile-menu {
            display: none;
            background: none;
            border: none;
            color: white;
            font-size: 1.5rem;
            cursor: pointer;
        }

        /* Hero Section */
        .hero {
            background: var(--gradient);
            color: white;
            padding: 4rem 0;
            text-align: center;
            position: relative;
            overflow: hidden;
        }

        .hero::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 100"><path d="M0,50 Q250,0 500,50 T1000,50 L1000,100 L0,100 Z" fill="white" opacity="0.1"/></svg>') bottom;
            background-size: 100% 50px;
        }

        .hero-content {
            max-width: 800px;
            margin: 0 auto;
            padding: 0 2rem;
            position: relative;
            z-index: 1;
        }

        .hero h1 {
            font-size: clamp(2rem, 5vw, 3.5rem);
            margin-bottom: 1rem;
            font-weight: 700;
            line-height: 1.2;
        }

        .hero p {
            font-size: 1.2rem;
            margin-bottom: 2rem;
            opacity: 0.9;
        }

        .search-box {
            max-width: 600px;
            margin: 0 auto;
            position: relative;
        }

        .search-input {
            width: 100%;
            padding: 1rem 3rem 1rem 1.5rem;
            border: none;
            border-radius: 50px;
            font-size: 1.1rem;
            outline: none;
            box-shadow: var(--shadow);
            background: rgba(255,255,255,0.95);
            backdrop-filter: blur(10px);
        }

        .search-btn {
            position: absolute;
            right: 0.5rem;
            top: 50%;
            transform: translateY(-50%);
            background: var(--primary);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 50px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 600;
        }

        .search-btn:hover {
            background: var(--primary-dark);
            transform: translateY(-50%) scale(1.05);
        }

        /* Filter Tabs */
        .filter-tabs {
            background: white;
            padding: 1rem 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            position: sticky;
            top: 70px;
            z-index: 999;
        }

        .filter-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
        }

        .filter-buttons {
            display: flex;
            gap: 1rem;
            overflow-x: auto;
            padding: 0.5rem 0;
            scrollbar-width: none;
            -ms-overflow-style: none;
        }

        .filter-buttons::-webkit-scrollbar {
            display: none;
        }

        .filter-btn {
            background: var(--bg-light);
            color: var(--text);
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 50px;
            cursor: pointer;
            font-weight: 500;
            white-space: nowrap;
            transition: all 0.3s ease;
            border: 2px solid transparent;
        }

        .filter-btn:hover,
        .filter-btn.active {
            background: var(--primary);
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(255,107,53,0.3);
        }

        /* Main Content */
        .main {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
            min-height: 60vh;
        }

        .section-title {
            font-size: 2rem;
            margin-bottom: 2rem;
            text-align: center;
            color: var(--secondary);
            font-weight: 600;
        }

        .section-title::after {
            content: '';
            display: block;
            width: 80px;
            height: 4px;
            background: var(--primary);
            margin: 1rem auto;
            border-radius: 2px;
        }

        /* Content Grid */
        .content-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 2rem;
            margin-bottom: 3rem;
        }

        .content-card {
            background: white;
            border-radius: var(--border-radius);
            overflow: hidden;
            box-shadow: var(--shadow);
            transition: all 0.3s ease;
            cursor: pointer;
            position: relative;
        }

        .content-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.15);
        }

        .card-image {
            height: 400px;
            background: var(--gradient);
            position: relative;
            overflow: hidden;
        }

        .card-image img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.3s ease;
        }

        .content-card:hover .card-image img {
            transform: scale(1.05);
        }

        .quality-badge {
            position: absolute;
            top: 1rem;
            right: 1rem;
            background: var(--primary);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }

        .year-badge {
            position: absolute;
            top: 1rem;
            left: 1rem;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
        }

        .card-content {
            padding: 1.5rem;
        }

        .card-title {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: var(--secondary);
            line-height: 1.3;
        }

        .card-meta {
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
            font-size: 0.9rem;
            color: var(--text-light);
        }

        .card-meta span {
            display: flex;
            align-items: center;
            gap: 0.25rem;
        }

        .card-description {
            color: var(--text-light);
            font-size: 0.9rem;
            line-height: 1.5;
            margin-bottom: 1rem;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .card-actions {
            display: flex;
            gap: 0.5rem;
            justify-content: space-between;
            align-items: center;
        }

        .view-btn {
            background: var(--primary);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 50px;
            cursor: pointer;
            font-weight: 600;
            font-size: 0.9rem;
            transition: all 0.3s ease;
            flex: 1;
        }

        .view-btn:hover {
            background: var(--primary-dark);
            transform: scale(1.05);
        }

        .rating {
            display: flex;
            align-items: center;
            gap: 0.25rem;
            color: var(--warning);
            font-weight: 600;
        }

        /* Modal */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            z-index: 10000;
            backdrop-filter: blur(5px);
        }

        .modal.active {
            display: flex;
            align-items: center;
            justify-content: center;
            animation: fadeIn 0.3s ease;
        }

        .modal-content {
            background: white;
            border-radius: var(--border-radius);
            max-width: 900px;
            max-height: 90vh;
            overflow-y: auto;
            position: relative;
            margin: 1rem;
            animation: slideUp 0.3s ease;
        }

        .modal-header {
            position: relative;
            height: 300px;
            background: var(--gradient);
            color: white;
            display: flex;
            align-items: flex-end;
            padding: 2rem;
        }

        .modal-poster {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .modal-overlay {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(to top, rgba(0,0,0,0.8), rgba(0,0,0,0.3));
        }

        .modal-title {
            position: relative;
            z-index: 1;
            font-size: 2.5rem;
            font-weight: 700;
            text-shadow: 0 2px 10px rgba(0,0,0,0.5);
        }

        .close-btn {
            position: absolute;
            top: 1rem;
            right: 1rem;
            background: rgba(255,255,255,0.1);
            border: none;
            color: white;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 1.2rem;
            z-index: 2;
            transition: all 0.3s ease;
        }

        .close-btn:hover {
            background: rgba(255,255,255,0.2);
            transform: scale(1.1);
        }

        .modal-body {
            padding: 2rem;
        }

        .modal-info {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 2rem;
            margin-bottom: 2rem;
        }

        .info-section h3 {
            color: var(--secondary);
            margin-bottom: 1rem;
            font-size: 1.2rem;
        }

        .info-list {
            list-style: none;
        }

        .info-list li {
            padding: 0.5rem 0;
            border-bottom: 1px solid var(--light);
            display: flex;
            justify-content: space-between;
        }

        .info-list li:last-child {
            border-bottom: none;
        }

        .download-section {
            background: var(--bg-light);
            padding: 2rem;
            border-radius: var(--border-radius);
            margin-top: 2rem;
        }

        .download-title {
            font-size: 1.5rem;
            color: var(--secondary);
            margin-bottom: 1.5rem;
            text-align: center;
        }

        .download-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
        }

        .download-btn {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: white;
            border: 2px solid var(--light);
            padding: 1rem 1.5rem;
            border-radius: var(--border-radius);
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            color: var(--text);
        }

        .download-btn:hover {
            border-color: var(--primary);
            background: var(--primary);
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(255,107,53,0.3);
        }

        .download-info {
            flex: 1;
        }

        .download-quality {
            font-weight: 600;
            font-size: 1.1rem;
        }

        .download-size {
            font-size: 0.9rem;
            opacity: 0.7;
        }

        .download-icon {
            font-size: 1.5rem;
            opacity: 0.7;
        }

        .download-btn:hover .download-icon {
            opacity: 1;
            transform: scale(1.1);
        }

        /* Loading and No Results */
        .loading {
            text-align: center;
            padding: 3rem;
            color: var(--text-light);
        }

        .loading i {
            font-size: 3rem;
            margin-bottom: 1rem;
            animation: spin 1s linear infinite;
        }

        .no-results {
            text-align: center;
            padding: 3rem;
            color: var(--text-light);
        }

        .no-results i {
            font-size: 4rem;
            margin-bottom: 1rem;
            opacity: 0.5;
        }

        /* Pagination */
        .pagination {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 0.5rem;
            margin: 2rem 0;
        }

        .page-btn {
            background: white;
            border: 2px solid var(--light);
            color: var(--text);
            padding: 0.75rem 1rem;
            border-radius: var(--border-radius);
            cursor: pointer;
            transition: all 0.3s ease;
            min-width: 45px;
            text-align: center;
        }

        .page-btn:hover,
        .page-btn.active {
            background: var(--primary);
            border-color: var(--primary);
            color: white;
        }

        .page-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        /* Footer */
        .footer {
            background: var(--secondary);
            color: white;
            padding: 3rem 0 1rem;
            margin-top: 4rem;
        }

        .footer-content {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 2rem;
        }

        .footer-section h3 {
            margin-bottom: 1rem;
            color: var(--primary);
        }

        .footer-section ul {
            list-style: none;
        }

        .footer-section ul li {
            padding: 0.25rem 0;
        }

        .footer-section ul li a {
            color: white;
            text-decoration: none;
            transition: color 0.3s ease;
        }

        .footer-section ul li a:hover {
            color: var(--primary);
        }

        .footer-bottom {
            text-align: center;
            padding-top: 2rem;
            margin-top: 2rem;
            border-top: 1px solid rgba(255,255,255,0.1);
            opacity: 0.7;
        }

        /* Animations */
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        @keyframes slideUp {
            from { 
                opacity: 0; 
                transform: translateY(50px);
            }
            to { 
                opacity: 1; 
                transform: translateY(0);
            }
        }

        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .nav-menu {
                display: none;
            }

            .mobile-menu {
                display: block;
            }

            .hero {
                padding: 2rem 0;
            }

            .hero h1 {
                font-size: 2rem;
            }

            .filter-buttons {
                padding: 0.5rem;
                margin: 0 -1rem;
            }

            .content-grid {
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                gap: 1rem;
            }

            .card-image {
                height: 300px;
            }

            .modal-content {
                margin: 0.5rem;
                max-height: 95vh;
            }

            .modal-header {
                height: 200px;
                padding: 1rem;
            }

            .modal-title {
                font-size: 1.8rem;
            }

            .modal-info {
                grid-template-columns: 1fr;
                gap: 1rem;
            }

            .download-grid {
                grid-template-columns: 1fr;
            }

            .footer-content {
                grid-template-columns: 1fr;
                text-align: center;
            }
        }

        @media (max-width: 480px) {
            .main {
                padding: 1rem;
            }

            .content-grid {
                grid-template-columns: 1fr;
            }

            .search-input {
                padding: 0.75rem 2.5rem 0.75rem 1rem;
                font-size: 1rem;
            }

            .search-btn {
                padding: 0.5rem 1rem;
                right: 0.25rem;
            }
        }

        /* Dark mode styles (optional) */
        @media (prefers-color-scheme: dark) {
            :root {
                --bg: #1a1a1a;
                --bg-light: #2d2d2d;
                --text: #ffffff;
                --text-light: #b0b0b0;
                --light: #404040;
            }

            .content-card {
                background: var(--bg-light);
            }

            .modal-content {
                background: var(--bg-light);
            }

            .download-btn {
                background: var(--bg);
                border-color: var(--light);
            }
        }
    </style>
</head>
<body>
    <!-- Header -->
    <header class="header">
        <div class="nav-container">
            <a href="#" class="logo">
                <i class="fas fa-film"></i>
                Kannada Entertainment
            </a>
            <nav class="nav-menu">
                <a href="#" class="nav-link active" data-filter="all">🏠 Home</a>
                <a href="#" class="nav-link" data-filter="movies">🎬 Movies</a>
                <a href="#" class="nav-link" data-filter="webseries">📺 Web Series</a>
                <a href="#" class="nav-link" data-filter="shows">🎭 Shows</a>
                <a href="#" class="nav-link" data-filter="dubbed">🗣️ Dubbed</a>
                <a href="https://t.me/your_bot_username" target="_blank" class="nav-link">🤖 Bot</a>
            </nav>
            <button class="mobile-menu">
                <i class="fas fa-bars"></i>
            </button>
        </div>
    </header>

    <!-- Hero Section -->
    <section class="hero">
        <div class="hero-content">
            <h1>Your Ultimate Kannada Entertainment Hub</h1>
            <p>Discover the latest Kannada movies, web series, TV shows and dubbed content. High-quality downloads in multiple formats.</p>
            
            <div class="search-box">
                <input type="text" class="search-input" placeholder="Search movies, series, actors, genres..." id="searchInput">
                <button class="search-btn" onclick="performSearch()">
                    <i class="fas fa-search"></i> Search
                </button>
            </div>
        </div>
    </section>

    <!-- Filter Tabs -->
    <section class="filter-tabs">
        <div class="filter-container">
            <div class="filter-buttons">
                <button class="filter-btn active" data-filter="all">🔥 All Content</button>
                <button class="filter-btn" data-filter="movies">🎬 Movies</button>
                <button class="filter-btn" data-filter="webseries">📺 Web Series</button>
                <button class="filter-btn" data-filter="tvseries">📻 TV Series</button>
                <button class="filter-btn" data-filter="shows">🎭 Shows</button>
                <button class="filter-btn" data-filter="dubbed">🗣️ Dubbed</button>
                <button class="filter-btn" data-filter="latest">⚡ Latest</button>
                <button class="filter-btn" data-filter="popular">🔥 Popular</button>
                <button class="filter-btn" data-filter="action">⚔️ Action</button>
                <button class="filter-btn" data-filter="drama">🎭 Drama</button>
                <button class="filter-btn" data-filter="comedy">😂 Comedy</button>
                <button class="filter-btn" data-filter="thriller">🕵️ Thriller</button>
            </div>
        </div>
    </section>

    <!-- Main Content -->
    <main class="main">
        <h2 class="section-title" id="sectionTitle">Latest Kannada Entertainment</h2>
        
        <!-- Loading State -->
        <div class="loading" id="loading" style="display: none;">
            <i class="fas fa-spinner"></i>
            <p>Loading awesome content...</p>
        </div>

        <!-- Content Grid -->
        <div class="content-grid" id="contentGrid">
            <!-- Content will be dynamically generated here -->
        </div>

        <!-- No Results -->
        <div class="no-results" id="noResults" style="display: none;">
            <i class="fas fa-search"></i>
            <h3>No Results Found</h3>
            <p>Try searching with different keywords or browse our categories.</p>
        </div>

        <!-- Pagination -->
        <div class="pagination" id="pagination" style="display: none;">
            <button class="page-btn" id="prevBtn" onclick="changePage(-1)">
                <i class="fas fa-chevron-left"></i>
            </button>
            <span id="pageNumbers"></span>
            <button class="page-btn" id="nextBtn" onclick="changePage(1)">
                <i class="fas fa-chevron-right"></i>
            </button>
        </div>
    </main>

    <!-- Modal -->
    <div class="modal" id="contentModal">
        <div class="modal-content">
            <div class="modal-header">
                <img class="modal-poster" id="modalPoster" src="" alt="">
                <div class="modal-overlay"></div>
                <h2 class="modal-title" id="modalTitle">Movie Title</h2>
                <button class="close-btn" onclick="closeModal()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            
            <div class="modal-body">
                <div class="modal-info">
                    <div class="info-section">
                        <h3>📋 Details</h3>
                        <ul class="info-list" id="movieDetails">
                            <!-- Details will be populated here -->
                        </ul>
                    </div>
                    
                    <div class="info-section">
                        <h3>📖 Description</h3>
                        <p id="movieDescription">Movie description will appear here...</p>
                        
                        <h3 style="margin-top: 2rem;">⭐ Rating & Stats</h3>
                        <div class="rating">
                            <span id="movieRating">4.5</span>
                            <i class="fas fa-star"></i>
                            <span>|</span>
                            <span id="viewCount">1.2K views</span>
                            <span>|</span>
                            <span id="downloadCount">856 downloads</span>
                        </div>
                    </div>
                </div>

                <div class="download-section">
                    <h3 class="download-title">💾 Download Options</h3>
                    <div class="download-grid" id="downloadGrid">
                        <!-- Download buttons will be generated here -->
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Footer -->
    <footer class="footer">
        <div class="footer-content">
            <div class="footer-section">
                <h3>🎬 Categories</h3>
                <ul>
                    <li><a href="#" onclick="filterContent('movies')">Movies</a></li>
                    <li><a href="#" onclick="filterContent('webseries')">Web Series</a></li>
                    <li><a href="#" onclick="filterContent('shows')">TV Shows</a></li>
                    <li><a href="#" onclick="filterContent('dubbed')">Dubbed Content</a></li>
                </ul>
            </div>
            
            <div class="footer-section">
                <h3>🎭 Genres</h3>
                <ul>
                    <li><a href="#" onclick="filterContent('action')">Action</a></li>
                    <li><a href="#" onclick="filterContent('drama')">Drama</a></li>
                    <li><a href="#" onclick="filterContent('comedy')">Comedy</a></li>
                    <li><a href="#" onclick="filterContent('thriller')">Thriller</a></li>
                    <li><a href="#" onclick="filterContent('romance')">Romance</a></li>
                </ul>
            </div>
            
            <div class="footer-section">
                <h3>🔗 Quick Links</h3>
                <ul>
                    <li><a href="https://t.me/your_bot_username" target="_blank">Telegram Bot</a></li>
                    <li><a href="#" onclick="filterContent('latest')">Latest Releases</a></li>
                    <li><a href="#" onclick="filterContent('popular')">Popular Content</a></li>
                    <li><a href="#top">Back to Top</a></li>
                </ul>
            </div>
            
            <div class="footer-section">
                <h3>📱 Connect With Us</h3>
                <ul>
                    <li><a href="https://t.me/your_channel" target="_blank"><i class="fab fa-telegram"></i> Telegram Channel</a></li>
                    <li><a href="https://t.me/your_bot_username" target="_blank"><i class="fas fa-robot"></i> Download Bot</a></li>
                    <li><a href="#" onclick="showContactModal()"><i class="fas fa-envelope"></i> Contact Us</a></li>
                    <li><a href="#" onclick="showAboutModal()"><i class="fas fa-info-circle"></i> About</a></li>
                </ul>
            </div>
        </div>
        
        <div class="footer-bottom">
            <p>&copy; 2024 Kannada Entertainment Hub. Made with ❤️ for Kannada cinema lovers.</p>
            <p>All content is hosted on Telegram channels. We do not store any files.</p>
        </div>
    </footer>

    <script>
        // Configuration
        const BOT_USERNAME = 'your_bot_username'; // Replace with actual bot username
        const API_BASE = 'https://your-api-endpoint.com'; // Replace with actual API endpoint
        
        // Global variables
        let currentPage = 1;
        let currentFilter = 'all';
        let currentSearchQuery = '';
        let allContent = [];
        let filteredContent = [];
        const itemsPerPage = 12;

        // Sample data - Replace with actual API calls
        const sampleContent = [
            {
                id: '1',
                name: 'KGF Chapter 2',
                type: 'movies',
                year: 2022,
                language: 'Kannada',
                genre: 'Action',
                actors: ['Yash', 'Srinidhi Shetty', 'Raveena Tandon'],
                director: 'Prashanth Neel',
                poster: 'https://via.placeholder.com/280x400/667eea/white?text=KGF+2',
                description: 'The blood-soaked land of Kolar Gold Fields (KGF) has a new overlord now - Rocky, whose name strikes fear in the heart of his foes. His allies look up to Rocky as their savior, the government sees him as a threat to law and order.',
                rating: 4.8,
                views: 15420,
                downloads: 8945,
                qualities: [
                    {quality: '4K', size: '8.5 GB', msgId: 'msg123'},
                    {quality: '1080P', size: '4.2 GB', msgId: 'msg124'},
                    {quality: '720P', size: '2.1 GB', msgId: 'msg125'},
                    {quality: '480P', size: '850 MB', msgId: 'msg126'}
                ],
                isDubbed: false,
                isLatest: false,
                isPopular: true
            },
            {
                id: '2',
                name: 'Kantara',
                type: 'movies',
                year: 2022,
                language: 'Kannada',
                genre: 'Drama',
                actors: ['Rishab Shetty', 'Sapthami Gowda', 'Kishore'],
                director: 'Rishab Shetty',
                poster: 'https://via.placeholder.com/280x400/764ba2/white?text=Kantara',
                description: 'A forest officer faces resistance from locals when he tries to carry out his duties. The situation becomes complicated when he falls in love with a local girl.',
                rating: 4.9,
                views: 12850,
                downloads: 7420,
                qualities: [
                    {quality: '1080P', size: '3.8 GB', msgId: 'msg127'},
                    {quality: '720P', size: '1.9 GB', msgId: 'msg128'},
                    {quality: '480P', size: '750 MB', msgId: 'msg129'}
                ],
                isDubbed: false,
                isLatest: false,
                isPopular: true
            },
            {
                id: '3',
                name: 'Scam 1992',
                type: 'webseries',
                year: 2020,
                language: 'Kannada Dub',
                genre: 'Drama',
                actors: ['Pratik Gandhi', 'Shreya Dhanwanthary'],
                director: 'Hansal Mehta',
                poster: 'https://via.placeholder.com/280x400/ff6b35/white?text=Scam+1992',
                description: 'Set in 1980s and 90s Bombay, it follows the life of Harshad Mehta, a stockbroker who took the stock market to dizzying heights and his catastrophic downfall.',
                rating: 4.7,
                views: 9420,
                downloads: 5680,
                seasons: 1,
                episodes: 10,
                qualities: [
                    {quality: '1080P', size: '500 MB/ep', msgId: 'msg130'},
                    {quality: '720P', size: '300 MB/ep', msgId: 'msg131'}
                ],
                isDubbed: true,
                isLatest: false,
                isPopular: true
            },
            {
                id: '4',
                name: 'Bigg Boss Kannada 10',
                type: 'shows',
                year: 2023,
                language: 'Kannada',
                genre: 'Reality',
                actors: ['Kiccha Sudeep'],
                director: 'Various',
                poster: 'https://via.placeholder.com/280x400/27ae60/white?text=Bigg+Boss+10',
                description: 'The ultimate reality show where celebrities live together in a house for 100 days, with eliminations based on audience voting.',
                rating: 4.2,
                views: 25420,
                downloads: 12450,
                seasons: 1,
                episodes: 105,
                qualities: [
                    {quality: '720P', size: '800 MB/ep', msgId: 'msg132'},
                    {quality: '480P', size: '400 MB/ep', msgId: 'msg133'}
                ],
                isDubbed: false,
                isLatest: true,
                isPopular: true
            },
            {
                id: '5',
                name: 'The Family Man',
                type: 'webseries',
                year: 2021,
                language: 'Kannada Dub',
                genre: 'Thriller',
                actors: ['Manoj Bajpayee', 'Samantha Ruth Prabhu'],
                director: 'Raj Nidimoru',
                poster: 'https://via.placeholder.com/280x400/e74c3c/white?text=Family+Man',
                description: 'A middle-class man secretly works for the National Investigation Agency while balancing his family life.',
                rating: 4.6,
                views: 8520,
                downloads: 4850,
                seasons: 2,
                episodes: 19,
                qualities: [
                    {quality: '1080P', size: '600 MB/ep', msgId: 'msg134'},
                    {quality: '720P', size: '350 MB/ep', msgId: 'msg135'}
                ],
                isDubbed: true,
                isLatest: false,
                isPopular: true
            },
            {
                id: '6',
                name: 'RRR',
                type: 'movies',
                year: 2022,
                language: 'Kannada Dub',
                genre: 'Action',
                actors: ['Ram Charan', 'Jr NTR', 'Alia Bhatt'],
                director: 'SS Rajamouli',
                poster: 'https://via.placeholder.com/280x400/3498db/white?text=RRR',
                description: 'A fictional story about two legendary revolutionaries and their journey away from home before they started fighting for their country in 1920s.',
                rating: 4.8,
                views: 18750,
                downloads: 11250,
                qualities: [
                    {quality: '4K', size: '12 GB', msgId: 'msg136'},
                    {quality: '1080P', size: '5.5 GB', msgId: 'msg137'},
                    {quality: '720P', size: '2.8 GB', msgId: 'msg138'},
                    {quality: '480P', size: '1.2 GB', msgId: 'msg139'}
                ],
                isDubbed: true,
                isLatest: false,
                isPopular: true
            }
        ];

        // Initialize the application
        document.addEventListener('DOMContentLoaded', function() {
            allContent = sampleContent;
            filteredContent = [...allContent];
            renderContent();
            setupEventListeners();
        });

        // Setup event listeners
        function setupEventListeners() {
            // Filter buttons
            document.querySelectorAll('.filter-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    const filter = this.dataset.filter;
                    filterContent(filter);
                    updateActiveFilter(this);
                });
            });

            // Navigation links
            document.querySelectorAll('.nav-link').forEach(link => {
                link.addEventListener('click', function(e) {
                    e.preventDefault();
                    const filter = this.dataset.filter;
                    if (filter) {
                        filterContent(filter);
                        updateActiveNavLink(this);
                    }
                });
            });

            // Search input
            document.getElementById('searchInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    performSearch();
                }
            });

            // Close modal when clicking outside
            document.getElementById('contentModal').addEventListener('click', function(e) {
                if (e.target === this) {
                    closeModal();
                }
            });
        }

        // Filter content
        function filterContent(filter) {
            currentFilter = filter;
            currentPage = 1;
            showLoading(true);

            setTimeout(() => {
                filteredContent = allContent.filter(item => {
                    switch(filter) {
                        case 'all':
                            return true;
                        case 'movies':
                        case 'webseries':
                        case 'tvseries':
                        case 'shows':
                            return item.type === filter;
                        case 'dubbed':
                            return item.isDubbed;
                        case 'latest':
                            return item.isLatest;
                        case 'popular':
                            return item.isPopular;
                        case 'action':
                        case 'drama':
                        case 'comedy':
                        case 'thriller':
                        case 'romance':
                            return item.genre.toLowerCase() === filter;
                        default:
                            return true;
                    }
                });

                updateSectionTitle(filter);
                renderContent();
                showLoading(false);
            }, 500);
        }

        // Perform search
        function performSearch() {
            const query = document.getElementById('searchInput').value.trim();
            if (!query) return;

            currentSearchQuery = query;
            currentPage = 1;
            showLoading(true);

            setTimeout(() => {
                filteredContent = allContent.filter(item => {
                    const searchText = `${item.name} ${item.actors.join(' ')} ${item.genre} ${item.director}`.toLowerCase();
                    return searchText.includes(query.toLowerCase());
                });

                updateSectionTitle('search', query);
                renderContent();
                showLoading(false);
            }, 500);
        }

        // Render content
        function renderContent() {
            const grid = document.getElementById('contentGrid');
            const startIndex = (currentPage - 1) * itemsPerPage;
            const endIndex = startIndex + itemsPerPage;
            const pageContent = filteredContent.slice(startIndex, endIndex);

            if (pageContent.length === 0) {
                grid.innerHTML = '';
                showNoResults(true);
                showPagination(false);
                return;
            }

            showNoResults(false);

            grid.innerHTML = pageContent.map(item => createContentCard(item)).join('');

            // Setup pagination
            const totalPages = Math.ceil(filteredContent.length / itemsPerPage);
            if (totalPages > 1) {
                updatePagination(totalPages);
                showPagination(true);
            } else {
                showPagination(false);
            }
        }

        // Create content card HTML
        function createContentCard(item) {
            const typeEmoji = {
                'movies': '🎬',
                'webseries': '📺',
                'tvseries': '📻',
                'shows': '🎭'
            };

            return `
                <div class="content-card" onclick="openModal('${item.id}')">
                    <div class="card-image">
                        <img src="${item.poster}" alt="${item.name}" loading="lazy">
                        <div class="quality-badge">${item.qualities[0].quality}</div>
                        <div class="year-badge">${item.year}</div>
                    </div>
                    
                    <div class="card-content">
                        <h3 class="card-title">${item.name}</h3>
                        
                        <div class="card-meta">
                            <span><i class="fas fa-calendar"></i> ${item.year}</span>
                            <span><i class="fas fa-language"></i> ${item.language}</span>
                            <span>${typeEmoji[item.type]} ${item.type.charAt(0).toUpperCase() + item.type.slice(1)}</span>
                        </div>
                        
                        <p class="card-description">${item.description}</p>
                        
                        <div class="card-actions">
                            <button class="view-btn">
                                <i class="fas fa-play"></i> View Details
                            </button>
                            <div class="rating">
                                <i class="fas fa-star"></i>
                                <span>${item.rating}</span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }

        // Open modal
        function openModal(contentId) {
            const content = allContent.find(item => item.id === contentId);
            if (!content) return;

            // Update modal content
            document.getElementById('modalTitle').textContent = content.name;
            document.getElementById('modalPoster').src = content.poster;
            document.getElementById('movieDescription').textContent = content.description;
            document.getElementById('movieRating').textContent = content.rating;
            document.getElementById('viewCount').textContent = `${content.views.toLocaleString()} views`;
            document.getElementById('downloadCount').textContent = `${content.downloads.toLocaleString()} downloads`;

            // Update movie details
            const details = document.getElementById('movieDetails');
            details.innerHTML = `
                <li><strong>Year:</strong> <span>${content.year}</span></li>
                <li><strong>Language:</strong> <span>${content.language}</span></li>
                <li><strong>Genre:</strong> <span>${content.genre}</span></li>
                <li><strong>Director:</strong> <span>${content.director}</span></li>
                <li><strong>Actors:</strong> <span>${content.actors.join(', ')}</span></li>
                ${content.seasons ? `<li><strong>Seasons:</strong> <span>${content.seasons}</span></li>` : ''}
                ${content.episodes ? `<li><strong>Episodes:</strong> <span>${content.episodes}</span></li>` : ''}
                <li><strong>Type:</strong> <span>${content.type.charAt(0).toUpperCase() + content.type.slice(1)}</span></li>
            `;

            // Update download buttons
            const downloadGrid = document.getElementById('downloadGrid');
            downloadGrid.innerHTML = content.qualities.map(quality => `
                <a href="https://t.me/${BOT_USERNAME}?start=media-${quality.msgId}" 
                   class="download-btn" target="_blank">
                    <div class="download-info">
                        <div class="download-quality">${quality.quality}</div>
                        <div class="download-size">${quality.size}</div>
                    </div>
                    <i class="fas fa-download download-icon"></i>
                </a>
            `).join('');

            // Show modal
            document.getElementById('contentModal').classList.add('active');
            document.body.style.overflow = 'hidden';
        }

        // Close modal
        function closeModal() {
            document.getElementById('contentModal').classList.remove('active');
            document.body.style.overflow = 'auto';
        }

        // Update section title
        function updateSectionTitle(filter, query = '') {
            const titles = {
                'all': 'Latest Kannada Entertainment',
                'movies': '🎬 Kannada Movies',
                'webseries': '📺 Kannada Web Series',
                'tvseries': '📻 Kannada TV Series',
                'shows': '🎭 Kannada Shows',
                'dubbed': '🗣️ Kannada Dubbed Content',
                'latest': '⚡ Latest Releases',
                'popular': '🔥 Popular Content',
                'action': '⚔️ Action Movies & Series',
                'drama': '🎭 Drama Content',
                'comedy': '😂 Comedy Content',
                'thriller': '🕵️ Thriller Content',
                'romance': '💕 Romance Content',
                'search': `🔍 Search Results for "${query}"`
            };

            document.getElementById('sectionTitle').textContent = titles[filter] || 'Kannada Entertainment';
        }

        // Update active filter button
        function updateActiveFilter(activeBtn) {
            document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
            activeBtn.classList.add('active');
        }

        // Update active nav link
        function updateActiveNavLink(activeLink) {
            document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
            activeLink.classList.add('active');
        }

        // Pagination functions
        function changePage(direction) {
            const totalPages = Math.ceil(filteredContent.length / itemsPerPage);
            const newPage = currentPage + direction;

            if (newPage >= 1 && newPage <= totalPages) {
                currentPage = newPage;
                renderContent();
                scrollToTop();
            }
        }

        function goToPage(page) {
            currentPage = page;
            renderContent();
            scrollToTop();
        }

        function updatePagination(totalPages) {
            const pagination = document.getElementById('pagination');
            const prevBtn = document.getElementById('prevBtn');
            const nextBtn = document.getElementById('nextBtn');
            const pageNumbers = document.getElementById('pageNumbers');

            prevBtn.disabled = currentPage === 1;
            nextBtn.disabled = currentPage === totalPages;

            // Generate page numbers
            let pageNumbersHTML = '';
            const maxVisiblePages = 5;
            let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
            let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

            if (endPage - startPage + 1 < maxVisiblePages) {
                startPage = Math.max(1, endPage - maxVisiblePages + 1);
            }

            for (let i = startPage; i <= endPage; i++) {
                pageNumbersHTML += `
                    <button class="page-btn ${i === currentPage ? 'active' : ''}" onclick="goToPage(${i})">
                        ${i}
                    </button>
                `;
            }

            pageNumbers.innerHTML = pageNumbersHTML;
        }

        // Utility functions
        function showLoading(show) {
            document.getElementById('loading').style.display = show ? 'block' : 'none';
            document.getElementById('contentGrid').style.display = show ? 'none' : 'grid';
        }

        function showNoResults(show) {
            document.getElementById('noResults').style.display = show ? 'block' : 'none';
        }

        function showPagination(show) {
            document.getElementById('pagination').style.display = show ? 'flex' : 'none';
        }

        function scrollToTop() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        }

        // Modal functions for footer links
        function showContactModal() {
            alert('Contact us on Telegram: @your_contact_username');
        }

        function showAboutModal() {
            alert('Kannada Entertainment Hub - Your one-stop destination for Kannada movies, series, and shows. All content is sourced from public Telegram channels.');
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeModal();
            }
            if (e.key === '/') {
                e.preventDefault();
                document.getElementById('searchInput').focus();
            }
        });

        // Lazy loading for images
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        imageObserver.unobserve(img);
                    }
                });
            });
        }

        // Auto-refresh content every 30 minutes
        setInterval(() => {
            // In real implementation, fetch new content from API
            console.log('Refreshing content...');
        }, 30 * 60 * 1000);

        // Analytics tracking (optional)
        function trackEvent(eventName, eventData) {
            // Implement analytics tracking here
            console.log('Event:', eventName, eventData);
        }

        // Track content views
        function trackContentView(contentId) {
            trackEvent('content_view', { contentId });
        }

        // Track downloads
        function trackDownload(contentId, quality) {
            trackEvent('download_start', { contentId, quality });
        }

        console.log('🎬 Kannada Entertainment Blog loaded successfully!');
        console.log('📱 Features: Search, Filter, Modal views, Pagination, Responsive design');
        console.log('🤖 Bot integration ready for:', BOT_USERNAME);
    </script>
</body>
</html>
