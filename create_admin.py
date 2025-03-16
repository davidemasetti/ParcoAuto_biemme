from app import create_app, db
from models import User

app = create_app()

with app.app_context():
    # Create admin user
    admin = User(
        username='ciao@wearefluo.com',
        email='ciao@wearefluo.com'
    )
    admin.set_password('Telecomando22')
    
    # Add to database
    db.session.add(admin)
    db.session.commit()
    print("Admin user created successfully!")
