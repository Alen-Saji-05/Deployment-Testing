# Product Store API — Week 12: Deployment

A simple Flask REST API with PostgreSQL, deployed on **Render (Free Tier)**.

## Features

- Full CRUD for **Products** and **Categories**
- PostgreSQL in production, SQLite for local development
- Search, filter, and pagination
- Environment-based configuration (dev/prod)
- Gunicorn production server
- Health check endpoint

---

## Tech Stack

| Component       | Technology              |
|-----------------|-------------------------|
| Backend         | Flask 3.0               |
| Database (Dev)  | SQLite                  |
| Database (Prod) | PostgreSQL (Render Free)|
| Server          | Gunicorn                |
| Hosting         | Render                  |

---

## API Endpoints

| Method | Endpoint                  | Description            |
|--------|---------------------------|------------------------|
| GET    | `/`                       | App info               |
| GET    | `/api/health`             | Health check           |
| GET    | `/api/categories`         | List categories        |
| POST   | `/api/categories`         | Create category        |
| PUT    | `/api/categories/<id>`    | Update category        |
| DELETE | `/api/categories/<id>`    | Delete category        |
| GET    | `/api/products`           | List products (paginated) |
| GET    | `/api/products/<id>`      | Get single product     |
| POST   | `/api/products`           | Create product         |
| PUT    | `/api/products/<id>`      | Update product         |
| DELETE | `/api/products/<id>`      | Delete product         |

### Query Parameters (GET /api/products)

- `search` — Filter by product name
- `category` — Filter by category name
- `min_price` / `max_price` — Price range filter
- `page` / `per_page` — Pagination (default: page=1, per_page=10)

---

## Local Development

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run locally (uses SQLite)
python app.py
```

Server runs at `http://localhost:5000`

---

## Deployment Guide (Render Free Tier)

### Step 1: Push to GitHub

```bash
cd "week 11"
git init
git add .
git commit -m "Initial commit - Product Store API"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### Step 2: Create PostgreSQL Database on Render

1. Go to [https://render.com](https://render.com) and sign in
2. Click **New** → **PostgreSQL**
3. Fill in:
   - **Name**: `product-store-db`
   - **Database**: `product_store`
   - **User**: `admin`
   - **Plan**: **Free**
4. Click **Create Database**
5. Copy the **Internal Database URL** (starts with `postgresql://...`)

### Step 3: Create Web Service on Render

1. Click **New** → **Web Service**
2. Connect your GitHub repo
3. Configure:
   - **Name**: `product-store-api`
   - **Runtime**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Plan**: **Free**
4. Add **Environment Variables**:

   | Key           | Value                                    |
   |---------------|------------------------------------------|
   | `DATABASE_URL`| *(paste Internal Database URL from Step 2)* |
   | `FLASK_ENV`   | `production`                             |
   | `SECRET_KEY`  | *(click Generate)*                       |
   | `PYTHON_VERSION` | `3.11.6`                              |

5. Click **Create Web Service**

### Step 4: Initialize Database Tables

After first deploy, go to your Web Service → **Shell** tab and run:

```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### Step 5: Verify

Visit your Render URL:
- `https://your-app.onrender.com/` — Should show app info
- `https://your-app.onrender.com/api/health` — Should show `{"status": "healthy"}`

---

## Alternative: One-Click Deploy with render.yaml

If you have the `render.yaml` (included), you can use Render's **Blueprint** feature:

1. Go to Render Dashboard → **Blueprints**
2. Connect repo → Render auto-detects `render.yaml`
3. Click **Apply** — it creates both DB and web service automatically

---

## Environment Variables

| Variable        | Dev Default            | Production              |
|-----------------|------------------------|-------------------------|
| `FLASK_ENV`     | `development`          | `production`            |
| `DATABASE_URL`  | `sqlite:///dev.db`     | Render PostgreSQL URL   |
| `SECRET_KEY`    | `dev-secret-key...`    | Auto-generated on Render|

---

## Example API Usage

### Create a Category
```bash
curl -X POST https://your-app.onrender.com/api/categories \
  -H "Content-Type: application/json" \
  -d '{"name": "Electronics"}'
```

### Create a Product
```bash
curl -X POST https://your-app.onrender.com/api/products \
  -H "Content-Type: application/json" \
  -d '{"name": "Laptop", "price": 999.99, "stock": 10, "category_id": 1}'
```

### List Products with Filters
```bash
curl "https://your-app.onrender.com/api/products?search=laptop&min_price=500&page=1"
```

---

## Project Structure

```
week 11/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── render.yaml         # Render deployment blueprint
├── build.sh            # Build script for Render
├── .env.example        # Environment variable template
├── .gitignore          # Git ignore rules
└── README.md           # This file (deployment guide)
```

---

## License

This project is for educational purposes (Week 12 Assignment).
