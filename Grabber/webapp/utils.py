def get_user_id_query(user_id) -> dict:
    """Returns a MongoDB query dict that matches user IDs stored as int or string."""
    try:
        uid_int = int(user_id)
        return {"id": {"$in": [uid_int, str(uid_int)]}}
    except (ValueError, TypeError):
        return {"id": str(user_id)}
