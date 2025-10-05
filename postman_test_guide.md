# 🚀 ScamShield AI - Postman Test Guide

## 📋 **Import Collection**
1. Open Postman
2. Click "Import" 
3. Select `postman_collection.json`
4. Collection will load with all endpoints

## 🌐 **Base URL**
```
https://submammary-correlatively-irma.ngrok-free.dev
```

## 📝 **Quick Test Commands**

### **1. Health Check**
```http
GET https://submammary-correlatively-irma.ngrok-free.dev/health
```
**Expected:** `{"ok": true}`

### **2. Root Page**
```http
GET https://submammary-correlatively-irma.ngrok-free.dev/
```
**Expected:** HTML welcome page

### **3. Twilio Voice (TwiML)**
```http
POST https://submammary-correlatively-irma.ngrok-free.dev/voice
```
**Expected:** XML TwiML response with Stream URL

### **4. Test Transcription**
```http
POST https://submammary-correlatively-irma.ngrok-free.dev/test_transcribe/
Content-Type: application/json

{
    "text": "This is the IRS calling about your tax debt. You need to pay immediately or face arrest."
}
```
**Expected:** JSON with transcript, risk_score, risk_band, prediction

### **5. Analyze Text**
```http
POST https://submammary-correlatively-irma.ngrok-free.dev/analyze/
Content-Type: application/json

{
    "text": "This is the IRS calling about your tax debt. You need to pay immediately or face arrest."
}
```
**Expected:** JSON with analysis details

### **6. Predict Risk**
```http
POST https://submammary-correlatively-irma.ngrok-free.dev/predict/
Content-Type: application/json

{
    "text": "This is the IRS calling about your tax debt. You need to pay immediately or face arrest."
}
```
**Expected:** JSON with prediction, risk_band, risk_score

### **7. Get Call History**
```http
GET https://submammary-correlatively-irma.ngrok-free.dev/api/calls
```
**Expected:** Array of call objects

### **8. Get Call Transcripts**
```http
GET https://submammary-correlatively-irma.ngrok-free.dev/api/calls/MZ86a38759ad0241b1b01e773378aa3a34/transcripts
```
**Expected:** Array of transcript objects

### **9. Get Risk Summary**
```http
GET https://submammary-correlatively-irma.ngrok-free.dev/api/risk-summary
```
**Expected:** JSON with summary statistics

### **10. Start Call Session**
```http
POST https://submammary-correlatively-irma.ngrok-free.dev/api/calls/MZ86a38759ad0241b1b01e773378aa3a34/start
Content-Type: application/json

{
    "stream_sid": "MZ86a38759ad0241b1b01e773378aa3a34"
}
```
**Expected:** JSON with success status

### **11. End Call Session**
```http
POST https://submammary-correlatively-irma.ngrok-free.dev/api/calls/MZ86a38759ad0241b1b01e773378aa3a34/end
Content-Type: application/json

{
    "final_risk_score": 0.85,
    "risk_band": "HIGH",
    "duration_seconds": 120.5
}
```
**Expected:** JSON with success status

### **12. Get Active Stream**
```http
GET https://submammary-correlatively-irma.ngrok-free.dev/active-stream
```
**Expected:** JSON with active stream info

## 🔌 **WebSocket Endpoints** (Use WebSocket client)

### **Twilio Media Stream**
```
wss://submammary-correlatively-irma.ngrok-free.dev/media
```

### **Frontend Notifications**
```
wss://submammary-correlatively-irma.ngrok-free.dev/notify
```

### **Browser Audio Bridge**
```
wss://submammary-correlatively-irma.ngrok-free.dev/browser/MZ86a38759ad0241b1b01e773378aa3a34
```

### **Test WebSocket**
```
wss://submammary-correlatively-irma.ngrok-free.dev/test
```

## 📊 **Test Data Examples**

### **High Risk Text**
```json
{
    "text": "This is the IRS calling about your tax debt. You need to pay immediately or face arrest."
}
```

### **Medium Risk Text**
```json
{
    "text": "Your bank account has been compromised. Please provide your PIN number immediately."
}
```

### **Low Risk Text**
```json
{
    "text": "Thank you for calling. This is a legitimate business call about your account."
}
```

## ✅ **Expected Responses**

### **Risk Bands**
- `LOW` - Risk score < 0.4
- `MEDIUM` - Risk score 0.4-0.7  
- `HIGH` - Risk score > 0.7

### **Predictions**
- `safe` - Legitimate call
- `suspicious` - Needs attention
- `scam` - High risk scam

## 🧪 **Testing Tips**
1. Start with health check to ensure server is running
2. Test transcription endpoints with different risk levels
3. Check database endpoints for call history
4. Use WebSocket clients for real-time testing
5. Monitor terminal for live transcription logs

## 📁 **Files Created**
- `postman_collection.json` - Complete Postman collection
- `postman_test_guide.md` - This guide
