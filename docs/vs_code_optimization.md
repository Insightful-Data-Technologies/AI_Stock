# 🛠️ VS Code Tools Optimization Guide
# מדריך אופטימיזציה של כלי VS Code

## הבעיה הנוכחית
VS Code מציג אזהרה: "423 tools enabled. You may experience degraded tool calling above 128 tools"

## כלים חיוניים לפרויקט AI Stock (מומלץ להשאיר)

### 🔧 Core Development Tools (חיוני)
- Python Extension Pack (פיתון)
- GitHub Copilot (עזרה בקוד)
- Git integration (בקרת גרסאות)
- Terminal management
- File operations (יצירה/עריכת קבצים)
- Semantic search (חיפוש בקוד)

### 💼 Azure & AI Tools (חיוני לפרויקט שלך)
- Azure Tools
- Azure OpenAI integration
- Database management tools (SQL Server)
- Python environment management

### 📊 Data & Financial Tools (מומלץ)
- Jupyter Notebook support
- Python data science packages
- Database client tools

## כלים שאפשר להשבית זמנית

### 🚫 כלים שכנראה לא נצרכים לפרויקט הנוכחי:
- Docker/Container tools (אם לא משתמש)
- Kubernetes tools
- Mobile development tools
- C++/Java development tools
- Game development tools
- Web development tools (אם לא בונה web UI)

## המלצות לאופטימיזציה

1. **השבת הרחבות לא רלוונטיות:**
   - לך ל- Extensions (Ctrl+Shift+X)
   - השבת הרחבות שלא קשורות לפיתון/Azure/מניות

2. **הפעל רק כלים נחוצים:**
   - השאר רק כלים הקשורים לפרויקט הנוכחי
   - אפשר להפעיל מחדש בעתיד לפי הצורך

3. **ארגן Workspace Settings:**
   - צור הגדרות ספציפיות לפרויקט

## פעולות מיידיות מומלצות

1. השבת הרחבות לא נחוצות זמנית
2. הפעל מחדש את VS Code
3. בדוק שהכלים החיוניים עדיין פועלים
4. אם הבעיה נפתרה - מצוין!
5. אם עדיין יש בעיות - נמשיך לחקור

## הערות חשובות

- ⚠️ אל תמחק כלים של Azure AI - אלה חיוניים!
- ⚠️ אל תמחק כלים של Python/Git - בסיסיים!
- ✅ בטוח למחוק כלים של שפות אחרות שלא בשימוש
- ✅ בטוח למחוק כלים של frameworks שלא בשימוש

## מדד הצלחה
המטרה: לרדת מ-423 כלים ל-~100-150 כלים (תחת 200)