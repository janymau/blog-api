#!/usr/bin/env bash
# scripts/start.sh — bring the project from zero to running with one command

set -euo pipefail

# ─── colours ────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

log()     { echo -e "${CYAN}[start.sh]${NC} $*"; }
success() { echo -e "${GREEN}[✓]${NC} $*"; }
warn()    { echo -e "${YELLOW}[!]${NC} $*"; }
fail()    { echo -e "${RED}[✗] FAILED: $*${NC}"; exit 1; }

# ─── trap: print which step failed ──────────────────────────────────────────
CURRENT_STEP="unknown"
trap 'fail "Step \"${CURRENT_STEP}\" exited with error on line ${LINENO}"' ERR

step() {
    CURRENT_STEP="$*"
    echo ""
    echo -e "${BOLD}▶ $*${NC}"
}

# ─── required environment variables ─────────────────────────────────────────
step "Validating environment variables"

REQUIRED_VARS=(
    "DJANGO_SECRET_KEY"
    "DJANGO_SETTINGS_MODULE"
    "SUPERUSER_EMAIL"
    "SUPERUSER_PASSWORD"
    "SUPERUSER_FIRST_NAME"
    "SUPERUSER_LAST_NAME"
)

MISSING=()
for var in "${REQUIRED_VARS[@]}"; do
    if [[ -z "${!var:-}" ]]; then
        MISSING+=("$var")
    fi
done

if [[ ${#MISSING[@]} -gt 0 ]]; then
    echo -e "${RED}[✗] Missing required environment variables:${NC}"
    for var in "${MISSING[@]}"; do
        echo -e "    ${RED}• ${var}${NC}"
    done
    exit 1
fi

success "All required environment variables are set"

# ─── locate project root (one level up from scripts/) ───────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"
log "Working directory: ${PROJECT_ROOT}"

# ─── python / venv ──────────────────────────────────────────────────────────
step "Checking Python environment"

if [[ ! -f "manage.py" ]]; then
    fail "manage.py not found in ${PROJECT_ROOT}. Is this the right directory?"
fi

PYTHON="${PYTHON:-python}"
if ! command -v "$PYTHON" &>/dev/null; then
    PYTHON=python3
fi
command -v "$PYTHON" &>/dev/null || fail "Python not found. Install Python 3.10+."
success "Using $($PYTHON --version)"

# ─── dependencies ────────────────────────────────────────────────────────────
step "Installing dependencies"

if [[ -f "requirements.txt" ]]; then
    $PYTHON -m pip install -q -r requirements.txt
    success "Dependencies installed"
else
    warn "requirements.txt not found — skipping pip install"
fi

# ─── migrations ──────────────────────────────────────────────────────────────
step "Running migrations"

$PYTHON manage.py migrate --run-syncdb 2>&1 | sed 's/^/  /'
success "Migrations complete"

# ─── static files ────────────────────────────────────────────────────────────
step "Collecting static files"

$PYTHON manage.py collectstatic --noinput 2>&1 | tail -3 | sed 's/^/  /'
success "Static files collected"

# ─── translation files ───────────────────────────────────────────────────────
step "Compiling translation files"

if command -v msgfmt &>/dev/null; then
    $PYTHON manage.py compilemessages 2>&1 | sed 's/^/  /' || warn "compilemessages had warnings (non-fatal)"
    success "Translations compiled"
else
    warn "GNU gettext (msgfmt) not found — skipping compilemessages"
    warn "Install from https://mlocati.github.io/articles/gettext-iconv-windows.html"
fi

# ─── superuser ───────────────────────────────────────────────────────────────
step "Creating superuser"

$PYTHON manage.py shell <<EOF
from apps.users.models import CustomUser

email    = "${SUPERUSER_EMAIL}"
password = "${SUPERUSER_PASSWORD}"
first    = "${SUPERUSER_FIRST_NAME}"
last     = "${SUPERUSER_LAST_NAME}"

if CustomUser.objects.filter(email=email).exists():
    print(f"  superuser {email} already exists — skipping")
else:
    CustomUser.objects.create_superuser(
        email=email,
        password=password,
        first_name=first,
        last_name=last,
    )
    print(f"  superuser {email} created")
EOF

success "Superuser ready"

# ─── seed data ───────────────────────────────────────────────────────────────
step "Seeding test data"

$PYTHON manage.py shell <<'EOF'
from django.utils.text import slugify
from apps.users.models import CustomUser
from apps.blogs.models import Category, Tag, Post, Comment

# ── users ────────────────────────────────────────────────────────────────────
users_data = [
    {"email": "alice@example.com",   "first_name": "Alice",   "last_name": "Smith",    "password": "Test1234!", "preferred_language": "en", "timezone": "UTC"},
    {"email": "bob@example.com",     "first_name": "Bob",     "last_name": "Jones",    "password": "Test1234!", "preferred_language": "ru", "timezone": "Europe/Moscow"},
    {"email": "carlos@example.com",  "first_name": "Carlos",  "last_name": "Garcia",   "password": "Test1234!", "preferred_language": "kz", "timezone": "Asia/Almaty"},
]

users = {}
for u in users_data:
    obj, created = CustomUser.objects.get_or_create(
        email=u["email"],
        defaults={k: v for k, v in u.items() if k != "password"}
    )
    if created:
        obj.set_password(u["password"])
        obj.save()
        print(f"  created user: {obj.email}")
    else:
        print(f"  user exists:  {obj.email}")
    users[u["email"]] = obj

# ── categories ───────────────────────────────────────────────────────────────
cats_data = [
    {"name_en": "Technology", "name_ru": "Технологии",  "name_kz": "Технология",   "slug": "technology"},
    {"name_en": "Travel",     "name_ru": "Путешествия", "name_kz": "Саяхат",       "slug": "travel"},
    {"name_en": "Food",       "name_ru": "Еда",         "name_kz": "Тамақ",        "slug": "food"},
    {"name_en": "Science",    "name_ru": "Наука",       "name_kz": "Ғылым",        "slug": "science"},
]

categories = {}
for c in cats_data:
    obj, created = Category.objects.get_or_create(
        slug=c["slug"],
        defaults=c
    )
    if created:
        print(f"  created category: {obj.name_en}")
    categories[c["slug"]] = obj

# ── tags ─────────────────────────────────────────────────────────────────────
tag_names = ["django", "python", "travel", "food", "ai", "science", "tutorial", "beginner"]

tags = {}
for name in tag_names:
    obj, created = Tag.objects.get_or_create(
        name=name,
        defaults={"slug": slugify(name)}
    )
    if created:
        print(f"  created tag: {name}")
    tags[name] = obj

# ── posts ─────────────────────────────────────────────────────────────────────
posts_data = [
    {
        "title": "Getting started with Django",
        "slug": "getting-started-django",
        "body": "Django is a high-level Python web framework that encourages rapid development.",
        "author": users["alice@example.com"],
        "category": categories["technology"],
        "tag_names": ["django", "python", "tutorial", "beginner"],
        "status": "published",
    },
    {
        "title": "My trip to Almaty",
        "slug": "trip-to-almaty",
        "body": "Almaty is a beautiful city nestled at the foot of the Tian Shan mountains.",
        "author": users["bob@example.com"],
        "category": categories["travel"],
        "tag_names": ["travel"],
        "status": "published",
    },
    {
        "title": "Best Kazakh dishes to try",
        "slug": "best-kazakh-dishes",
        "body": "Beshbarmak, kurt, baursak — Kazakh cuisine is rich and hearty.",
        "author": users["carlos@example.com"],
        "category": categories["food"],
        "tag_names": ["food"],
        "status": "published",
    },
    {
        "title": "Introduction to AI",
        "slug": "intro-to-ai",
        "body": "Artificial intelligence is transforming every industry on the planet.",
        "author": users["alice@example.com"],
        "category": categories["science"],
        "tag_names": ["ai", "science", "python"],
        "status": "published",
    },
    {
        "title": "Draft: upcoming post",
        "slug": "draft-upcoming",
        "body": "This post is still a work in progress.",
        "author": users["bob@example.com"],
        "category": categories["technology"],
        "tag_names": ["django"],
        "status": "draft",
    },
]

post_objects = []
for p in posts_data:
    tag_names_list = p.pop("tag_names")
    obj, created = Post.objects.get_or_create(
        slug=p["slug"],
        defaults=p
    )
    obj.tags.set([tags[t] for t in tag_names_list])
    if created:
        print(f"  created post: {obj.title}")
    post_objects.append(obj)

# ── comments ──────────────────────────────────────────────────────────────────
comments_data = [
    {"post": post_objects[0], "author": users["bob@example.com"],    "body": "Great introduction, very helpful!"},
    {"post": post_objects[0], "author": users["carlos@example.com"], "body": "I learned a lot from this post."},
    {"post": post_objects[1], "author": users["alice@example.com"],  "body": "Almaty is on my bucket list!"},
    {"post": post_objects[2], "author": users["bob@example.com"],    "body": "Beshbarmak is amazing, totally agree."},
    {"post": post_objects[3], "author": users["carlos@example.com"], "body": "AI is the future for sure."},
]

for c in comments_data:
    exists = Comment.objects.filter(post=c["post"], author=c["author"], body=c["body"]).exists()
    if not exists:
        Comment.objects.create(**c)
        print(f"  created comment by {c['author'].email} on \"{c['post'].title}\"")

print("  seed complete")
EOF

success "Test data seeded"

# ─── summary ─────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}${GREEN}  Blog API is ready                                       ${NC}"
echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  ${BOLD}URLs${NC}"
echo -e "  API root   →  http://127.0.0.1:8000/api/"
echo -e "  Swagger UI →  http://127.0.0.1:8000/api/docs/"
echo -e "  ReDoc      →  http://127.0.0.1:8000/api/redoc/"
echo -e "  Admin      →  http://127.0.0.1:8000/admin/"
echo -e "  Stats      →  http://127.0.0.1:8000/api/stats/"
echo ""
echo -e "  ${BOLD}Superuser credentials${NC}"
echo -e "  Email      →  ${SUPERUSER_EMAIL}"
echo -e "  Password   →  ${SUPERUSER_PASSWORD}"
echo ""
echo -e "  ${BOLD}Seed user credentials${NC}  (all passwords: Test1234!)"
echo -e "  alice@example.com   (en / UTC)"
echo -e "  bob@example.com     (ru / Europe/Moscow)"
echo -e "  carlos@example.com  (kz / Asia/Almaty)"
echo ""
echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# ─── start server ────────────────────────────────────────────────────────────
step "Starting development server"
$PYTHON manage.py runserver