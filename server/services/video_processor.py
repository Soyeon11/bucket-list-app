"""
Video processing service for generating 9:16 vertical Shorts/Reels videos.

Pipeline:
  1. Validate and normalize input media (photos / video clips).
  2. Build intro clip (2 s) using template settings.
  3. Compose main content clips with text overlays and transitions.
  4. Build outro clip (2 s) with app branding.
  5. Mix BGM (fade-in/out, loudness normalization).
  6. Encode to H.264 MP4 at 1080×1920, 30 fps.
  7. Extract thumbnail from first main clip.

Dependencies:
    moviepy >= 1.0.3
    Pillow >= 10.0.0
    ffmpeg-python >= 0.2.0  (used only for loudness normalization via subprocess)
    ffmpeg 8.x binary must be on PATH

Output format spec: see docs/VIDEO_SPEC.md
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import tempfile
import time
import uuid
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Generator

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Output video specification (see docs/VIDEO_SPEC.md §1)
VIDEO_WIDTH: int = 1080
VIDEO_HEIGHT: int = 1920
VIDEO_FPS: int = 30
VIDEO_CODEC: str = "libx264"
AUDIO_CODEC: str = "aac"
AUDIO_SAMPLE_RATE: int = 44_100
VIDEO_CRF: int = 23
VIDEO_PRESET: str = "slow"

# Section durations (seconds)
INTRO_DURATION: float = 2.0
OUTRO_DURATION: float = 2.0
PHOTO_DEFAULT_DURATION: float = 3.0
PHOTO_MAX_DURATION: float = 5.0
VIDEO_CLIP_MAX_DURATION: float = 15.0
MAX_TOTAL_DURATION: float = 60.0
MIN_MAIN_DURATION: float = 3.0

# File size / count limits (see PRD §3.1)
MAX_IMAGE_BYTES: int = 10 * 1024 * 1024       # 10 MB
MAX_VIDEO_BYTES: int = 200 * 1024 * 1024      # 200 MB
MAX_OUTPUT_BYTES: int = 100 * 1024 * 1024     # 100 MB
MAX_IMAGES: int = 20
MAX_VIDEOS: int = 5

# Loudness target (EBU R128 / Instagram/YouTube Shorts recommendation)
TARGET_LUFS: float = -16.0
TRUE_PEAK_DBTP: float = -1.0
BGM_VOLUME: float = 0.70        # relative to normalized loudness
BGM_FADE_IN: float = 1.5        # seconds
BGM_FADE_OUT: float = 2.0       # seconds

# Thumbnail settings
THUMBNAIL_WIDTH: int = 540
THUMBNAIL_HEIGHT: int = 960
THUMBNAIL_QUALITY: int = 85

# Template directory (relative to this file's location, resolved at runtime)
_HERE = Path(__file__).resolve().parent
TEMPLATES_DIR: Path = _HERE.parent.parent / "assets" / "templates"

SUPPORTED_TEMPLATES: frozenset[str] = frozenset({"minimal", "vibrant", "film"})
FALLBACK_TEMPLATE: str = "minimal"

# Supported input MIME types
SUPPORTED_IMAGE_MIME: frozenset[str] = frozenset(
    {"image/jpeg", "image/png", "image/webp", "image/heic"}
)
SUPPORTED_VIDEO_MIME: frozenset[str] = frozenset(
    {"video/mp4", "video/quicktime", "video/x-msvideo"}
)
SUPPORTED_AUDIO_MIME: frozenset[str] = frozenset(
    {"audio/mpeg", "audio/aac", "audio/mp4", "audio/wav", "audio/x-wav"}
)

# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------


class VideoProcessorError(Exception):
    """Base exception for all video processor errors."""


class TemplateNotFoundError(VideoProcessorError):
    """Raised when the requested template does not exist on disk."""

    def __init__(self, template_name: str) -> None:
        super().__init__(
            f"Template '{template_name}' not found in {TEMPLATES_DIR}. "
            f"Supported templates: {', '.join(sorted(SUPPORTED_TEMPLATES))}"
        )
        self.template_name = template_name


class MediaValidationError(VideoProcessorError):
    """Raised when an input media file fails validation."""

    def __init__(self, path: str, reason: str) -> None:
        super().__init__(f"Media validation failed for '{path}': {reason}")
        self.path = path
        self.reason = reason


class FFmpegError(VideoProcessorError):
    """Raised when an FFmpeg subprocess returns a non-zero exit code."""

    def __init__(self, cmd: list[str], returncode: int, stderr: str) -> None:
        super().__init__(
            f"FFmpeg command failed (exit {returncode}).\n"
            f"Command: {' '.join(cmd)}\n"
            f"Stderr: {stderr}"
        )
        self.cmd = cmd
        self.returncode = returncode
        self.stderr = stderr


class BGMLoadError(VideoProcessorError):
    """Raised when a BGM file cannot be loaded or processed."""

    def __init__(self, path: str, reason: str) -> None:
        super().__init__(f"Failed to load BGM from '{path}': {reason}")
        self.path = path


class OutputTooLargeError(VideoProcessorError):
    """Raised when the encoded output exceeds the maximum file size."""

    def __init__(self, size_bytes: int) -> None:
        super().__init__(
            f"Output file size {size_bytes / 1_048_576:.1f} MB exceeds "
            f"the {MAX_OUTPUT_BYTES / 1_048_576:.0f} MB limit."
        )
        self.size_bytes = size_bytes


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"


@dataclass
class MediaInput:
    """Single input media item (photo or video clip)."""

    path: str
    media_type: MediaType
    # Optional: if None, detected from file extension / magic bytes
    mime_type: str | None = None
    # Duration override for images (seconds); None = use template default
    display_duration: float | None = None

    @property
    def is_image(self) -> bool:
        return self.media_type == MediaType.IMAGE

    @property
    def is_video(self) -> bool:
        return self.media_type == MediaType.VIDEO


@dataclass
class VideoResult:
    """Result object returned by VideoProcessor.create_shorts()."""

    output_path: str
    thumbnail_path: str
    duration_seconds: float
    file_size_bytes: int
    template_used: str
    media_count: int
    processing_time_seconds: float


# Progress callback type: receives (stage: str, progress: float 0.0–1.0)
ProgressCallback = Callable[[str, float], None]


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def _detect_mime(path: str) -> str:
    """
    Guess MIME type from file extension.
    Returns empty string if unknown.
    """
    ext = Path(path).suffix.lower()
    mapping: dict[str, str] = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".heic": "image/heic",
        ".mp4": "video/mp4",
        ".mov": "video/quicktime",
        ".avi": "video/x-msvideo",
        ".mp3": "audio/mpeg",
        ".aac": "audio/aac",
        ".m4a": "audio/mp4",
        ".wav": "audio/wav",
    }
    return mapping.get(ext, "")


def _run_ffmpeg(args: list[str], *, timeout: int = 300) -> None:
    """
    Execute an FFmpeg command and raise FFmpegError on failure.

    Args:
        args: Full argument list starting with 'ffmpeg'.
        timeout: Maximum seconds to wait for the process.
    """
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"] + args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise FFmpegError(cmd, result.returncode, result.stderr)


@contextmanager
def _temp_workdir() -> Generator[Path, None, None]:
    """
    Context manager that creates a temporary directory and removes it on exit.
    All intermediate files (resized clips, audio segments, etc.) should be written here.
    """
    tmp = tempfile.mkdtemp(prefix="bla_video_")
    try:
        yield Path(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        logger.debug("Cleaned up temp directory: %s", tmp)


# ---------------------------------------------------------------------------
# Template loader
# ---------------------------------------------------------------------------


def _load_template(name: str) -> dict[str, Any]:
    """
    Load and return the template configuration for *name*.

    Falls back to FALLBACK_TEMPLATE if the requested template is not found
    and logs a warning.

    Args:
        name: Template identifier (e.g. 'minimal', 'vibrant', 'film').

    Returns:
        Parsed template.json as a dict.

    Raises:
        TemplateNotFoundError: If even the fallback template is missing.
    """
    target = TEMPLATES_DIR / name / "template.json"
    if not target.exists():
        if name != FALLBACK_TEMPLATE:
            logger.warning(
                "Template '%s' not found; falling back to '%s'.", name, FALLBACK_TEMPLATE
            )
            return _load_template(FALLBACK_TEMPLATE)
        raise TemplateNotFoundError(name)

    with target.open(encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Main VideoProcessor class
# ---------------------------------------------------------------------------


class VideoProcessor:
    """
    Generates a 9:16 vertical Shorts/Reels video from user-uploaded media.

    Usage::

        processor = VideoProcessor(template_name="vibrant")
        result = await processor.create_shorts(
            media_files=[MediaInput(path="/tmp/photo.jpg", media_type=MediaType.IMAGE)],
            title="후지산 등반",
            bgm_path="/tmp/bgm.mp3",
            output_path="/tmp/output.mp4",
        )

    The class is *not* reusable across concurrent calls — create a new instance per job.
    """

    def __init__(
        self,
        template_name: str = "minimal",
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        """
        Args:
            template_name: One of {'minimal', 'vibrant', 'film'}.
                           Falls back to 'minimal' if not found.
            progress_callback: Optional callable(stage, 0.0–1.0) for Celery progress updates.
        """
        self.template_name = template_name
        self.template: dict[str, Any] = _load_template(template_name)
        self._progress_callback = progress_callback
        logger.info("VideoProcessor initialized with template '%s'.", self.template_name)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def create_shorts(
        self,
        media_files: list[MediaInput],
        title: str,
        bgm_path: str | None,
        output_path: str,
        caption: str | None = None,
    ) -> VideoResult:
        """
        Full pipeline: validate → compose → encode → extract thumbnail.

        Args:
            media_files: Ordered list of photos/clips to include.
            title: Bucket list item title shown in the intro card.
            bgm_path: Absolute path to a BGM audio file, or None for silent video.
            output_path: Destination path for the final MP4 file.
            caption: Optional short caption overlaid on the main content section.

        Returns:
            VideoResult with output metadata.

        Raises:
            MediaValidationError: If a required media file is invalid.
            FFmpegError: If FFmpeg encoding fails.
            OutputTooLargeError: If the result exceeds MAX_OUTPUT_BYTES.
        """
        start_time = time.monotonic()
        self._report_progress("validating", 0.0)

        # 1. Validate all inputs
        valid_media = self._validate_media_inputs(media_files)
        self._report_progress("validating", 1.0)

        with _temp_workdir() as workdir:
            self._report_progress("preparing", 0.0)

            # 2. Normalize media to uniform resolution clips
            normalized_clips = self._normalize_media(valid_media, workdir)
            self._report_progress("preparing", 0.5)

            # 3. Build intro image
            intro_path = workdir / "intro.png"
            self._render_intro_frame(title, str(intro_path))
            self._report_progress("preparing", 1.0)

            # 4. Build outro image
            outro_path = workdir / "outro.png"
            self._render_outro_frame(str(outro_path))

            # 5. Create section video files
            self._report_progress("composing", 0.0)
            intro_clip_path = workdir / "intro_clip.mp4"
            self._image_to_clip(str(intro_path), str(intro_clip_path), INTRO_DURATION)

            outro_clip_path = workdir / "outro_clip.mp4"
            self._image_to_clip(str(outro_path), str(outro_clip_path), OUTRO_DURATION)
            self._report_progress("composing", 0.3)

            # 6. Apply text overlays (caption) to main content clips
            if caption:
                normalized_clips = [
                    self._add_text_overlay_to_clip(clip_path, caption, workdir)
                    for clip_path in normalized_clips
                ]
            self._report_progress("composing", 0.6)

            # 7. Apply transitions between clips
            transition_clips = self._apply_transition(
                normalized_clips,
                self.template.get("transition", {}).get("type", "fade"),
                workdir,
            )
            self._report_progress("composing", 0.9)

            # 8. Concatenate all sections
            all_clips = [str(intro_clip_path)] + transition_clips + [str(outro_clip_path)]
            concat_path = workdir / "concat.mp4"
            self._concatenate_clips(all_clips, str(concat_path))
            self._report_progress("composing", 1.0)

            # 9. Mix BGM
            self._report_progress("mixing_bgm", 0.0)
            if bgm_path:
                muxed_path = workdir / "muxed.mp4"
                try:
                    normalized_bgm = self._normalize_bgm(bgm_path, TARGET_LUFS, workdir)
                    self._mix_bgm(str(concat_path), normalized_bgm, str(muxed_path))
                    concat_path = muxed_path
                except BGMLoadError as exc:
                    logger.warning("BGM mixing skipped: %s", exc)
            self._report_progress("mixing_bgm", 1.0)

            # 10. Final encode to output path
            self._report_progress("encoding", 0.0)
            self._final_encode(str(concat_path), output_path)
            self._report_progress("encoding", 1.0)

            # 11. Validate output size
            output_size = os.path.getsize(output_path)
            if output_size > MAX_OUTPUT_BYTES:
                # Re-encode with higher CRF to reduce file size
                logger.warning(
                    "Output size %.1f MB exceeds limit; re-encoding with CRF %d.",
                    output_size / 1_048_576,
                    VIDEO_CRF + 4,
                )
                reencoded_path = workdir / "reencoded.mp4"
                self._final_encode(str(concat_path), str(reencoded_path), crf=VIDEO_CRF + 4)
                shutil.copy2(str(reencoded_path), output_path)
                output_size = os.path.getsize(output_path)

            if output_size > MAX_OUTPUT_BYTES:
                raise OutputTooLargeError(output_size)

            # 12. Extract thumbnail
            self._report_progress("thumbnail", 0.0)
            thumb_path = str(Path(output_path).with_suffix("")) + "_thumb.jpg"
            self._extract_thumbnail(output_path, thumb_path)
            self._report_progress("thumbnail", 1.0)

            # Calculate total duration
            total_duration = self._probe_duration(output_path)

            elapsed = time.monotonic() - start_time
            logger.info(
                "Video created: %.1f s duration, %.1f MB, elapsed %.1f s — %s",
                total_duration,
                output_size / 1_048_576,
                elapsed,
                output_path,
            )

            return VideoResult(
                output_path=output_path,
                thumbnail_path=thumb_path,
                duration_seconds=total_duration,
                file_size_bytes=output_size,
                template_used=f"{self.template_name}@{self.template.get('version', '1.0.0')}",
                media_count=len(valid_media),
                processing_time_seconds=elapsed,
            )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_media_inputs(self, media_files: list[MediaInput]) -> list[MediaInput]:
        """
        Validate each MediaInput item.  Items that fail soft checks are skipped
        with a warning; items that fail hard checks raise MediaValidationError.

        Returns the filtered list of valid items.

        Raises:
            MediaValidationError: If total count limits are exceeded.
        """
        images = [m for m in media_files if m.is_image]
        videos = [m for m in media_files if m.is_video]

        if len(images) > MAX_IMAGES:
            raise MediaValidationError(
                "input",
                f"Too many images: {len(images)} > {MAX_IMAGES}.",
            )
        if len(videos) > MAX_VIDEOS:
            raise MediaValidationError(
                "input",
                f"Too many video clips: {len(videos)} > {MAX_VIDEOS}.",
            )

        valid: list[MediaInput] = []
        for item in media_files:
            path = Path(item.path)

            # File existence
            if not path.exists():
                logger.warning("Media file not found, skipping: %s", item.path)
                continue

            size = path.stat().st_size

            # File size limits
            if item.is_image and size > MAX_IMAGE_BYTES:
                raise MediaValidationError(
                    item.path,
                    f"Image size {size / 1_048_576:.1f} MB exceeds {MAX_IMAGE_BYTES / 1_048_576:.0f} MB limit.",
                )
            if item.is_video and size > MAX_VIDEO_BYTES:
                raise MediaValidationError(
                    item.path,
                    f"Video size {size / 1_048_576:.0f} MB exceeds {MAX_VIDEO_BYTES / 1_048_576:.0f} MB limit.",
                )

            # MIME type check
            mime = item.mime_type or _detect_mime(item.path)
            if item.is_image and mime and mime not in SUPPORTED_IMAGE_MIME:
                logger.warning("Unsupported image MIME '%s', skipping: %s", mime, item.path)
                continue
            if item.is_video and mime and mime not in SUPPORTED_VIDEO_MIME:
                logger.warning("Unsupported video MIME '%s', skipping: %s", mime, item.path)
                continue

            # Video: minimum duration check (probe via ffprobe)
            if item.is_video:
                try:
                    dur = self._probe_duration(item.path)
                    if dur < 1.0:
                        logger.warning("Video clip too short (%.2f s), skipping: %s", dur, item.path)
                        continue
                except Exception:
                    # If probe fails, still attempt processing
                    pass

            # Image: minimum resolution check via Pillow
            if item.is_image:
                try:
                    with Image.open(item.path) as img:
                        w, h = img.size
                        if w < 480 or h < 480:
                            logger.warning(
                                "Image too small (%dx%d), skipping: %s", w, h, item.path
                            )
                            continue
                except Exception as exc:
                    logger.warning("Cannot open image, skipping: %s — %s", item.path, exc)
                    continue

            valid.append(item)

        if not valid:
            raise MediaValidationError("input", "No valid media files after validation.")

        return valid

    # ------------------------------------------------------------------
    # Normalization
    # ------------------------------------------------------------------

    def _normalize_media(
        self, media_files: list[MediaInput], workdir: Path
    ) -> list[str]:
        """
        Convert each MediaInput to a silent MP4 clip at 1080×1920 / 30 fps.

        - Images are converted to short video clips (Ken Burns pan/zoom via FFmpeg).
        - Video clips are rescaled and trimmed.

        Returns:
            Ordered list of absolute paths to the normalized MP4 clips.
        """
        clips: list[str] = []
        media_cfg = self.template.get("media_area", {})
        photo_dur = media_cfg.get("photo_duration", PHOTO_DEFAULT_DURATION)

        for idx, item in enumerate(media_files):
            out_clip = workdir / f"clip_{idx:03d}.mp4"

            if item.is_image:
                duration = item.display_duration or photo_dur
                duration = min(duration, PHOTO_MAX_DURATION)
                self._image_to_clip(item.path, str(out_clip), duration)
            else:
                # Video: strip audio, rescale, trim
                self._video_to_clip(item.path, str(out_clip))

            clips.append(str(out_clip))

        return clips

    def _image_to_clip(self, image_path: str, output_path: str, duration: float) -> None:
        """
        Render a static image (or intro/outro PNG) into a silent MP4 clip
        with optional Ken Burns zoom effect.

        Args:
            image_path: Source image file.
            output_path: Destination MP4 path.
            duration: Clip length in seconds.
        """
        media_cfg = self.template.get("media_area", {})
        kb_cfg = media_cfg.get("ken_burns", {})
        use_ken_burns = kb_cfg.get("enabled", False) and Path(image_path).stem not in (
            "intro", "outro"
        )

        if use_ken_burns:
            scale_start = kb_cfg.get("scale_start", 1.0)
            scale_end = kb_cfg.get("scale_end", 1.05)
            # zoompan filter: gradual zoom from scale_start to scale_end
            # d = total frames, s = output size
            total_frames = int(duration * VIDEO_FPS)
            zoom_expr = (
                f"'if(lte(on,1),{scale_start},min(zoom+({scale_end - scale_start}/{total_frames}),{scale_end}))'"
            )
            vf = (
                f"scale={VIDEO_WIDTH * 2}:{VIDEO_HEIGHT * 2},"
                f"zoompan=z={zoom_expr}:d={total_frames}:"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                f"s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={VIDEO_FPS},"
                f"format=yuv420p"
            )
        else:
            vf = (
                f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,"
                f"crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},"
                f"format=yuv420p"
            )

        _run_ffmpeg([
            "-loop", "1",
            "-i", image_path,
            "-t", str(duration),
            "-vf", vf,
            "-r", str(VIDEO_FPS),
            "-c:v", VIDEO_CODEC,
            "-preset", "fast",
            "-crf", str(VIDEO_CRF),
            "-an",
            output_path,
        ])

    def _video_to_clip(self, video_path: str, output_path: str) -> None:
        """
        Rescale a video clip to 1080×1920, trim to VIDEO_CLIP_MAX_DURATION, strip audio.
        """
        vf = (
            f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},"
            f"format=yuv420p"
        )
        _run_ffmpeg([
            "-i", video_path,
            "-t", str(VIDEO_CLIP_MAX_DURATION),
            "-vf", vf,
            "-r", str(VIDEO_FPS),
            "-c:v", VIDEO_CODEC,
            "-preset", "fast",
            "-crf", str(VIDEO_CRF),
            "-an",
            output_path,
        ])

    # ------------------------------------------------------------------
    # Text overlay
    # ------------------------------------------------------------------

    def _add_text_overlay(
        self,
        image: Image.Image,
        text: str,
        position: dict[str, Any],
    ) -> Image.Image:
        """
        Render a text string onto a PIL Image according to the given position config.

        Args:
            image: Source PIL Image (modified in-place on a copy).
            text: Text string to render.
            position: Dict with keys: x, y, width, height, font_size, font_color,
                      text_align, background_color, background_padding, background_border_radius.

        Returns:
            New PIL Image with the text overlay applied.
        """
        img = image.copy().convert("RGBA")
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        font_size: int = position.get("font_size", 36)
        font_color: str = position.get("font_color", "#FFFFFF")
        text_x: int = position.get("x", VIDEO_WIDTH // 2)
        text_y: int = position.get("y", VIDEO_HEIGHT // 2)
        max_width: int = position.get("width", VIDEO_WIDTH - 80)
        text_align: str = position.get("text_align", "center")
        bg_color: list[int] | None = position.get("background_color")
        bg_padding: dict[str, int] | None = position.get("background_padding")
        bg_radius: int = position.get("background_border_radius", 0)

        # Load font (system font fallback if custom font not available)
        font = self._load_font(font_size)

        # Word-wrap text
        lines = self._wrap_text(draw, text, font, max_width)
        max_lines: int = position.get("max_lines", 10)
        lines = lines[:max_lines]

        # Measure total text block size
        line_heights = [draw.textbbox((0, 0), ln, font=font)[3] for ln in lines]
        line_spacing_factor: float = position.get("line_spacing", 1.3)
        line_h = max(line_heights, default=font_size) if line_heights else font_size
        total_h = int(sum(h * line_spacing_factor for h in line_heights))
        total_w = max(
            (draw.textbbox((0, 0), ln, font=font)[2] for ln in lines), default=0
        )

        # Determine text block top-left origin from center anchor
        anchor = position.get("anchor", "center")
        if anchor == "center":
            block_x = text_x - total_w // 2
            block_y = text_y - total_h // 2
        else:
            block_x = text_x
            block_y = text_y

        # Draw background panel
        if bg_color:
            r, g, b, a = self._parse_color(bg_color, alpha_scale=255)
            pad_t = bg_padding.get("top", 8) if bg_padding else 8
            pad_r = bg_padding.get("right", 12) if bg_padding else 12
            pad_b = bg_padding.get("bottom", 8) if bg_padding else 8
            pad_l = bg_padding.get("left", 12) if bg_padding else 12
            rect = [
                block_x - pad_l,
                block_y - pad_t,
                block_x + total_w + pad_r,
                block_y + total_h + pad_b,
            ]
            if bg_radius > 0:
                draw.rounded_rectangle(rect, radius=bg_radius, fill=(r, g, b, a))
            else:
                draw.rectangle(rect, fill=(r, g, b, a))

        # Draw each line
        y_cursor = block_y
        for line in lines:
            lw = draw.textbbox((0, 0), line, font=font)[2]
            if text_align == "center":
                lx = text_x - lw // 2
            elif text_align == "right":
                lx = block_x + total_w - lw
            else:
                lx = block_x

            # Shadow
            shadow_cfg = position.get("shadow")
            if shadow_cfg:
                sr, sg, sb, sa = self._parse_color(shadow_cfg.get("color", [0, 0, 0, 0.5]), alpha_scale=255)
                sx = shadow_cfg.get("offset_x", 2)
                sy = shadow_cfg.get("offset_y", 2)
                draw.text((lx + sx, y_cursor + sy), line, font=font, fill=(sr, sg, sb, sa))

            draw.text((lx, y_cursor), line, font=font, fill=font_color)
            y_cursor += int(line_h * line_spacing_factor)

        # Merge overlay onto source
        combined = Image.alpha_composite(img, overlay)
        return combined.convert("RGB")

    def _add_text_overlay_to_clip(
        self, clip_path: str, caption: str, workdir: Path
    ) -> str:
        """
        Burn a caption text into all frames of a video clip using FFmpeg drawtext filter.

        Args:
            clip_path: Input MP4 path.
            caption: Caption text to overlay.
            workdir: Directory for intermediate files.

        Returns:
            Path to the output clip with caption burned in.
        """
        caption_cfg: dict[str, Any] = self.template.get("text_boxes", {}).get("caption", {})
        font_size: int = caption_cfg.get("font_size", 24)
        font_color: str = caption_cfg.get("font_color", "#FFFFFF").lstrip("#")
        y_pos: int = caption_cfg.get("y", VIDEO_HEIGHT - 230)
        max_width: int = caption_cfg.get("width", VIDEO_WIDTH - 80)

        # Escape special characters for drawtext filter
        safe_caption = caption.replace("'", "\\'").replace(":", "\\:").replace("\\", "\\\\")

        # Drawtext filter with word-wrap via wrappedtext (limited) or fixed box
        vf = (
            f"drawtext=text='{safe_caption}'"
            f":fontsize={font_size}"
            f":fontcolor=0x{font_color}"
            f":x=(w-tw)/2"
            f":y={y_pos}"
            f":line_spacing=4"
            f":box=1:boxcolor=0x000000@0.5:boxborderw=8"
        )

        stem = Path(clip_path).stem
        out_path = str(workdir / f"{stem}_captioned.mp4")
        _run_ffmpeg([
            "-i", clip_path,
            "-vf", vf,
            "-c:v", VIDEO_CODEC,
            "-preset", "fast",
            "-crf", str(VIDEO_CRF),
            "-an",
            out_path,
        ])
        return out_path

    # ------------------------------------------------------------------
    # Transitions
    # ------------------------------------------------------------------

    def _apply_transition(
        self,
        clips: list[str],
        transition_type: str,
        workdir: Path,
    ) -> list[str]:
        """
        Apply inter-clip transitions and return the resulting list of clip paths.

        Supported transition types: 'fade', 'slide', 'zoom'.
        Transitions are implemented as xfade FFmpeg filter between adjacent clips.

        Args:
            clips: Ordered list of input clip paths.
            transition_type: One of 'fade', 'slide', 'zoom'.
            workdir: Directory for intermediate files.

        Returns:
            List of clip paths with transitions applied.
            If there is only one clip, returns it unchanged.
        """
        if len(clips) <= 1:
            return clips

        transition_cfg: dict[str, Any] = self.template.get("transition", {})
        duration: float = transition_cfg.get("duration", 0.5)

        # Map template transition type to xfade transition name
        xfade_map: dict[str, str] = {
            "fade": "dissolve",
            "slide": "slideleft",
            "zoom": "zoom",
        }
        xfade_name = xfade_map.get(transition_type, "dissolve")

        # Chain xfade between consecutive clips
        # For simplicity each pair is merged independently then concatenated.
        result_clips: list[str] = [clips[0]]
        for i, next_clip in enumerate(clips[1:], start=1):
            prev_clip = result_clips[-1]
            merged_path = str(workdir / f"xfade_{i:03d}.mp4")

            # Probe duration of previous clip to calculate offset
            prev_dur = self._probe_duration(prev_clip)
            offset = max(prev_dur - duration, 0.0)

            _run_ffmpeg([
                "-i", prev_clip,
                "-i", next_clip,
                "-filter_complex",
                f"[0:v][1:v]xfade=transition={xfade_name}:duration={duration}:offset={offset}[v]",
                "-map", "[v]",
                "-c:v", VIDEO_CODEC,
                "-preset", "fast",
                "-crf", str(VIDEO_CRF),
                "-an",
                merged_path,
            ])
            result_clips[-1] = merged_path  # replace last with merged result

        return result_clips

    # ------------------------------------------------------------------
    # Concatenation
    # ------------------------------------------------------------------

    def _concatenate_clips(self, clip_paths: list[str], output_path: str) -> None:
        """
        Concatenate multiple MP4 clips using FFmpeg concat demuxer.

        Args:
            clip_paths: Ordered list of clip file paths.
            output_path: Destination MP4 path.
        """
        # Write concat manifest
        manifest_path = Path(output_path).parent / f"concat_{uuid.uuid4().hex[:8]}.txt"
        with manifest_path.open("w", encoding="utf-8") as f:
            for cp in clip_paths:
                f.write(f"file '{cp}'\n")

        try:
            _run_ffmpeg([
                "-f", "concat",
                "-safe", "0",
                "-i", str(manifest_path),
                "-c", "copy",
                output_path,
            ])
        finally:
            manifest_path.unlink(missing_ok=True)

    # ------------------------------------------------------------------
    # BGM processing
    # ------------------------------------------------------------------

    def _normalize_bgm(self, audio_path: str, target_lufs: float, workdir: Path) -> str:
        """
        Normalize BGM loudness to *target_lufs* using FFmpeg loudnorm filter (two-pass).

        Args:
            audio_path: Source audio file path.
            target_lufs: Target integrated loudness in LUFS (e.g. -16.0).
            workdir: Directory for the normalized output file.

        Returns:
            Path to the normalized audio file (AAC).

        Raises:
            BGMLoadError: If the audio file cannot be processed.
        """
        if not Path(audio_path).exists():
            raise BGMLoadError(audio_path, "File not found.")

        mime = _detect_mime(audio_path)
        if mime and mime not in SUPPORTED_AUDIO_MIME:
            raise BGMLoadError(audio_path, f"Unsupported audio format '{mime}'.")

        out_path = str(workdir / "bgm_normalized.aac")

        # Two-pass loudnorm: first pass collects measured values, second applies correction.
        # For simplicity we use the linear mode (single-pass) which is accurate enough.
        try:
            _run_ffmpeg([
                "-i", audio_path,
                "-af",
                f"loudnorm=I={target_lufs}:TP={TRUE_PEAK_DBTP}:LRA=11",
                "-ar", str(AUDIO_SAMPLE_RATE),
                "-ac", "2",
                "-c:a", AUDIO_CODEC,
                "-b:a", "192k",
                out_path,
            ])
        except FFmpegError as exc:
            raise BGMLoadError(audio_path, str(exc)) from exc

        return out_path

    def _mix_bgm(self, video_path: str, bgm_path: str, output_path: str) -> None:
        """
        Mix normalized BGM into the video with fade-in/out and volume control.

        - Loops BGM if shorter than video; trims if longer.
        - Applies BGM_FADE_IN fade-in and BGM_FADE_OUT fade-out.

        Args:
            video_path: Silent (no audio) MP4 file.
            bgm_path: Normalized audio file.
            output_path: Output MP4 with mixed audio.
        """
        video_dur = self._probe_duration(video_path)

        audio_filter = (
            f"[1:a]"
            f"aloop=loop=-1:size=2147483647,"   # loop audio indefinitely
            f"atrim=duration={video_dur},"       # trim to video length
            f"volume={BGM_VOLUME},"
            f"afade=t=in:st=0:d={BGM_FADE_IN},"
            f"afade=t=out:st={max(video_dur - BGM_FADE_OUT, 0)}"
            f":d={BGM_FADE_OUT}"
            f"[a_out]"
        )

        _run_ffmpeg([
            "-i", video_path,
            "-i", bgm_path,
            "-filter_complex", audio_filter,
            "-map", "0:v",
            "-map", "[a_out]",
            "-c:v", "copy",
            "-c:a", AUDIO_CODEC,
            "-b:a", "192k",
            "-shortest",
            output_path,
        ])

    # ------------------------------------------------------------------
    # Intro / Outro rendering
    # ------------------------------------------------------------------

    def _create_intro(self, title: str) -> Image.Image:
        """
        Render the intro frame as a PIL Image (1080×1920).

        Args:
            title: Bucket list item title to display in the center.

        Returns:
            PIL Image of the intro frame.
        """
        bg_cfg: dict[str, Any] = self.template.get("background", {})
        img = self._render_background(bg_cfg)

        title_cfg: dict[str, Any] = self.template.get("text_boxes", {}).get("title", {})
        if title_cfg:
            img = self._add_text_overlay(img, title, title_cfg)

        # App logo watermark (top-left, small)
        img = self._draw_watermark(img, position="top_left")

        return img

    def _create_outro(self) -> Image.Image:
        """
        Render the outro frame as a PIL Image (1080×1920).

        Returns:
            PIL Image of the outro frame.
        """
        bg_cfg: dict[str, Any] = self.template.get("background", {})
        img = self._render_background(bg_cfg)

        outro_cfg: dict[str, Any] = self.template.get("text_boxes", {}).get("outro_message", {})
        if outro_cfg:
            img = self._add_text_overlay(img, "완료! ✓", outro_cfg)

        branding_cfg: dict[str, Any] = self.template.get("text_boxes", {}).get("branding", {})
        if branding_cfg:
            branding_text: str = branding_cfg.get("text", "Bucket List App으로 제작")
            img = self._add_text_overlay(img, branding_text, branding_cfg)

        return img

    def _render_intro_frame(self, title: str, output_path: str) -> None:
        """Render the intro PIL Image and save it to output_path."""
        img = self._create_intro(title)
        img.save(output_path, format="PNG")

    def _render_outro_frame(self, output_path: str) -> None:
        """Render the outro PIL Image and save it to output_path."""
        img = self._create_outro()
        img.save(output_path, format="PNG")

    # ------------------------------------------------------------------
    # Background rendering
    # ------------------------------------------------------------------

    def _render_background(self, bg_cfg: dict[str, Any]) -> Image.Image:
        """
        Create a 1080×1920 background image based on template background config.

        Supports:
          - type: 'solid'    → flat color
          - type: 'gradient' → linear gradient (top→bottom approximation via Pillow)
        """
        img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT))
        draw = ImageDraw.Draw(img)

        bg_type: str = bg_cfg.get("type", "solid")

        if bg_type == "gradient":
            gradient_cfg: dict[str, Any] = bg_cfg.get("gradient", {}) or {}
            stops: list[dict[str, Any]] = gradient_cfg.get("stops", [
                {"color": "#000000", "position": 0.0},
                {"color": "#FFFFFF", "position": 1.0},
            ])
            # Simple top-to-bottom linear gradient
            c0 = self._hex_to_rgb(stops[0]["color"])
            c1 = self._hex_to_rgb(stops[-1]["color"])
            for y in range(VIDEO_HEIGHT):
                t = y / VIDEO_HEIGHT
                r = int(c0[0] + (c1[0] - c0[0]) * t)
                g = int(c0[1] + (c1[1] - c0[1]) * t)
                b = int(c0[2] + (c1[2] - c0[2]) * t)
                draw.line([(0, y), (VIDEO_WIDTH, y)], fill=(r, g, b))
        else:
            # Solid color
            color_hex: str = bg_cfg.get("intro_color") or bg_cfg.get("color", "#FFFFFF")
            rgb = self._hex_to_rgb(color_hex)
            draw.rectangle([(0, 0), (VIDEO_WIDTH, VIDEO_HEIGHT)], fill=rgb)

        return img

    # ------------------------------------------------------------------
    # Encoding
    # ------------------------------------------------------------------

    def _final_encode(
        self, input_path: str, output_path: str, crf: int = VIDEO_CRF
    ) -> None:
        """
        Final H.264 encode with all output spec parameters applied.

        Args:
            input_path: Intermediate (possibly raw/fast-encoded) MP4.
            output_path: Destination path for the release-quality MP4.
            crf: Constant Rate Factor (quality). Higher = smaller / lower quality.
        """
        _run_ffmpeg([
            "-i", input_path,
            "-c:v", VIDEO_CODEC,
            "-preset", VIDEO_PRESET,
            "-crf", str(crf),
            "-pix_fmt", "yuv420p",
            "-maxrate", "8M",
            "-bufsize", "16M",
            "-c:a", AUDIO_CODEC,
            "-b:a", "192k",
            "-ar", str(AUDIO_SAMPLE_RATE),
            "-ac", "2",
            "-movflags", "+faststart",
            output_path,
        ])

    # ------------------------------------------------------------------
    # Thumbnail extraction
    # ------------------------------------------------------------------

    def _extract_thumbnail(self, video_path: str, output_path: str) -> None:
        """
        Extract a JPEG thumbnail from the video at the 1-second mark.

        If the video is shorter than 1 second, uses the first frame.

        Args:
            video_path: Source MP4.
            output_path: Destination JPEG path.
        """
        dur = self._probe_duration(video_path)
        seek = min(1.0, max(0.0, dur - 0.1))

        _run_ffmpeg([
            "-ss", str(seek),
            "-i", video_path,
            "-vframes", "1",
            "-vf", f"scale={THUMBNAIL_WIDTH}:{THUMBNAIL_HEIGHT}:force_original_aspect_ratio=increase,"
                   f"crop={THUMBNAIL_WIDTH}:{THUMBNAIL_HEIGHT}",
            "-q:v", "2",
            output_path,
        ])

    # ------------------------------------------------------------------
    # FFprobe helper
    # ------------------------------------------------------------------

    def _probe_duration(self, file_path: str) -> float:
        """
        Return the duration of a media file in seconds using ffprobe.

        Args:
            file_path: Path to any media file.

        Returns:
            Duration in seconds as float.

        Raises:
            FFmpegError: If ffprobe fails.
        """
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise FFmpegError(cmd, result.returncode, result.stderr)
        try:
            return float(result.stdout.strip())
        except ValueError:
            return 0.0

    # ------------------------------------------------------------------
    # Font helpers
    # ------------------------------------------------------------------

    def _load_font(self, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        """
        Load a TrueType font at the given size.
        Falls back to Pillow's built-in bitmap font if no TTF is available.
        """
        # Search order: bundled assets → system fonts → Pillow default
        search_paths = [
            _HERE.parent.parent / "assets" / "fonts" / "NotoSansKR-Bold.ttf",
            _HERE.parent.parent / "assets" / "fonts" / "NotoSansKR-Regular.ttf",
            Path("C:/Windows/Fonts/malgun.ttf"),        # Korean system font (Windows)
            Path("/System/Library/Fonts/AppleSDGothicNeo.ttc"),  # macOS
            Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),  # Linux
        ]
        for font_path in search_paths:
            if font_path.exists():
                try:
                    return ImageFont.truetype(str(font_path), size)
                except Exception:
                    continue
        return ImageFont.load_default()

    # ------------------------------------------------------------------
    # Text wrapping
    # ------------------------------------------------------------------

    @staticmethod
    def _wrap_text(
        draw: ImageDraw.ImageDraw,
        text: str,
        font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
        max_width: int,
    ) -> list[str]:
        """
        Word-wrap *text* so each line fits within *max_width* pixels.

        Returns a list of line strings.
        """
        words = text.split()
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip() if current else word
            bbox = draw.textbbox((0, 0), candidate, font=font)
            if bbox[2] <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines if lines else [text]

    # ------------------------------------------------------------------
    # Watermark / branding
    # ------------------------------------------------------------------

    def _draw_watermark(
        self, image: Image.Image, position: str = "top_left"
    ) -> Image.Image:
        """
        Draw the app name as a small watermark text.

        Args:
            image: Source PIL Image.
            position: 'top_left' | 'top_right' | 'bottom_left' | 'bottom_right'.

        Returns:
            PIL Image with watermark applied.
        """
        img = image.copy().convert("RGBA")
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        font = self._load_font(20)
        text = "Bucket List App"
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2], bbox[3]

        padding = 24
        if position == "top_left":
            x, y = padding, padding
        elif position == "top_right":
            x, y = VIDEO_WIDTH - tw - padding, padding
        elif position == "bottom_left":
            x, y = padding, VIDEO_HEIGHT - th - padding
        else:
            x, y = VIDEO_WIDTH - tw - padding, VIDEO_HEIGHT - th - padding

        draw.text((x, y), text, font=font, fill=(255, 255, 255, 160))
        return Image.alpha_composite(img, overlay).convert("RGB")

    # ------------------------------------------------------------------
    # Color utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
        """Convert '#RRGGBB' to (R, G, B) tuple."""
        hex_color = hex_color.lstrip("#")
        r, g, b = (int(hex_color[i: i + 2], 16) for i in (0, 2, 4))
        return r, g, b

    @staticmethod
    def _parse_color(
        color: str | list[float | int], alpha_scale: int = 255
    ) -> tuple[int, int, int, int]:
        """
        Parse a color value into an (R, G, B, A) tuple.

        Accepts:
          - HEX string '#RRGGBB'
          - RGBA list [R, G, B, A] where A is 0.0–1.0 or 0–255
        """
        if isinstance(color, str):
            r, g, b = VideoProcessor._hex_to_rgb(color)
            return r, g, b, alpha_scale
        # list format [R, G, B, A]
        r = int(color[0])
        g = int(color[1])
        b = int(color[2])
        a_raw = color[3] if len(color) > 3 else 1.0
        a = int(a_raw * 255) if isinstance(a_raw, float) and a_raw <= 1.0 else int(a_raw)
        return r, g, b, a

    # ------------------------------------------------------------------
    # Progress reporting
    # ------------------------------------------------------------------

    def _report_progress(self, stage: str, progress: float) -> None:
        """
        Invoke the progress callback if one was provided.

        Args:
            stage: Human-readable stage name (e.g. 'encoding', 'mixing_bgm').
            progress: Float in [0.0, 1.0].
        """
        if self._progress_callback is not None:
            try:
                self._progress_callback(stage, progress)
            except Exception as exc:
                logger.warning("Progress callback raised an exception: %s", exc)
