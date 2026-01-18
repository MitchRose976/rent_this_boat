from pymongo import AsyncMongoClient


class AuthService:
    def __init__(self, db_client: AsyncMongoClient):
        self.db_client = db_client

    