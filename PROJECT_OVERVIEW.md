# Sage Inventory System

A full-stack inventory management application built with Django REST Framework backend and vanilla JavaScript frontend. Features role-based access control, real-time stock tracking, and Progressive Web App capabilities.

## Architecture

### Backend — Django + PostgreSQL

The backend is a Django application using Django REST Framework (DRF) for API endpoints and Token Authentication for stateless client authentication. PostgreSQL serves as the primary database.

#### Models

| Model | Purpose | Key Fields |
|---|---|---|
| **User** | Custom auth with roles | `username`, `password`, `role` (ceo/coo/cto/manager/staff), `location` (FK) |
| **Location** | Business locations | `name`, `address`, `contact`, `is_active` |
| **Vendor** | Suppliers of products | `name`, `contact`, `address`, `location` (FK), `user` (FK) |
| **Product** | Items in inventory | `name`, `description`, `price`, `vendor` (FK), `location` (FK) |
| **Stock** | Current quantity tracking | `product` (OneToOne), `quantity`, `last_updated`, `updated_by` (FK), `location` (FK) |
| **MissingStock** | Discrepancy reports | `product` (FK), `quantity_missing`, `date_reported`, `action_taken`, `location` (FK) |
| **MissingStockLog** | Audit trail for missing stock | `missing_stock` (FK), `quantity`, `note`, `updated_by` (FK), `location` (FK) |
| **DeliveryEntry** | Delivery records | `vendor`, `product`, `price`, `delivery_fee`, `quantity`, `rider`, `delivery_location`, `date`, `location` (FK) |
| **Expense** | Expense records | `description`, `amount`, `date`, `location` (FK) |

**Relationships:**
- A `Location` has many `User`, `Vendor`, `Product`, `Stock`, `MissingStock`, `DeliveryEntry`, `Expense` records
- A `User` has a `role` and optionally a `location` (null for multi-location roles)
- A `User` creates/manages multiple `Vendor` records
- A `Vendor` supplies multiple `Product` records
- Each `Product` has exactly one `Stock` record (OneToOne)
- A `Product` can have multiple `MissingStock` reports over time
- `Stock.updated_by` tracks which user last modified the quantity

#### API Endpoints

All API routes are prefixed with `/api/`.

| Method | Endpoint | Access | Description |
|---|---|---|---|
| POST | `/api/auth/login/` | Public | Username/password login, returns auth token |
| POST | `/api/auth/register/` | CEO / Superuser only | Create new user accounts with role and location |
| GET | `/api/user/` | Authenticated | Returns current user info including role and location flags |
| GET/POST | `/api/locations/` | Authenticated | List / Add locations (CEO/COO/CTO see all; others see assigned) |
| GET | `/api/vendors/` | Authenticated | List all vendors |
| POST | `/api/vendors/` | Superuser only | Create new vendor |
| GET/PUT/DELETE | `/api/vendors/<id>/` | Authenticated | Retrieve, update, or delete a vendor |
| GET | `/api/products/` | Authenticated | List all products |
| POST | `/api/products/` | Authenticated | Create new product |
| GET/PUT/DELETE | `/api/products/<id>/` | Authenticated | Retrieve, update, or delete a product |
| GET | `/api/stock/` | Authenticated | List all stock records |
| POST | `/api/stock/` | Authenticated | Create or link a stock record to a product |
| GET | `/api/stock/<id>/` | Authenticated | Retrieve a specific stock record |
| PATCH | `/api/stock/<id>/` | Authenticated | Update stock quantity (sets `updated_by` to current user) |
| GET | `/api/missing-stock/` | Authenticated | List all missing stock reports |
| POST | `/api/missing-stock/` | Superuser only | Report missing stock |

**Authentication:** All authenticated endpoints require an `Authorization: Token <token>` header. The token is obtained from the login endpoint and stored in the client's `localStorage`.

**Permissions:**
- `IsAuthenticated` — any logged-in user (superuser or regular)
- `IsAdminUser` — superuser only (`is_superuser=True`)

### Frontend — Vanilla JavaScript + HTML5 + CSS3

The frontend is a single-page-style experience served through static HTML files. There is no frontend framework — all interactivity is built with vanilla JavaScript using the Fetch API.

#### Pages

| Page | Route | Purpose |
|---|---|---|
| **Login** | `/` | Authentication form, token storage, redirect to dashboard |
| **Dashboard** | `/dashboard/` | Overview with summary cards (vendor count, product count, stock count) |
| **Vendors** | `/vendors/` | CRUD operations for vendors |
| **Products** | `/products/` | CRUD operations for products |
| **Stock** | `/stock/` | View and update stock quantities |
| **Missing Stock** | `/missing-stock/` | View and report missing stock (superuser only) |

#### JavaScript Architecture

The frontend is organized into modular scripts:

**`auth.js`** — Authentication state management
- Reads/writes the DRF token to `localStorage`
- Decodes the token payload to extract `username` and `is_superuser`
- Provides `isSuperuser()` check used across all pages
- Handles logout (clear token, redirect to login)
- Auto-redirects logged-in users away from login page

**`api.js`** — HTTP client wrapper
- `apiGet()`, `apiPost()`, `apiPut()`, `apiPatch()`, `apiDelete()`
- Automatically attaches `Authorization: Token <token>` header from `localStorage`
- Handles 401 Unauthorized responses by clearing the token and redirecting to login
- All responses parsed as JSON

**`utils.js`** — Shared utilities
- `showNotification()` — Toast messages for success/error feedback
- `hideSuperuserElements()` — Hides DOM elements marked with `data-superuser-only` when the current user is not a superuser
- `formatDate()` — ISO string to human-readable format
- `escapeHtml()` — Basic XSS prevention for rendering user-generated content

**Page-specific scripts** (`dashboard.js`, `vendors.js`, `products.js`, `stock.js`, `missing-stock.js`)
- Each page has its own script that runs on `DOMContentLoaded`
- Fetches data from the relevant API endpoint
- Renders data into HTML tables
- Attaches event listeners for forms, buttons, and inline edits
- Calls `hideSuperuserElements()` on load to enforce UI-level permissions

#### CSS Architecture

The stylesheet uses CSS custom properties for a consistent design system:

- **Sidebar:** Fixed 240px dark panel with navigation links. Collapses to a hamburger menu on screens below 768px.
- **Header:** Top bar showing current user name and logout button.
- **Content area:** Light background with card-based layouts.
- **Tables:** Full-width with hover states, action buttons per row.
- **Forms:** Consistent input styling with focus states.
- **Modals:** Overlay forms for add/edit operations.
- **Notifications:** Fixed-position toast bar for API feedback.

### Progressive Web App (PWA)

The app is installable on mobile and desktop through PWA configuration:

**`manifest.json`**
- Defines app name (`Sage Inventory`), short name (`SageInv`), theme colors, and start URL
- Configures `display: standalone` for a native-app feel

**`service-worker.js`**
- **Install phase:** Precaches all static assets (HTML pages, CSS, JS) into a Cache Storage bucket
- **Fetch phase:**
  - API requests use a **network-first** strategy (fetch from network, fall back to cache if offline)
  - Static assets use a **cache-first** strategy (serve from cache, update in background)
- **Activate phase:** Cleans up old cache versions

**Registration:** Each HTML page registers the service worker via a small inline script or shared `pwa.js`.

### User Roles & Permissions

| Feature | CEO / Superuser | COO | CTO | Manager | Staff |
|---|---|---|---|---|---|
| All Locations | ✅ | ✅ | ✅ | ❌ | ❌ |
| Vendors | ✅ | ✅ | ❌ | ✅* | ✅* |
| Products | ✅ | ✅ | ❌ | ✅* | ✅* |
| Stock | ✅ | ✅ | ❌ | ✅* | ✅* |
| Deliveries | ✅ | ✅ | ✅ | ✅* | ✅* |
| Expenses | ✅ | ✅ | ✅ | ✅* | ✅* |
| Report / Calculations | ✅ | ❌ | ✅ | ✅* | ✅* |
| Missing Stock | ✅ | ✅ | ❌ | ❌ | ❌ |
| Register Users | ✅ | ❌ | ❌ | ❌ | ❌ |

\* Manager and Staff access is restricted to their **assigned location only**.

**Role Hierarchy:**
- **CEO / Superuser:** Full access to all locations and all data
- **COO:** Access to all locations, operations-focused (vendors, products, stock, deliveries, expenses, missing stock)
- **CTO:** Access to all locations, calculations-focused (reports, expenses, deliveries, payment service)
- **Manager:** Access to assigned location only, all endpoints within that location
- **Staff:** Access to assigned location only, all endpoints within that location

**Enforcement happens at three levels:**
1. **Backend:** Viewsets filter queryset by user role and location. `can_access_missing_stock`, `can_access_operations`, `can_access_calculations` properties control endpoint access.
2. **Frontend:** JavaScript stores role flags in `localStorage` and hides/shows navigation items and page guards based on role.
3. **Location Filter:** Users with multi-location access (CEO, COO, CTO) see a location dropdown in the navbar to filter data by specific location.

### Data Flow

1. User opens `/` (login page)
2. If no token in `localStorage`, show login form
3. User submits credentials → POST to `/api/auth/login/` → receives token
4. Token stored in `localStorage`, user redirected to `/dashboard/`
5. Dashboard fetches counts from `/api/vendors/`, `/api/products/`, `/api/stock/`
6. User navigates to other pages via sidebar links
7. Each page fetches its own data on load and renders tables
8. Forms submit via Fetch API, on success the table refreshes and a toast notification appears
9. On 401 response from any API call, token is cleared and user is redirected to login

### Security Considerations

- **Token storage:** DRF tokens are stored in `localStorage`. This is acceptable for this use case but would be hardened with httpOnly cookies in a production environment.
- **CSRF:** Not needed for token-authenticated API calls (DRF TokenAuthentication is stateless).
- **XSS:** User-generated content (vendor names, product descriptions) is escaped before DOM insertion via `escapeHtml()`.
- **Authorization:** Backend permissions are the source of truth. Frontend UI hiding is a convenience, not a security mechanism.
- **SQL Injection:** Protected by Django ORM (all queries use parameterized statements).

### Deployment Notes

- **Database:** PostgreSQL connection configured via environment variables (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`)
- **Static files:** Collected to `staticfiles/` directory for production serving
- **Secret key:** Must be overridden via `DJANGO_SECRET_KEY` environment variable in production
- **Debug mode:** Controlled by `DJANGO_DEBUG` environment variable
- **Allowed hosts:** Configured via `DJANGO_ALLOWED_HOSTS` environment variable
