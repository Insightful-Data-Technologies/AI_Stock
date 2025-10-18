# 📝 מדריך עריכת האתר - מה אפשר לשנות

## 🎯 הקובץ הראשי לעריכה:
**`C:\AI_Stock\website\index.html`**

## 📝 מה אפשר לערוך וכיצד:

### **1. כותרת האתר (שורה 291):**
```html
<div class="logo">🚀 AI STOCK</div>
```
**שנה ל:** `🚀 השם שלך` או `📈 MONEY MAKER` וכו'

### **2. הכותרת הגדולה (שורה 292):**
```html
<h1 class="coming-soon">COMING SOON</h1>
```
**שנה ל:** `בקרוב` או `IN PROGRESS` או `LAUNCHING SOON`

### **3. התיאור (שורה 293):**
```html
<h2 class="subtitle">Advanced AI-Powered Stock Market Analysis Platform</h2>
```
**שנה ל:** הטקסט שלך, למשל:
- `פלטפורמת ניתוח מניות מתקדמת עם בינה מלאכותית`
- `המערכת החכמה ביותר לניתוח שוק ההון`

### **4. כתובת אימייל (שורה 330):**
```html
<a href="mailto:info@aizevinstocks.com" class="email-link">info@aizevinstocks.com</a>
```
**שנה ל:** האימייל שלך

### **5. התכונות (שורות 295-316):**
מצא את החלק:
```html
<div class="feature">
    <div class="feature-icon">🤖</div>
    <div class="feature-title">AI Analysis</div>
    <div class="feature-desc">Machine learning algorithms for market prediction</div>
</div>
```

**אפשר לשנות:**
- האייקון: 🤖 → 📊, 💎, ⚡, 🎯
- הכותרת: `AI Analysis` → `ניתוח חכם`
- התיאור: `Machine learning...` → הטקסט שלך

### **6. אחוז התקדמות (שורה ~325):**
```css
.progress-fill {
    width: 75%;  /* שנה את המספר הזה */
}
```

### **7. שינוי צבעים:**
בתחילת הקובץ, מצא:
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```
**שנה את הצבעים:** `#667eea` ו-`#764ba2` לצבעים אחרים

## 🛠️ איך לערוך:

### **דרך 1: VS Code (הכי קל)**
1. פתח VS Code
2. פתח את הקובץ: `C:\AI_Stock\website\index.html`
3. חפש (Ctrl+F) את הטקסט שרוצה לשנות
4. ערוך
5. שמור (Ctrl+S)

### **דרך 2: כל עורך טקסט**
- Notepad++
- Sublime Text
- אפילו Notepad רגיל

## 🚀 איך להעלות שינויים:

### **בטרמינל (PowerShell):**
```bash
cd C:\AI_Stock
git add .
git commit -m "עדכנתי את האתר"
git push origin main
```

### **תוצאה:**
תוך 2-3 דקות האתר יתעדכן ב:
- https://victorious-smoke-01f2b7f0f.3.azurestaticapps.net

## 💡 טיפים:
1. **תמיד גבה** לפני שינויים
2. **שמור בקידוד UTF-8** לתמיכה בעברית
3. **בדוק את האתר** אחרי העלאה
4. **אם משהו נשבר** - תוכל לחזור לגיבוי מהקבצים האחרים

## 🎨 דוגמאות לשינויים:

### **עברית:**
```html
<div class="logo">📈 מניות חכמות</div>
<h1 class="coming-soon">בקרוב</h1>
<h2 class="subtitle">פלטפורמת ניתוח מניות עם בינה מלאכותית</h2>
```

### **אנגלית מותאמת:**
```html
<div class="logo">💰 SMART MONEY</div>
<h1 class="coming-soon">LAUNCHING SOON</h1>
<h2 class="subtitle">The Ultimate AI Trading Platform</h2>
```

**הקובץ `index.html` הוא המקום המרכזי לכל השינויים! 🎯**