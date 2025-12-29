# CRITICAL: Set Up PostgreSQL on Railway to Prevent Data Loss

## The Problem
Railway's filesystem is **ephemeral** - SQLite databases get **DELETED on every deploy**. This is why your data keeps disappearing.

## The Solution: PostgreSQL
PostgreSQL is a proper database that persists data. Railway provides it as a service.

## Step-by-Step Setup (5 minutes):

### 1. Add PostgreSQL to Your Railway Project
1. Go to your Railway dashboard
2. Click **"+ New"** → **"Database"** → **"Add PostgreSQL"**
3. Railway will create a PostgreSQL database and automatically set `DATABASE_URL`

### 2. Connect Your App to PostgreSQL
The code is already updated to use `DATABASE_URL` automatically. Railway will:
- ✅ Automatically provide `DATABASE_URL` environment variable
- ✅ Your app will detect it and use PostgreSQL instead of SQLite
- ✅ Data will persist across deploys

### 3. Deploy
1. Push the updated code (already done - `psycopg2-binary` added to requirements.txt)
2. Railway will automatically:
   - Install PostgreSQL driver
   - Connect to your PostgreSQL database
   - Create tables on first run
   - **KEEP YOUR DATA FOREVER**

## That's It!

Once PostgreSQL is added:
- ✅ Data persists across deploys
- ✅ No more data loss
- ✅ Production-ready database
- ✅ Automatic backups (Railway handles this)

## Verify It's Working

After adding PostgreSQL and deploying:
1. Upload some test data
2. Check Railway logs - you should see it connecting to PostgreSQL
3. Redeploy - your data should still be there!

## Important Notes

- **First deploy after adding PostgreSQL**: Tables will be created automatically
- **Existing SQLite data**: You'll need to re-upload (one last time)
- **Future uploads**: Will persist forever

---

**DO THIS NOW** - Add PostgreSQL to Railway and your data loss problem is solved forever.

