'''
Image storage abstraction for room pictures.

The whole point of this module: nothing outside it should ever need to
know whether a room image lives on local disk or in Cloudinary (or,
later, Cloudflare R2). Every route/template calls get_room_image_url()
to display an image and upload_room_image() to store one -- the actual
backend is decided here, once, based on Config.IMAGE_BACKEND.

What gets stored in Rooms.image1-6 is always just a KEY (a local
filename, or a Cloudinary public_id) -- never a full provider URL. This
is what makes switching providers later a one-file change instead of a
database migration: existing keys stay valid, only how they're turned
into a displayable URL changes.
'''

import os
from flask import current_app, url_for

try:
    import cloudinary
    import cloudinary.uploader
except ImportError:
    cloudinary = None  # only required if IMAGE_BACKEND=cloudinary is actually used


def _cloudinary_configured():
    '''Configures the cloudinary SDK from app config on first use. Safe
    to call repeatedly -- cheap, idempotent.'''
    if cloudinary is None:
        raise RuntimeError(
            "IMAGE_BACKEND is 'cloudinary' but the cloudinary package isn't "
            "installed. Run: pip install cloudinary --break-system-packages"
        )
    cloudinary.config(
        cloud_name=current_app.config["CLOUDINARY_CLOUD_NAME"],
        api_key=current_app.config["CLOUDINARY_API_KEY"],
        api_secret=current_app.config["CLOUDINARY_API_SECRET"],
        secure=True,
    )


def upload_room_image(pil_image, key_hint):
    '''
    Stores an already-resized PIL Image and returns the KEY to save in
    Rooms.image1-6 -- never a full URL. `key_hint` is used to build a
    filename/public_id (e.g. "username1a2b3c4d").

    quality=80 + optimize=True on every save below: optimize=True is
    fully lossless (same pixels, just better Huffman-table encoding --
    typically 2-10% smaller for free), and quality=80 is barely above
    Pillow's own implicit default of 75, so there's no meaningful visual
    difference -- just consistently smaller, faster-loading files.
    '''
    backend = current_app.config.get("IMAGE_BACKEND", "local")

    if backend == "cloudinary":
        _cloudinary_configured()
        # Cloudinary needs bytes, not a PIL Image directly -- save to an
        # in-memory buffer instead of a file path, same resize logic as
        # before, just a different destination.
        import io
        buffer = io.BytesIO()
        pil_image.save(buffer, format="JPEG", quality=80, optimize=True)
        buffer.seek(0)

        result = cloudinary.uploader.upload(
            buffer,
            public_id=f"jambo/roompics/{key_hint}",
            # FIXED: slashes in public_id alone don't organize anything
            # in the Media Library on accounts using Cloudinary's
            # "dynamic folder mode" (the default for every account
            # created since June 2024) -- they only shape the delivery
            # URL. Without this, every upload lands flat in the account
            # root regardless of the path-looking public_id. This is
            # the actual, separate parameter that controls visible
            # folder placement.
            asset_folder="jambo/roompics",
            overwrite=True,
        )
        # Store the public_id, not result["secure_url"] -- keeps the
        # "stored value is always a key" rule intact.
        return result["public_id"]

    else:  # local
        filename = f"{key_hint}.jpg"
        picture_path = os.path.join(
            current_app.root_path, 'static/userpics/roompics/', filename
        )
        pil_image.save(picture_path, format="JPEG", quality=80, optimize=True)
        return filename


def get_room_image_url(key):
    '''
    Turns a stored key (from Rooms.image1-6) into a displayable URL.
    Safe to call from both Python code and Jinja templates (registered
    as a template global in app/__init__.py).
    '''
    # FIXED: the default placeholder ("roomdef1.jpg", from Rooms.image1's
    # column default) is a permanent app asset bundled with the code --
    # it's never actually uploaded via upload_room_image(), so it can
    # never exist on Cloudinary. Previously only `if not key` was
    # checked, which never caught this case (the string "roomdef1.jpg"
    # is truthy), so it fell through to the Cloudinary branch whenever
    # that backend was active and tried to fetch something that was
    # never there. Routing this one specific filename to local static
    # unconditionally, regardless of IMAGE_BACKEND.
    if not key or key == 'roomdef1.jpg':
        return url_for('static', filename='userpics/roompics/roomdef1.jpg')

    backend = current_app.config.get("IMAGE_BACKEND", "local")

    if backend == "cloudinary":
        if cloudinary is None:
            raise RuntimeError("IMAGE_BACKEND is 'cloudinary' but the cloudinary package isn't installed.")
        _cloudinary_configured()
        return cloudinary.CloudinaryImage(key).build_url()

    else:  # local
        return url_for('static', filename='userpics/roompics/' + key)