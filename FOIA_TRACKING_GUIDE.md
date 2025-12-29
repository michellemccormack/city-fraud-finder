# FOIA Tracking - What to Look For

## 🎯 Quick Test Checklist

### 1. **Open the Site**
- Go to: http://127.0.0.1:8000/
- Should see: Entity list table, filters, buttons in header

### 2. **Find an Entity to Test**
- Click on any entity row in the table
- OR: If no entities, upload test data first (use `test_upload.csv`)

### 3. **Look for the FOIA Requests Section**
In the entity detail panel (right side), you should see:

**✅ What You Should See:**
- Section header: **"FOIA Requests"**
- If no requests exist: Text saying "No FOIA requests yet."
- Button: **"+ Create FOIA Request"** (green button)

### 4. **Test Creating a Request**
1. Click **"+ Create FOIA Request"**
2. Prompt appears: "Recipient email/address (optional):"
3. Enter email (e.g., "records@city.gov") or press Enter to skip
4. Click OK
5. Alert: "✅ FOIA request created!"
6. Page refreshes automatically

**✅ What Should Appear:**
- A new box/card showing:
  - Status badge: **"draft"** (gray color)
  - Button: **"Update"** (blue button)
  - Request text preview (first 200 chars)
  - If you entered recipient: "To: [email]"

### 5. **Test Updating Status**
1. Click **"Update"** button on the FOIA request
2. Prompt: "Update status (draft, sent, responded, denied, partial):"
3. Type: **"sent"**
4. Prompt: "Sent date (YYYY-MM-DD, or press Enter for today):"
5. Press Enter (uses today's date) or type a date
6. Prompt: "Notes (optional):"
7. Type notes or press Enter
8. Click OK

**✅ What Should Happen:**
- Status badge changes to **"sent"** (blue color)
- Date appears: "Sent: [today's date]"
- Notes appear if you entered them

### 6. **Test Response Tracking**
1. Click **"Update"** again
2. Type: **"responded"**
3. Prompt: "Response date..."
4. Press Enter (uses today)
5. Prompt: "Response text (optional):"
6. Type response summary or press Enter
7. Prompt: "Notes (optional):"
8. Type notes or press Enter

**✅ What Should Happen:**
- Status badge changes to **"responded"** (green color)
- Shows: "Response received: [date]"
- Shows your notes

## 📍 Visual Guide

### FOIA Request Card Layout:
```
┌─────────────────────────────────────┐
│ [draft]        [Update]             │  ← Status badge + Update button
│ To: records@city.gov                │  ← Recipient (if provided)
│                                     │
│ [Request text preview...]           │  ← First 200 chars of request
│                                     │
│ Response received: 1/15/2025        │  ← Only if responded
│ Notes: Got partial data             │  ← Notes (if any)
└─────────────────────────────────────┘
```

### Status Color Coding:
- **draft** = Gray (#999)
- **sent** = Blue (#2196F3)
- **responded** = Green (#4CAF50)
- **denied** = Red (#f44336)
- **partial** = Orange (#FF9800)

## 🔍 Where to Find It

1. **In Entity Detail Panel** (right side of screen)
2. **Below** the "Evidence" section
3. **Replaces** the old "Records request draft" section
4. **Scroll down** if entity detail is long

## ✅ Expected Behavior

- ✅ FOIA requests persist (reload page, they're still there)
- ✅ Multiple requests can exist per entity
- ✅ Each request shows its own status, dates, notes
- ✅ Update button changes status and dates correctly
- ✅ Request text is auto-generated from entity info

## 🐛 If Something's Wrong

**No FOIA Requests section?**
- Check browser console (F12) for errors
- Make sure server restarted after code changes
- Try refreshing the page (Cmd+R / Ctrl+R)

**Create button doesn't work?**
- Check browser console for JavaScript errors
- Make sure you clicked on an entity row first
- Verify entity detail panel is showing

**Database errors?**
- Server should auto-create the table on startup
- Check server logs in terminal for errors
- Try restarting the server

## 🎯 Full Workflow Test

1. ✅ View entity → See "FOIA Requests" section
2. ✅ Create request → Status shows "draft"
3. ✅ Update to "sent" → Status changes, date appears
4. ✅ Update to "responded" → Status changes, response date appears
5. ✅ Add notes → Notes display in request card
6. ✅ Refresh page → Requests persist (still visible)

## 💡 Pro Tips

- **Multiple requests**: Create multiple requests for same entity to test listing
- **Status workflow**: Try all statuses (draft → sent → responded)
- **Date formats**: Use YYYY-MM-DD format (e.g., "2025-01-15") or press Enter for today
- **Notes**: Add notes at each status change to track progress

