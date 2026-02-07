"""
OAuth Provider management following Frappe's Social Login Key pattern
"""
import logging
from urllib.parse import quote, urlencode

import httpx
from cryptography.fernet import Fernet
from environs import Env

from .database import Database

_logger = logging.getLogger(__name__)


class OAuthProvider:
	id: int | None
	name: str | None
	provider_name: str | None
	client_id: str | None
	client_secret: str | None  # Will be encrypted
	base_url: str | None
	icon: str | None
	enable_social_login: bool
	custom_base_url: str | None
	authorize_url: str | None
	access_token_url: str | None
	api_endpoint: str | None
	scopes: str
	creation: str | None
	modified: str | None
	owner: str | None
	modified_by: str | None

	def __init__(self, data: dict):
		self.id = data.get("id")
		self.name = data.get("name")
		self.provider_name = data.get("provider_name")
		self.client_id = data.get("client_id")
		self.client_secret = data.get("client_secret")  # Will be encrypted
		self.base_url = data.get("base_url")
		self.icon = data.get("icon")
		self.enable_social_login = data.get("enable_social_login", True)
		self.custom_base_url = data.get("custom_base_url")
		self.authorize_url = data.get("authorize_url")
		self.access_token_url = data.get("access_token_url")
		self.api_endpoint = data.get("api_endpoint")
		self.scopes = data.get("scopes", "openid email profile")
		self.creation = data.get("creation")
		self.modified = data.get("modified")
		self.owner = data.get("owner")
		self.modified_by = data.get("modified_by")


async def create_oauth_schema(db: Database) -> None:

	await db.execute(
		"""
			CREATE TABLE IF NOT EXISTS "oauth_provider" (
				id SERIAL PRIMARY KEY,
				name TEXT NOT NULL UNIQUE,
				provider_name TEXT NOT NULL,
				client_id TEXT NOT NULL,
				client_secret BYTEA,
				base_url TEXT,
				icon TEXT,
				enable_social_login BOOLEAN NOT NULL DEFAULT TRUE,
				custom_base_url TEXT,
				authorize_url TEXT,
				access_token_url TEXT,
				api_endpoint TEXT,
				scopes TEXT DEFAULT 'openid email profile',
				creation TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
				modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
				owner TEXT NOT NULL,
				modified_by TEXT NOT NULL
			)
		"""
	)

	# Create indexes
	await db.execute(
		'CREATE INDEX IF NOT EXISTS idx_oauth_provider_name ON "oauth_provider"(name)'
	)
	await db.execute(
		'CREATE INDEX IF NOT EXISTS idx_oauth_provider_enabled ON "oauth_provider"(enable_social_login)'
	)

	_logger.info("OAuth provider schema created successfully")


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
	"""Create or update an OAuth provider"""

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
		# Create new provider
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


async def get_enabled_providers(db: Database) -> list[OAuthProvider]:
	"""Get all enabled OAuth providers (similar to Frappe's get_all query)"""

	query = """
		SELECT id, name, provider_name, client_id, client_secret, base_url, icon,
			enable_social_login, custom_base_url, authorize_url, access_token_url,
			api_endpoint, scopes, creation, modified, owner, modified_by
		FROM "oauth_provider"
		WHERE enable_social_login = TRUE
		ORDER BY name
	"""

	rows = await db.fetch_all(query)
	return [OAuthProvider(dict(row)) for row in rows]


async def get_provider_by_name(db: Database, name: str) -> OAuthProvider | None:
	query = """
		SELECT id, name, provider_name, client_id, client_secret, base_url, icon,
			enable_social_login, custom_base_url, authorize_url, access_token_url,
			api_endpoint, scopes, creation, modified, owner, modified_by
  	FROM "oauth_provider"
		WHERE name = $1 AND enable_social_login = TRUE
	"""

	row = await db.fetch_one(query, name)
	_logger.info(f"get_provider_by_name: {row}")
	return OAuthProvider(dict(row)) if row else None


def build_authorize_url(
	provider: OAuthProvider, redirect_uri: str, state: str | None = None
) -> str:
	base_url = provider.custom_base_url or provider.base_url
	if not base_url:
		raise ValueError(f"No base URL configured for provider {provider.name}")
	base_url = base_url.replace("host.docker.internal", "localhost")

	# Build full authorize URL
	if provider.authorize_url and provider.authorize_url.startswith("http"):
		auth_url = provider.authorize_url
	else:
		auth_url = f"{base_url.rstrip('/')}{provider.authorize_url}"

	params = {
		"client_id": provider.client_id,
		"response_type": "code",
		"scope": provider.scopes,
		"redirect_uri": redirect_uri,
	}

	if state:
		params["state"] = state

	return f"{auth_url}?{urlencode(params, quote_via=quote)}"


async def exchange_code_for_token(
	provider: OAuthProvider, fernet: Fernet, code: str, redirect_uri: str
) -> dict | None:
	"""Exchange authorization code for access token"""

	if not provider.client_secret:
		_logger.error(f"No client secret for provider {provider.name}")
		return None

	try:
		client_secret = fernet.decrypt(provider.client_secret).decode()
	except Exception as e:
		_logger.error(f"Failed to decrypt client secret for {provider.name}: {e}")
		return None

	base_url = provider.custom_base_url or provider.base_url or ""
	if provider.access_token_url and provider.access_token_url.startswith("http"):
		token_url = provider.access_token_url
	else:
		token_url = f"{base_url.rstrip('/')}{provider.access_token_url}"

	data = {
		"grant_type": "authorization_code",
		"code": code,
		"redirect_uri": redirect_uri,
		"client_id": provider.client_id,
		"client_secret": client_secret,
	}

	try:
		async with httpx.AsyncClient() as client:
			response = await client.post(token_url, data=data)
			if response.status_code == 200:
				return response.json()
			else:
				_logger.error(
					f"Token exchange failed for {provider.name}: {response.status_code} - {response.text}"
				)
				return None
	except httpx.ConnectError as e:
		_logger.error(f"Connection error while exchanging token for {provider.name}: {e}")
		return None
	except httpx.ReadTimeout:
		_logger.error(f"Request for exchanging token with {provider.name} timed out")
		return None
	except Exception as e:
		_logger.error(f"Token exchange error for {provider.name}: {e}")
		return None


async def get_user_info(provider: OAuthProvider, access_token: str) -> dict | None:
	base_url = provider.custom_base_url or provider.base_url or ""
	if not base_url.startswith(("http://", "https://")):
		base_url = f"http://{base_url}"
		base_url = base_url.rstrip("/")
	api_endpoint = provider.api_endpoint and provider.api_endpoint.lstrip("/")
	if not api_endpoint:
		_logger.error(f"No API endpoint configured for provider {provider.name}")
		return None
	api_url = f"{base_url}/{api_endpoint}"

	try:
		async with httpx.AsyncClient() as client:
			headers = {"Authorization": f"Bearer {access_token}"}
			response = await client.get(api_url, headers=headers)
			if response.status_code == 200:
				return response.json()
			else:
				_logger.error(
					f"User info request failed for {provider.name}: {response.status_code}"
				)
				return None
	except Exception as e:
		_logger.error(f"User info error for {provider.name}: {e}")
		return None
