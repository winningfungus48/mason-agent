# Connect to your server (SSH) — beginner guide

**What this is:** Your “droplet” is a computer in the cloud. **SSH** is how you open a **text window** that runs commands **on that computer**, from your PC. You are not editing your website in a browser for this — you use a **terminal** (black or blue window where you type lines).

---

## What you need before you start (one-time lookup)

1. **Your droplet’s IP address** — a number like `104.131.39.150`.  
   - Log in to **DigitalOcean** → **Droplets** → click your droplet → copy **Public IPv4 address**.

2. **Your login name** — this project uses **`mason`** (all lowercase). If DigitalOcean shows a different “user” in their docs, use what they gave you when you created the droplet.

3. **How you log in:**
   - **Password** — only if you set one and DigitalOcean emailed it or you saved it.
   - **SSH key** — common: you don’t type a password; your PC proves it has a secret file. If login fails, you may need to add your key in DigitalOcean (see “If it won’t connect” below).

**Write these on a sticky note:** IP = `___` · User = `mason`

---

## Step 1 — Open a terminal on your Windows PC

Pick **one** way:

- Press **Windows key**, type **PowerShell**, press **Enter**.  
  **or**
- Press **Windows key**, type **Terminal**, open **Windows Terminal**, choose **PowerShell**.

You should see a line ending in something like `PS C:\Users\YourName>`.

---

## Step 2 — Connect (copy-paste to reduce typing)

1. In DigitalOcean, **copy** the IP address (Ctrl+C).

2. In PowerShell, **type** `ssh` then a **space**, then type **`mason@`** then **paste** the IP.

   It should look exactly like this (your numbers will differ):

   ```text
   ssh mason@104.131.39.150
   ```

3. Press **Enter**.

---

## Step 3 — First time only: trust the server

You may see a question like **“Are you sure you want to continue connecting?”**

- Type **`yes`** and press **Enter**.  
  (You only do this the first time you connect from this PC.)

---

## Step 4 — Password or key

- If it asks for **`mason@...'s password`:** type the password **carefully** (nothing will show as you type — that’s normal) → **Enter**.

- If it **doesn’t** ask for a password and logs you in, you’re using an **SSH key**. Good — less typing next time.

---

## Step 5 — You’re in when you see a Linux prompt

You might see something like:

```text
mason@your-droplet-name:~$
```

That means commands you type now run **on the server**, not on your home PC.

**To leave safely:** type **`exit`** and press **Enter**.

---

## Make it one word next time (optional, saves labor)

After you’ve connected successfully **once**, you can create a **shortcut name** so you don’t type the IP every time.

1. On your PC, open **Notepad**.

2. Paste this **exactly** (change the IP to yours; keep `mason` if that’s your user):

   ```
   Host mydroplet
       HostName 104.131.39.150
       User mason
   ```

3. Save the file as **`config`** (no `.txt`) in this folder:

   `C:\Users\YOUR_WINDOWS_USERNAME\.ssh\`

   If `.ssh` doesn’t exist: in File Explorer, go to your user folder, create a new folder named `.ssh`, put `config` inside.

4. Next time, in PowerShell you only type:

   ```text
   ssh mydroplet
   ```

---

## If it won’t connect (short list)

| What you see | What to try |
|----------------|-------------|
| **Connection timed out** | Droplet may be off, or a **firewall** is blocking. In DigitalOcean: droplet should be **On**. Check **Networking → Firewalls**. |
| **Permission denied** | Wrong user name, wrong password, or **SSH key** not added to the droplet / DigitalOcean account. |
| **ssh: command not found** | Rare on Windows 10/11. Install **OpenSSH Client**: Settings → Apps → Optional features → Add OpenSSH Client. |

**DigitalOcean “Recovery” / “Console”:** In the droplet page, open the **Recovery** or **Console** (web terminal) so you can log in from the browser without SSH — useful if SSH keys are wrong.

---

## After you’re connected

Your main setup steps (install packages, edit `.env`, restart services) are in **`dashboard-setup.md`**. You only need to **copy each command** from that doc into this same SSH window and press **Enter** one at a time.

**Rule:** Don’t paste random commands from the internet. Only use commands from **your** project docs or from someone you trust.
