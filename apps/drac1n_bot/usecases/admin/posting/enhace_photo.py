from io import BytesIO

from PIL import (
    Image,
    ImageFilter,
)

from configs.logging_setup import log


MAX_WIDTH = 1280

async def enhance_thumbnail(
    photo_data,
):

    if not isinstance(photo_data, BytesIO):

        log.info(
            "[THUMB] enhancer skipped "
            "| non-bytes source"
        )

        return photo_data

    # =====================================
    # ORIGINAL SIZE
    # =====================================

    photo_data.seek(0, 2)
    original_size = photo_data.tell()
    photo_data.seek(0)

    # =====================================
    # OPEN IMAGE
    # =====================================

    img = Image.open(
        photo_data
    ).convert("RGB")

    img.load()

    img = Image.open(photo_data)

    width, height = img.size

    log.info(
        "[THUMB] opened "
        "| resolution=%sx%s",
        width,
        height,
    )

    # =====================================
    # PRESERVE HD IMAGE
    # =====================================

    if width >= 1200:

        log.info(
            "[THUMB] preserve original "
            "| already_hd=%sx%s",
            width,
            height,
        )

        photo_data.seek(0)

        return photo_data

    # =====================================
    # SMART UPSCALE
    # =====================================

    if width < 500:

        scale = 2.0
        strategy = "upscale_2x"

    elif width < 900:

        scale = 1.5
        strategy = "upscale_1_5x"

    else:

        scale = 1.0
        strategy = "preserve"

    log.info(
        "[THUMB] strategy=%s",
        strategy,
    )

    # =====================================
    # RESIZE
    # =====================================

    if scale > 1:

        new_width = int(width * scale)
        new_height = int(height * scale)

        if new_width > MAX_WIDTH:

            ratio = (
                MAX_WIDTH / new_width
            )

            new_width = MAX_WIDTH

            new_height = int(
                new_height * ratio
            )

        img = img.resize(
            (
                new_width,
                new_height,
            ),
            Image.LANCZOS,
        )

        log.info(
            "[THUMB] upscale applied "
            "| scale=%.1f "
            "| new=%sx%s",
            scale,
            new_width,
            new_height,
        )

    else:

        log.info(
            "[THUMB] upscale skipped "
            "| already_hd=%sx%s",
            width,
            height,
        )

    # =====================================
    # SHARPEN
    # =====================================

    if scale >= 1.5:

        # =====================================
        # UNSHARP MASK
        # =====================================
        img = img.filter(
            ImageFilter.UnsharpMask(
                radius=1.2,
                percent=140,
                threshold=3,
            )
        )

        log.info(
            "[THUMB] unsharp mask applied "
            "| radius=1.2 "
            "| percent=140 "
            "| threshold=3"
        )

    else:

        log.info(
            "[THUMB] sharpen skipped"
        )

    # =====================================
    # EXPORT
    # =====================================

    output = BytesIO()

    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    img.save(
        output,
        format="JPEG",
        quality=93,
        optimize=True,
        subsampling=1,
    )

    final_size = output.tell()

    size_change = (
        (final_size - original_size)
        / original_size
    ) * 100

    log.info(
        "[THUMB] export complete "
        "| final_size=%.1fKB "
        "| size_change=%+.1f%%",
        final_size / 1024,
        size_change,
    )

    output.name = "thumb.jpg"

    output.seek(0)

    return output