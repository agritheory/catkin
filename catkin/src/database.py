import logging
from typing import Any

import asyncpg
from cryptography.fernet import Fernet
from environs import Env

_logger = logging.getLogger(__name__)


class Database:
	def __init__(self, database_url: str | None = None):
		env = Env()
		if not database_url:
			try:
				self.database_url = env.str("DATABASE_URL")
			except Exception:
				raise ValueError(
					"No DATABASE_URL environment variable set. A database connection is required."
				)
		else:
			self.database_url = database_url

		if not self.database_url.startswith("postgresql://"):
			raise ValueError(
				"Only PostgreSQL databases are supported. DATABASE_URL must start with postgresql://"
			)

		self.pool = None

	async def connect(self) -> asyncpg.Pool:
		self.pool = await asyncpg.create_pool(self.database_url)
		return self.pool

	async def disconnect(self) -> None:
		if self.pool:
			await self.pool.close()

	async def execute(self, query: str, *args: Any) -> Any:
		if self.pool is None:
			raise ValueError("Database connection pool is not initialized")

		async with self.pool.acquire() as conn:
			return await conn.execute(query, *args)

	async def fetch_one(self, query: str, *args: Any) -> Any:
		if self.pool is None:
			raise ValueError("Database connection pool is not initialized")

		async with self.pool.acquire() as conn:
			return await conn.fetchrow(query, *args)

	async def fetch_all(self, query: str, *args: Any) -> Any:
		if self.pool is None:
			raise ValueError("Database connection pool is not initialized")

		async with self.pool.acquire() as conn:
			return await conn.fetch(query, *args)


async def create_schema(db: Database) -> None:
	await db.execute(
		"""
		CREATE TABLE IF NOT EXISTS "user" (
			id SERIAL PRIMARY KEY,
			username TEXT NOT NULL UNIQUE,
			password_hash BYTEA,
			disabled BOOLEAN NOT NULL DEFAULT FALSE,
			creation TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
			modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
			owner TEXT NOT NULL,
			modified_by TEXT NOT NULL
		)
		"""
	)

	# Create indexes - matching your pattern
	await db.execute('CREATE INDEX IF NOT EXISTS idx_user_username ON "user"(username)')

	_logger.info("Database schema created successfully")


async def create_admin_user(
	db: Database, fernet: Fernet, admin_email: str, admin_password: str
) -> None:
	query = 'SELECT id FROM "user" WHERE username = $1'
	exists = await db.fetch_one(query, admin_email)

	if not exists:
		encrypted_password = (
			fernet.encrypt(admin_password.encode()) if admin_password else None
		)

		query = """
			INSERT INTO "user" (username, password_hash, disabled, owner, modified_by)
			VALUES ($1, $2, false, $3, $4)
		"""
		await db.execute(
			query,
			admin_email,
			encrypted_password,
			admin_email,
			admin_email,
		)
		_logger.info(f"{admin_email} user created successfully")


async def initialize_db() -> None:
	"""Initialize database with schema and admin user - matching your pattern"""
	env = Env()

	db = Database()
	await db.connect()

	try:
		# Create main schema
		await create_schema(db)

		# Create OAuth provider schema
		from .oauth_provider import create_default_providers, create_oauth_schema

		await create_oauth_schema(db)

		# Create admin user and OAuth providers if credentials provided
		fernet_key = env.str("FERNET_KEY", None)
		admin_email = env.str("ADMIN_EMAIL", "admin@agritheory.com")
		admin_password = env.str("ADMIN_PASSWORD", "password123")

		if fernet_key:
			fernet = Fernet(fernet_key.encode())

			# Create admin user
			if admin_email and admin_password:
				await create_admin_user(db, fernet, admin_email, admin_password)

			# Create default OAuth providers
			await create_default_providers(db, fernet)
		else:
			_logger.warning(
				"Missing FERNET_KEY - skipping admin user and OAuth provider creation"
			)

	finally:
		await db.disconnect()


async def create_default_providers(db: Database, fernet: Fernet) -> None:
	env = Env()

	# Default providers configuration
	default_providers = [
		{
			"name": "frappe",
			"provider_name": "Frappe",
			"base_url": env.str("FRAPPE_BASE_URL", None),
			"client_id": env.str("FRAPPE_CLIENT_ID", None),
			"client_secret": env.str("FRAPPE_CLIENT_SECRET", None),
			"icon": "/static/icons/frappe.svg",
			"authorize_url": "/api/method/frappe.integrations.oauth2.authorize",
			"access_token_url": "/api/method/frappe.integrations.oauth2.get_token",
			"api_endpoint": "/api/method/frappe.integrations.oauth2.openid_profile",
			"scopes": "openid email profile",
		},
		{
			"name": "google",
			"provider_name": "Google",
			"base_url": "https://accounts.google.com",
			"client_id": env.str("GOOGLE_CLIENT_ID", None),
			"client_secret": env.str("GOOGLE_CLIENT_SECRET", None),
			"icon": "/static/icons/google.svg",
			"authorize_url": "/o/oauth2/auth",
			"access_token_url": "/o/oauth2/token",
			"api_endpoint": "https://www.googleapis.com/oauth2/v2/userinfo",
			"scopes": "openid email profile",
		},
		{
			"name": "github",
			"provider_name": "GitHub",
			"base_url": "https://github.com",
			"client_id": env.str("GITHUB_CLIENT_ID", None),
			"client_secret": env.str("GITHUB_CLIENT_SECRET", None),
			"icon": "/static/icons/github.svg",
			"authorize_url": "/login/oauth/authorize",
			"access_token_url": "/login/oauth/access_token",
			"api_endpoint": "https://api.github.com/user",
			"scopes": "user:email",
		},
	]

	for provider_data in default_providers:
		if provider_data["client_id"] and provider_data["client_secret"]:
			await create_or_update_provider(db, fernet, provider_data)


async def create_or_update_provider(
	db: Database, fernet: Fernet, provider_data: dict
) -> None:
	query = 'SELECT id FROM "oauth_provider" WHERE name = $1'
	exists = await db.fetch_one(query, provider_data["name"])

	encrypted_secret = None
	if provider_data.get("client_secret"):
		encrypted_secret = fernet.encrypt(provider_data["client_secret"].encode())

	if exists:
		query = """
				UPDATE "oauth_provider"
				SET provider_name = $2, client_id = $3, client_secret = $4, base_url = $5,
						icon = $6, enable_social_login = $7, authorize_url = $8,
						access_token_url = $9, api_endpoint = $10, scopes = $11,
						modified = CURRENT_TIMESTAMP, modified_by = $12
				WHERE name = $1
				"""
		await db.execute(
			query,
			provider_data["name"],
			provider_data["provider_name"],
			provider_data["client_id"],
			encrypted_secret,
			provider_data.get("base_url"),
			provider_data.get("icon"),
			provider_data.get("enable_social_login", True),
			provider_data.get("authorize_url"),
			provider_data.get("access_token_url"),
			provider_data.get("api_endpoint"),
			provider_data.get("scopes", "openid email profile"),
			provider_data.get("owner", "system"),
		)
		_logger.info(f"Updated OAuth provider: {provider_data['name']}")
	else:
		query = """
					INSERT INTO "oauth_provider"
					(name, provider_name, client_id, client_secret, base_url, icon,
					enable_social_login, authorize_url, access_token_url, api_endpoint,
					scopes, owner, modified_by)
					VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
				"""
		await db.execute(
			query,
			provider_data["name"],
			provider_data["provider_name"],
			provider_data["client_id"],
			encrypted_secret,
			provider_data.get("base_url"),
			provider_data.get("icon"),
			provider_data.get("enable_social_login", True),
			provider_data.get("authorize_url"),
			provider_data.get("access_token_url"),
			provider_data.get("api_endpoint"),
			provider_data.get("scopes", "openid email profile"),
			provider_data.get("owner", "system"),
			provider_data.get("modified_by", "system"),
		)
		_logger.info(f"Created OAuth provider: {provider_data['name']}")
