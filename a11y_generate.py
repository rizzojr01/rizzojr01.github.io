#!/usr/bin/env python3
"""
a11y_generate.py — AI-powered accessibility enrichment for Rizzo Labs site

Step 4: Generate alt text for images via Claude vision
Step 5: Extract video keyframes via ffmpeg + generate audio descriptions
"""

import os
import re
import sys
import json
import base64
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path

# ── Config ─────────────────────────────────────────────────────────────────
REPO = Path(__file__).parent
HTML_FILES = [
    "index.html", "projects.html", "funding.html", "publications.html",
    "team.html", "join.html", "photos.html", "contact.html",
]
MODEL = "claude-sonnet-4-6"
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
if not API_KEY:
    print("ERROR: ANTHROPIC_API_KEY environment variable not set.")
    sys.exit(1)

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
HEADERS_BASE = {
    "x-api-key": API_KEY,
    "anthropic-version": "2023-06-01",
    "content-type": "application/json",
}

# Images to skip generating alt text for (decorative icons, etc.)
SKIP_IMAGES = {"images/web_logo.png"}

# Generic alt values that need replacement
GENERIC_ALT = {"background", "image", "photo", "logo", "gallery image", ""}


# ── Anthropic API helper ────────────────────────────────────────────────────
def call_claude(messages, max_tokens=400):
    payload = json.dumps({
        "model": MODEL,
        "max_tokens": max_tokens,
        "messages": messages,
    }).encode()
    req = urllib.request.Request(ANTHROPIC_URL, data=payload, headers=HEADERS_BASE, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data["content"][0]["text"].strip()
    except Exception as e:
        return None


def encode_image(path: Path) -> tuple[str, str]:
    """Return (base64_data, media_type)."""
    suffix = path.suffix.lower()
    types = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
             ".png": "image/png", ".gif": "image/gif", ".webp": "image/webp"}
    mt = types.get(suffix, "image/jpeg")
    return base64.standard_b64encode(path.read_bytes()).decode(), mt


def generate_alt_text(img_path: Path) -> str:
    """Call Claude vision to generate alt text for a single image."""
    b64, mt = encode_image(img_path)
    messages = [{
        "role": "user",
        "content": [
            {
                "type": "image",
                "source": {"type": "base64", "media_type": mt, "data": b64},
            },
            {
                "type": "text",
                "text": (
                    "You are writing alt text for a website belonging to Rizzo Labs, "
                    "a rehabilitation engineering research lab at NYU Langone. "
                    "Look at this image and write concise, descriptive alt text (1-2 sentences max). "
                    "Focus on what the image actually shows — content and purpose, not aesthetics. "
                    "For lab logos: describe the logo design and what it represents. "
                    "For video thumbnails: describe what is visually happening in the scene. "
                    "For background/decorative images: briefly describe the visual content, "
                    "and if it is purely decorative with no meaningful information, return exactly: DECORATIVE\n"
                    "Return ONLY the alt text string, no quotes, no explanation."
                ),
            },
        ],
    }]
    return call_claude(messages, max_tokens=120)


def fallback_alt(img_path: Path) -> str:
    stem = img_path.stem.replace("_", " ").replace("-", " ")
    return stem.capitalize() + " image"


# ── Step 4: Alt text for images ─────────────────────────────────────────────
def step4_alt_text():
    print("\n── Step 4: Generating AI alt text for images ──────────────────────")

    # Find all img tags needing work across HTML files
    img_pattern = re.compile(r'(<img\b[^>]*\bsrc=["\'])([^"\']+)(["\'][^>]*)(>)', re.IGNORECASE)
    alt_attr_pat = re.compile(r'\balt=["\']([^"\']*)["\']', re.IGNORECASE)

    # Collect unique image paths needing alt text
    imgs_to_process = {}  # rel_path -> set of (html_file,)

    for html_name in HTML_FILES:
        html_path = REPO / html_name
        if not html_path.exists():
            continue
        content = html_path.read_text(encoding="utf-8")
        for m in img_pattern.finditer(content):
            src = m.group(2).strip()
            # Resolve relative to repo root
            rel = src.lstrip("/")
            if rel in SKIP_IMAGES:
                continue
            alt_match = alt_attr_pat.search(m.group(0))
            current_alt = alt_match.group(1).strip().lower() if alt_match else None
            # Needs attention if: missing, generic, or is the filename
            needs_update = (
                current_alt is None or
                current_alt in GENERIC_ALT or
                current_alt == Path(src).stem.lower()
            )
            if needs_update:
                if rel not in imgs_to_process:
                    imgs_to_process[rel] = []
                imgs_to_process[rel].append(html_name)

    # Also add known candidates that may have been missed
    known = [
        "images/background.png",
        "images/REACTIV.jpg",
        "images/vmil.jpg",
        "video/video_cover/video2.png",
        "video/video_cover/video3.png",
        "video/video_cover/video4.png",
        "video/video_cover/tedx.png",
        "video/video_cover/video5.png",
        "video/video_cover/video6.png",
        "video/video_cover/video7.png",
        "video/video_cover/video8.png",
    ]
    for k in known:
        if k not in imgs_to_process and (REPO / k).exists():
            imgs_to_process[k] = ["index.html"]

    generated = {}  # rel_path -> alt_text
    updated_count = 0

    for rel, html_list in imgs_to_process.items():
        img_path = REPO / rel
        if not img_path.exists():
            print(f"  ⚠ Not found: {rel}")
            continue

        alt = generate_alt_text(img_path)
        if alt is None:
            alt = fallback_alt(img_path)
            print(f"  ⚠ API fail, fallback: {rel} → \"{alt}\"")
        elif alt.strip().upper() == "DECORATIVE":
            generated[rel] = "DECORATIVE"
            print(f"  ✓ {rel} → [decorative]")
        else:
            generated[rel] = alt
            print(f"  ✓ {rel} → \"{alt}\"")

    # Write alt text back into HTML files
    for html_name in HTML_FILES:
        html_path = REPO / html_name
        if not html_path.exists():
            continue
        content = html_path.read_text(encoding="utf-8")
        changed = False

        def replace_alt(m):
            nonlocal changed
            full_tag = m.group(0)
            src = m.group(2).strip()
            rel = src.lstrip("/")
            if rel not in generated:
                return full_tag
            new_alt = generated[rel]

            if new_alt == "DECORATIVE":
                # Remove existing alt, set empty + role=presentation
                tag = alt_attr_pat.sub('', full_tag)
                # Inject alt="" role="presentation"
                tag = re.sub(r'(<img\b)', r'\1 alt="" role="presentation"', tag, count=1)
            else:
                escaped = new_alt.replace('"', '&quot;')
                if alt_attr_pat.search(full_tag):
                    tag = alt_attr_pat.sub(f'alt="{escaped}"', full_tag, count=1)
                else:
                    # Insert alt before closing >
                    tag = re.sub(r'(/?>)$', f' alt="{escaped}"\\1', full_tag)
            if tag != full_tag:
                changed = True
            return tag

        new_content = img_pattern.sub(replace_alt, content)
        if changed:
            html_path.write_text(new_content, encoding="utf-8")
            updated_count += 1

    print(f"\n  → Updated alt text in {updated_count} HTML file(s).")
    return len(generated)


# ── Step 5: Video audio descriptions ────────────────────────────────────────
MP4_FILES = [
    "video/video2.mp4", "video/video3.mp4", "video/video4.mp4",
    "video/video5.mp4", "video/video6.mp4", "video/video7.mp4",
    "video/video8.mp4", "video/tedx.mp4",
    "images/Commute Booster Demo Edited.mp4",
    "images/point2tell.mp4",
    "images/vw.mp4",
    "images/unav.mp4",
    "images/curb.mp4",
    "images/construction.mp4",
    "images/VMIL_website_video1.mp4",
    "images/VMIL_website_video2.mp4",
    "images/Peds rehab hand tracking sample.mp4",
    "images/ss.mp4",
    "images/Jebsen_&_Taylor_Video.mp4",
    "images/MS-9_Hole_Peg_Test_Video.mp4",
]

# Map video filename stem → aria-label selector in HTML
VIDEO_SRC_PAT = re.compile(r'(src=["\'])([^"\']*\.mp4)(["\'])', re.IGNORECASE)
ARIA_LABEL_PAT = re.compile(r'\baria-label=["\'][^"\']*["\']', re.IGNORECASE)


def get_video_duration(mp4_path: Path) -> float:
    """Return video duration in seconds using ffprobe."""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(mp4_path)],
            capture_output=True, text=True, timeout=15
        )
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def extract_frames(mp4_path: Path, out_dir: Path) -> list[Path]:
    """Extract 3 keyframes at 10%, 50%, 90% of duration."""
    duration = get_video_duration(mp4_path)
    if duration <= 0:
        return []
    times = [duration * 0.10, duration * 0.50, duration * 0.90]
    frames = []
    for i, t in enumerate(times):
        out = out_dir / f"frame_{i+1}.jpg"
        r = subprocess.run(
            ["ffmpeg", "-y", "-ss", str(t), "-i", str(mp4_path),
             "-frames:v", "1", "-q:v", "3", str(out)],
            capture_output=True, timeout=30
        )
        if out.exists():
            frames.append(out)
    return frames


def generate_video_description(frames: list[Path], video_name: str) -> dict | None:
    """Send 3 frames to Claude and get aria_label + audio_description."""
    content = []
    for f in frames:
        b64, mt = encode_image(f)
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": mt, "data": b64},
        })
    content.append({
        "type": "text",
        "text": (
            "You are writing accessibility descriptions for a research lab website video.\n"
            "These 3 frames are from the start, middle, and end of the video.\n"
            "The lab is Rizzo Labs at NYU — they build assistive technology for people "
            "with visual and motor disabilities. Their projects include things like "
            "wearable navigation aids, gesture-controlled assistive devices, and "
            "rehabilitation assessment tools.\n\n"
            "Write two things:\n"
            "1. aria_label: 1 sentence describing what this video shows, for a link label.\n"
            "2. audio_description: 2-4 sentences describing key visual content for a "
            "visually impaired visitor — include people, actions, technology, "
            "settings, and anything meaningful shown across the 3 frames.\n\n"
            "Return ONLY valid JSON: { \"aria_label\": \"...\", \"audio_description\": \"...\" }"
        ),
    })

    result = call_claude([{"role": "user", "content": content}], max_tokens=300)
    if not result:
        return None
    # Extract JSON from response
    try:
        m = re.search(r'\{[^{}]+\}', result, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception:
        pass
    return None


def step5_video_descriptions():
    print("\n── Step 5: Generating AI audio descriptions for videos ─────────────")

    # Check ffmpeg
    if not shutil.which("ffmpeg"):
        print("  ffmpeg not found. Install with: brew install ffmpeg")
        return 0

    tmp_base = Path(tempfile.mkdtemp(prefix="a11y_frames_"))
    results = {}  # rel_path -> {aria_label, audio_description}
    fail_list = []

    for rel in MP4_FILES:
        mp4_path = REPO / rel
        if not mp4_path.exists():
            print(f"  ⚠ Not found: {rel}")
            continue

        stem = mp4_path.stem
        out_dir = tmp_base / re.sub(r'[^a-zA-Z0-9]', '_', stem)
        out_dir.mkdir(parents=True, exist_ok=True)

        frames = extract_frames(mp4_path, out_dir)
        if not frames:
            print(f"  ⚠ Frame extraction failed: {rel}")
            fail_list.append(rel)
            continue

        desc = generate_video_description(frames, stem)
        if desc:
            results[rel] = desc
            print(f"  ✓ {rel}")
            print(f"      aria_label: {desc.get('aria_label','')[:80]}")
        else:
            print(f"  ⚠ Description generation failed: {rel}")
            fail_list.append(rel)

    # Apply to HTML files
    updated = 0
    for html_name in HTML_FILES:
        html_path = REPO / html_name
        if not html_path.exists():
            continue
        content = html_path.read_text(encoding="utf-8")
        changed = False

        for rel, desc in results.items():
            # Find video src references for this file
            mp4_name = Path(rel).name
            # Build escaped version for URL-encoded references
            mp4_enc = mp4_name.replace(" ", "%20").replace("&", "%26")

            # Match <video ... src="...thisfile.mp4" ...>
            vid_pat = re.compile(
                r'(<video\b[^>]*\bsrc=["\'][^"\']*' +
                re.escape(mp4_name).replace(r'\ ', r'(%20|\+| )').replace(r'\&', r'(&amp;|&)') +
                r'[^"\']*["\'][^>]*>)',
                re.IGNORECASE
            )

            def apply_aria(m2, d=desc):
                nonlocal changed
                tag = m2.group(1)
                new_label = d.get("aria_label", "Research video")
                escaped = new_label.replace('"', '&quot;')
                if ARIA_LABEL_PAT.search(tag):
                    new_tag = ARIA_LABEL_PAT.sub(f'aria-label="{escaped}"', tag, count=1)
                else:
                    new_tag = re.sub(r'(<video\b)', f'\\1 aria-label="{escaped}"', tag, count=1)
                if new_tag != tag:
                    changed = True
                return new_tag

            content = vid_pat.sub(apply_aria, content)

            # Insert audio description paragraph after </video> if not already present
            audio_desc = desc.get("audio_description", "")
            if audio_desc and mp4_name in content and "a11y-audio-desc" not in content:
                # Find </video> following this src and insert after it
                ins_tag = (
                    '\n<p class="a11y-audio-desc" aria-live="polite">'
                    + audio_desc.replace('<', '&lt;').replace('>', '&gt;')
                    + '</p>'
                )
                # Insert after first </video> that follows this src
                marker = re.escape(mp4_name)
                content = re.sub(
                    r'(' + marker + r'[^<]*</video>)',
                    r'\1' + ins_tag,
                    content, count=1, flags=re.IGNORECASE
                )
                changed = True

        if changed:
            html_path.write_text(content, encoding="utf-8")
            updated += 1

    # Cleanup
    shutil.rmtree(tmp_base, ignore_errors=True)
    print(f"\n  → Applied video descriptions to {updated} HTML file(s).")
    if fail_list:
        print(f"  ⚠ Failed: {fail_list}")
    return len(results)


# ── Step 6: Verification ────────────────────────────────────────────────────
def step6_verify(alt_count, video_count):
    print("\n── Step 6: Verification ────────────────────────────────────────────")

    pages_ok = []
    pages_missing_script = []
    for html_name in HTML_FILES:
        html_path = REPO / html_name
        if not html_path.exists():
            continue
        content = html_path.read_text(encoding="utf-8")
        if "accessibility.js" in content:
            pages_ok.append(html_name)
        else:
            pages_missing_script.append(html_name)

    # Images still missing alt
    img_pat = re.compile(r'<img\b[^>]*>', re.IGNORECASE)
    alt_missing = []
    for html_name in HTML_FILES:
        html_path = REPO / html_name
        if not html_path.exists():
            continue
        content = html_path.read_text(encoding="utf-8")
        for m in img_pat.finditer(content):
            tag = m.group(0)
            alt_m = re.search(r'alt=["\']([^"\']*)["\']', tag, re.I)
            if not alt_m:
                src_m = re.search(r'src=["\']([^"\']+)["\']', tag, re.I)
                src = src_m.group(1) if src_m else "unknown"
                alt_missing.append(f"{html_name}: {src}")

    # Videos not wrapped with role=region (check in HTML source)
    unwrapped = []
    video_pat = re.compile(r'<video\b[^>]*src=["\']([^"\']+\.mp4)[^"\']*["\'][^>]*>', re.IGNORECASE)
    for html_name in HTML_FILES:
        html_path = REPO / html_name
        if not html_path.exists():
            continue
        content = html_path.read_text(encoding="utf-8")
        for m in video_pat.finditer(content):
            src = m.group(1)
            # accessibility.js handles wrapping at runtime; just flag for reference
            pass

    print(f"\n  ✓ {len(pages_ok)} pages have accessibility.js: {', '.join(pages_ok)}")
    if pages_missing_script:
        print(f"  ⚠ Missing script: {pages_missing_script}")
    print(f"  ✓ {alt_count} images given AI-generated alt text")
    print(f"  ✓ {video_count} videos given AI-generated audio descriptions")
    if alt_missing:
        print(f"  ⚠ {len(alt_missing)} img tags still missing alt attribute:")
        for a in alt_missing[:10]:
            print(f"      {a}")
    else:
        print("  ✓ No img tags missing alt attributes")
    print()


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    alt_count = step4_alt_text()
    video_count = step5_video_descriptions()
    step6_verify(alt_count, video_count)
