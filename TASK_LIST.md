# WhatsApp Inventory & Invoice Bots - Task List

## Phase 1: Project Setup
- [ ] Create project repository structure
- [ ] Initialize FastAPI backend with virtual environment
- [ ] Set up PostgreSQL database (local/cloud)
- [ ] Create requirements.txt with dependencies
- [ ] Set up environment variables (.env file)

## Phase 2: Database Schema & Models
- [ ] Design and create database tables:
  - [ ] `users` table (id, name, whatsapp_number, password_hash, created_at)
  - [ ] `items` table (id, name, quantity, price, created_at, updated_at)
  - [ ] `sales` table (id, customer_name, items_sold_json, total_amount, date, pdf_path, status)
  - [ ] `whatsapp_sessions` table (user_id, whatsapp_number, session_token, bot_type, expires_at, is_active)
- [ ] Create SQLAlchemy models
- [ ] Set up Alembic for database migrations

## Phase 3: Backend API Development
- [ ] Create FastAPI main application
- [ ] Implement authentication endpoints
- [ ] Create inventory management endpoints:
  - [ ] GET /items (view all items)
  - [ ] POST /items (add new item)
  - [ ] PUT /items/{id} (update item quantity/price)
  - [ ] DELETE /items/{id} (remove item)
- [ ] Create sales/invoice endpoints:
  - [ ] POST /sales (create new sale)
  - [ ] GET /sales (view sales history)
  - [ ] PUT /sales/{id}/status (update sale status)

## Phase 4: WhatsApp Integration
- [ ] Set up WhatsApp Cloud API credentials
- [ ] Create webhook endpoints:
  - [ ] POST /webhook/inventory (for stock management bot)
  - [ ] POST /webhook/invoice (for invoice generation bot)
- [ ] Implement message parsing logic:
  - [ ] Parse inventory commands (add, update, view stock)
  - [ ] Parse invoice format: "customer_name: item_name: quantity"
- [ ] Implement WhatsApp message sending functionality

## Phase 5: Invoice Generation & PDF
- [ ] Install and configure ReportLab for PDF generation
- [ ] Create PDF invoice template
- [ ] Implement invoice generation logic:
  - [ ] Parse customer order message
  - [ ] Calculate total amount
  - [ ] Generate PDF with customer details, items, total
  - [ ] Save PDF to storage
- [ ] Send PDF via WhatsApp to retailer

## Phase 6: Stock Update Logic
- [ ] Implement retailer response handling:
  - [ ] Listen for "success" response → decrease stock quantity
  - [ ] Listen for "fail" response → mark sale as failed, no stock change
  - [ ] Update sale status in database
- [ ] Add stock validation (check if sufficient quantity available)
- [ ] Implement low stock alerts

## Phase 7: Session Management
- [ ] Implement WhatsApp login system:
  - [ ] Login command with user_id and password
  - [ ] Create 24-hour session tokens
  - [ ] Session validation middleware
- [ ] Handle session expiry:
  - [ ] Auto-expire sessions after 24 hours
  - [ ] Notify users of session expiry
  - [ ] Require re-login for expired sessions

## Phase 8: Testing & Validation
- [ ] Test inventory bot commands
- [ ] Test invoice generation flow
- [ ] Test retailer success/fail responses
- [ ] Test session management
- [ ] Validate PDF generation and WhatsApp sending

## Phase 9: Optional Dashboard (React.js)
- [ ] Set up React.js frontend
- [ ] Create inventory management page
- [ ] Create sales history page
- [ ] Create user management page
- [ ] Integrate with backend APIs

## Phase 10: Deployment
- [ ] Deploy backend to cloud (Render/Railway/AWS)
- [ ] Deploy frontend to Vercel/Netlify (if created)
- [ ] Configure production database
- [ ] Update WhatsApp webhook URLs
- [ ] Set up environment variables in production

## Current Priority
Start with Phase 1 (Project Setup) and Phase 2 (Database Schema)
