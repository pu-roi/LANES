import sys
import os
sys.path.append(os.getcwd())
from app.core.database import SessionLocal
from app.models.comment import Comment

db = SessionLocal()
comments = db.query(Comment).order_by(Comment.id.desc()).limit(10).all()
for c in comments:
    print(f"id={c.id} post={c.post_id} parent={c.parent_id} content='{c.content}'")
