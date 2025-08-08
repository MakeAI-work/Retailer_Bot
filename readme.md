# Smart Inventory & Billing on WhatsApp: End-to-End Plan

## Notes
- Two WhatsApp bots: Inventory Bot (stock management) and Billing Bot (billing/invoicing).
- Backend: FastAPI; Database: PostgreSQL; Frontend: React.js dashboard.
- Security requirement: Users must register on website to create a profile in the DB; WhatsApp bot access requires user_id and password activation.
- Both bots connect to the same DB; all state is centralized.
- WhatsApp users must log in every 24 hours; session expires after 24 hours of inactivity.
- WhatsApp session management: Sessions tracked in DB, expire after 24h, must re-login explicitly (no auto-extension).
- WhatsApp integration via Twilio or WhatsApp Cloud API.
- PDF invoice generation with ReportLab; files can be sent via WhatsApp (direct or via cloud storage link).

## Task List
- [ ] Project Setup
  - [ ] Create GitHub repo
  - [ ] Initialize FastAPI backend (app/ folder)
  - [ ] Set up React.js frontend
  - [ ] Set up PostgreSQL instance
- [ ] Database Schema Design
  - [ ] users table (id, name, whatsapp_number, role, password hash, etc.)
  - [ ] items table (id, name, quantity, price)
  - [ ] sales table (id, customer_name, items_sold [JSON], total_amount, date)
- [ ] Backend API Development
  - [ ] Set up SQLAlchemy ORM & Alembic migrations
  - [ ] Implement user registration & authentication endpoints
  - [ ] Inventory Bot webhook: /webhook/inventory
    - [ ] Parse add/update/view commands (parser.py)
    - [ ] Stock DB operations
    - [ ] WhatsApp confirmation
  - [ ] Billing Bot webhook: /webhook/billing
    - [ ] Parse bill command (customer, items)
    - [ ] Check stock, deduct, record sale
    - [ ] Generate PDF invoice (pdf_generator.py)
    - [ ] Send PDF via WhatsApp
- [ ] WhatsApp Integration
  - [ ] Register two sender numbers (Twilio/Meta)
  - [ ] Configure webhooks for each bot
  - [ ] Implement WhatsApp API send logic (text & document)
- [ ] WhatsApp Session Management
  - [ ] Design whatsapp_sessions table (user_id, whatsapp_number, session_token, bot_type, created_at, last_activity, expires_at, is_active)
  - [ ] Implement login command for WhatsApp bots (creates session, 24h expiry)
  - [ ] Middleware to check session validity on every WhatsApp command
  - [ ] Notify user on session expiry or near-expiry
  - [ ] Dashboard: List/expire sessions (admin)
- [ ] PDF Invoice Generation
  - [ ] Implement invoice PDF creation (ReportLab)
  - [ ] Add QR code (optional)
  - [ ] Store/send PDF (local or cloud)
- [ ] React.js Dashboard
  - [ ] Inventory Management page (view/add/update items)
  - [ ] Sales History page (view/download bills)
  - [ ] Reports page (low stock, monthly sales)
  - [ ] Integrate with backend APIs
- [ ] Deployment
  - [ ] Backend: Render/Railway/AWS EC2
  - [ ] Frontend: Vercel/Netlify
  - [ ] Update WhatsApp webhook URLs in provider console

## Current Goal
Finalize and scaffold project structure, DB schema, and WhatsApp session logic.what