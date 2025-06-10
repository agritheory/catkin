# mypy: disable-error-code="misc"

import logging
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import jwt
import uvicorn
from cryptography.fernet import Fernet
from environs import Env
from quart import Quart, make_response, redirect, render_template, request, url_for
from quart.typing import ResponseTypes

from .database import Database, initialize_db
from .oauth_provider import (
	build_authorize_url,
	exchange_code_for_token,
	get_enabled_providers,
	get_provider_by_name,
	get_user_info,
)

_logger = logging.getLogger(__name__)

catkin_dir = Path(__file__).parent.parent

app = Quart(
	__name__,
	template_folder=str(catkin_dir / "templates"),
	static_folder=str(catkin_dir / "static"),
)

env = Env()
try:
	DATABASE_URL = env.str("DATABASE_URL")
except Exception:
	raise ValueError(
		"No DATABASE_URL environment variable set. A database connection is required."
	)

JWT_SECRET = env.str("JWT_SECRET", "your-secret-key-change-in-production")
FERNET_KEY = env.str("FERNET_KEY", None)
DEFAULT_REDIRECT = env.str("DEFAULT_REDIRECT", "/")

db = Database(DATABASE_URL)
fernet = None

if FERNET_KEY:
	fernet = Fernet(FERNET_KEY.encode())


async def get_user_by_username(username: str) -> Any:
	"""Get user from database by username - matching your pattern"""
	query = """
		SELECT id, username, password_hash, disabled, creation, modified, owner, modified_by
		FROM "user"
		WHERE username = $1 AND disabled = FALSE
	"""
	return await db.fetch_one(query, username)


async def verify_password(password: str, encrypted_password: bytes) -> bool:
	"""Verify password using Fernet decryption - matching your pattern"""
	if not fernet or not encrypted_password:
		return False

	try:
		decrypted_password = fernet.decrypt(encrypted_password).decode()
		return decrypted_password == password
	except Exception:
		return False


def create_jwt_token(user_id: int, username: str) -> str:
	"""Create JWT token for user"""
	payload = {
		"user_id": user_id,
		"username": username,
		"exp": datetime.utcnow() + timedelta(hours=24),
	}
	return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def verify_jwt_token(token: str) -> dict | None:
	"""Verify and decode JWT token"""
	try:
		return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
	except jwt.InvalidTokenError:
		return None


@app.before_serving
async def startup() -> None:
	await db.connect()
	try:
		await initialize_db()
		_logger.info("Database initialization completed")
	except Exception as e:
		_logger.error(f"Database initialization failed: {e}")


@app.route("/")
async def index() -> str:
	"""Simple home page"""
	return "<h1>Auth Server Running</h1><p><a href='/auth/login'>Login</a></p>"


@app.route("/auth/login", methods=["GET"])
async def login_page() -> str:
	"""Display login form with OAuth providers"""
	redirect_url = request.args.get("redirect", DEFAULT_REDIRECT)
	error = request.args.get("error")

	try:
		oauth_providers = await get_enabled_providers(db)
	except Exception as e:
		_logger.error(f"Failed to get OAuth providers: {e}")
		oauth_providers = []

	return await render_template(
		"login.html", redirect_url=redirect_url, error=error, oauth_providers=oauth_providers
	)


@app.route("/auth/login", methods=["POST"])
async def handle_login() -> ResponseTypes:
	"""Handle login form submission"""
	form = await request.form
	username: str = form.get("username")  # type: ignore
	password: str = form.get("password")  # type: ignore
	redirect_url: str = form.get("redirect", DEFAULT_REDIRECT)

	try:
		user = await get_user_by_username(username)

		if user and await verify_password(password, user["password_hash"]):
			token = create_jwt_token(user["id"], user["username"])

			response = await make_response(redirect(redirect_url))
			response.set_cookie(
				"auth_token",
				token,
				max_age=86400,  # 24 hours
				httponly=True,
				secure=False,  # Set to True in production with HTTPS
				samesite="Lax",
			)
			return response
		else:
			return redirect(f"/auth/login?error=Invalid credentials&redirect={redirect_url}")

	except Exception as e:
		_logger.error(f"Login error: {e}")
		return redirect(f"/auth/login?error=Login failed&redirect={redirect_url}")


@app.route("/health", methods=["GET"])
async def health() -> ResponseTypes:
	"""Health check endpoint for load balancers and monitoring"""
	return await make_response("OK", 200)


@app.route("/auth/verify", methods=["GET"])
async def verify() -> ResponseTypes:
	"""Caddy forward_auth endpoint - checks if user is authenticated"""
	token = request.cookies.get("auth_token")

	if token:
		payload = verify_jwt_token(token)
		if payload:
			response = await make_response("", 200)
			response.headers["X-User-Email"] = payload["username"]
			response.headers["X-User-ID"] = str(payload["user_id"])
			response.headers["X-Auth-Method"] = "jwt"
			return response

	# For forward_auth, return a redirect to login when not authenticated
	# Caddy's forward_auth automatically sets X-Forwarded-Uri
	original_uri = request.headers.get("X-Forwarded-Uri", "/")
	redirect_url = f"/auth/login?redirect={original_uri}"
	return await make_response("", 302, {"Location": redirect_url})


@app.route("/auth/oauth/<provider_name>")
async def oauth_login(provider_name: str) -> ResponseTypes:
	try:
		provider = await get_provider_by_name(db, provider_name)

		if not provider:
			_logger.error(f"Provider '{provider_name}' not found in database")
			return redirect(url_for("login_page", error=f"Provider {provider_name} not found"))

		redirect_uri = request.url_root.rstrip("/") + f"/auth/oauth/{provider_name}/callback"
		state = secrets.token_urlsafe(32)
		original_redirect = request.args.get("redirect", DEFAULT_REDIRECT)

		state_data = {
			"state": state,
			"redirect": original_redirect,
			"exp": datetime.utcnow() + timedelta(minutes=10),
		}
		state_token = jwt.encode(state_data, JWT_SECRET, algorithm="HS256")
		auth_url = build_authorize_url(provider, redirect_uri, state)

		response = await make_response(redirect(auth_url))
		response.set_cookie("oauth_state", state_token, max_age=600, httponly=True)
		return response

	except Exception as e:
		_logger.error(f"OAuth login error for {provider_name}: {e}", exc_info=True)
		return redirect(url_for("login_page", error="OAuth login failed"))


@app.route("/auth/oauth/<provider_name>/callback")
async def oauth_callback(provider_name: str) -> ResponseTypes:
	try:
		provider = await get_provider_by_name(db, provider_name)
		if not provider:
			return redirect(url_for("login_page", error=f"Provider {provider_name} not found"))

		code = request.args.get("code")
		returned_state = request.args.get("state")

		if not code:
			error_desc = request.args.get("error_description", "Authorization failed")
			return redirect(url_for("login_page", error=error_desc))

		state_cookie = request.cookies.get("oauth_state")
		if not state_cookie:
			return redirect(url_for("login_page", error="Invalid OAuth state"))

		try:
			state_data = jwt.decode(state_cookie, JWT_SECRET, algorithms=["HS256"])
			if state_data.get("state") != returned_state:
				return redirect(url_for("login_page", error="OAuth state mismatch"))
			original_redirect = state_data.get("redirect", DEFAULT_REDIRECT)
		except jwt.InvalidTokenError:
			return redirect(url_for("login_page", error="Invalid OAuth state token"))

		if not fernet:
			_logger.error("Fernet key is not configured, cannot decrypt state")
			return redirect(url_for("login_page", error="OAuth configuration error"))

		redirect_uri = request.url_root.rstrip("/") + f"/auth/oauth/{provider_name}/callback"
		token_data = await exchange_code_for_token(provider, fernet, code, redirect_uri)

		if not token_data or "access_token" not in token_data:
			return redirect(url_for("login_page", error="Failed to get access token"))

		user_info = await get_user_info(provider, token_data["access_token"])
		if not user_info:
			return redirect(url_for("login_page", error="Failed to get user information"))

		email = extract_email_from_user_info(provider_name, user_info)
		if not email:
			return redirect(url_for("login_page", error="No email found in OAuth response"))

		user = await get_or_create_oauth_user(email, user_info, provider_name)
		if not user:
			return redirect(url_for("login_page", error="Failed to create user account"))

		token = create_jwt_token(user["id"], user["username"])

		response = await make_response(redirect(original_redirect))
		response.set_cookie(
			"auth_token",
			token,
			max_age=86400,  # 24 hours
			httponly=True,
			secure=False,  # Set to True in production with HTTPS
			samesite="Lax",
		)
		response.set_cookie("oauth_state", "", expires=0)
		return response

	except Exception as e:
		_logger.error(f"OAuth callback error for {provider_name}: {e}")
		return redirect(url_for("login_page", error="OAuth authentication failed"))


def extract_email_from_user_info(provider_name: str, user_info: dict) -> str:
	return user_info.get("email") or user_info.get("mail") or user_info.get("emailAddress")  # type: ignore


async def get_or_create_oauth_user(
	email: str, user_info: dict, provider_name: str
) -> dict | None:
	if not email:
		return None

	user = await get_user_by_username(email)
	if user:
		return dict(user)

	query = """
		INSERT INTO "user" (username, disabled, owner, modified_by)
		VALUES ($1, false, $2, $3)
		RETURNING id, username, disabled, creation, modified, owner, modified_by
	"""

	try:
		row = await db.fetch_one(query, email, email, f"oauth_{provider_name}")
		_logger.info(f"Created new OAuth user: {email} via {provider_name}")
		return dict(row) if row else None
	except Exception as e:
		_logger.error(f"Failed to create OAuth user {email}: {e}")
		return None


@app.route("/auth/logout", methods=["GET", "POST"])
async def logout() -> ResponseTypes:
	"""Logout endpoint - clears auth cookie"""
	redirect_url = request.args.get("redirect", DEFAULT_REDIRECT)

	response = await make_response(redirect(redirect_url))
	# Clear the auth cookie by setting it to expire immediately
	response.set_cookie(
		"auth_token",
		"",
		expires=0,
		httponly=True,
		secure=False,  # Set to True in production with HTTPS
		samesite="Lax",
	)
	return response


def main() -> None:
	uvicorn.run(
		"catkin.src.app:app",
		host="0.0.0.0",
		port=5000,
		reload=True,
		log_level="info",
	)


if __name__ == "__main__":
	main()
