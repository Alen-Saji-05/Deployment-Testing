import os
from datetime import datetime
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# --- App Setup ---
app = Flask(__name__)

# --- Environment Configuration ---
ENV = os.environ.get('FLASK_ENV', 'development')

# Database — use DATABASE_URL (Render sets this automatically for PostgreSQL)
# Fallback to local SQLite for development
database_url = os.environ.get('DATABASE_URL', 'sqlite:///dev.db')
# Render gives postgres:// but SQLAlchemy needs postgresql://
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')

db = SQLAlchemy(app)
migrate = Migrate(app, db)


# ==================== MODELS ====================

class Category(db.Model):
    """Product category model."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    products = db.relationship('Product', backref='category', lazy=True)

    def to_dict(self):
        return {'id': self.id, 'name': self.name}


class Product(db.Model):
    """Product model with basic fields."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, default='')
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'stock': self.stock,
            'category': self.category.name if self.category else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


# ==================== ROUTES ====================

@app.route('/')
def index():
    """Health check / info endpoint."""
    return jsonify({
        'app': 'Product Store API',
        'version': '1.0',
        'environment': ENV,
        'endpoints': {
            'categories': '/api/categories',
            'products': '/api/products',
            'health': '/api/health'
        }
    })


@app.route('/api/health')
def health():
    """Health check for Render."""
    try:
        db.session.execute(db.text('SELECT 1'))
        return jsonify({'status': 'healthy', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'database': str(e)}), 500


# ---------- CATEGORY CRUD ----------

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """List all categories."""
    categories = Category.query.all()
    return jsonify([c.to_dict() for c in categories])


@app.route('/api/categories', methods=['POST'])
def create_category():
    """Create a new category."""
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'error': 'name is required'}), 400

    if Category.query.filter_by(name=data['name']).first():
        return jsonify({'error': 'Category already exists'}), 409

    category = Category(name=data['name'])
    db.session.add(category)
    db.session.commit()
    return jsonify(category.to_dict()), 201


@app.route('/api/categories/<int:cid>', methods=['PUT'])
def update_category(cid):
    """Update a category."""
    category = Category.query.get_or_404(cid)
    data = request.get_json()
    if data.get('name'):
        category.name = data['name']
    db.session.commit()
    return jsonify(category.to_dict())


@app.route('/api/categories/<int:cid>', methods=['DELETE'])
def delete_category(cid):
    """Delete a category."""
    category = Category.query.get_or_404(cid)
    db.session.delete(category)
    db.session.commit()
    return jsonify({'message': 'Category deleted'})


# ---------- PRODUCT CRUD ----------

@app.route('/api/products', methods=['GET'])
def get_products():
    """List all products with optional filters."""
    # Optional filters
    category = request.args.get('category')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    search = request.args.get('search', '')

    query = Product.query

    if category:
        query = query.join(Category).filter(Category.name.ilike(f'%{category}%'))
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))

    # Simple pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'products': [p.to_dict() for p in paginated.items],
        'total': paginated.total,
        'page': paginated.page,
        'pages': paginated.pages
    })


@app.route('/api/products/<int:pid>', methods=['GET'])
def get_product(pid):
    """Get a single product."""
    product = Product.query.get_or_404(pid)
    return jsonify(product.to_dict())


@app.route('/api/products', methods=['POST'])
def create_product():
    """Create a new product."""
    data = request.get_json()
    if not data or not data.get('name') or data.get('price') is None:
        return jsonify({'error': 'name and price are required'}), 400

    product = Product(
        name=data['name'],
        description=data.get('description', ''),
        price=data['price'],
        stock=data.get('stock', 0),
        category_id=data.get('category_id')
    )
    db.session.add(product)
    db.session.commit()
    return jsonify(product.to_dict()), 201


@app.route('/api/products/<int:pid>', methods=['PUT'])
def update_product(pid):
    """Update a product."""
    product = Product.query.get_or_404(pid)
    data = request.get_json()

    if data.get('name'):
        product.name = data['name']
    if data.get('description') is not None:
        product.description = data['description']
    if data.get('price') is not None:
        product.price = data['price']
    if data.get('stock') is not None:
        product.stock = data['stock']
    if data.get('category_id') is not None:
        product.category_id = data['category_id']

    db.session.commit()
    return jsonify(product.to_dict())


@app.route('/api/products/<int:pid>', methods=['DELETE'])
def delete_product(pid):
    """Delete a product."""
    product = Product.query.get_or_404(pid)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product deleted'})


# ==================== INIT ====================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
