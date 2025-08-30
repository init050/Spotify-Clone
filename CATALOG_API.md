# مستندات ماژول کاتالوگ موسیقی

این مستندات به شما کمک می‌کند تا ماژول کاتالوگ موسیقی را راه‌اندازی کرده و از APIهای آن استفاده کنید.

## ۱. راه‌اندازی محیط توسعه

این پروژه با استفاده از Docker و Docker Compose اجرا می‌شود. اطمینان حاصل کنید که هر دو روی سیستم شما نصب هستند.

### متغیرهای محیطی (`.env`)

قبل از اجرا، یک فایل `.env` در ریشه پروژه ایجاد کرده و متغیرهای زیر را بر اساس فایل `.env.example` تکمیل کنید. مقادیر پیش‌فرض برای S3/MinIO برای محیط توسعه مناسب هستند.

```env
# Django Core
SECRET_KEY='your-secret-key'
DEBUG=True

# Database (PostgreSQL)
POSTGRES_DB='spotify_clone'
POSTGRES_USER='spotify_clone'
POSTGRES_PASSWORD='ZhWVEmq3'
POSTGRES_HOST='db'
POSTGRES_PORT=5432

# Celery (Redis)
CELERY_BROKER_URL='redis://redis:6379/0'
CELERY_RESULT_BACKEND='redis://redis:6379/0'

# S3 Storage (for MinIO in dev)
AWS_ACCESS_KEY_ID='minioadmin'
AWS_SECRET_ACCESS_KEY='minioadmin'
AWS_STORAGE_BUCKET_NAME='spotify-clone-media'
AWS_S3_ENDPOINT_URL='http://localhost:9000' # Note: Use localhost for client-side access

# Catalog Settings
CATALOG_HLS_VARIANTS='64,128,256' # in kbps
```

**نکته مهم:** مقدار `AWS_S3_ENDPOINT_URL` برای دسترسی از سمت کلاینت (مانند اپلیکیشن شما یا Postman) باید `http://localhost:9000` باشد، اما برای ارتباطات داخلی بین سرویس‌های داکر (مانند ارتباط Celery با MinIO) از `http://minio:9000` استفاده می‌شود. تنظیمات فعلی برای هر دو سناریو به درستی کار می‌کند.

### اجرای پروژه

۱. **ساخت و اجرای کانتینرها:**
   دستور زیر را در ریشه پروژه اجرا کنید. این دستور تمام سرویس‌ها (وب، دیتابیس، Redis, MinIO) را راه‌اندازی کرده و باکت مورد نیاز را در MinIO ایجاد می‌کند.
   ```bash
   sudo docker compose up --build -d
   ```

۲. **اجرای مایگریشن‌ها:**
   پس از اجرای کانتینرها، مایگریشن‌های پایگاه داده را اعمال کنید:
   ```bash
   sudo docker compose exec web python manage.py migrate
   ```

۳. **ایجاد کاربر Superuser (اختیاری):**
   برای دسترسی به پنل ادمین جنگو، یک superuser ایجاد کنید:
   ```bash
   sudo docker compose exec web python manage.py createsuperuser
   ```

۴. **اجرای Celery Worker:**
   برای پردازش فایل‌های صوتی، باید حداقل یک Celery worker را در یک ترمینال جداگانه اجرا کنید:
   ```bash
   sudo docker compose exec web celery -A Spotify_Clone worker --loglevel=info
   ```

حالا پروژه شما در آدرس `http://localhost:8000` در دسترس است و MinIO در `http://localhost:9001` قابل مشاهده است.

## ۲. نمونه درخواست‌های API (HTTPie)

در ادامه چند مثال برای استفاده از API با ابزار [HTTPie](https://httpie.io/) آورده شده است.

**توکن JWT:** برای تمام درخواست‌هایی که نیاز به احراز هویت دارند، ابتدا باید با یک کاربر لاگین کرده و توکن access را دریافت کنید.

```bash
# دریافت توکن (مثال)
http POST http://localhost:8000/api/v1/auth/login/ email='user@example.com' password='password'
```
سپس توکن را در هدر تمام درخواست‌های بعدی قرار دهید: `Authorization:"Bearer <your_access_token>"`

### هنرمندان (Artists)

- **لیست هنرمندان:**
  ```bash
  http GET http://localhost:8000/api/v1/catalog/artists/
  ```
- **ایجاد هنرمند (نیاز به دسترسی staff/manager):**
  ```bash
  http POST http://localhost:8000/api/v1/catalog/artists/ name='New Artist' slug='new-artist' Authorization:"Bearer <token>"
  ```
- **فالو کردن یک هنرمند:**
  ```bash
  http POST http://localhost:8000/api/v1/catalog/artists/new-artist/follow/ Authorization:"Bearer <token>"
  ```
- **آنفالو کردن:**
  ```bash
  http DELETE http://localhost:8000/api/v1/catalog/artists/new-artist/follow/ Authorization:"Bearer <token>"
  ```

### جستجو

- **جستجوی سراسری:**
  ```bash
  http GET http://localhost:8000/api/v1/catalog/search/ q=='new'
  ```

### آپلود فایل صوتی (دو مرحله‌ای)

**مرحله ۱: شروع آپلود**
یک درخواست `POST` برای دریافت لینک امن آپلود ارسال کنید.

```bash
http POST http://localhost:8000/api/v1/catalog/uploads/audio/init/ \
  filename="my-song.mp3" \
  file_size:=1234567 \
  mime_type="audio/mpeg" \
  Authorization:"Bearer <token>"
```
پاسخ شامل یک `url` و یک دیکشنری `fields` خواهد بود.

**مرحله ۲: آپلود مستقیم فایل**
فایل خود را مستقیماً با استفاده از اطلاعات دریافتی به سرویس S3/MinIO آپلود کنید. مثال با `curl`:

```bash
# از پاسخ مرحله قبل استفاده کنید
curl -X POST "URL_FROM_RESPONSE" \
  -F "key=FIELDS_KEY" \
  -F "Content-Type=FIELDS_CONTENT_TYPE" \
  ... # Other fields from the response
  -F "file=@/path/to/your/my-song.mp3"
```

**مرحله ۳: تکمیل آپلود**
پس از آپلود موفق، به API اطلاع دهید تا پردازش را شروع کند. (فرض کنید قبلاً یک رکورد `Track` با `status=pending` ایجاد کرده‌اید)

```bash
http POST http://localhost:8000/api/v1/catalog/uploads/audio/complete/ \
  upload_id="UPLOAD_ID_FROM_STEP_1" \
  object_name="OBJECT_NAME_FROM_STEP_1" \
  track_id="YOUR_PENDING_TRACK_ID" \
  Authorization:"Bearer <token>"
```

با این کار، تسک Celery برای پردازش فایل آغاز می‌شود.

### دریافت لینک پخش

- **دریافت مانیفست HLS:**
  ```bash
  http GET http://localhost:8000/api/v1/catalog/streams/your-track-slug/manifest/ Authorization:"Bearer <token>"
  ```
  پاسخ حاوی یک `manifest_url` است که می‌توانید از آن در هر پلیر HLS استفاده کنید.
