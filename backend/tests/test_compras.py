"""Compras: validación de stock y transacción."""


def test_compra_descuenta_stock(client, ana, db):
    r = client.post("/compras/", json={"items": [{"producto_id": 1, "cantidad": 2}]}, headers=ana)
    assert r.status_code == 201
    from app import models
    db.expire_all()
    assert db.get(models.Producto, 1).stock == 0


def test_stock_insuficiente_es_400_y_no_cambia_nada(client, ana, db):
    r = client.post("/compras/", json={"items": [{"producto_id": 1, "cantidad": 3}]}, headers=ana)
    assert r.status_code == 400
    from app import models
    db.expire_all()
    assert db.get(models.Producto, 1).stock == 2


def test_producto_inexistente_es_404(client, ana):
    assert client.post("/compras/", json={"items": [{"producto_id": 99, "cantidad": 1}]}, headers=ana).status_code == 404


def test_cantidad_invalida_es_422(client, ana):
    assert client.post("/compras/", json={"items": [{"producto_id": 1, "cantidad": 0}]}, headers=ana).status_code == 422
    assert client.post("/compras/", json={"items": []}, headers=ana).status_code == 422
