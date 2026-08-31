# Slim base image -- smaller than the full python image, still has
# enough system libraries for Pillow/bcrypt's prebuilt wheels to work
# without needing extra system packages installed manually.
FROM python:3.12-slim

# Prevents Python from writing .pyc files and buffering stdout/stderr --
# the second one matters for Docker specifically, so `docker logs`
# shows output immediately instead of it sitting in a buffer.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy and install dependencies FIRST, separately from the rest of the
# code. Docker caches each instruction as a layer -- as long as
# requirements.txt doesn't change, this layer is reused on every
# rebuild instead of re-installing everything from scratch, which is
# the slowest part of the build by far.
COPY requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# Now copy the actual application code
COPY . .

# Gunicorn's port -- must match whatever docker-compose.yml/Nginx
# expects it to proxy to.
EXPOSE 8000

# Runs the app via Gunicorn, never Flask's own dev server (`flask run`
# is explicitly not meant for production use). -k gevent is required
# here, not optional -- Gunicorn's default sync workers cannot hold a
# WebSocket connection open at all, which silently broke the real-time
# chat feature (Flask-SocketIO) entirely.
#
# FIXED: originally used -k eventlet, but Gunicorn 26.0.0 (the version
# this app pins) removed the eventlet worker class entirely -- see
# https://gunicorn.org/news/. gevent is Gunicorn's own recommended
# replacement, and Flask-SocketIO officially supports it the same way.
#
# --workers scales with available CPU; 3 is a reasonable starting
# point for a small VPS, adjust once you know the real load -- though
# gevent workers handle many concurrent connections each via green
# threads, so fewer workers are typically needed than with sync workers.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "-k", "gevent", "--workers", "3", "run:app"]