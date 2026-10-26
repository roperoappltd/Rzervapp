'''
Safe loading of uploaded photos.

Why: the upload forms accept jpg/png/webp, and Pillow's thumbnail() alone
(the old code) mishandled several perfectly normal files:
  * PNG with transparency, and palette PNGs, crashed the JPEG save
    ("cannot write mode RGBA as JPEG") -> HTTP 500 for the host;
  * phone photos stored "sideways" with an EXIF rotation flag came out
    rotated the wrong way;
  * CMYK files were saved as CMYK JPEGs, which browsers show with wrong
    colours;
  * a damaged file, a non-image renamed to .jpg, or a gigantic image
    (decompression bomb) raised an unhandled error.
open_clean_image() returns a plain RGB image, upright, or raises
ImageError with a message that is safe to show to the user.
'''
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError

# ~64 megapixels: above any phone camera, far below a memory-exhausting bomb.
Image.MAX_IMAGE_PIXELS = 64_000_000


class ImageError(ValueError):
    '''The uploaded file cannot be used as a photo.'''


def open_clean_image(file_storage, decode_hint=None):
    '''decode_hint=(w, h): for JPEGs, let Pillow decode at a reduced size
    (>= twice the target), which cuts memory use and time for big photos.'''
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            img = Image.open(file_storage)
            if decode_hint and img.format == "JPEG":
                img.draft("RGB", (decode_hint[0] * 2, decode_hint[1] * 2))
            img.load()  # decode now so truncated/corrupt files fail here
    except (UnidentifiedImageError, Image.DecompressionBombError,
            Image.DecompressionBombWarning):
        raise ImageError("This file is not a readable image, or it is too large.")
    except (OSError, SyntaxError, ValueError):
        raise ImageError("This image file looks damaged and could not be read.")

    # honour the camera's rotation flag, then drop it
    img = ImageOps.exif_transpose(img) or img

    # JPEG has no transparency: flatten onto white instead of failing
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.split()[-1])
        return background
    if img.mode != "RGB":
        img = img.convert("RGB")  # CMYK, palette, grayscale, 16-bit...
    return img
