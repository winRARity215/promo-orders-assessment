# Promo Orders Assessment

Django проект для управления заказами с промокодами.

## Установка

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd src
python manage.py migrate
python manage.py runserver
```

## API

POST /api/orders/create/

```json
{
  "user_id": 1,
  "goods": [{"good_id": 1, "quantity": 2}],
  "promo_code": "SUMMER2025"
}
```

## Тесты

```bash
python manage.py test
```
