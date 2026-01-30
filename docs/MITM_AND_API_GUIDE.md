# 🔥 Operation Spite: API Reverse Engineering Guide

## 🎯 Objective
Intercept HTTPS traffic from the Xiaomi Community app (`com.mi.global.bbs`) to find the **Unlock Ticket API Endpoint**.

## 🚧 The Hurdle: Certificate Pinning
Since you are on a **non-rooted** device, this is the hardest part.
1. **Standard HTTPS:** Easy. Install a User Certificate.
2. **Pinned HTTPS:** The app checks if the certificate matches Xiaomi's hardcoded one. It will reject `mitmproxy`'s certificate.

## 🛠️ Strategy Levels (Try in Order)

### Level 1: Standard MITM (The "Hail Mary")
Sometimes apps only pin the login endpoints but leave engagement/feed endpoints unpinned.
1. **Install mitmproxy:**
   ```bash
   pip install mitmproxy
   ```
2. **Run it:**
   ```bash
   mitmproxy --listen-host 0.0.0.0 --listen-port 8080
   ```
   *(`mitmweb` gives you a web UI, usually easier)*
3. **Configure Phone:**
   - Wi-Fi Settings -> Proxy -> Manual.
   - Host: Your PC's IP (check with `ip a`, e.g., `192.168.1.x`).
   - Port: `8080`.
4. **Install Cert:**
   - Open browser on phone, go to `mitm.it`.
   - Download the Android certificate.
   - Settings -> Security -> Encryption & Credentials -> Install a certificate -> CA Certificate.
5. **Test:** Open the app. If you see traffic in mitmproxy, **WE ARE GOLDEN**. If you see "Connection Error" or TLS alerts, pinning is active. Proceed to Level 2.

### Level 2: Virtual Environment (VirtualXposed) - **RECOMMENDED**
Since you can't root your phone, we use a "Virtual Space" app that simulates root for apps inside it.
1. Download **VirtualXposed** or **Taichi** (non-root Xposed frameworks) to your phone.
2. Install **JustTrustMe** (an Xposed module that disables SSL pinning).
3. Open VirtualXposed:
   - "Add App" -> Select Xiaomi Community.
   - "Add Module" -> Enable JustTrustMe.
4. Launch Xiaomi Community *from inside* VirtualXposed.
5. With `mitmproxy` running on your PC, the traffic should now be visible!

### Level 3: The Emulator (The "Brute Force")
If Level 2 fails (app detects virtual environment), use your Linux PC's power.
1. Install **Genymotion** (Personal use is free) or use **Android Studio AVD**.
2. Create a virtual device (e.g., Pixel 5, Android 11).
   - **Crucial:** Genymotion is usually rooted by default.
3. Install **Frida** server on the emulator.
4. Use Frida to hook the app and bypass SSL pinning dynamically.
   ```bash
   frida -U -f com.mi.global.bbs -l hooks.js --no-pause
   ```
   *(I can provide the `hooks.js` script if we get here).*

### Level 4: Static Analysis (Decompilation)
If we can't inspect traffic live, we look at the code.
1. Pull the APK:
   ```bash
   adb shell pm path com.mi.global.bbs
   adb pull /data/app/com.mi.global.bbs.../base.apk xiaomi_community.apk
   ```
2. Use **JADX-GUI**:
   - Open the APK.
   - Search for strings: `"unlock"`, `"apply"`, `"limit"`, `"quota"`.
   - Look for API URLs (e.g., `https://api.mi.com/...`).

---

## 🕵️ What to Look For
Once you have visibility, perform the "Unlock" action (or just browse) and look for:
1. **POST Requests:** Usually to `api.mi.com` or `global.bbs.mi.com`.
2. **Headers:**
   - `Cookie`: The session token (VERY IMPORTANT).
   - `User-Agent`: Might be specific.
   - `X-Request-Id`: Some tracking ID?
3. **Payload:** JSON data sent with the request.

## 📝 Next Steps for You
1. Try **Level 1** immediately. It takes 5 minutes.
2. If it fails, try **Level 2** (VirtualXposed + JustTrustMe).
3. Report back!

---

## ❓ FAQ
**Q: Can I extract the "engagement score"?**
A: Likely yes. Look for a `GET` request to `.../user/profile` or `.../score` when you open your profile page. The JSON response will likely contain your exact point value.

**Q: Legal?**
A: Intercepting your own traffic to a service you use on a device you own to unlock features you are entitled to? Generally considered research/interoperability. Just don't DDOS them (that's why we respect rate limits).
