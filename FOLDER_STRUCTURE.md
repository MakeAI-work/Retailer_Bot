# WhatsApp Inventory & Invoice Bots - Folder Structure

```
whatsapp_retailer/
├── README.md
├── TASK_LIST.md
├── plan.md
├── .env.example
├── .gitignore
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI application entry point
│   │   ├── config.py               # Configuration settings
│   │   ├── database.py             # Database connection setup
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py             # User model
│   │   │   ├── item.py             # Item/inventory model
│   │   │   ├── sale.py             # Sales model
│   │   │   └── session.py          # WhatsApp session model
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── user.py             # User Pydantic schemas
│   │   │   ├── item.py             # Item Pydantic schemas
│   │   │   ├── sale.py             # Sale Pydantic schemas
│   │   │   └── session.py          # Session Pydantic schemas
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py             # Authentication endpoints
│   │   │   ├── items.py            # Inventory management endpoints
│   │   │   ├── sales.py            # Sales management endpoints
│   │   │   └── webhooks.py         # WhatsApp webhook endpoints
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py     # Authentication logic
│   │   │   ├── inventory_service.py # Inventory management logic
│   │   │   ├── sales_service.py    # Sales management logic
│   │   │   └── session_service.py  # Session management logic
│   │   │
│   │   ├── whatsapp/
│   │   │   ├── __init__.py
│   │   │   ├── inventory_bot.py    # Stock management bot logic
│   │   │   ├── invoice_bot.py      # Invoice generation bot logic
│   │   │   ├── message_parser.py   # Parse WhatsApp messages
│   │   │   ├── whatsapp_client.py  # WhatsApp API client
│   │   │   └── pdf_generator.py    # PDF invoice generation
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── security.py         # Password hashing, JWT tokens
│   │       ├── helpers.py          # General utility functions
│   │       └── validators.py       # Input validation functions
│   │
│   ├── alembic/
│   │   ├── versions/               # Database migration files
│   │   ├── env.py
│   │   └── alembic.ini
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_inventory_bot.py
│   │   ├── test_invoice_bot.py
│   │   └── test_api.py
│   │
│   ├── requirements.txt            # Python dependencies
│   └── Dockerfile                 # Docker configuration (optional)
│
├── frontend/ (optional)
│   ├── public/
│   │   ├── index.html
│   │   └── favicon.ico
│   ├── src/
│   │   ├── components/
│   │   │   ├── InventoryTable.js
│   │   │   ├── SalesHistory.js
│   │   │   └── Dashboard.js
│   │   ├── pages/
│   │   │   ├── Login.js
│   │   │   ├── Inventory.js
│   │   │   └── Sales.js
│   │   ├── services/
│   │   │   └── api.js              # API calls to backend
│   │   ├── App.js
│   │   └── index.js
│   ├── package.json
│   └── package-lock.json
│
├── storage/
│   └── invoices/                   # Generated PDF invoices
│
└── docs/
    ├── API.md                      # API documentation
    ├── SETUP.md                    # Setup instructions
    └── WHATSAPP_SETUP.md          # WhatsApp API setup guide
```

## Key Files Description

### Backend Core Files
- **`main.py`**: FastAPI application entry point with route registration
- **`config.py`**: Environment variables and configuration settings
- **`database.py`**: PostgreSQL connection and session management

### WhatsApp Bot Files
- **`inventory_bot.py`**: Handles stock management commands (add, update, view)
- **`invoice_bot.py`**: Processes invoice requests and handles success/fail responses
- **`message_parser.py`**: Parses incoming WhatsApp messages
- **`pdf_generator.py`**: Generates PDF invoices using ReportLab

### Database Models
- **`user.py`**: User authentication and profile data
- **`item.py`**: Inventory items with quantity and pricing
- **`sale.py`**: Sales records with customer info and status
- **`session.py`**: WhatsApp session management with 24h expiry

### API Endpoints
- **`webhooks.py`**: WhatsApp webhook handlers for both bots
- **`items.py`**: CRUD operations for inventory management
- **`sales.py`**: Sales history and status updates
- **`auth.py`**: User authentication and session management

This structure separates concerns clearly and makes the codebase maintainable and scalable.
