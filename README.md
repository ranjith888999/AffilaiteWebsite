# Affiliate Deals Hub

A comprehensive affiliate marketing website built with FastAPI, PostgreSQL, and Cuelinks API integration. Features a beautiful, responsive design with real-time chat support for finding the best deals and offers.

## 🚀 Features

- **Fast & Modern**: Built with FastAPI for high performance
- **Beautiful UI**: Responsive design with smooth animations
- **Real-time Chat**: AI-powered assistant to help users find offers
- **Enhanced Search**: Search by campaign name, description, or title
- **Affiliate Link Generator**: Convert any URL to affiliate links
- **Category Filtering**: Browse offers by categories
- **Live Data**: Real-time sync with Cuelinks API
- **PostgreSQL Database**: Robust data storage and retrieval

## 🛠️ Tech Stack

- **Backend**: FastAPI, Python 3.8+
- **Database**: PostgreSQL (Supabase)
- **API Integration**: Cuelinks API v2
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Styling**: Custom CSS with animations
- **Icons**: Font Awesome
- **Deployment**: Ready for cloud deployment

## 📁 Project Structure

```
affiliate-website/
├── app/
│   ├── controllers/          # API route handlers
│   │   ├── campaigns_controller.py
│   │   ├── offers_controller.py
│   │   ├── chat_controller.py
│   │   └── links_controller.py
│   ├── models/              # Database models
│   │   └── database.py
│   ├── services/            # Business logic
│   │   ├── cuelinks_service.py
│   │   ├── chat_service.py
│   │   ├── rag_service.py
│   │   └── ultra_fast_service.py
│   └── database.py          # Database configuration
├── templates/               # Jinja2 HTML templates
│   ├── base.html
│   ├── index.html
│   ├── offers.html
│   ├── categories.html
│   ├── chat.html
│   └── link_generator.html
├── static/                  # Static assets
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   ├── main.js
│   │   └── chat.js
│   └── images/
├── scripts/                 # Database management scripts
│   ├── migrate_database.py
│   ├── reset_and_rebuild_db.py
│   └── rebuild_embeddings.py
├── main.py                  # Application entry point
├── manage_database.bat      # Database management utility
└── requirements.txt         # Python dependencies
```

## 🔍 New Search Improvements

The chat search functionality has been enhanced to provide better results:

- **Campaign Name Search**: Now searches by campaign/merchant name (e.g., "Nykaa offers")
- **Proper Database Relationships**: Campaign and Offer tables now have proper relationships
- **Enhanced Embeddings**: Search embeddings include campaign information
- **Ultra-Fast Search**: Optimized SQL queries for quick results
- **Fallback Mechanisms**: Multiple search strategies for comprehensive results

## 🗄️ Database Management

A new database management utility has been added:

```bash
# Run the database management utility
./manage_database.bat
```

Options include:
1. Migrate existing database (preserves data)
2. Reset and rebuild database (WARNING: Deletes all data)
3. Rebuild embeddings (updates search functionality)
│   └── js/
│       └── main.js
├── main.py                  # FastAPI application
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables
└── populate_db.py          # Database population script
```

## 🔧 Installation & Setup

### Prerequisites

- Python 3.8 or higher
- PostgreSQL database
- Cuelinks API key

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd affiliate-website
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On macOS/Linux
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```env
# Database Configuration - Supabase
DATABASE_HOST=db.yyksfmfrsiewpiwajtzw.supabase.co
DATABASE_PORT=5432
DATABASE_NAME=postgres
DATABASE_USER=postgres
DATABASE_PASSWORD=Ranjith123

# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://yyksfmfrsiewpiwajtzw.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl5a3NmbWZyc2lld3Bpd2FqdHp3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM1MjYzMjMsImV4cCI6MjA2OTEwMjMyM30.qXUi52X7HNChoCyiroSX5Nh48PZlNfVWhzkNquHh130

# Cuelinks API Configuration
CUELINKS_API_KEY=MUmQPF2MLjDzMOHi0PSCdOwI082JAfj6vRLLT1QcY00
CUELINKS_BASE_URL=https://www.cuelinks.com/api/v2

# Application Configuration
SECRET_KEY=your-secret-key-here
DEBUG=True
```

### Step 5: Populate Database

```bash
python populate_db.py
```

### Step 6: Run the Application

```bash
python main.py
```

The application will be available at `http://localhost:8000`

## 🌐 API Endpoints

### Campaigns
- `GET /api/campaigns/` - Get campaigns from Cuelinks API
- `GET /api/campaigns/all` - Get all campaigns including paused ones
- `GET /api/campaigns/database` - Get campaigns from local database

### Offers
- `GET /api/offers/` - Get offers from Cuelinks API
- `GET /api/offers/database` - Get offers from local database
- `GET /api/offers/categories` - Get available categories
- `GET /api/offers/featured` - Get featured offers

### Chat
- `POST /api/chat/` - Send chat message
- `GET /api/chat/history/{session_id}` - Get chat history

### Links
- `POST /api/links/` - Generate affiliate link
- `GET /api/links/history` - Get link generation history

## 🎨 Features Overview

### Homepage
- Hero section with animated floating cards
- Popular categories grid
- Featured offers showcase
- Statistics counter animation
- Call-to-action sections

### Offers Page
- Advanced filtering and search
- Pagination
- Category filtering
- Responsive grid layout
- Copy coupon functionality

### Chat Support
- Real-time messaging interface
- AI-powered offer recommendations
- Session-based conversations
- Quick action buttons
- Typing indicators

### Link Generator
- Convert any URL to affiliate link
- Optional URL shortening
- Sub ID tracking
- Link history
- Copy to clipboard functionality

### Categories Page
- Visual category browsing
- Offer count per category
- Dynamic offer loading
- Smooth animations

## 🔐 Environment Configuration

The application uses the following environment variables:

- `DATABASE_*`: PostgreSQL connection parameters
- `CUELINKS_API_KEY`: Your Cuelinks API key
- `CUELINKS_BASE_URL`: Cuelinks API base URL
- `SECRET_KEY`: Application secret key
- `DEBUG`: Debug mode flag

## 📱 Responsive Design

The website is fully responsive and works on:
- Desktop computers
- Tablets
- Mobile phones
- All modern browsers

## 🚀 Deployment

### Prepare for Deployment

1. Set `DEBUG=False` in production
2. Configure production database
3. Set up SSL certificates
4. Configure reverse proxy (nginx)

### Deploy to Cloud

The application is ready for deployment on:
- Heroku
- Digital Ocean
- AWS
- Google Cloud Platform
- Azure

## 🔧 Customization

### Adding New Features

1. Create new controllers in `app/controllers/`
2. Add database models in `app/models/database.py`
3. Implement business logic in `app/services/`
4. Create templates in `templates/`
5. Add routes to `main.py`

### Styling

- Modify `static/css/style.css` for styling changes
- Update `static/js/main.js` for JavaScript functionality
- Add new animations using Animate.css classes

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Check database credentials in `.env`
   - Ensure PostgreSQL is running
   - Verify network connectivity

2. **API Key Issues**
   - Verify Cuelinks API key is correct
   - Check API key permissions
   - Ensure API key is not expired

3. **Import Errors**
   - Activate virtual environment
   - Install all dependencies
   - Check Python path

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support and questions:
- Check the documentation
- Review the troubleshooting section
- Contact the development team

## 🚀 Future Enhancements

- [ ] User authentication system
- [ ] Advanced analytics dashboard
- [ ] Email marketing integration
- [ ] Social media sharing
- [ ] Advanced caching
- [ ] API rate limiting
- [ ] Multi-language support
- [ ] Mobile app

---

Built with ❤️ using FastAPI and modern web technologies.
