# WhatsApp Inventory & Invoice Bots

A FastAPI-based system with two WhatsApp bots for inventory management and invoice generation for retailers.

## Bots Overview

### 1. Stock Management Bot
- Easily update inventory/stock levels
- Add, update, and view items
- Real-time stock tracking

### 2. Invoice Generation Bot
- Receives orders in format: `customer_name: item_name: quantity`
- Example: `raghav: natraj pencils: 2`
- Generates PDF invoices automatically
- Sends invoice to retailer via WhatsApp
- Handles retailer responses ("success" or "fail")
- Updates stock based on retailer confirmation

## Architecture

- **Backend**: FastAPI with PostgreSQL
- **WhatsApp Integration**: WhatsApp Cloud API
- **PDF Generation**: ReportLab
- **Authentication**: JWT tokens with 24-hour sessions
- **Database**: PostgreSQL with SQLAlchemy ORM

## Project Structure

```
whatsapp_retailer/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Configuration settings
│   │   ├── database.py          # Database connection
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── api/                 # API endpoints
│   │   ├── services/            # Business logic
│   │   ├── whatsapp/            # WhatsApp bot logic
│   │   └── utils/               # Utility functions
│   └── requirements.txt         # Python dependencies
├── storage/invoices/            # Generated PDF invoices
├── .env.example                 # Environment variables template
└── setup.sh                    # Project setup script
```

## Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL
- WhatsApp Business Account

### Installation

1. **Clone and setup the project:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual configuration
   ```

3. **Set up PostgreSQL database:**
   ```bash
   # Create database
   createdb whatsapp_retailer_db
   
   # Update .env file with your database credentials
   ```

4. **Run the application:**
   ```bash
   cd backend
   source ../venv/bin/activate
   python -m uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`

## Configuration

### Environment Variables (.env)

```bash
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/whatsapp_retailer_db

# Security
SECRET_KEY=your-super-secret-key-here

# WhatsApp API
WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token
WHATSAPP_PHONE_NUMBER_ID_INVENTORY=your_inventory_bot_phone_number_id
WHATSAPP_PHONE_NUMBER_ID_INVOICE=your_invoice_bot_phone_number_id
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_webhook_verify_token
```

### WhatsApp Setup

1. Create a WhatsApp Business Account
2. Set up two phone numbers (one for each bot)
3. Configure webhooks:
   - Inventory Bot: `https://yourdomain.com/webhook/inventory`
   - Invoice Bot: `https://yourdomain.com/webhook/invoice`
4. Add webhook verify token to `.env`

## Bot Usage

### Stock Management Bot
```
Commands:
- "add item_name quantity price" - Add new item
- "update item_name quantity" - Update stock quantity
- "view" - View all items
- "stock item_name" - Check specific item stock
```

### Invoice Generation Bot
```
Format: customer_name: item_name: quantity
Example: "raghav: natraj pencils: 2"

Bot Response:
1. Generates PDF invoice
2. Sends PDF to retailer
3. Waits for retailer response:
   - "success" → decreases stock
   - "fail" → marks sale as failed
```

## Authentication

- Users must register via web interface
- WhatsApp access requires login with user_id and password
- Sessions expire after 24 hours
- Must re-login for continued access

## API Endpoints

- `GET /` - API status
- `GET /health` - Health check
- `POST /api/auth/login` - User authentication
- `GET /api/items` - List all items
- `POST /api/items` - Add new item
- `PUT /api/items/{id}` - Update item
- `GET /api/sales` - Sales history
- `POST /webhook/inventory` - Inventory bot webhook
- `POST /webhook/invoice` - Invoice bot webhook

## Development

### Running Tests
```bash
cd backend
pytest
```

### Code Formatting
```bash
black app/
flake8 app/
```

## Dependencies

Key packages:
- `fastapi` - Web framework
- `sqlalchemy` - ORM
- `psycopg2-binary` - PostgreSQL adapter
- `reportlab` - PDF generation
- `python-jose` - JWT tokens
- `passlib` - Password hashing

## Deployment

1. **Backend**: Deploy to Render, Railway, or AWS EC2
2. **Database**: Use managed PostgreSQL service
3. **Environment**: Update webhook URLs in WhatsApp console
4. **Storage**: Configure cloud storage for PDFs (optional)

## License

This project is licensed under the MIT License.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

For support and questions, please create an issue in the repository.

---

**Phase 1 Complete** 
- [x] Project repository structure created
- [x] FastAPI backend initialized
- [x] Requirements.txt with dependencies
- [x] Environment variables setup
- [x] Database configuration ready

**Next**: Phase 2 - Database Schema & Models
