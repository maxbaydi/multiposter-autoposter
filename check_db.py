# -*- coding: utf-8 -*-
from db_manager import DBManager
from datetime import datetime

# Создаем подключение к БД
db = DBManager('autoposter.db')

print("📊 Публикации за последний день:")
print("=" * 50)

# Получаем публикации за последний день
recent = db.get_recent_publications(days=1)
today = datetime.now().date().isoformat()

for row in recent:
    brand, topic, platform, published_at = row
    date_only = published_at[:10]
    if date_only == today:
        print(f"✅ {brand} - {topic} - {platform} - {published_at}")

print(f"\n📊 Всего публикаций сегодня: {len([r for r in recent if r[3][:10] == today])}")

print("\n📋 Все публикации за последние 3 дня:")
print("=" * 50)
all_recent = db.get_recent_publications(days=3)
for row in all_recent:
    brand, topic, platform, published_at = row
    print(f"{brand} - {topic} - {platform} - {published_at}") 